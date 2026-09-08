"""Pure paired monthly scenario trajectories with explicit local interventions."""

from __future__ import annotations

import hashlib
import json
import math
from dataclasses import dataclass, field
from datetime import date
from typing import Iterable

from .coupled_state import CANONICAL_STATION_IDS, MonthlyCoupledState, project_biological_components, step_month
from .scenario_experiment import PairedDrawKey, PairedEndpointResult, PairedExperimentPlan, ProcessDraw


START_MONTH = date(2026, 1, 1)
END_MONTH = date(2050, 12, 1)
MONTH_COUNT = 300


class ScenarioRunnerValidationError(ValueError):
    """Raised before a paired simulation can expose an incomplete result."""


def _text(value: object, field: str) -> str:
    if not isinstance(value, str) or not value.strip() or value != value.strip():
        raise ScenarioRunnerValidationError(f"{field} must be a normalized non-empty string")
    return value


def _finite(value: object, field: str, *, lower: float = 0.0, upper: float | None = None) -> float:
    if isinstance(value, bool):
        raise ScenarioRunnerValidationError(f"{field} must be finite")
    try:
        result = float(value)
    except (TypeError, ValueError) as error:
        raise ScenarioRunnerValidationError(f"{field} must be finite") from error
    if not math.isfinite(result) or result < lower or upper is not None and result > upper:
        raise ScenarioRunnerValidationError(f"{field} is outside its range")
    return result


def _month(value: object, field: str) -> date:
    if type(value) is not date or value.day != 1 or not START_MONTH <= value <= END_MONTH:
        raise ScenarioRunnerValidationError(f"{field} must be a scenario first-of-month date")
    return value


def _hash(payload: object) -> str:
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":"), allow_nan=False).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _station(value: object) -> str:
    if value not in CANONICAL_STATION_IDS:
        raise ScenarioRunnerValidationError("station_id must be canonical")
    return str(value)


def _following(value: date) -> date:
    return date(value.year + (value.month == 12), 1 if value.month == 12 else value.month + 1, 1)


@dataclass(frozen=True)
class CoralRestorationDose:
    month: date
    station_id: str
    requested_cover_pct: float
    survival_fraction: float
    capacity_pct: float
    evidence_id: str

    def __post_init__(self) -> None:
        object.__setattr__(self, "month", _month(self.month, "month"))
        object.__setattr__(self, "station_id", _station(self.station_id))
        for name in ("requested_cover_pct", "capacity_pct"):
            object.__setattr__(self, name, _finite(getattr(self, name), name, upper=100.0))
        object.__setattr__(self, "survival_fraction", _finite(self.survival_fraction, "survival_fraction", upper=1.0))
        object.__setattr__(self, "evidence_id", _text(self.evidence_id, "evidence_id"))

    def payload(self) -> dict[str, object]:
        return {"kind": "coral_restoration", **self.__dict__, "month": self.month.isoformat()}


@dataclass(frozen=True)
class MacroalgaeRemovalDose:
    month: date
    station_id: str
    removal_pct_points: float
    evidence_id: str

    def __post_init__(self) -> None:
        object.__setattr__(self, "month", _month(self.month, "month"))
        object.__setattr__(self, "station_id", _station(self.station_id))
        object.__setattr__(self, "removal_pct_points", _finite(self.removal_pct_points, "removal_pct_points", upper=100.0))
        object.__setattr__(self, "evidence_id", _text(self.evidence_id, "evidence_id"))

    def payload(self) -> dict[str, object]:
        return {"kind": "macroalgae_removal", **self.__dict__, "month": self.month.isoformat()}


@dataclass(frozen=True)
class GrazingDose:
    start_month: date
    end_month: date
    station_id: str
    monthly_fraction_removed: float
    evidence_id: str

    def __post_init__(self) -> None:
        start, end = _month(self.start_month, "start_month"), _month(self.end_month, "end_month")
        if start > end:
            raise ScenarioRunnerValidationError("grazing dose end_month must not precede start_month")
        object.__setattr__(self, "start_month", start)
        object.__setattr__(self, "end_month", end)
        object.__setattr__(self, "station_id", _station(self.station_id))
        object.__setattr__(self, "monthly_fraction_removed", _finite(self.monthly_fraction_removed, "monthly_fraction_removed", upper=1.0))
        object.__setattr__(self, "evidence_id", _text(self.evidence_id, "evidence_id"))

    def payload(self) -> dict[str, object]:
        return {"kind": "grazing", **self.__dict__, "start_month": self.start_month.isoformat(), "end_month": self.end_month.isoformat()}


@dataclass(frozen=True)
class LarvalRecruitmentDose:
    start_month: date
    end_month: date
    station_id: str
    fraction_of_free_substrate_per_month: float
    evidence_id: str

    def __post_init__(self) -> None:
        start, end = _month(self.start_month, "start_month"), _month(self.end_month, "end_month")
        if start > end:
            raise ScenarioRunnerValidationError("larval dose end_month must not precede start_month")
        object.__setattr__(self, "start_month", start)
        object.__setattr__(self, "end_month", end)
        object.__setattr__(self, "station_id", _station(self.station_id))
        object.__setattr__(self, "fraction_of_free_substrate_per_month", _finite(self.fraction_of_free_substrate_per_month, "fraction_of_free_substrate_per_month", upper=1.0))
        object.__setattr__(self, "evidence_id", _text(self.evidence_id, "evidence_id"))

    def payload(self) -> dict[str, object]:
        return {"kind": "larval_recruitment", **self.__dict__, "start_month": self.start_month.isoformat(), "end_month": self.end_month.isoformat()}


Dose = CoralRestorationDose | MacroalgaeRemovalDose | GrazingDose | LarvalRecruitmentDose


@dataclass(frozen=True)
class InterventionSchedule:
    arm: str
    schedule_id: str
    model_version: str
    evidence_id: str
    doses: tuple[Dose, ...]
    placebo: bool = False
    content_hash: str | None = None

    def __post_init__(self) -> None:
        if self.arm not in {"control", "intervention"} or type(self.placebo) is not bool:
            raise ScenarioRunnerValidationError("schedule arm or placebo is invalid")
        doses = tuple(self.doses)
        if any(not isinstance(item, (CoralRestorationDose, MacroalgaeRemovalDose, GrazingDose, LarvalRecruitmentDose)) for item in doses):
            raise ScenarioRunnerValidationError("schedule doses are invalid")
        if self.arm == "control" and (doses or self.placebo):
            raise ScenarioRunnerValidationError("control schedule must be an explicit zero-dose schedule")
        if self.arm == "intervention" and not doses and not self.placebo:
            raise ScenarioRunnerValidationError("intervention requires doses or explicit placebo")
        object.__setattr__(self, "schedule_id", _text(self.schedule_id, "schedule_id"))
        object.__setattr__(self, "model_version", _text(self.model_version, "model_version"))
        object.__setattr__(self, "evidence_id", _text(self.evidence_id, "evidence_id"))
        ordered = tuple(sorted(doses, key=lambda item: _hash(item.payload())))
        object.__setattr__(self, "doses", ordered)
        expected = _hash({"arm": self.arm, "schedule_id": self.schedule_id, "model_version": self.model_version, "evidence_id": self.evidence_id, "placebo": self.placebo, "doses": [item.payload() for item in ordered]})
        if self.content_hash is not None and self.content_hash != expected:
            raise ScenarioRunnerValidationError("schedule content_hash does not match canonical content")
        object.__setattr__(self, "content_hash", expected)


@dataclass(frozen=True)
class ProcessInitialState:
    process_draw_id: str
    state: MonthlyCoupledState

    def __post_init__(self) -> None:
        object.__setattr__(self, "process_draw_id", _text(self.process_draw_id, "process_draw_id"))
        if not isinstance(self.state, MonthlyCoupledState) or self.state.month != START_MONTH:
            raise ScenarioRunnerValidationError("initial state must be a January 2026 MonthlyCoupledState")

    def payload(self) -> dict[str, object]:
        return {"process_draw_id": self.process_draw_id, "month": self.state.month.isoformat(), "station_ids": self.state.station_ids,
                "coral_cover_pct": self.state.coral_cover_pct, "macroalgae_cover_pct": self.state.macroalgae_cover_pct,
                "biodiversity_index": self.state.biodiversity_index}


@dataclass(frozen=True)
class ProcessInitialStateSet:
    states: tuple[ProcessInitialState, ...]
    content_hash: str | None = None

    def __post_init__(self) -> None:
        states = tuple(self.states)
        if not states or any(not isinstance(item, ProcessInitialState) for item in states) or len({item.process_draw_id for item in states}) != len(states):
            raise ScenarioRunnerValidationError("initial states require unique process draw IDs")
        ordered = tuple(sorted(states, key=lambda item: item.process_draw_id))
        expected = _hash([item.payload() for item in ordered])
        if self.content_hash is not None and self.content_hash != expected:
            raise ScenarioRunnerValidationError("initial state content_hash does not match canonical biology")
        object.__setattr__(self, "states", ordered)
        object.__setattr__(self, "content_hash", expected)


@dataclass(frozen=True)
class PairedRunSpecification:
    plan: PairedExperimentPlan
    initial_states: ProcessInitialStateSet
    control_schedule: InterventionSchedule
    intervention_schedule: InterventionSchedule

    def __post_init__(self) -> None:
        if not isinstance(self.plan, PairedExperimentPlan) or not isinstance(self.initial_states, ProcessInitialStateSet) or not isinstance(self.control_schedule, InterventionSchedule) or not isinstance(self.intervention_schedule, InterventionSchedule):
            raise ScenarioRunnerValidationError("paired run requires validated plan, states, and schedules")
        expected = {draw.process_draw_id for draw in self.plan.process_draws}
        if {item.process_draw_id for item in self.initial_states.states} != expected:
            raise ScenarioRunnerValidationError("initial states must map every process draw exactly once")
        if self.plan.initial_state_hash != self.initial_states.content_hash or self.plan.control_dose_hash != self.control_schedule.content_hash or self.plan.intervention_dose_hash != self.intervention_schedule.content_hash:
            raise ScenarioRunnerValidationError("plan hashes do not match paired run inputs")
        if self.control_schedule.arm != "control" or self.intervention_schedule.arm != "intervention":
            raise ScenarioRunnerValidationError("paired schedules must be control and intervention")


@dataclass(frozen=True)
class PairedTrajectory:
    key: PairedDrawKey
    control: tuple[MonthlyCoupledState, ...]
    intervention: tuple[MonthlyCoupledState, ...]

    def __post_init__(self) -> None:
        control, intervention = tuple(self.control), tuple(self.intervention)
        expected_months = tuple(date(year, month, 1) for year in range(2026, 2051) for month in range(1, 13))
        if not isinstance(self.key, PairedDrawKey) or len(control) != MONTH_COUNT or len(intervention) != MONTH_COUNT or any(not isinstance(item, MonthlyCoupledState) for item in (*control, *intervention)):
            raise ScenarioRunnerValidationError("trajectory must contain two 300-month state sequences")
        if tuple(item.month for item in control) != expected_months or tuple(item.month for item in intervention) != expected_months:
            raise ScenarioRunnerValidationError("trajectory months are invalid")
        object.__setattr__(self, "control", control)
        object.__setattr__(self, "intervention", intervention)


@dataclass(frozen=True)
class PairedScenarioRun:
    specification: PairedRunSpecification
    trajectories: tuple[PairedTrajectory, ...]
    endpoints: tuple[PairedEndpointResult, ...]

    def __post_init__(self) -> None:
        trajectories, endpoints = tuple(self.trajectories), tuple(self.endpoints)
        expected = {key for key in self.specification.plan.draw_keys}
        if not isinstance(self.specification, PairedRunSpecification) or {item.key for item in trajectories} != expected or len(trajectories) != len(expected):
            raise ScenarioRunnerValidationError("run must cover every paired draw once")
        if len(endpoints) != len(expected) * len(CANONICAL_STATION_IDS) or any(not isinstance(item, PairedEndpointResult) for item in endpoints):
            raise ScenarioRunnerValidationError("run endpoints are incomplete")
        object.__setattr__(self, "trajectories", tuple(sorted(trajectories, key=lambda item: item.key)))
        object.__setattr__(self, "endpoints", tuple(sorted(endpoints, key=lambda item: (item.key, item.station_id))))


class MonthlyPairedScenarioRunner:
    """Run no-RNG control/intervention pairs; it neither assimilates nor persists."""

    def run(self, specification: PairedRunSpecification) -> PairedScenarioRun:
        if not isinstance(specification, PairedRunSpecification):
            raise TypeError("specification must be a PairedRunSpecification")
        members = {item.forcing_member_id: item for item in specification.plan.forcing_members}
        draws = {item.process_draw_id: item for item in specification.plan.process_draws}
        initials = {item.process_draw_id: item.state for item in specification.initial_states.states}
        trajectories: list[PairedTrajectory] = []
        endpoints: list[PairedEndpointResult] = []
        for key in specification.plan.draw_keys:
            member, draw, biological = members[key.forcing_member_id], draws[key.process_draw_id], initials[key.process_draw_id]
            control = [_rewrap(biological, member.monthly_forcings[0])]
            intervention = [_apply_effects(_rewrap(biological, member.monthly_forcings[0]), specification.intervention_schedule)]
            for forcing in member.monthly_forcings[1:]:
                control.append(step_month(control[-1], forcing, draw.connectivity, draw.parameters))
                intervention.append(_apply_effects(step_month(intervention[-1], forcing, draw.connectivity, draw.parameters), specification.intervention_schedule))
            trajectory = PairedTrajectory(key, tuple(control), tuple(intervention))
            trajectories.append(trajectory)
            for index, station_id in enumerate(CANONICAL_STATION_IDS):
                endpoints.append(PairedEndpointResult(key, station_id, END_MONTH, trajectory.control[-1].coral_cover_pct[index], trajectory.intervention[-1].coral_cover_pct[index], member.content_hash, draw.content_hash, specification.plan.initial_state_hash, "simulated", False))
        return PairedScenarioRun(specification, tuple(trajectories), tuple(endpoints))


def _rewrap(state: MonthlyCoupledState, forcing) -> MonthlyCoupledState:
    return MonthlyCoupledState(forcing.month, state.station_ids, state.coral_cover_pct, state.macroalgae_cover_pct, state.biodiversity_index, forcing)


def _apply_effects(state: MonthlyCoupledState, schedule: InterventionSchedule) -> MonthlyCoupledState:
    if schedule.arm == "control" or not schedule.doses:
        return state
    coral, macroalgae, biodiversity = list(state.coral_cover_pct), list(state.macroalgae_cover_pct), list(state.biodiversity_index)
    active = [item for item in schedule.doses if _active(item, state.month)]
    for index, station_id in enumerate(state.station_ids):
        removals = sum(item.removal_pct_points for item in active if isinstance(item, MacroalgaeRemovalDose) and item.station_id == station_id)
        grazings = [item.monthly_fraction_removed for item in active if isinstance(item, GrazingDose) and item.station_id == station_id]
        restorations = [item for item in active if isinstance(item, CoralRestorationDose) and item.station_id == station_id]
        recruitments = sum(item.fraction_of_free_substrate_per_month for item in active if isinstance(item, LarvalRecruitmentDose) and item.station_id == station_id)
        next_macro = max(0.0, macroalgae[index] - min(removals, macroalgae[index]))
        for fraction in grazings:
            next_macro *= 1.0 - fraction
        capacity = min((item.capacity_pct for item in restorations), default=100.0)
        restored = min(sum(item.requested_cover_pct * item.survival_fraction for item in restorations), max(0.0, capacity - coral[index]), max(0.0, 100.0 - coral[index] - next_macro))
        next_coral = coral[index] + restored
        recruited = max(0.0, 100.0 - next_coral - next_macro) * min(1.0, recruitments)
        coral[index], macroalgae[index], biodiversity[index] = project_biological_components(next_coral + recruited, next_macro, biodiversity[index])
    return MonthlyCoupledState(state.month, state.station_ids, tuple(coral), tuple(macroalgae), tuple(biodiversity), state.forcing)


def _active(dose: Dose, month: date) -> bool:
    if isinstance(dose, (CoralRestorationDose, MacroalgaeRemovalDose)):
        return dose.month == month
    return dose.start_month <= month <= dose.end_month


__all__ = [
    "CoralRestorationDose", "GrazingDose", "InterventionSchedule", "LarvalRecruitmentDose", "MacroalgaeRemovalDose",
    "MonthlyPairedScenarioRunner", "PairedRunSpecification", "PairedScenarioRun", "PairedTrajectory", "ProcessInitialState",
    "ProcessInitialStateSet", "ScenarioRunnerValidationError",
]
