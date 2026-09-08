"""Deterministic, biological-only ensemble Kalman analysis for one month.

This module supplies mechanics, not ecological calibration: callers must provide
all observation mappings, topology, uncertainty floor, inflation, and seed.
"""

from __future__ import annotations

import math
import random
import sys
from dataclasses import dataclass
from typing import Iterable

from .coupled_state import (
    CANONICAL_STATION_IDS,
    ConnectivityMatrix,
    MonthlyCoupledState,
    project_biological_components,
)
from .monthly_observations import MonthlyObservationBatch


class EnKFValidationError(ValueError):
    """Raised when an EnKF configuration or assimilation boundary is invalid."""


_COMPONENTS = ("coral_cover_pct", "macroalgae_cover_pct", "biodiversity_index")
_SIZE = len(CANONICAL_STATION_IDS)
_BIOLOGICAL_VECTOR_SIZE = len(_COMPONENTS) * _SIZE
_MAX_FLOAT = sys.float_info.max
_MAX_STANDARD_DEVIATION = math.sqrt(_MAX_FLOAT)
# C/M/B values are bounded by 100.  This leaves ample headroom for products
# used in the sample covariance after anomaly inflation.
_MAX_INFLATION = math.sqrt(_MAX_FLOAT / 1_000_000.0)


def _text(value: object, field: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise EnKFValidationError(f"{field} must be a non-empty string")
    return value.strip()


def _finite(value: object, field: str) -> float:
    if isinstance(value, bool):
        raise EnKFValidationError(f"{field} must be numeric")
    try:
        result = float(value)
    except (TypeError, ValueError) as error:
        raise EnKFValidationError(f"{field} must be numeric") from error
    if not math.isfinite(result):
        raise EnKFValidationError(f"{field} must be finite")
    return result


@dataclass(frozen=True)
class ObservationTarget:
    """Explicit mapping from one observed metric to one biological component."""

    metric: str
    component: str
    unit: str

    def __post_init__(self) -> None:
        object.__setattr__(self, "metric", _text(self.metric, "metric"))
        component = _text(self.component, "component")
        if component not in _COMPONENTS:
            raise EnKFValidationError("component must be coral_cover_pct, macroalgae_cover_pct, or biodiversity_index")
        object.__setattr__(self, "component", component)
        object.__setattr__(self, "unit", _text(self.unit, "unit"))


@dataclass(frozen=True)
class EnKFConfig:
    """All caller-supplied, non-scientific-default analysis configuration."""

    targets: tuple[ObservationTarget, ...]
    connectivity: ConnectivityMatrix
    inflation: float
    variance_floor: float
    minimum_members: int
    seed: int

    def __post_init__(self) -> None:
        try:
            targets = tuple(self.targets)
        except TypeError as error:
            raise EnKFValidationError("targets must be an iterable of ObservationTarget values") from error
        if not targets or any(not isinstance(target, ObservationTarget) for target in targets):
            raise EnKFValidationError("targets must be a non-empty iterable of ObservationTarget values")
        if len({target.metric for target in targets}) != len(targets):
            raise EnKFValidationError("targets must map each metric at most once")
        if len({target.component for target in targets}) != len(targets):
            raise EnKFValidationError("targets must map each biological component at most once")
        if not isinstance(self.connectivity, ConnectivityMatrix) or self.connectivity.station_ids != CANONICAL_STATION_IDS:
            raise EnKFValidationError("connectivity must use the canonical station axis")
        inflation = _finite(self.inflation, "inflation")
        variance_floor = _finite(self.variance_floor, "variance_floor")
        if inflation < 1.0:
            raise EnKFValidationError("inflation must be >= 1")
        if inflation > _MAX_INFLATION:
            raise EnKFValidationError("inflation would overflow EnKF covariance calculations")
        if variance_floor <= 0.0:
            raise EnKFValidationError("variance_floor must be > 0")
        if type(self.minimum_members) is not int or self.minimum_members < 3:
            raise EnKFValidationError("minimum_members must be an integer >= 3")
        if type(self.seed) is not int:
            raise EnKFValidationError("seed must be an integer, not bool")
        object.__setattr__(self, "targets", targets)
        object.__setattr__(self, "inflation", inflation)
        object.__setattr__(self, "variance_floor", variance_floor)


@dataclass(frozen=True)
class MonthlyStateEnsemble:
    """An immutable set of states sharing one exact monthly forcing contract."""

    members: tuple[MonthlyCoupledState, ...]

    def __post_init__(self) -> None:
        try:
            members = tuple(self.members)
        except TypeError as error:
            raise EnKFValidationError("members must be an iterable of MonthlyCoupledState values") from error
        if not members or any(not isinstance(member, MonthlyCoupledState) for member in members):
            raise EnKFValidationError("members must be a non-empty iterable of MonthlyCoupledState values")
        first = members[0]
        if any(
            member.month != first.month
            or member.station_ids != CANONICAL_STATION_IDS
            or member.forcing != first.forcing
            for member in members
        ):
            raise EnKFValidationError("all ensemble members must share the canonical axis, month, and exact forcing")
        object.__setattr__(self, "members", members)

    @property
    def month(self):
        return self.members[0].month

    @property
    def station_ids(self) -> tuple[str, ...]:
        return self.members[0].station_ids

    @property
    def forcing(self):
        return self.members[0].forcing


@dataclass(frozen=True)
class EnKFDiagnostics:
    ensemble_size: int
    assimilated_count: int
    assimilated_keys: tuple[tuple[str, str], ...]
    skipped: tuple[tuple[tuple[str, str], str], ...]
    seed: int
    inflation: float
    variance_floor: float

    def __post_init__(self) -> None:
        if type(self.ensemble_size) is not int or self.ensemble_size < 1:
            raise EnKFValidationError("ensemble_size must be a positive integer")
        keys = tuple(self.assimilated_keys)
        skipped = tuple(self.skipped)
        if type(self.assimilated_count) is not int or self.assimilated_count != len(keys):
            raise EnKFValidationError("assimilated_count must equal the number of assimilated keys")
        if any(not _key(key) for key in keys) or any(not _key(key) or not isinstance(reason, str) or not reason for key, reason in skipped):
            raise EnKFValidationError("diagnostic keys and reasons must be valid")
        inflation = _finite(self.inflation, "inflation")
        variance_floor = _finite(self.variance_floor, "variance_floor")
        if type(self.seed) is not int or inflation < 1.0 or variance_floor <= 0.0:
            raise EnKFValidationError("diagnostic configuration is invalid")
        object.__setattr__(self, "inflation", inflation)
        object.__setattr__(self, "variance_floor", variance_floor)
        object.__setattr__(self, "assimilated_keys", keys)
        object.__setattr__(self, "skipped", skipped)


def _key(value: object) -> bool:
    return isinstance(value, tuple) and len(value) == 2 and all(isinstance(part, str) and part for part in value)


@dataclass(frozen=True)
class EnKFResult:
    forecast: MonthlyStateEnsemble
    analysis: MonthlyStateEnsemble
    diagnostics: EnKFDiagnostics

    def __post_init__(self) -> None:
        if not isinstance(self.forecast, MonthlyStateEnsemble) or not isinstance(self.analysis, MonthlyStateEnsemble):
            raise EnKFValidationError("forecast and analysis must be MonthlyStateEnsemble values")
        if not isinstance(self.diagnostics, EnKFDiagnostics):
            raise EnKFValidationError("diagnostics must be EnKFDiagnostics")
        if (
            len(self.forecast.members) != len(self.analysis.members)
            or self.forecast.month != self.analysis.month
            or self.forecast.station_ids != self.analysis.station_ids
            or self.forecast.forcing != self.analysis.forcing
            or self.diagnostics.ensemble_size != len(self.forecast.members)
        ):
            raise EnKFValidationError("result forecast and analysis must retain a common ensemble contract")


def _vector(state: MonthlyCoupledState) -> list[float]:
    return list((*state.coral_cover_pct, *state.macroalgae_cover_pct, *state.biodiversity_index))


def _state(template: MonthlyCoupledState, values: Iterable[float]) -> MonthlyCoupledState:
    vector = tuple(values)
    if len(vector) != _BIOLOGICAL_VECTOR_SIZE:
        raise EnKFValidationError("biological state vector must contain exactly 75 values")
    coral: list[float] = []
    macroalgae: list[float] = []
    biodiversity: list[float] = []
    for index in range(_SIZE):
        bounded = project_biological_components(vector[index], vector[_SIZE + index], vector[2 * _SIZE + index])
        coral.append(bounded[0])
        macroalgae.append(bounded[1])
        biodiversity.append(bounded[2])
    return MonthlyCoupledState(template.month, template.station_ids, tuple(coral), tuple(macroalgae), tuple(biodiversity), template.forcing)


def _inflate(vectors: list[list[float]], multiplier: float) -> list[list[float]]:
    count = len(vectors)
    means = [sum(vector[index] for vector in vectors) / count for index in range(_BIOLOGICAL_VECTOR_SIZE)]
    inflated: list[list[float]] = []
    for vector in vectors:
        member: list[float] = []
        for index, value in enumerate(vector):
            result = means[index] + multiplier * (value - means[index])
            if not math.isfinite(result):
                raise EnKFValidationError("inflation produced a non-finite biological state")
            member.append(result)
        inflated.append(member)
    return inflated


def _select_inputs(batch: MonthlyObservationBatch, targets: dict[str, ObservationTarget]) -> tuple[list[tuple[tuple[str, str], ObservationTarget, int, float, float]], tuple[tuple[tuple[str, str], str], ...]]:
    inputs = batch.assimilation_inputs()
    selected: list[tuple[tuple[str, str], ObservationTarget, int, float, float]] = []
    skipped: list[tuple[tuple[str, str], str]] = []
    for item, key, value, sigma, enabled in zip(batch.observations, inputs.keys, inputs.values, inputs.uncertainties, inputs.mask, strict=True):
        target = targets.get(key[0])
        if target is None:
            skipped.append((key, "unmapped_metric"))
        elif item.unit != target.unit:
            skipped.append((key, "unit_mismatch"))
        elif item.status == "simulated_bootstrap":
            skipped.append((key, "simulated_bootstrap"))
        elif item.status != "observed":
            skipped.append((key, item.status))
        elif not enabled:
            skipped.append((key, "masked"))
        elif value is None or sigma is None or not math.isfinite(value) or not math.isfinite(sigma) or sigma <= 0.0:
            skipped.append((key, "invalid_value_or_uncertainty"))
        elif sigma > _MAX_STANDARD_DEVIATION:
            skipped.append((key, "uncertainty_overflow"))
        else:
            selected.append((key, target, batch.station_ids.index(key[1]), value, sigma))
    return selected, tuple(skipped)


def _sample_covariance(left: list[float], right: list[float], left_mean: float, right_mean: float) -> float:
    covariance = sum((left_value - left_mean) * (right_value - right_mean) for left_value, right_value in zip(left, right, strict=True)) / (len(left) - 1)
    if not math.isfinite(covariance):
        raise EnKFValidationError("sample covariance is non-finite")
    return covariance


def _observation_variance(sigma: float, variance_floor: float) -> float:
    if sigma > _MAX_STANDARD_DEVIATION:
        raise EnKFValidationError("observation uncertainty would overflow its variance")
    variance = sigma * sigma
    result = max(variance, variance_floor)
    if not math.isfinite(result) or result <= 0.0:
        raise EnKFValidationError("observation variance is invalid")
    return result


def _finite_result(value: float, field: str) -> float:
    if not math.isfinite(value):
        raise EnKFValidationError(f"{field} is non-finite")
    return value


def _assimilate_one(vectors: list[list[float]], component: int, station: int, observation: float, sigma: float, config: EnKFConfig, rng: random.Random) -> list[list[float]]:
    count = len(vectors)
    observed_index = component * _SIZE + station
    predicted = [vector[observed_index] for vector in vectors]
    predicted_mean = sum(predicted) / count
    anomalies = [value - predicted_mean for value in predicted]
    predicted_variance = _sample_covariance(predicted, predicted, predicted_mean, predicted_mean)
    observation_variance = _observation_variance(sigma, config.variance_floor)
    denominator = _finite_result(predicted_variance + observation_variance, "innovation variance")
    if denominator <= 0.0:
        raise EnKFValidationError("innovation variance must be positive")
    gains = [0.0] * _BIOLOGICAL_VECTOR_SIZE
    for destination in range(_SIZE):
        index = component * _SIZE + destination
        local_weight = 1.0 if destination == station else config.connectivity.weights[station][destination]
        if local_weight:
            state_mean = sum(vector[index] for vector in vectors) / count
            covariance = _sample_covariance([vector[index] for vector in vectors], predicted, state_mean, predicted_mean)
            gains[index] = _finite_result(local_weight * covariance / denominator, "Kalman gain")
    standard_deviation = math.sqrt(observation_variance)
    updated: list[list[float]] = []
    for member, vector in enumerate(vectors):
        perturbation = _finite_result(rng.gauss(0.0, standard_deviation), "observation perturbation")
        innovation = _finite_result(observation + perturbation - predicted[member], "observation innovation")
        updated.append([_finite_result(value + gains[index] * innovation, "analysis state") for index, value in enumerate(vector)])
    return updated


def analyze_month(forecast: MonthlyStateEnsemble, batch: MonthlyObservationBatch, config: EnKFConfig) -> EnKFResult:
    """Assimilate only explicit observed C/M/B metrics in batch order.

    Forcing does not belong to this analysis vector and is carried unchanged in
    every reconstructed state.  Connectivity is source-observation to
    destination-update, and applies only within the observed component.
    """

    if not isinstance(forecast, MonthlyStateEnsemble) or not isinstance(batch, MonthlyObservationBatch) or not isinstance(config, EnKFConfig):
        raise TypeError("forecast, batch, and config must use their validated dataclasses")
    if len(forecast.members) < config.minimum_members:
        raise EnKFValidationError("ensemble has fewer members than minimum_members")
    if batch.month != forecast.month or batch.station_ids != forecast.station_ids:
        raise EnKFValidationError("batch must share the forecast month and canonical station axis")
    selected, skipped = _select_inputs(batch, {target.metric: target for target in config.targets})
    assimilated_keys = tuple(key for key, _, _, _, _ in selected)
    diagnostics = EnKFDiagnostics(len(forecast.members), len(assimilated_keys), assimilated_keys, skipped, config.seed, config.inflation, config.variance_floor)
    if not selected:
        return EnKFResult(forecast, forecast, diagnostics)
    vectors = _inflate([_vector(member) for member in forecast.members], config.inflation)
    rng = random.Random(config.seed)
    templates = forecast.members
    for _, target, station, value, sigma in selected:
        vectors = _assimilate_one(vectors, _COMPONENTS.index(target.component), station, value, sigma, config, rng)
        vectors = [_vector(_state(template, vector)) for template, vector in zip(templates, vectors, strict=True)]
    analysis = MonthlyStateEnsemble(tuple(_state(template, vector) for template, vector in zip(templates, vectors, strict=True)))
    return EnKFResult(forecast, analysis, diagnostics)


__all__ = [
    "EnKFConfig", "EnKFDiagnostics", "EnKFResult", "EnKFValidationError", "MonthlyStateEnsemble",
    "ObservationTarget", "analyze_month",
]
