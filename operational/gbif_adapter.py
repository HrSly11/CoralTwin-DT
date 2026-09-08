"""Bounded, public GBIF occurrence ingestion without persistence side effects."""

from __future__ import annotations

import json
import math
import re
from collections import Counter
from dataclasses import dataclass
from datetime import date, datetime, timezone
from typing import Any, Callable, Mapping
from urllib.error import HTTPError
from urllib.parse import urlencode, urlsplit
from urllib.request import HTTPRedirectHandler, Request, build_opener

from .observations import CanonicalObservation, ObservationValidationError
from .stations import StationNotFoundError, get_station


BASE_URL = "https://api.gbif.org/v1"
SEARCH_URL = f"{BASE_URL}/occurrence/search"
SOURCE = "gbif"
_DATE = re.compile(r"^\d{4}-\d{2}-\d{2}$")


class GbifAdapterError(RuntimeError):
    """Raised when a GBIF response cannot be used safely and completely."""


@dataclass(frozen=True)
class GbifHttpResponse:
    status: int
    body: bytes | str | Mapping[str, Any]
    url: str | None = None


class _RejectRedirectHandler(HTTPRedirectHandler):
    """Reject redirects before urllib can issue a second request."""

    def redirect_request(self, req, fp, code, msg, headers, newurl):  # type: ignore[no-untyped-def]
        raise HTTPError(req.full_url, code, "GBIF redirects are not permitted", headers, fp)


@dataclass(frozen=True)
class GbifOccurrencePolicy:
    """Explicit inclusion, quality, and bounded pagination policy."""

    allowed_licenses: frozenset[str]
    allowed_basis_of_record: frozenset[str]
    blocking_issues: frozenset[str]
    max_coordinate_uncertainty_m: float
    page_size: int
    max_pages: int
    max_records: int

    def __post_init__(self) -> None:
        object.__setattr__(self, "allowed_licenses", _string_set(self.allowed_licenses, "allowed_licenses"))
        object.__setattr__(self, "allowed_basis_of_record", _string_set(self.allowed_basis_of_record, "allowed_basis_of_record"))
        object.__setattr__(self, "blocking_issues", _string_set(self.blocking_issues, "blocking_issues"))
        object.__setattr__(
            self, "max_coordinate_uncertainty_m", _finite(self.max_coordinate_uncertainty_m, "max_coordinate_uncertainty_m", nonnegative=True)
        )
        for field in ("page_size", "max_pages", "max_records"):
            value = getattr(self, field)
            if type(value) is not int or value < 1:
                raise ValueError(f"{field} must be a positive integer")
        if self.page_size > 300:
            raise ValueError("page_size must not exceed GBIF's 300-record limit")
        if self.max_records > 100_000 or self.page_size * self.max_pages > 100_000:
            raise ValueError("GBIF pagination window must not exceed 100000 records")


@dataclass(frozen=True)
class RejectedOccurrence:
    reason: str
    record_key: int | None

    def __post_init__(self) -> None:
        if not isinstance(self.reason, str) or not self.reason:
            raise ValueError("reason must be a non-empty string")
        if self.record_key is not None and (type(self.record_key) is not int or self.record_key < 1):
            raise ValueError("record_key must be a positive integer when supplied")

    def to_dict(self) -> dict[str, Any]:
        return {"reason": self.reason, "record_key": self.record_key}


@dataclass(frozen=True)
class GbifIngestionResult:
    observations: tuple[CanonicalObservation, ...]
    rejected: tuple[RejectedOccurrence, ...]
    pages_fetched: int
    reported_count: int
    end_of_records: bool

    def __post_init__(self) -> None:
        observations = tuple(self.observations)
        rejected = tuple(self.rejected)
        if any(not isinstance(item, CanonicalObservation) for item in observations):
            raise ValueError("observations must contain CanonicalObservation values")
        if any(not isinstance(item, RejectedOccurrence) for item in rejected):
            raise ValueError("rejected must contain RejectedOccurrence values")
        if type(self.pages_fetched) is not int or self.pages_fetched < 0:
            raise ValueError("pages_fetched must be a non-negative integer")
        if type(self.reported_count) is not int or self.reported_count < 0:
            raise ValueError("reported_count must be a non-negative integer")
        if not isinstance(self.end_of_records, bool):
            raise ValueError("end_of_records must be a boolean")
        object.__setattr__(self, "observations", observations)
        object.__setattr__(self, "rejected", rejected)

    @property
    def rejected_total(self) -> int:
        return len(self.rejected)

    @property
    def rejected_by_reason(self) -> tuple[tuple[str, int], ...]:
        return tuple(sorted(Counter(item.reason for item in self.rejected).items()))

    def to_dict(self) -> dict[str, Any]:
        return {
            "observations": [item.to_dict() for item in self.observations],
            "rejected": [item.to_dict() for item in self.rejected],
            "rejected_by_reason": [[reason, count] for reason, count in self.rejected_by_reason],
            "rejected_total": self.rejected_total,
            "pages_fetched": self.pages_fetched,
            "reported_count": self.reported_count,
            "end_of_records": self.end_of_records,
        }


Transport = Callable[[str, dict[str, str], float], GbifHttpResponse]


def _default_transport(url: str, headers: dict[str, str], timeout: float) -> GbifHttpResponse:
    _require_gbif_url(url, "request")
    request = Request(url, headers=headers)
    opener = build_opener(_RejectRedirectHandler())
    try:
        with opener.open(request, timeout=timeout) as response:  # nosec B310 - URL is validated above
            return GbifHttpResponse(int(response.status), response.read(), response.geturl())
    except HTTPError as error:
        return GbifHttpResponse(error.code, error.read(), error.url)


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _string(value: object, field: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{field} must be a non-empty string")
    return value.strip()


def _string_set(values: object, field: str) -> frozenset[str]:
    if isinstance(values, (str, bytes, Mapping)):
        raise ValueError(f"{field} must be a collection of strings")
    try:
        normalized = frozenset(_string(value, f"{field} item") for value in values)  # type: ignore[union-attr]
    except TypeError as error:
        raise ValueError(f"{field} must be an iterable") from error
    if not normalized:
        raise ValueError(f"{field} must not be empty")
    return normalized


def _finite(value: object, field: str, *, nonnegative: bool = False) -> float:
    if type(value) not in (int, float):
        raise ValueError(f"{field} must be numeric")
    result = float(value)
    if not math.isfinite(result) or (nonnegative and result < 0):
        raise ValueError(f"{field} must be finite" + (" and non-negative" if nonnegative else ""))
    return result


def _utc(value: datetime, field: str) -> datetime:
    if not isinstance(value, datetime) or value.tzinfo is None:
        raise ValueError(f"{field} must be timezone-aware")
    return value.astimezone(timezone.utc)


def _require_gbif_url(value: object, field: str) -> None:
    if not isinstance(value, str) or not value:
        raise GbifAdapterError(f"GBIF {field} URL must be a non-empty string")
    try:
        parsed = urlsplit(value)
        valid = (
            parsed.scheme == "https"
            and parsed.hostname == "api.gbif.org"
            and parsed.port in (None, 443)
            and parsed.username is None
            and parsed.password is None
            and parsed.path.startswith("/v1/occurrence/")
        )
    except ValueError as error:
        raise GbifAdapterError(f"GBIF {field} URL is invalid") from error
    if not valid:
        raise GbifAdapterError(f"GBIF {field} URL escaped the required HTTPS host")


class GbifOccurrenceAdapter:
    """Read public occurrence pages and emit auditable presence claims only."""

    def __init__(
        self,
        transport: Transport | None = None,
        *,
        clock: Callable[[], datetime] = _utc_now,
        contact: str,
        user_agent: str,
        timeout: float = 15.0,
    ) -> None:
        self._transport = transport or _default_transport
        self._clock = clock
        self._contact = _string(contact, "contact")
        self._user_agent = _string(user_agent, "user_agent")
        self._timeout = _finite(timeout, "timeout")
        if self._timeout <= 0:
            raise ValueError("timeout must be positive")

    def build_search_url(
        self, *, taxon_key: int, start_date: date, end_date: date, bbox: tuple[float, float, float, float], limit: int, offset: int
    ) -> str:
        west, south, east, north = bbox
        query = urlencode(
            (
                ("taxon_key", str(taxon_key)),
                ("eventDate", f"{start_date.isoformat()},{end_date.isoformat()}"),
                ("decimalLongitude", f"{west},{east}"),
                ("decimalLatitude", f"{south},{north}"),
                ("limit", str(limit)),
                ("offset", str(offset)),
            )
        )
        return f"{SEARCH_URL}?{query}"

    def fetch(
        self,
        *,
        station_id: str,
        bbox: tuple[float, float, float, float],
        start_date: date,
        end_date: date,
        taxon_key: int,
        policy: GbifOccurrencePolicy,
    ) -> GbifIngestionResult:
        station, normalized_bbox, start, end, normalized_taxon, normalized_policy = self._validate_request(
            station_id, bbox, start_date, end_date, taxon_key, policy
        )
        accessed_at = _utc(self._clock(), "clock result")
        observations: dict[int, CanonicalObservation] = {}
        rejected: list[RejectedOccurrence] = []
        offset = 0
        pages = 0
        reported_count = 0
        while True:
            remaining = min(normalized_policy.page_size, normalized_policy.max_records - offset, 100_000 - offset)
            if remaining < 1:
                raise GbifAdapterError("GBIF pagination exhausted configured record window")
            url = self.build_search_url(
                taxon_key=normalized_taxon, start_date=start, end_date=end, bbox=normalized_bbox, limit=remaining, offset=offset
            )
            payload = self._request(url)
            results, end_of_records, reported_count = self._page(payload, remaining)
            pages += 1
            for raw in results:
                item = self._to_observation(raw, station_id=station.station_id, station_latitude=station.latitude,
                                            station_longitude=station.longitude, bbox=normalized_bbox, start_date=start,
                                            end_date=end, accessed_at=accessed_at, policy=normalized_policy)
                if isinstance(item, RejectedOccurrence):
                    rejected.append(item)
                    continue
                key = int(item.logical_observation_id.split(":", 2)[1])
                previous = observations.get(key)
                if previous is not None:
                    if previous.content_hash != item.content_hash:
                        raise GbifAdapterError(f"conflicting GBIF key {key}")
                    continue
                observations[key] = item
            if end_of_records:
                return GbifIngestionResult(tuple(observations[key] for key in sorted(observations)), tuple(sorted(rejected, key=lambda item: (item.reason, item.record_key or -1))), pages, reported_count, True)
            if not results:
                raise GbifAdapterError("GBIF pagination reported more records but returned an empty page")
            offset += len(results)
            if pages >= normalized_policy.max_pages:
                raise GbifAdapterError("GBIF pagination exceeded configured max_pages")

    def _validate_request(
        self, station_id: str, bbox: object, start_date: object, end_date: object, taxon_key: object, policy: object
    ) -> tuple[Any, tuple[float, float, float, float], date, date, int, GbifOccurrencePolicy]:
        try:
            station = get_station(station_id)
        except StationNotFoundError as error:
            raise ValueError("station_id must identify a canonical station") from error
        try:
            west, south, east, north = tuple(bbox)  # type: ignore[arg-type]
        except (TypeError, ValueError) as error:
            raise ValueError("bbox must contain west, south, east, north") from error
        normalized = tuple(_finite(value, "bbox value") for value in (west, south, east, north))
        if not (-180 <= normalized[0] < normalized[2] <= 180 and -90 <= normalized[1] < normalized[3] <= 90):
            raise ValueError("bbox must be finite, ordered, and within longitude/latitude bounds")
        if not isinstance(start_date, date) or isinstance(start_date, datetime) or not isinstance(end_date, date) or isinstance(end_date, datetime):
            raise ValueError("start_date and end_date must be plain dates")
        if start_date > end_date:
            raise ValueError("start_date must not be after end_date")
        if type(taxon_key) is not int or taxon_key < 1:
            raise ValueError("taxon_key must be a positive integer")
        if not isinstance(policy, GbifOccurrencePolicy):
            raise ValueError("policy must be a GbifOccurrencePolicy")
        return station, normalized, start_date, end_date, taxon_key, policy

    def _request(self, url: str) -> Mapping[str, Any]:
        _require_gbif_url(url, "request")
        response = self._transport(url, {"Accept": "application/json", "User-Agent": f"{self._user_agent} ({self._contact})", "From": self._contact}, self._timeout)
        if not isinstance(response, GbifHttpResponse):
            raise GbifAdapterError("GBIF transport must return GbifHttpResponse")
        if not isinstance(response.url, str) or not response.url:
            raise GbifAdapterError("GBIF transport response must expose the final URL")
        _require_gbif_url(response.url, "transport response")
        if response.url != url:
            raise GbifAdapterError("GBIF transport response final URL differs from the requested URL")
        if type(response.status) is not int:
            raise GbifAdapterError("GBIF transport response status must be an integer")
        if response.status != 200:
            raise GbifAdapterError(f"GBIF HTTP {response.status}")
        body = response.body
        if isinstance(body, Mapping):
            return body
        try:
            decoded = body.decode("utf-8") if isinstance(body, bytes) else body
            payload = json.loads(decoded)
        except (UnicodeDecodeError, json.JSONDecodeError, TypeError) as error:
            raise GbifAdapterError("GBIF response is not valid JSON") from error
        if not isinstance(payload, Mapping):
            raise GbifAdapterError("GBIF JSON response must be an object")
        return payload

    @staticmethod
    def _page(payload: Mapping[str, Any], limit: int) -> tuple[list[Mapping[str, Any]], bool, int]:
        results, end_of_records, count = payload.get("results"), payload.get("endOfRecords"), payload.get("count")
        if not isinstance(results, list) or not isinstance(end_of_records, bool) or type(count) is not int or count < 0:
            raise GbifAdapterError("GBIF search response schema is invalid")
        if len(results) > limit or any(not isinstance(item, Mapping) for item in results):
            raise GbifAdapterError("GBIF search response results are invalid")
        return results, end_of_records, count

    @staticmethod
    def _to_observation(
        raw: Mapping[str, Any], *, station_id: str, station_latitude: float, station_longitude: float,
        bbox: tuple[float, float, float, float], start_date: date, end_date: date, accessed_at: datetime,
        policy: GbifOccurrencePolicy,
    ) -> CanonicalObservation | RejectedOccurrence:
        key = raw.get("key")
        record_key = key if type(key) is int and key > 0 else None
        try:
            if record_key is None:
                raise ValueError("invalid_schema")
            dataset_id = _string(raw.get("datasetKey"), "datasetKey")
            scientific_name = _string(raw.get("scientificName"), "scientificName")
            taxon_key = raw.get("taxonKey")
            if type(taxon_key) is not int or taxon_key < 1:
                raise ValueError("invalid_schema")
            basis = _string(raw.get("basisOfRecord"), "basisOfRecord")
            license_name = _string(raw.get("license"), "license")
            issues_raw = raw.get("issues")
            if not isinstance(issues_raw, list):
                raise ValueError("invalid_schema")
            issues = tuple(_string(issue, "issue") for issue in issues_raw)
            observed_at = _event_date(raw.get("eventDate"))
            latitude, longitude = _coordinate_pair(raw, bbox)
            uncertainty = _finite(raw.get("coordinateUncertaintyInMeters"), "coordinateUncertaintyInMeters", nonnegative=True)
        except ValueError as error:
            return RejectedOccurrence(str(error), record_key)
        if observed_at.date() < start_date or observed_at.date() > end_date:
            return RejectedOccurrence("event_date_outside_window", record_key)
        if license_name not in policy.allowed_licenses:
            return RejectedOccurrence("license_not_allowed", record_key)
        if basis not in policy.allowed_basis_of_record:
            return RejectedOccurrence("basis_not_allowed", record_key)
        if set(issues).intersection(policy.blocking_issues):
            return RejectedOccurrence("blocking_issue", record_key)
        if uncertainty > policy.max_coordinate_uncertainty_m:
            return RejectedOccurrence("coordinate_uncertainty_exceeds_policy", record_key)
        flags = tuple(sorted({
            *(f"issue:{issue}" for issue in issues),
            f"basis_of_record:{basis}",
            f"dataset:{dataset_id}",
            f"license:{license_name}",
            f"scientific_name:{scientific_name}",
            f"taxon_key:{taxon_key}",
        }))
        try:
            return CanonicalObservation(
                station_id=station_id, metric="biodiversity_occurrence_presence", observed_at=observed_at, unit="count", value=1.0,
                provenance_kind="observed", logical_observation_id=f"gbif:{record_key}:{station_id}", provider=SOURCE,
                dataset_id=dataset_id, accessed_at=accessed_at, request_url=f"{BASE_URL}/occurrence/{record_key}",
                requested_latitude=station_latitude, requested_longitude=station_longitude,
                returned_latitude=latitude, returned_longitude=longitude, quality_flags=flags, uncertainty=uncertainty,
            )
        except ObservationValidationError as error:
            return RejectedOccurrence(f"canonical_validation:{error}", record_key)


def _event_date(value: object) -> datetime:
    if not isinstance(value, str) or "/" in value:
        raise ValueError("invalid_event_date")
    if _DATE.fullmatch(value):
        try:
            return datetime.combine(date.fromisoformat(value), datetime.min.time(), tzinfo=timezone.utc)
        except ValueError as error:
            raise ValueError("invalid_event_date") from error
    if "T" not in value:
        raise ValueError("invalid_event_date")
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as error:
        raise ValueError("invalid_event_date") from error
    if parsed.tzinfo is None:
        raise ValueError("invalid_event_date")
    return parsed.astimezone(timezone.utc)


def _coordinate_pair(raw: Mapping[str, Any], bbox: tuple[float, float, float, float]) -> tuple[float, float]:
    latitude = _finite(raw.get("decimalLatitude"), "invalid_coordinates")
    longitude = _finite(raw.get("decimalLongitude"), "invalid_coordinates")
    west, south, east, north = bbox
    if not south <= latitude <= north or not west <= longitude <= east:
        raise ValueError("coordinate_outside_bbox")
    return latitude, longitude


__all__ = [
    "BASE_URL", "GbifAdapterError", "GbifHttpResponse", "GbifIngestionResult", "GbifOccurrenceAdapter",
    "GbifOccurrencePolicy", "RejectedOccurrence", "SEARCH_URL", "SOURCE",
]
