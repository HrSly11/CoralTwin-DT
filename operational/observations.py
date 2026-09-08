"""Validated, immutable evidence records for operational twin observations."""

from __future__ import annotations

import hashlib
import json
import math
import re
from dataclasses import dataclass
from datetime import datetime, timezone
from types import MappingProxyType
from typing import Any, Iterable, Mapping


class ObservationValidationError(ValueError):
    """Raised when an observation cannot make a scientifically auditable claim."""


PROVENANCE_KINDS = frozenset({"observed", "derived", "simulated"})
_LOGICAL_OBSERVATION_ID = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:-]{2,191}$")


def _timestamp(value: datetime, field: str) -> datetime:
    if not isinstance(value, datetime):
        raise ObservationValidationError(f"{field} must be a datetime")
    return (value if value.tzinfo else value.replace(tzinfo=timezone.utc)).astimezone(timezone.utc)


def _nonempty(value: str | None, field: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ObservationValidationError(f"{field} must be a non-empty string")
    return value.strip()


def _finite(value: float | int | None, field: str) -> float:
    try:
        result = float(value)  # type: ignore[arg-type]
    except (TypeError, ValueError) as error:
        raise ObservationValidationError(f"{field} must be numeric") from error
    if not math.isfinite(result):
        raise ObservationValidationError(f"{field} must be finite")
    return result


def _canonical_json(value: Any, field: str) -> str:
    try:
        return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False)
    except (TypeError, ValueError) as error:
        raise ObservationValidationError(f"{field} must be JSON-safe") from error


def _freeze_json(value: Any) -> Any:
    if isinstance(value, Mapping):
        return MappingProxyType({key: _freeze_json(item) for key, item in value.items()})
    if isinstance(value, list | tuple):
        return tuple(_freeze_json(item) for item in value)
    return value


def _thaw_json(value: Any) -> Any:
    if isinstance(value, Mapping):
        return {key: _thaw_json(item) for key, item in value.items()}
    if isinstance(value, tuple):
        return [_thaw_json(item) for item in value]
    return value


def _json_values(values: Iterable[Any], field: str) -> tuple[Any, ...]:
    try:
        normalized = tuple(_freeze_json(json.loads(_canonical_json(value, field))) for value in values)
    except TypeError as error:
        raise ObservationValidationError(f"{field} must be an iterable") from error
    return normalized


@dataclass(frozen=True)
class CanonicalObservation:
    """One explicit observation claim with enough metadata to audit its origin."""

    station_id: str
    metric: str
    observed_at: datetime
    unit: str
    value: float
    provenance_kind: str
    logical_observation_id: str | None = None
    provider: str | None = None
    dataset_id: str | None = None
    accessed_at: datetime | None = None
    request_url: str | None = None
    asset_id: str | None = None
    asset_href: str | None = None
    requested_latitude: float | None = None
    requested_longitude: float | None = None
    returned_latitude: float | None = None
    returned_longitude: float | None = None
    quality_flags: tuple[str, ...] = ()
    uncertainty: float | None = None
    derivation_method: str | None = None
    input_lineage: tuple[Any, ...] = ()
    model_version: str | None = None
    scenario_id: str | None = None

    def __post_init__(self) -> None:
        object.__setattr__(self, "station_id", _nonempty(self.station_id, "station_id"))
        object.__setattr__(self, "metric", _nonempty(self.metric, "metric"))
        object.__setattr__(self, "unit", _nonempty(self.unit, "unit"))
        object.__setattr__(self, "observed_at", _timestamp(self.observed_at, "observed_at"))
        object.__setattr__(self, "value", _finite(self.value, "value"))
        logical_id = _nonempty(self.logical_observation_id, "logical_observation_id")
        if not _LOGICAL_OBSERVATION_ID.fullmatch(logical_id):
            raise ObservationValidationError(
                "logical_observation_id must use 3-192 URL-safe letters, digits, dots, colons, underscores, or hyphens"
            )
        object.__setattr__(self, "logical_observation_id", logical_id)
        if self.provenance_kind not in PROVENANCE_KINDS:
            raise ObservationValidationError("provenance_kind must be observed, derived, or simulated")
        for field in ("provider", "dataset_id", "request_url", "asset_id", "asset_href", "derivation_method", "model_version", "scenario_id"):
            value = getattr(self, field)
            if value is not None:
                object.__setattr__(self, field, _nonempty(value, field))
        if self.accessed_at is not None:
            object.__setattr__(self, "accessed_at", _timestamp(self.accessed_at, "accessed_at"))
        for field in ("requested_latitude", "requested_longitude", "returned_latitude", "returned_longitude"):
            value = getattr(self, field)
            if value is not None:
                object.__setattr__(self, field, _finite(value, field))
        flags = tuple(_nonempty(flag, "quality_flags item") for flag in self.quality_flags)
        object.__setattr__(self, "quality_flags", flags)
        if self.uncertainty is not None:
            uncertainty = _finite(self.uncertainty, "uncertainty")
            if uncertainty < 0:
                raise ObservationValidationError("uncertainty must be non-negative")
            object.__setattr__(self, "uncertainty", uncertainty)
        lineage = _json_values(self.input_lineage, "input_lineage")
        object.__setattr__(self, "input_lineage", lineage)

        observational_fields = (
            self.provider, self.dataset_id, self.accessed_at, self.request_url, self.asset_id, self.asset_href,
            self.requested_latitude, self.requested_longitude, self.returned_latitude, self.returned_longitude,
        )
        if self.provenance_kind == "observed":
            if not self.provider or not self.dataset_id or not self.accessed_at:
                raise ObservationValidationError("observed evidence requires provider, dataset_id, and accessed_at")
            if not (self.request_url or self.asset_id or self.asset_href):
                raise ObservationValidationError("observed evidence requires request_url or an asset identity")
            if self.derivation_method or self.input_lineage:
                raise ObservationValidationError("observed evidence prohibits derivation fields")
            if self.model_version or self.scenario_id:
                raise ObservationValidationError("observed evidence prohibits model fields")
        elif self.provenance_kind == "derived":
            if not self.derivation_method or not self.input_lineage:
                raise ObservationValidationError("derived evidence requires derivation_method and input_lineage")
            if any(value is not None for value in observational_fields):
                raise ObservationValidationError("derived evidence prohibits observational fields")
            if self.model_version or self.scenario_id:
                raise ObservationValidationError("derived evidence prohibits model fields")
        else:
            if not self.model_version or not self.scenario_id:
                raise ObservationValidationError("simulated evidence requires model_version and scenario_id")
            if any(value is not None for value in observational_fields):
                raise ObservationValidationError("simulated evidence prohibits observational fields")
            if self.derivation_method or self.input_lineage:
                raise ObservationValidationError("simulated evidence prohibits derivation fields")

    @property
    def identity(self) -> str:
        """Immutable axis key for one logical evidence chain."""

        payload = {
            "logical_observation_id": self.logical_observation_id,
            "station_id": self.station_id,
            "metric": self.metric,
            "observed_at": self.observed_at.isoformat(),
        }
        return hashlib.sha256(_canonical_json(payload, "identity").encode("utf-8")).hexdigest()

    @staticmethod
    def noaa_logical_observation_id(station_id: str, metric: str, observed_at: datetime) -> str:
        timestamp = _timestamp(observed_at, "observed_at").strftime("%Y%m%dT%H%M%SZ")
        return f"noaa-crw:{_nonempty(station_id, 'station_id')}:{_nonempty(metric, 'metric')}:{timestamp}"

    @property
    def content_hash(self) -> str:
        payload = self.to_dict()
        payload.pop("identity")
        return hashlib.sha256(_canonical_json(payload, "content").encode("utf-8")).hexdigest()

    @classmethod
    def from_noaa(cls, observation: Any) -> "CanonicalObservation":
        """Map a NOAA adapter result without manufacturing additional provenance."""

        return cls(
            station_id=observation.station_id,
            metric=observation.product,
            observed_at=observation.observed_at,
            unit=observation.unit,
            value=observation.value,
            provenance_kind="observed",
            logical_observation_id=cls.noaa_logical_observation_id(
                observation.station_id, observation.product, observation.observed_at
            ),
            provider=observation.source,
            dataset_id=observation.dataset_id,
            accessed_at=observation.accessed_at,
            request_url=observation.request_url,
            requested_latitude=observation.requested_latitude,
            requested_longitude=observation.requested_longitude,
            returned_latitude=observation.returned_latitude,
            returned_longitude=observation.returned_longitude,
        )

    def to_dict(self) -> dict[str, Any]:
        """Return only JSON-safe primitives and ISO-8601 timestamps."""

        return {
            "identity": self.identity,
            "logical_observation_id": self.logical_observation_id,
            "station_id": self.station_id,
            "metric": self.metric,
            "observed_at": self.observed_at.isoformat(),
            "unit": self.unit,
            "value": self.value,
            "provenance_kind": self.provenance_kind,
            "provider": self.provider,
            "dataset_id": self.dataset_id,
            "accessed_at": self.accessed_at.isoformat() if self.accessed_at else None,
            "request_url": self.request_url,
            "asset_id": self.asset_id,
            "asset_href": self.asset_href,
            "requested_latitude": self.requested_latitude,
            "requested_longitude": self.requested_longitude,
            "returned_latitude": self.returned_latitude,
            "returned_longitude": self.returned_longitude,
            "quality_flags": list(self.quality_flags),
            "uncertainty": self.uncertainty,
            "derivation_method": self.derivation_method,
            "input_lineage": [_thaw_json(item) for item in self.input_lineage],
            "model_version": self.model_version,
            "scenario_id": self.scenario_id,
        }

    def json_columns(self) -> tuple[str, str, str]:
        return (
            _canonical_json(list(self.quality_flags), "quality_flags"),
            _canonical_json([_thaw_json(item) for item in self.input_lineage], "input_lineage"),
            _canonical_json(
                {"asset_id": self.asset_id, "asset_href": self.asset_href, "request_url": self.request_url},
                "source_evidence",
            ),
        )

    def validated_copy(self) -> "CanonicalObservation":
        """Rebuild the record from JSON-safe values before persistence."""

        return CanonicalObservation(
            station_id=self.station_id, metric=self.metric, observed_at=self.observed_at, unit=self.unit,
            value=self.value, provenance_kind=self.provenance_kind, provider=self.provider,
            logical_observation_id=self.logical_observation_id,
            dataset_id=self.dataset_id, accessed_at=self.accessed_at, request_url=self.request_url,
            asset_id=self.asset_id, asset_href=self.asset_href, requested_latitude=self.requested_latitude,
            requested_longitude=self.requested_longitude, returned_latitude=self.returned_latitude,
            returned_longitude=self.returned_longitude, quality_flags=self.quality_flags,
            uncertainty=self.uncertainty, derivation_method=self.derivation_method,
            input_lineage=tuple(_thaw_json(item) for item in self.input_lineage),
            model_version=self.model_version, scenario_id=self.scenario_id,
        )


__all__ = ["CanonicalObservation", "ObservationValidationError", "PROVENANCE_KINDS"]
