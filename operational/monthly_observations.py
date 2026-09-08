"""Deterministic monthly observed-value batches for the 25-station twin."""

from __future__ import annotations

import math
from dataclasses import dataclass
from datetime import date, datetime, timezone
from typing import Any, Iterable, Mapping, Protocol

from .stations import CANONICAL_STATIONS


CANONICAL_STATION_IDS = tuple(station.station_id for station in CANONICAL_STATIONS)


class MonthlyObservationValidationError(ValueError):
    """Raised when a monthly aggregation would make an ambiguous claim."""


def _text(value: object, field: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise MonthlyObservationValidationError(f"{field} must be a non-empty string")
    return value.strip()


def _finite(value: object, field: str, *, nonnegative: bool = False) -> float:
    try:
        result = float(value)
    except (TypeError, ValueError) as error:
        raise MonthlyObservationValidationError(f"{field} must be numeric") from error
    if not math.isfinite(result) or (nonnegative and result < 0):
        raise MonthlyObservationValidationError(f"{field} must be finite" + (" and non-negative" if nonnegative else ""))
    return result


def _month(value: date) -> date:
    if type(value) is not date or value.day != 1:
        raise MonthlyObservationValidationError("month must be a calendar month represented by its first day")
    return value


def _utc(value: object, field: str) -> datetime:
    if not isinstance(value, datetime) or value.tzinfo is None:
        raise MonthlyObservationValidationError(f"{field} must be timezone-aware")
    return value.astimezone(timezone.utc)


def _station_axis(values: Iterable[str]) -> tuple[str, ...]:
    result = tuple(values)
    if result != CANONICAL_STATION_IDS:
        raise MonthlyObservationValidationError("station_ids must exactly match the ordered 25-station canonical registry")
    return result


@dataclass(frozen=True)
class SourceKey:
    provider: str
    dataset_id: str

    def __post_init__(self) -> None:
        object.__setattr__(self, "provider", _text(self.provider, "provider"))
        object.__setattr__(self, "dataset_id", _text(self.dataset_id, "dataset_id"))


@dataclass(frozen=True)
class RevisionReference:
    logical_observation_id: str
    revision: int
    available_at: datetime
    accessed_at: datetime

    def __post_init__(self) -> None:
        object.__setattr__(self, "logical_observation_id", _text(self.logical_observation_id, "logical_observation_id"))
        if not isinstance(self.revision, int) or isinstance(self.revision, bool) or self.revision < 1:
            raise MonthlyObservationValidationError("revision must be a positive integer")
        object.__setattr__(self, "available_at", _utc(self.available_at, "available_at"))
        object.__setattr__(self, "accessed_at", _utc(self.accessed_at, "accessed_at"))


@dataclass(frozen=True)
class MetricAggregationPolicy:
    """All quality and selection choices for one metric, with no implicit defaults."""

    metric: str
    unit: str
    accepted_quality_flags: frozenset[str]
    max_uncertainty: float
    fallback_uncertainty: float
    minimum_samples: int
    provider_priority: tuple[SourceKey, ...]

    def __post_init__(self) -> None:
        object.__setattr__(self, "metric", _text(self.metric, "metric"))
        object.__setattr__(self, "unit", _text(self.unit, "unit"))
        try:
            flags = frozenset(_text(flag, "accepted_quality_flags item") for flag in self.accepted_quality_flags)
        except TypeError as error:
            raise MonthlyObservationValidationError("accepted_quality_flags must be an iterable") from error
        object.__setattr__(self, "accepted_quality_flags", flags)
        object.__setattr__(self, "max_uncertainty", _finite(self.max_uncertainty, "max_uncertainty", nonnegative=True))
        object.__setattr__(self, "fallback_uncertainty", _finite(self.fallback_uncertainty, "fallback_uncertainty", nonnegative=True))
        if not isinstance(self.minimum_samples, int) or isinstance(self.minimum_samples, bool) or self.minimum_samples < 1:
            raise MonthlyObservationValidationError("minimum_samples must be a positive integer")
        try:
            priority = tuple(self.provider_priority)
        except TypeError as error:
            raise MonthlyObservationValidationError("provider_priority must be an iterable") from error
        if any(not isinstance(source, SourceKey) for source in priority):
            raise MonthlyObservationValidationError("provider_priority must contain SourceKey values")
        if len(set(priority)) != len(priority):
            raise MonthlyObservationValidationError("provider_priority must not contain duplicate sources")
        object.__setattr__(self, "provider_priority", priority)


@dataclass(frozen=True)
class MonthlyObservation:
    month: date
    station_id: str
    metric: str
    unit: str
    value: float | None
    uncertainty: float | None
    sample_count: int
    sources: tuple[SourceKey, ...]
    revisions: tuple[RevisionReference, ...]
    status: str
    assimilation_mask: bool

    def __post_init__(self) -> None:
        object.__setattr__(self, "month", _month(self.month))
        object.__setattr__(self, "station_id", _text(self.station_id, "station_id"))
        object.__setattr__(self, "metric", _text(self.metric, "metric"))
        object.__setattr__(self, "unit", _text(self.unit, "unit"))
        if self.value is not None:
            object.__setattr__(self, "value", _finite(self.value, "value"))
        if self.uncertainty is not None:
            object.__setattr__(self, "uncertainty", _finite(self.uncertainty, "uncertainty", nonnegative=True))
        if not isinstance(self.sample_count, int) or isinstance(self.sample_count, bool) or self.sample_count < 0:
            raise MonthlyObservationValidationError("sample_count must be a non-negative integer")
        sources = tuple(self.sources)
        revisions = tuple(self.revisions)
        if any(not isinstance(source, SourceKey) for source in sources):
            raise MonthlyObservationValidationError("sources must contain SourceKey values")
        if any(not isinstance(revision, RevisionReference) for revision in revisions):
            raise MonthlyObservationValidationError("revisions must contain RevisionReference values")
        object.__setattr__(self, "sources", sources)
        object.__setattr__(self, "revisions", revisions)
        object.__setattr__(self, "status", _text(self.status, "status"))
        if not isinstance(self.assimilation_mask, bool):
            raise MonthlyObservationValidationError("assimilation_mask must be a boolean")
        if self.assimilation_mask != (self.status == "observed"):
            raise MonthlyObservationValidationError("assimilation_mask is true only for observed monthly values")
        if self.status == "observed" and (self.value is None or self.uncertainty is None or self.sample_count < 1):
            raise MonthlyObservationValidationError("observed monthly values require value, uncertainty, and samples")
        if self.status != "observed" and self.assimilation_mask:
            raise MonthlyObservationValidationError("non-observed monthly values cannot enter assimilation")


@dataclass(frozen=True)
class AssimilationInputs:
    """Metric-major numerical inputs that are safe to pass to an assimilator."""

    keys: tuple[tuple[str, str], ...]
    values: tuple[float | None, ...]
    uncertainties: tuple[float | None, ...]
    mask: tuple[bool, ...]

    def __post_init__(self) -> None:
        keys = tuple(self.keys)
        values = tuple(self.values)
        uncertainties = tuple(self.uncertainties)
        mask = tuple(self.mask)
        if not keys or len(keys) != len(values) or len(keys) != len(uncertainties) or len(keys) != len(mask):
            raise MonthlyObservationValidationError("assimilation inputs must have equally-sized non-empty fields")
        if any(not isinstance(key, tuple) or len(key) != 2 or not all(isinstance(part, str) and part for part in key) for key in keys):
            raise MonthlyObservationValidationError("assimilation keys must be non-empty (metric, station_id) pairs")
        if len(set(keys)) != len(keys):
            raise MonthlyObservationValidationError("assimilation keys must be unique")
        for value, uncertainty, enabled in zip(values, uncertainties, mask, strict=True):
            if not isinstance(enabled, bool):
                raise MonthlyObservationValidationError("assimilation mask must contain booleans")
            if enabled:
                if value is None or uncertainty is None:
                    raise MonthlyObservationValidationError("enabled assimilation entries require value and uncertainty")
                _finite(value, "assimilation value")
                _finite(uncertainty, "assimilation uncertainty", nonnegative=True)
            elif value is not None or uncertainty is not None:
                raise MonthlyObservationValidationError("masked assimilation entries must not expose numeric values")
        object.__setattr__(self, "keys", keys)
        object.__setattr__(self, "values", values)
        object.__setattr__(self, "uncertainties", uncertainties)
        object.__setattr__(self, "mask", mask)


@dataclass(frozen=True)
class SimulatedBootstrapValue:
    station_id: str
    metric: str
    month: date
    unit: str
    value: float
    uncertainty: float

    def __post_init__(self) -> None:
        object.__setattr__(self, "station_id", _text(self.station_id, "station_id"))
        object.__setattr__(self, "metric", _text(self.metric, "metric"))
        object.__setattr__(self, "month", _month(self.month))
        object.__setattr__(self, "unit", _text(self.unit, "unit"))
        object.__setattr__(self, "value", _finite(self.value, "value"))
        object.__setattr__(self, "uncertainty", _finite(self.uncertainty, "uncertainty", nonnegative=True))


@dataclass(frozen=True)
class MonthlyObservationBatch:
    month: date
    station_ids: tuple[str, ...]
    metrics: tuple[str, ...]
    observations: tuple[MonthlyObservation, ...]

    def __post_init__(self) -> None:
        object.__setattr__(self, "month", _month(self.month))
        axis = _station_axis(self.station_ids)
        object.__setattr__(self, "station_ids", axis)
        metrics = tuple(_text(metric, "metrics item") for metric in self.metrics)
        if not metrics or len(set(metrics)) != len(metrics):
            raise MonthlyObservationValidationError("metrics must be a non-empty unique ordered sequence")
        object.__setattr__(self, "metrics", metrics)
        observations = tuple(self.observations)
        expected = tuple((metric, station_id) for metric in metrics for station_id in axis)
        actual = tuple((item.metric, item.station_id) for item in observations if isinstance(item, MonthlyObservation))
        if len(observations) != len(expected) or actual != expected or any(not isinstance(item, MonthlyObservation) for item in observations):
            raise MonthlyObservationValidationError("observations must be metric-major and station-major across exactly 25 stations")
        if any(item.month != self.month for item in observations):
            raise MonthlyObservationValidationError("all observations must belong to the batch month")
        object.__setattr__(self, "observations", observations)

    def assimilation_inputs(self) -> AssimilationInputs:
        """Expose only observed finite values in the immutable batch order."""

        keys = tuple((item.metric, item.station_id) for item in self.observations)
        mask = tuple(item.status == "observed" and item.assimilation_mask for item in self.observations)
        values = tuple(item.value if enabled else None for item, enabled in zip(self.observations, mask, strict=True))
        uncertainties = tuple(item.uncertainty if enabled else None for item, enabled in zip(self.observations, mask, strict=True))
        return AssimilationInputs(keys, values, uncertainties, mask)


class _AsOfRepository(Protocol):
    def list_canonical_observations_as_of(
        self, month: date, cutoff: datetime, *, station_ids: tuple[str, ...] | None = None, metrics: tuple[str, ...] | None = None
    ) -> list[dict[str, Any]]: ...


def _reference(row: Mapping[str, Any]) -> RevisionReference:
    return RevisionReference(
        logical_observation_id=row["logical_observation_id"],
        revision=row["revision"],
        available_at=datetime.fromisoformat(row["available_at"]),
        accessed_at=datetime.fromisoformat(row["accessed_at"]),
    )


def _missing(month: date, station_id: str, policy: MetricAggregationPolicy, status: str) -> MonthlyObservation:
    return MonthlyObservation(month, station_id, policy.metric, policy.unit, None, None, 0, (), (), status, False)


def _select_source(rows: tuple[Mapping[str, Any], ...], policy: MetricAggregationPolicy) -> tuple[SourceKey | None, tuple[Mapping[str, Any], ...], str | None]:
    by_source: dict[SourceKey, list[Mapping[str, Any]]] = {}
    for row in rows:
        by_source.setdefault(SourceKey(row["provider"], row["dataset_id"]), []).append(row)
    if not by_source:
        return None, (), "missing"
    if len(by_source) == 1:
        source = next(iter(by_source))
        return source, tuple(by_source[source]), None
    for source in policy.provider_priority:
        if source in by_source:
            return source, tuple(by_source[source]), None
    return None, (), "missing_ambiguous"


def _aggregate(month: date, station_id: str, policy: MetricAggregationPolicy, rows: tuple[Mapping[str, Any], ...]) -> MonthlyObservation:
    source, selected, missing_status = _select_source(rows, policy)
    if missing_status is not None:
        return _missing(month, station_id, policy, missing_status)
    assert source is not None
    if any(row["unit"] != policy.unit for row in selected):
        return _missing(month, station_id, policy, "missing_unit")
    if any(not set(row["quality_flags"]).issubset(policy.accepted_quality_flags) for row in selected):
        return _missing(month, station_id, policy, "missing_qc")
    uncertainties: list[float] = []
    for row in selected:
        raw = row["uncertainty"]
        sigma = policy.fallback_uncertainty if raw is None else _finite(raw, "uncertainty", nonnegative=True)
        if sigma > policy.max_uncertainty:
            return _missing(month, station_id, policy, "missing_uncertainty")
        uncertainties.append(sigma)
    if len(selected) < policy.minimum_samples:
        return _missing(month, station_id, policy, "missing_insufficient")
    values = tuple(_finite(row["value"], "value") for row in selected)
    return MonthlyObservation(
        month, station_id, policy.metric, policy.unit, sum(values) / len(values),
        math.sqrt(sum(sigma * sigma for sigma in uncertainties)) / len(uncertainties), len(values),
        (source,), tuple(_reference(row) for row in selected), "observed", True,
    )


def build_monthly_observation_batch(
    repository: _AsOfRepository,
    month: date,
    cutoff: datetime,
    policies: Iterable[MetricAggregationPolicy],
    *,
    bootstrap_values: Iterable[SimulatedBootstrapValue] = (),
) -> MonthlyObservationBatch:
    """Aggregate only observed, visible revisions; simulated bootstraps stay masked."""

    normalized_month = _month(month)
    normalized_cutoff = _utc(cutoff, "cutoff")
    policies_tuple = tuple(policies)
    if not policies_tuple or any(not isinstance(policy, MetricAggregationPolicy) for policy in policies_tuple):
        raise MonthlyObservationValidationError("policies must be a non-empty sequence of MetricAggregationPolicy values")
    if len({policy.metric for policy in policies_tuple}) != len(policies_tuple):
        raise MonthlyObservationValidationError("policies must not repeat a metric")
    try:
        bootstrap = tuple(bootstrap_values)
    except TypeError as error:
        raise MonthlyObservationValidationError("bootstrap_values must be an iterable") from error
    if any(not isinstance(item, SimulatedBootstrapValue) for item in bootstrap):
        raise MonthlyObservationValidationError("bootstrap_values must contain SimulatedBootstrapValue values")
    bootstrap_by_axis = {(item.station_id, item.metric): item for item in bootstrap if item.month == normalized_month}
    rows = repository.list_canonical_observations_as_of(
        normalized_month, normalized_cutoff, station_ids=CANONICAL_STATION_IDS, metrics=tuple(policy.metric for policy in policies_tuple)
    )
    grouped: dict[tuple[str, str], list[Mapping[str, Any]]] = {}
    for row in rows:
        grouped.setdefault((row["metric"], row["station_id"]), []).append(row)
    output: list[MonthlyObservation] = []
    for policy in policies_tuple:
        for station_id in CANONICAL_STATION_IDS:
            item = _aggregate(normalized_month, station_id, policy, tuple(grouped.get((policy.metric, station_id), ())))
            candidate = bootstrap_by_axis.get((station_id, policy.metric))
            if item.status != "observed" and candidate is not None:
                if candidate.unit != policy.unit:
                    raise MonthlyObservationValidationError("bootstrap unit must match the metric policy")
                item = MonthlyObservation(
                    normalized_month, station_id, policy.metric, policy.unit, candidate.value, candidate.uncertainty,
                    0, (), (), "simulated_bootstrap", False,
                )
            output.append(item)
    return MonthlyObservationBatch(normalized_month, CANONICAL_STATION_IDS, tuple(policy.metric for policy in policies_tuple), tuple(output))


__all__ = [
    "AssimilationInputs", "CANONICAL_STATION_IDS", "MetricAggregationPolicy", "MonthlyObservation", "MonthlyObservationBatch",
    "MonthlyObservationValidationError", "RevisionReference", "SimulatedBootstrapValue", "SourceKey",
    "build_monthly_observation_batch",
]
