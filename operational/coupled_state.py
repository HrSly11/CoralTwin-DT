"""Pure, deterministic monthly ecosystem state for the canonical station axis.

This module deliberately provides a bounded transition *contract*, not calibrated
ecological rates or hydrodynamic transport.  Parameters and any non-identity
connectivity must be supplied by a later, evidence-backed integration layer.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from datetime import date
from typing import Iterable

from .stations import CANONICAL_STATIONS


class CoupledStateValidationError(ValueError):
    """Raised when a monthly state, forcing, topology, or parameter is invalid."""


CANONICAL_STATION_IDS = tuple(station.station_id for station in CANONICAL_STATIONS)
STATE_COMPONENTS = (
    "coral_cover_pct",
    "macroalgae_cover_pct",
    "biodiversity_index",
    "sst_deg_c",
    "dhw_deg_c_weeks",
    "omega_arag",
)

# Nominal geographic groups restrict topology only.  They assert no transport
# links; the default matrix is identity until empirical connectivity is supplied.
REGIONAL_BLOCKS = (
    ("station-01", "station-02", "station-03", "station-04"),
    ("station-05", "station-06"),
    ("station-07", "station-08"),
    ("station-09", "station-10"),
    ("station-11", "station-12"),
    ("station-13", "station-14", "station-15"),
    ("station-16", "station-17", "station-18", "station-19"),
    ("station-20",),
    ("station-21", "station-22"),
    ("station-23", "station-24"),
    ("station-25",),
)
_BLOCK_BY_STATION = {
    station_id: block_index
    for block_index, block in enumerate(REGIONAL_BLOCKS)
    for station_id in block
}
_VECTOR_LENGTH = len(CANONICAL_STATION_IDS) * len(STATE_COMPONENTS)


def _month(value: date, field: str) -> date:
    if type(value) is not date or value.day != 1:
        raise CoupledStateValidationError(f"{field} must be a plain calendar date on the month's first day")
    return value


def _following_month(value: date) -> date:
    return date(value.year + (value.month == 12), 1 if value.month == 12 else value.month + 1, 1)


def _finite(value: object, field: str) -> float:
    try:
        result = float(value)
    except (TypeError, ValueError) as error:
        raise CoupledStateValidationError(f"{field} must be numeric") from error
    if not math.isfinite(result):
        raise CoupledStateValidationError(f"{field} must be finite")
    return result


def _axis(station_ids: Iterable[str]) -> tuple[str, ...]:
    result = tuple(station_ids)
    if result != CANONICAL_STATION_IDS:
        raise CoupledStateValidationError("station_ids must exactly match the ordered 25-station canonical registry")
    return result


def _series(values: Iterable[object], field: str, *, lower: float | None = None, strict_lower: bool = False, upper: float | None = None) -> tuple[float, ...]:
    try:
        result = tuple(_finite(value, f"{field}[{index}]") for index, value in enumerate(values))
    except TypeError as error:
        raise CoupledStateValidationError(f"{field} must be an iterable of 25 values") from error
    if len(result) != len(CANONICAL_STATION_IDS):
        raise CoupledStateValidationError(f"{field} must contain exactly 25 values")
    if lower is not None and any(value <= lower if strict_lower else value < lower for value in result):
        comparator = ">" if strict_lower else ">="
        raise CoupledStateValidationError(f"{field} values must be {comparator} {lower}")
    if upper is not None and any(value > upper for value in result):
        raise CoupledStateValidationError(f"{field} values must be <= {upper}")
    return result


def _project_benthic(coral: float, macroalgae: float) -> tuple[float, float]:
    coral, macroalgae = max(0.0, coral), max(0.0, macroalgae)
    total = coral + macroalgae
    if total <= 100.0:
        return coral, macroalgae
    return 100.0 * coral / total, 100.0 * macroalgae / total


def project_biological_components(
    coral_cover_pct: object, macroalgae_cover_pct: object, biodiversity_index: object,
) -> tuple[float, float, float]:
    """Project one C/M/B triplet to the public state-space bounds."""

    coral, macroalgae = _project_benthic(
        _finite(coral_cover_pct, "coral_cover_pct"),
        _finite(macroalgae_cover_pct, "macroalgae_cover_pct"),
    )
    biodiversity = min(1.0, max(0.0, _finite(biodiversity_index, "biodiversity_index")))
    return coral, macroalgae, biodiversity


@dataclass(frozen=True)
class MonthlyForcing:
    """Finite monthly abiotic inputs; only DHW and omega have generic hard bounds."""

    month: date
    sst_deg_c: tuple[float, ...]
    dhw_deg_c_weeks: tuple[float, ...]
    omega_arag: tuple[float, ...]

    def __post_init__(self) -> None:
        object.__setattr__(self, "month", _month(self.month, "month"))
        object.__setattr__(self, "sst_deg_c", _series(self.sst_deg_c, "sst_deg_c"))
        object.__setattr__(self, "dhw_deg_c_weeks", _series(self.dhw_deg_c_weeks, "dhw_deg_c_weeks", lower=0.0))
        object.__setattr__(self, "omega_arag", _series(self.omega_arag, "omega_arag", lower=0.0, strict_lower=True))


@dataclass(frozen=True)
class MonthlyCoupledState:
    """C/M cover percentages, normalized B, and the forcing for one monthly state."""

    month: date
    station_ids: tuple[str, ...]
    coral_cover_pct: tuple[float, ...]
    macroalgae_cover_pct: tuple[float, ...]
    biodiversity_index: tuple[float, ...]
    forcing: MonthlyForcing

    def __post_init__(self) -> None:
        object.__setattr__(self, "month", _month(self.month, "month"))
        object.__setattr__(self, "station_ids", _axis(self.station_ids))
        coral = _series(self.coral_cover_pct, "coral_cover_pct", lower=0.0, upper=100.0)
        macroalgae = _series(self.macroalgae_cover_pct, "macroalgae_cover_pct", lower=0.0, upper=100.0)
        if any(coral_value + macroalgae_value > 100.0 for coral_value, macroalgae_value in zip(coral, macroalgae)):
            raise CoupledStateValidationError("coral_cover_pct + macroalgae_cover_pct must not exceed 100")
        if not isinstance(self.forcing, MonthlyForcing) or self.forcing.month != self.month:
            raise CoupledStateValidationError("forcing must be a MonthlyForcing for the state's month")
        object.__setattr__(self, "coral_cover_pct", coral)
        object.__setattr__(self, "macroalgae_cover_pct", macroalgae)
        object.__setattr__(self, "biodiversity_index", _series(self.biodiversity_index, "biodiversity_index", lower=0.0, upper=1.0))

    def to_vector(self) -> tuple[float, ...]:
        """Return the EnKF-ready field-major vector in ``STATE_COMPONENTS`` order."""

        return (
            *self.coral_cover_pct,
            *self.macroalgae_cover_pct,
            *self.biodiversity_index,
            *self.forcing.sst_deg_c,
            *self.forcing.dhw_deg_c_weeks,
            *self.forcing.omega_arag,
        )

    @classmethod
    def from_vector(cls, month: date, station_ids: Iterable[str], values: Iterable[object]) -> "MonthlyCoupledState":
        vector = tuple(values)
        if len(vector) != _VECTOR_LENGTH:
            raise CoupledStateValidationError(f"state vector must contain exactly {_VECTOR_LENGTH} values")
        size = len(CANONICAL_STATION_IDS)
        forcing = MonthlyForcing(month, vector[3 * size:4 * size], vector[4 * size:5 * size], vector[5 * size:6 * size])
        return cls(month, tuple(station_ids), vector[:size], vector[size:2 * size], vector[2 * size:3 * size], forcing)


@dataclass(frozen=True)
class ConnectivityMatrix:
    """Validated source-row to destination-column connectivity over the canonical axis."""

    station_ids: tuple[str, ...]
    weights: tuple[tuple[float, ...], ...]

    def __post_init__(self) -> None:
        axis = _axis(self.station_ids)
        try:
            rows = tuple(tuple(_finite(value, f"weights[{source}][{destination}]") for destination, value in enumerate(row)) for source, row in enumerate(self.weights))
        except TypeError as error:
            raise CoupledStateValidationError("weights must be a 25x25 matrix") from error
        if len(rows) != len(axis) or any(len(row) != len(axis) for row in rows):
            raise CoupledStateValidationError("weights must be a 25x25 matrix")
        for source, row in enumerate(rows):
            if any(value < 0.0 for value in row):
                raise CoupledStateValidationError("weights must be non-negative")
            if not math.isclose(sum(row), 1.0, rel_tol=0.0, abs_tol=1e-12):
                raise CoupledStateValidationError("each connectivity row must sum to one")
            if any(value != 0.0 and _BLOCK_BY_STATION[axis[source]] != _BLOCK_BY_STATION[axis[destination]] for destination, value in enumerate(row)):
                raise CoupledStateValidationError("connectivity weights must be zero outside nominal regional blocks")
        object.__setattr__(self, "station_ids", axis)
        object.__setattr__(self, "weights", rows)

    @classmethod
    def default(cls) -> "ConnectivityMatrix":
        size = len(CANONICAL_STATION_IDS)
        return cls(CANONICAL_STATION_IDS, tuple(tuple(1.0 if row == column else 0.0 for column in range(size)) for row in range(size)))


@dataclass(frozen=True)
class MonthlyTransitionParameters:
    """Non-negative, caller-supplied monthly rates; this module supplies no calibration."""

    coral_growth_per_month: float
    macroalgae_growth_per_month: float
    heat_mortality_per_dhw: float
    grazing_per_month: float
    larval_recruitment_per_month: float
    biodiversity_recovery_per_month: float
    biodiversity_macroalgae_loss_per_month: float
    biodiversity_heat_loss_per_dhw: float

    def __post_init__(self) -> None:
        for field in self.__dataclass_fields__:
            value = _finite(getattr(self, field), field)
            if value < 0.0:
                raise CoupledStateValidationError(f"{field} must be non-negative")
            object.__setattr__(self, field, value)


def step_month(state: MonthlyCoupledState, next_forcing: MonthlyForcing, connectivity: ConnectivityMatrix, parameters: MonthlyTransitionParameters) -> MonthlyCoupledState:
    """Advance one month using bounded C/M/B dynamics and source-to-destination larvae.

    ``W[i][j]`` moves source ``i`` coral cover to destination ``j``; thus
    ``L[j] = sum_i(W[i][j] * C[i])``.  The simplex projection conserves the
    C:M proportion whenever provisional benthic cover exceeds 100 percent.
    """

    if not isinstance(state, MonthlyCoupledState) or not isinstance(next_forcing, MonthlyForcing):
        raise TypeError("state and next_forcing must use their monthly dataclasses")
    if not isinstance(connectivity, ConnectivityMatrix) or not isinstance(parameters, MonthlyTransitionParameters):
        raise TypeError("connectivity and parameters must use their validated dataclasses")
    if next_forcing.month != _following_month(state.month):
        raise CoupledStateValidationError("next_forcing must be for the immediately following month")
    if connectivity.station_ids != state.station_ids:
        raise CoupledStateValidationError("connectivity station_ids must match state station_ids")

    coral: list[float] = []
    macroalgae: list[float] = []
    biodiversity: list[float] = []
    for destination in range(len(state.station_ids)):
        current_coral = state.coral_cover_pct[destination]
        current_macroalgae = state.macroalgae_cover_pct[destination]
        current_biodiversity = state.biodiversity_index[destination]
        unoccupied = max(0.0, 1.0 - (current_coral + current_macroalgae) / 100.0)
        heat = next_forcing.dhw_deg_c_weeks[destination]
        larvae = sum(connectivity.weights[source][destination] * state.coral_cover_pct[source] for source in range(len(state.station_ids)))
        provisional_coral = current_coral + parameters.coral_growth_per_month * current_coral * unoccupied - parameters.heat_mortality_per_dhw * heat * current_coral + parameters.larval_recruitment_per_month * (larvae / 100.0) * unoccupied
        provisional_macroalgae = current_macroalgae + parameters.macroalgae_growth_per_month * current_macroalgae * unoccupied - parameters.grazing_per_month * current_macroalgae
        next_biodiversity = current_biodiversity + parameters.biodiversity_recovery_per_month * (current_coral / 100.0 - current_biodiversity) - parameters.biodiversity_macroalgae_loss_per_month * (current_macroalgae / 100.0) * current_biodiversity - parameters.biodiversity_heat_loss_per_dhw * heat * current_biodiversity
        bounded_coral, bounded_macroalgae, bounded_biodiversity = project_biological_components(
            provisional_coral, provisional_macroalgae, next_biodiversity,
        )
        coral.append(bounded_coral)
        macroalgae.append(bounded_macroalgae)
        biodiversity.append(bounded_biodiversity)
    return MonthlyCoupledState(next_forcing.month, state.station_ids, tuple(coral), tuple(macroalgae), tuple(biodiversity), next_forcing)


__all__ = [
    "CANONICAL_STATION_IDS", "ConnectivityMatrix", "CoupledStateValidationError", "MonthlyCoupledState",
    "MonthlyForcing", "MonthlyTransitionParameters", "REGIONAL_BLOCKS", "STATE_COMPONENTS",
    "project_biological_components", "step_month",
]
