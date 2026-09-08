"""Pure in-memory importer for auditable human field observations."""

from __future__ import annotations

import csv
import hashlib
import io
import json
import math
import re
import unicodedata
from dataclasses import dataclass
from datetime import date, datetime, timezone
from typing import Any, Callable, Iterable, Mapping
from urllib.parse import urlsplit

from .observations import CanonicalObservation
from .stations import CANONICAL_STATIONS, StationNotFoundError, get_station


UTC = timezone.utc
_PSEUDONYM = re.compile(r"^(?:observer|obs|anon)-[A-Za-z0-9][A-Za-z0-9._-]{1,62}$")


class _FieldProblem(ValueError):
    def __init__(self, reason: str) -> None:
        super().__init__(reason)
        self.reason = reason


def _text(value: object, field: str) -> str:
    if not isinstance(value, str) or not value.strip() or any(ord(char) < 32 for char in value):
        raise _FieldProblem(f"invalid_{field}")
    return value.strip()


def _number(value: object, field: str, *, lower: float | None = None, upper: float | None = None) -> float:
    if isinstance(value, bool):
        raise _FieldProblem(f"invalid_{field}")
    try:
        number = float(value)  # CSV fields are textual at this boundary.
    except (TypeError, ValueError) as error:
        raise _FieldProblem(f"invalid_{field}") from error
    if not math.isfinite(number) or lower is not None and number < lower or upper is not None and number > upper:
        raise _FieldProblem(f"invalid_{field}")
    return number


def _positive_int(value: object, field: str) -> int:
    if isinstance(value, bool):
        raise _FieldProblem(f"invalid_{field}")
    if isinstance(value, str):
        if not value.isdecimal():
            raise _FieldProblem(f"invalid_{field}")
        number = int(value)
    elif type(value) is int:
        number = value
    else:
        raise _FieldProblem(f"invalid_{field}")
    if number < 1:
        raise _FieldProblem(f"invalid_{field}")
    return number


def _string_set(value: object, field: str) -> frozenset[str]:
    if isinstance(value, str | bytes) or not isinstance(value, Iterable):
        raise ValueError(f"{field} must be a non-string iterable")
    normalized: set[str] = set()
    for item in value:
        if not isinstance(item, str) or not item.strip() or any(ord(char) < 32 for char in item):
            raise ValueError(f"{field} items must be non-empty strings")
        normalized.add(item.strip())
    if not normalized:
        raise ValueError(f"{field} must not be empty")
    return frozenset(normalized)


def _marker_text(value: str) -> str:
    """Compare generated-data markers independent of Unicode presentation."""

    return "".join(character for character in unicodedata.normalize("NFKC", value).casefold() if character.isalnum())


def _policy_number(value: object, field: str, *, minimum: float) -> float:
    if isinstance(value, bool) or not isinstance(value, int | float):
        raise ValueError(f"{field} must be a finite number")
    number = float(value)
    if not math.isfinite(number) or number < minimum:
        raise ValueError(f"{field} is outside its valid range")
    return number


def _policy_positive_int(value: object, field: str) -> int:
    if type(value) is not int or value < 1:
        raise ValueError(f"{field} must be a positive integer")
    return value


def _utc_now(clock: Callable[[], datetime]) -> datetime:
    now = clock()
    if not isinstance(now, datetime) or now.tzinfo is None or now.utcoffset() is None:
        raise ValueError("clock must return a UTC-aware datetime")
    return now.astimezone(UTC)


def _haversine_m(first_lat: float, first_lon: float, second_lat: float, second_lon: float) -> float:
    radians = math.pi / 180.0
    latitude_delta = (second_lat - first_lat) * radians
    longitude_delta = (second_lon - first_lon) * radians
    a = math.sin(latitude_delta / 2) ** 2 + math.cos(first_lat * radians) * math.cos(second_lat * radians) * math.sin(longitude_delta / 2) ** 2
    return 6_371_000.0 * 2.0 * math.atan2(math.sqrt(a), math.sqrt(1.0 - a))


def _stable_id(*parts: str) -> str:
    payload = "\x1f".join(parts).encode("utf-8")
    return "field:" + hashlib.sha256(payload).hexdigest()


@dataclass(frozen=True)
class FieldImportPolicy:
    """All scientific inclusion rules are explicit at the import boundary."""

    max_station_distance_m: float
    cover_sum_tolerance_pct: float
    allowed_licenses: frozenset[str]
    allowed_consent_codes: frozenset[str]
    allowed_qc_flags: frozenset[str]
    forbidden_generated_markers: frozenset[str]
    allow_day_precision: bool
    max_input_bytes: int
    max_rows: int

    def __post_init__(self) -> None:
        object.__setattr__(self, "max_station_distance_m", _policy_number(self.max_station_distance_m, "max_station_distance_m", minimum=0.000001))
        object.__setattr__(self, "cover_sum_tolerance_pct", _policy_number(self.cover_sum_tolerance_pct, "cover_sum_tolerance_pct", minimum=0.0))
        for name in ("allowed_licenses", "allowed_consent_codes", "allowed_qc_flags", "forbidden_generated_markers"):
            values = _string_set(getattr(self, name), name)
            if name == "forbidden_generated_markers":
                values = frozenset(_marker_text(item) for item in values)
                if "" in values:
                    raise ValueError("forbidden_generated_markers must contain visible characters")
            object.__setattr__(self, name, values)
        if type(self.allow_day_precision) is not bool:
            raise ValueError("allow_day_precision must be a boolean")
        object.__setattr__(self, "max_input_bytes", _policy_positive_int(self.max_input_bytes, "max_input_bytes"))
        object.__setattr__(self, "max_rows", _policy_positive_int(self.max_rows, "max_rows"))


@dataclass(frozen=True)
class RejectedFieldRecord:
    row_index: int
    reason: str
    record_id: str | None

    def __post_init__(self) -> None:
        if type(self.row_index) is not int or self.row_index < 0 or not isinstance(self.reason, str) or not self.reason:
            raise ValueError("invalid field rejection")
        if self.record_id is not None and (not isinstance(self.record_id, str) or not self.record_id):
            raise ValueError("invalid rejected record_id")


@dataclass(frozen=True)
class FieldImportResult:
    candidates: tuple[CanonicalObservation, ...]
    rejected: tuple[RejectedFieldRecord, ...]
    ready_for_persistence: bool

    def __post_init__(self) -> None:
        candidates, rejected = tuple(self.candidates), tuple(self.rejected)
        if any(not isinstance(candidate, CanonicalObservation) for candidate in candidates) or any(not isinstance(item, RejectedFieldRecord) for item in rejected):
            raise ValueError("field import result is invalid")
        if type(self.ready_for_persistence) is not bool or self.ready_for_persistence != (not rejected):
            raise ValueError("field import readiness must match rejections")
        if rejected and candidates:
            raise ValueError("rejected field imports must not expose partial candidates")
        object.__setattr__(self, "candidates", candidates)
        object.__setattr__(self, "rejected", tuple(sorted(rejected, key=lambda item: (item.row_index, item.reason, item.record_id or ""))))


@dataclass(frozen=True)
class _RawCandidate:
    observation: CanonicalObservation
    row_index: int
    record_id: str
    record_version: int
    survey_id: str
    taxon_id: str | None
    survey_complete: bool | None
    fingerprint: str


class FieldObservationImporter:
    """Validate field records only; callers decide whether to save an all-ready batch."""

    def __init__(self, *, clock: Callable[[], datetime]) -> None:
        if not callable(clock):
            raise ValueError("clock must be callable")
        self._clock = clock

    def import_csv(self, source: str | bytes, *, policy: FieldImportPolicy) -> FieldImportResult:
        if not isinstance(source, str | bytes):
            raise ValueError("CSV source must be text or bytes")
        if not isinstance(policy, FieldImportPolicy):
            raise ValueError("policy must be a FieldImportPolicy")
        try:
            encoded = source if isinstance(source, bytes) else source.encode("utf-8")
            if len(encoded) > policy.max_input_bytes:
                raise _FieldProblem("max_input_bytes_exceeded")
            text = encoded.decode("utf-8")
            reader = csv.reader(io.StringIO(text))
            header = next(reader, None)
            if not header or any(not _valid_header(name) for name in header) or len(set(header)) != len(header):
                raise _FieldProblem("invalid_csv_header")
            rows: list[dict[str, object]] = []
            for values in reader:
                if len(rows) >= policy.max_rows:
                    raise _FieldProblem("max_rows_exceeded")
                if len(values) != len(header):
                    raise _FieldProblem("invalid_csv")
                rows.append(dict(zip(header, values)))
        except (UnicodeDecodeError, UnicodeEncodeError, csv.Error, _FieldProblem) as error:
            reason = error.reason if isinstance(error, _FieldProblem) else "invalid_csv"
            return FieldImportResult((), (RejectedFieldRecord(0, reason, None),), False)
        return self.import_records(rows, policy=policy)

    def import_records(self, records: Iterable[Mapping[str, object]], *, policy: FieldImportPolicy) -> FieldImportResult:
        if not isinstance(policy, FieldImportPolicy):
            raise ValueError("policy must be a FieldImportPolicy")
        if isinstance(records, str | bytes) or not isinstance(records, Iterable):
            raise ValueError("records must be an iterable of JSON-object mappings")
        accessed_at = _utc_now(self._clock)
        try:
            iterator = iter(records)
        except TypeError as error:
            raise ValueError("records must be an iterable of JSON-object mappings") from error
        raw_candidates: list[_RawCandidate] = []
        rejected: list[RejectedFieldRecord] = []
        for index in range(policy.max_rows + 1):
            try:
                raw = next(iterator)
            except StopIteration:
                break
            except Exception:
                return FieldImportResult((), (RejectedFieldRecord(index, "invalid_records", None),), False)
            if index == policy.max_rows:
                return FieldImportResult((), (RejectedFieldRecord(index, "max_rows_exceeded", None),), False)
            record_id = raw.get("record_id") if isinstance(raw, Mapping) and isinstance(raw.get("record_id"), str) and raw.get("record_id") else None
            if not isinstance(raw, Mapping):
                rejected.append(RejectedFieldRecord(index, "invalid_record", record_id))
                continue
            try:
                raw_candidates.append(self._row(raw, index=index, policy=policy, accessed_at=accessed_at))
            except _FieldProblem as error:
                rejected.append(RejectedFieldRecord(index, error.reason, record_id))
        if rejected:
            return FieldImportResult((), tuple(rejected), False)
        try:
            selected = self._resolve_revisions(raw_candidates)
            self._validate_cover_sums(selected, policy)
            all_candidates = [item.observation for item in selected]
            all_candidates.extend(self._derive(selected))
        except _FieldProblem as error:
            return FieldImportResult((), (RejectedFieldRecord(0, error.reason, None),), False)
        return FieldImportResult(tuple(sorted(all_candidates, key=lambda item: item.logical_observation_id)), (), True)

    def _row(self, raw: Mapping[str, object], *, index: int, policy: FieldImportPolicy, accessed_at: datetime) -> _RawCandidate:
        kind = _text(raw.get("dataset_kind"), "dataset_kind")
        dataset_id = _text(raw.get("dataset_id"), "dataset_id")
        record_id = _text(raw.get("record_id"), "record_id")
        survey_id = _text(raw.get("survey_id"), "survey_id")
        method = _text(raw.get("method"), "method")
        organization = _text(raw.get("organization"), "organization")
        source_url = _source_url(raw.get("source_url"))
        haystack = _marker_text(" ".join((kind, dataset_id, source_url, organization, method)))
        if any(marker in haystack for marker in policy.forbidden_generated_markers):
            raise _FieldProblem("forbidden_generated_marker")
        if kind != "field_observed":
            raise _FieldProblem("invalid_dataset_kind")
        record_version = _positive_int(raw.get("record_version"), "record_version")
        observed_at = _observed_at(raw.get("observed_at"), raw.get("time_precision"), policy)
        station_id, latitude, longitude = _station(raw, policy)
        protocol = _text(raw.get("protocol"), "protocol")
        observer_id = _text(raw.get("observer_id"), "observer_id")
        if not _PSEUDONYM.fullmatch(observer_id):
            raise _FieldProblem("invalid_observer_id")
        measurement_type = _text(raw.get("measurement_type"), "measurement_type")
        unit = _text(raw.get("unit"), "unit")
        value = _number(raw.get("value"), "value")
        uncertainty = _number(raw.get("uncertainty"), "uncertainty", lower=0.0)
        sample_size = _positive_int(raw.get("sample_size"), "sample_size")
        license_name = _text(raw.get("license"), "license")
        consent = _text(raw.get("consent"), "consent")
        flags = _qc_flags(raw.get("qc_flags"), policy)
        if license_name not in policy.allowed_licenses:
            raise _FieldProblem("unallowed_license")
        if consent not in policy.allowed_consent_codes:
            raise _FieldProblem("unallowed_consent")
        taxon_id, survey_complete = _measurement(raw, measurement_type, unit, value)
        logical_id = _stable_id(dataset_id, record_id, measurement_type, taxon_id or "")
        quality_flags = tuple(sorted((
            f"method:{method}", f"protocol:{protocol}", f"observer:{observer_id}", f"organization:{organization}",
            f"license:{license_name}", f"consent:{consent}", f"sample_size:{sample_size}", f"record_version:{record_version}",
            *(f"qc:{flag}" for flag in flags),
        )))
        observation = CanonicalObservation(
            station_id=station_id, metric=measurement_type, observed_at=observed_at, unit=unit, value=value,
            provenance_kind="observed", logical_observation_id=logical_id, provider=organization, dataset_id=dataset_id,
            accessed_at=accessed_at, request_url=source_url, requested_latitude=get_station(station_id).latitude,
            requested_longitude=get_station(station_id).longitude, returned_latitude=latitude, returned_longitude=longitude,
            quality_flags=quality_flags, uncertainty=uncertainty,
        )
        signature = json.dumps({key: value for key, value in observation.to_dict().items() if key not in {"identity", "accessed_at", "quality_flags"}}, sort_keys=True, separators=(",", ":"), allow_nan=False)
        signature += "|" + "|".join(flag for flag in quality_flags if not flag.startswith("record_version:"))
        return _RawCandidate(observation, index, record_id, record_version, survey_id, taxon_id, survey_complete, signature)

    @staticmethod
    def _resolve_revisions(candidates: list[_RawCandidate]) -> tuple[_RawCandidate, ...]:
        by_record: dict[tuple[str, str], _RawCandidate] = {}
        for candidate in candidates:
            key = (candidate.observation.dataset_id or "", candidate.record_id)
            prior = by_record.get(key)
            if prior is None:
                by_record[key] = candidate
                continue
            old_axis = (prior.observation.station_id, prior.observation.metric, prior.observation.observed_at, prior.taxon_id)
            new_axis = (candidate.observation.station_id, candidate.observation.metric, candidate.observation.observed_at, candidate.taxon_id)
            if old_axis != new_axis:
                raise _FieldProblem("correction_axis_changed")
            if candidate.record_version == prior.record_version:
                if candidate.fingerprint != prior.fingerprint:
                    raise _FieldProblem("conflicting_record_version")
                continue
            later, earlier = (candidate, prior) if candidate.record_version > prior.record_version else (prior, candidate)
            by_record[key] = later
        return tuple(by_record[key] for key in sorted(by_record))

    @staticmethod
    def _derive(candidates: tuple[_RawCandidate, ...]) -> tuple[CanonicalObservation, ...]:
        groups: dict[tuple[str, str], list[_RawCandidate]] = {}
        for candidate in candidates:
            if candidate.taxon_id is not None:
                groups.setdefault((candidate.observation.dataset_id or "", candidate.survey_id), []).append(candidate)
        derived: list[CanonicalObservation] = []
        for (dataset_id, survey_id), group in sorted(groups.items()):
            if not all(item.survey_complete is True for item in group):
                continue
            axis = {(item.observation.station_id, item.observation.observed_at) for item in group}
            if len(axis) != 1:
                raise _FieldProblem("survey_axis_mismatch")
            if len({item.taxon_id for item in group}) != len(group):
                raise _FieldProblem("duplicate_taxon_in_survey")
            total = sum(item.observation.value for item in group)
            if total <= 0:
                raise _FieldProblem("zero_total_abundance")
            station_id, observed_at = next(iter(axis))
            richness = float(sum(item.observation.value > 0 for item in group))
            shannon = -sum((item.observation.value / total) * math.log(item.observation.value / total) for item in group if item.observation.value > 0)
            lineage = tuple({"logical_observation_id": item.observation.logical_observation_id, "record_version": item.record_version} for item in sorted(group, key=lambda item: item.observation.logical_observation_id))
            for metric, unit, value, method in (
                ("species_richness", "count", richness, "field-taxonomy-richness-v1"),
                ("shannon_diversity_h", "dimensionless", shannon, "field-taxonomy-shannon-v1"),
            ):
                derived.append(CanonicalObservation(
                    station_id=station_id, metric=metric, observed_at=observed_at, unit=unit, value=value,
                    provenance_kind="derived", logical_observation_id=_stable_id(dataset_id, survey_id, metric),
                    derivation_method=method, input_lineage=lineage,
                ))
        return tuple(derived)

    @staticmethod
    def _validate_cover_sums(candidates: tuple[_RawCandidate, ...], policy: FieldImportPolicy) -> None:
        """Check only paired cover claims from the same auditable survey."""

        covers: dict[tuple[str, str], dict[str, float]] = {}
        for candidate in candidates:
            metric = candidate.observation.metric
            if metric in {"coral_cover_pct", "macroalgae_cover_pct"}:
                bucket = covers.setdefault((candidate.observation.dataset_id or "", candidate.survey_id), {})
                if metric in bucket:
                    raise _FieldProblem("duplicate_cover_measurement")
                bucket[metric] = candidate.observation.value
        for values in covers.values():
            if values.get("coral_cover_pct", 0.0) + values.get("macroalgae_cover_pct", 0.0) > 100.0 + policy.cover_sum_tolerance_pct:
                raise _FieldProblem("cover_sum_exceeds_limit")


def _source_url(value: object) -> str:
    url = _text(value, "source_url")
    if "?" in url or "#" in url:
        raise _FieldProblem("invalid_source_url")
    try:
        parsed = urlsplit(url)
        hostname, _port = parsed.hostname, parsed.port
    except (ValueError, UnicodeError):
        raise _FieldProblem("invalid_source_url") from None
    if parsed.scheme != "https" or not parsed.netloc or not hostname or parsed.username or parsed.password:
        raise _FieldProblem("invalid_source_url")
    return url


def _valid_header(value: object) -> bool:
    if not isinstance(value, str):
        return False
    normalized = unicodedata.normalize("NFKC", value)
    return value == normalized and bool(re.fullmatch(r"[a-z][a-z0-9_]*", value))


def _observed_at(value: object, precision: object, policy: FieldImportPolicy) -> datetime:
    precision_text = _text(precision, "time_precision")
    text = _text(value, "observed_at")
    if precision_text == "day":
        if not policy.allow_day_precision:
            raise _FieldProblem("day_precision_not_allowed")
        try:
            if len(text) != 10:
                raise ValueError
            return datetime.combine(date.fromisoformat(text), datetime.min.time(), UTC)
        except ValueError as error:
            raise _FieldProblem("invalid_observed_at") from error
    if precision_text != "instant" or "T" not in text:
        raise _FieldProblem("invalid_observed_at")
    try:
        parsed = datetime.fromisoformat(text.replace("Z", "+00:00"))
    except ValueError as error:
        raise _FieldProblem("invalid_observed_at") from error
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        raise _FieldProblem("invalid_observed_at")
    return parsed.astimezone(UTC)


def _station(raw: Mapping[str, object], policy: FieldImportPolicy) -> tuple[str, float, float]:
    raw_station = raw.get("station_id")
    if raw_station is not None and not isinstance(raw_station, str):
        raise _FieldProblem("invalid_station")
    if isinstance(raw_station, str) and raw_station != raw_station.strip():
        raise _FieldProblem("invalid_station")
    station_id = raw_station if isinstance(raw_station, str) else ""
    latitude_raw, longitude_raw = raw.get("latitude"), raw.get("longitude")
    coordinates_supplied = latitude_raw not in (None, "") or longitude_raw not in (None, "")
    if not station_id and not coordinates_supplied:
        raise _FieldProblem("missing_station")
    station = None
    if station_id:
        try:
            station = get_station(station_id)
        except StationNotFoundError as error:
            raise _FieldProblem("invalid_station") from error
    if not coordinates_supplied:
        assert station is not None
        return station.station_id, station.latitude, station.longitude
    if latitude_raw in (None, "") or longitude_raw in (None, ""):
        raise _FieldProblem("invalid_coordinates")
    latitude, longitude = _number(latitude_raw, "coordinates", lower=-90.0, upper=90.0), _number(longitude_raw, "coordinates", lower=-180.0, upper=180.0)
    matches = [candidate for candidate in CANONICAL_STATIONS if _haversine_m(latitude, longitude, candidate.latitude, candidate.longitude) <= policy.max_station_distance_m]
    if station is not None:
        if _haversine_m(latitude, longitude, station.latitude, station.longitude) > policy.max_station_distance_m:
            raise _FieldProblem("station_coordinates_mismatch")
        return station.station_id, latitude, longitude
    if len(matches) != 1:
        raise _FieldProblem("ambiguous_station_coordinates" if matches else "station_not_within_tolerance")
    return matches[0].station_id, latitude, longitude


def _qc_flags(value: object, policy: FieldImportPolicy) -> tuple[str, ...]:
    if isinstance(value, str):
        try:
            value = json.loads(value)
        except json.JSONDecodeError as error:
            raise _FieldProblem("invalid_qc_flags") from error
    if isinstance(value, str | bytes) or not isinstance(value, Iterable):
        raise _FieldProblem("invalid_qc_flags")
    flags = tuple(sorted({_text(item, "qc_flags") for item in value}))
    if not flags or any(flag not in policy.allowed_qc_flags for flag in flags):
        raise _FieldProblem("invalid_qc_flags")
    return flags


def _measurement(raw: Mapping[str, object], measurement_type: str, unit: str, value: float) -> tuple[str | None, bool | None]:
    if measurement_type in {"coral_cover_pct", "macroalgae_cover_pct"}:
        if unit != "percent" or not 0.0 <= value <= 100.0:
            raise _FieldProblem("invalid_measurement")
        return None, None
    if measurement_type != "taxon_abundance" or unit != "count" or value < 0:
        raise _FieldProblem("invalid_measurement")
    if not value.is_integer():
        raise _FieldProblem("invalid_measurement")
    taxon_id = _text(raw.get("taxon_id"), "taxon_id")
    complete = raw.get("survey_complete")
    if type(complete) is not bool:
        raise _FieldProblem("invalid_survey_complete")
    return taxon_id, complete
