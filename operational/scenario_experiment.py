"""Pure contracts and summaries for paired SSP2-4.5 scenario endpoints.

This module deliberately does not simulate a trajectory.  It validates the
inputs and endpoints supplied by a later scenario runner, then summarizes
paired draws without treating model draws as independent stations.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, timezone
import hashlib
import json
import math
import re
from typing import Iterable

from .coupled_state import ConnectivityMatrix, MonthlyForcing, MonthlyTransitionParameters
from .stations import CANONICAL_STATIONS


CANONICAL_STATION_IDS = tuple(station.station_id for station in CANONICAL_STATIONS)
_SHA256 = re.compile(r"[0-9a-f]{64}\Z")
_START_MONTH = date(2026, 1, 1)
_END_MONTH = date(2050, 12, 1)
_MONTH_COUNT = 300


def compute_forcing_content_hash(
    forcing_member_id: str,
    source_id: str,
    grid_id: str,
    experiment_id: str,
    monthly_forcings: Iterable[object],
    **_ignored: object,
) -> str:
    forcings_payload = []
    for f in monthly_forcings:
        if isinstance(f, MonthlyForcing):
            forcings_payload.append([f.month.isoformat(), list(f.sst_deg_c), list(f.dhw_deg_c_weeks), list(f.omega_arag)])
        else:
            forcings_payload.append(str(f))
    payload = {
        "forcing_member_id": str(forcing_member_id),
        "source_id": str(source_id),
        "grid_id": str(grid_id),
        "experiment_id": str(experiment_id),
        "monthly_forcings": forcings_payload,
    }
    return hashlib.sha256(json.dumps(payload, sort_keys=True).encode("utf-8")).hexdigest()


def compute_process_content_hash(
    process_draw_id: str,
    parameters: MonthlyTransitionParameters,
    connectivity: ConnectivityMatrix,
    **_ignored: object,
) -> str:
    params_payload = (
        [
            parameters.coral_growth_per_month,
            parameters.macroalgae_growth_per_month,
            parameters.heat_mortality_per_dhw,
            parameters.grazing_per_month,
            parameters.larval_recruitment_per_month,
            parameters.biodiversity_recovery_per_month,
            parameters.biodiversity_macroalgae_loss_per_month,
            parameters.biodiversity_heat_loss_per_dhw,
        ]
        if isinstance(parameters, MonthlyTransitionParameters)
        else str(parameters)
    )
    conn_payload = (
        {
            "station_ids": list(connectivity.station_ids),
            "weights": [list(row) for row in connectivity.weights],
        }
        if isinstance(connectivity, ConnectivityMatrix)
        else str(connectivity)
    )
    payload = {
        "process_draw_id": str(process_draw_id),
        "parameters": params_payload,
        "connectivity": conn_payload,
    }
    return hashlib.sha256(json.dumps(payload, sort_keys=True).encode("utf-8")).hexdigest()


def compute_stratum_assignment_content_hash(
    assignment_id: str,
    prioritized_station_ids: Iterable[str],
    non_prioritized_station_ids: Iterable[str],
    assignment_cutoff: datetime,
    evidence_kind: str,
    rationale: str,
    **_ignored: object,
) -> str:
    cutoff_utc = assignment_cutoff.astimezone(timezone.utc).isoformat() if isinstance(assignment_cutoff, datetime) else str(assignment_cutoff)
    payload = {
        "assignment_id": str(assignment_id),
        "prioritized_station_ids": list(prioritized_station_ids),
        "non_prioritized_station_ids": list(non_prioritized_station_ids),
        "assignment_cutoff": cutoff_utc,
        "evidence_kind": str(evidence_kind),
        "rationale": str(rationale),
    }
    return hashlib.sha256(json.dumps(payload, sort_keys=True).encode("utf-8")).hexdigest()


class ScenarioExperimentValidationError(ValueError):
    """Raised when a paired scenario experiment is incomplete or ambiguous."""


def _text(value: object, field: str) -> str:
    if not isinstance(value, str) or not value.strip() or value != value.strip():
        raise ScenarioExperimentValidationError(f"{field} must be a non-empty normalized string")
    return value


def _hash(value: object, field: str) -> str:
    if not isinstance(value, str) or not _SHA256.fullmatch(value):
        raise ScenarioExperimentValidationError(f"{field} must be a lowercase SHA-256 hash")
    return value


def _month(value: object, field: str, *, endpoint: bool = False) -> date:
    if type(value) is not date or value.day != 1:
        raise ScenarioExperimentValidationError(f"{field} must be a first-of-month date")
    if endpoint and value != _END_MONTH:
        raise ScenarioExperimentValidationError("endpoint_month must be December 2050")
    return value


def _utc(value: object, field: str) -> datetime:
    if not isinstance(value, datetime) or value.tzinfo is None or value.utcoffset() is None:
        raise ScenarioExperimentValidationError(f"{field} must be timezone-aware")
    return value.astimezone(timezone.utc)


def _finite_cover(value: object, field: str) -> float:
    if not isinstance(value, (int, float)) or isinstance(value, bool) or not math.isfinite(value):
        raise ScenarioExperimentValidationError(f"{field} must be finite")
    result = float(value)
    if not 0.0 <= result <= 100.0:
        raise ScenarioExperimentValidationError(f"{field} must be within [0, 100]")
    return result


@dataclass(frozen=True)
class ForcingEnsembleMember:
    forcing_member_id: str
    source_id: str
    grid_id: str
    experiment_id: str
    content_hash: str
    monthly_forcings: tuple[MonthlyForcing, ...]

    def __post_init__(self) -> None:
        object.__setattr__(self, "forcing_member_id", _text(self.forcing_member_id, "forcing_member_id"))
        object.__setattr__(self, "source_id", _text(self.source_id, "source_id"))
        object.__setattr__(self, "grid_id", _text(self.grid_id, "grid_id"))
        if self.experiment_id != "ssp245":
            raise ScenarioExperimentValidationError("experiment_id must be ssp245")
        object.__setattr__(self, "content_hash", _hash(self.content_hash, "content_hash"))
        try:
            forcings = tuple(self.monthly_forcings)
        except TypeError as error:
            raise ScenarioExperimentValidationError("monthly_forcings must be iterable") from error
        if len(forcings) != _MONTH_COUNT or any(not isinstance(item, MonthlyForcing) for item in forcings):
            raise ScenarioExperimentValidationError("monthly_forcings must contain exactly 300 MonthlyForcing values")
        expected = tuple(date(year, month, 1) for year in range(2026, 2051) for month in range(1, 13))
        if tuple(item.month for item in forcings) != expected:
            raise ScenarioExperimentValidationError("monthly_forcings must be contiguous from January 2026 through December 2050")
        expected_hash = compute_forcing_content_hash(
            self.forcing_member_id, self.source_id, self.grid_id, self.experiment_id, forcings
        )
        if self.content_hash != expected_hash:
            raise ScenarioExperimentValidationError("content_hash does not match canonical forcing values")
        object.__setattr__(self, "monthly_forcings", forcings)


@dataclass(frozen=True, order=True)
class PairedDrawKey:
    forcing_member_id: str
    process_draw_id: str

    def __post_init__(self) -> None:
        object.__setattr__(self, "forcing_member_id", _text(self.forcing_member_id, "forcing_member_id"))
        object.__setattr__(self, "process_draw_id", _text(self.process_draw_id, "process_draw_id"))


@dataclass(frozen=True)
class ProcessDraw:
    process_draw_id: str
    parameters: MonthlyTransitionParameters
    connectivity: ConnectivityMatrix
    content_hash: str

    def __post_init__(self) -> None:
        object.__setattr__(self, "process_draw_id", _text(self.process_draw_id, "process_draw_id"))
        if not isinstance(self.parameters, MonthlyTransitionParameters) or not isinstance(self.connectivity, ConnectivityMatrix):
            raise ScenarioExperimentValidationError("process draw requires validated parameters and connectivity")
        object.__setattr__(self, "content_hash", _hash(self.content_hash, "content_hash"))
        expected_hash = compute_process_content_hash(
            self.process_draw_id, self.parameters, self.connectivity
        )
        if self.content_hash != expected_hash:
            raise ScenarioExperimentValidationError("content_hash does not match process parameters")


@dataclass(frozen=True)
class StratumAssignment:
    assignment_id: str
    prioritized_station_ids: tuple[str, ...]
    non_prioritized_station_ids: tuple[str, ...]
    assignment_cutoff: datetime
    evidence_kind: str
    rationale: str
    content_hash: str

    def __post_init__(self) -> None:
        object.__setattr__(self, "assignment_id", _text(self.assignment_id, "assignment_id"))
        try:
            prioritized = tuple(self.prioritized_station_ids)
            non_prioritized = tuple(self.non_prioritized_station_ids)
        except TypeError as error:
            raise ScenarioExperimentValidationError("station strata must be iterable") from error
        if not prioritized or not non_prioritized or any(not isinstance(item, str) for item in (*prioritized, *non_prioritized)):
            raise ScenarioExperimentValidationError("both strata require station IDs")
        assigned = (*prioritized, *non_prioritized)
        if len(set(assigned)) != len(assigned) or set(assigned) != set(CANONICAL_STATION_IDS):
            raise ScenarioExperimentValidationError("strata must partition the canonical station axis exactly")
        object.__setattr__(self, "prioritized_station_ids", prioritized)
        object.__setattr__(self, "non_prioritized_station_ids", non_prioritized)
        cutoff = _utc(self.assignment_cutoff, "assignment_cutoff")
        if cutoff >= datetime.combine(_START_MONTH, datetime.min.time(), tzinfo=timezone.utc):
            raise ScenarioExperimentValidationError("assignment_cutoff must be strictly before the January 2026 forcing baseline")
        object.__setattr__(self, "assignment_cutoff", cutoff)
        if self.evidence_kind not in {"derived", "observed"}:
            raise ScenarioExperimentValidationError("evidence_kind must be derived or observed")
        object.__setattr__(self, "rationale", _text(self.rationale, "rationale"))
        object.__setattr__(self, "content_hash", _hash(self.content_hash, "content_hash"))
        expected_hash = compute_stratum_assignment_content_hash(
            self.assignment_id, self.prioritized_station_ids, self.non_prioritized_station_ids, cutoff, self.evidence_kind, self.rationale
        )
        if self.content_hash != expected_hash:
            raise ScenarioExperimentValidationError("content_hash does not match stratum values")


@dataclass(frozen=True)
class ExperimentCell:
    key: PairedDrawKey
    stratum: str
    arm: str
    forcing_content_hash: str
    process_content_hash: str
    initial_state_hash: str

    def __post_init__(self) -> None:
        if not isinstance(self.key, PairedDrawKey) or self.stratum not in {"prioritized", "non_prioritized"} or self.arm not in {"control", "intervention"}:
            raise ScenarioExperimentValidationError("experiment cell has an invalid key, stratum, or arm")
        for field in ("forcing_content_hash", "process_content_hash", "initial_state_hash"):
            object.__setattr__(self, field, _hash(getattr(self, field), field))


@dataclass(frozen=True)
class PairedExperimentPlan:
    forcing_members: tuple[ForcingEnsembleMember, ...]
    process_draws: tuple[ProcessDraw, ...]
    assignment: StratumAssignment
    initial_state_hash: str
    climate_pathway: str
    control_dose_hash: str
    intervention_dose_hash: str
    draw_keys: tuple[PairedDrawKey, ...] = ()
    cells: tuple[ExperimentCell, ...] = ()

    def __post_init__(self) -> None:
        try:
            members = tuple(self.forcing_members)
            draws = tuple(self.process_draws)
        except TypeError as error:
            raise ScenarioExperimentValidationError("forcing_members and process_draws must be iterable") from error
        if not members or not draws or any(not isinstance(item, ForcingEnsembleMember) for item in members) or any(not isinstance(item, ProcessDraw) for item in draws):
            raise ScenarioExperimentValidationError("plan requires forcing members and process draws")
        if len({item.forcing_member_id for item in members}) != len(members) or len({item.process_draw_id for item in draws}) != len(draws):
            raise ScenarioExperimentValidationError("forcing member and process draw IDs must be unique")
        if not isinstance(self.assignment, StratumAssignment):
            raise ScenarioExperimentValidationError("assignment must be a StratumAssignment")
        if self.climate_pathway != "ssp245":
            raise ScenarioExperimentValidationError("climate_pathway must be ssp245")
        object.__setattr__(self, "forcing_members", tuple(sorted(members, key=lambda item: item.forcing_member_id)))
        object.__setattr__(self, "process_draws", tuple(sorted(draws, key=lambda item: item.process_draw_id)))
        object.__setattr__(self, "initial_state_hash", _hash(self.initial_state_hash, "initial_state_hash"))
        object.__setattr__(self, "control_dose_hash", _hash(self.control_dose_hash, "control_dose_hash"))
        object.__setattr__(self, "intervention_dose_hash", _hash(self.intervention_dose_hash, "intervention_dose_hash"))
        earliest_forcing_month = min(member.monthly_forcings[0].month for member in self.forcing_members)
        earliest_forcing = datetime.combine(earliest_forcing_month, datetime.min.time(), tzinfo=timezone.utc)
        if self.assignment.assignment_cutoff >= earliest_forcing:
            raise ScenarioExperimentValidationError("assignment_cutoff must precede the earliest forcing month")
        keys = tuple(PairedDrawKey(member.forcing_member_id, draw.process_draw_id) for member in self.forcing_members for draw in self.process_draws)
        if self.draw_keys not in ((), keys) or self.cells not in ((), _cells(keys, self)):
            raise ScenarioExperimentValidationError("draw_keys and cells are generated by the plan")
        object.__setattr__(self, "draw_keys", keys)
        object.__setattr__(self, "cells", _cells(keys, self))


def _cells(keys: tuple[PairedDrawKey, ...], plan: PairedExperimentPlan) -> tuple[ExperimentCell, ...]:
    members = {member.forcing_member_id: member for member in plan.forcing_members}
    draws = {draw.process_draw_id: draw for draw in plan.process_draws}
    return tuple(
        ExperimentCell(key, stratum, arm, members[key.forcing_member_id].content_hash, draws[key.process_draw_id].content_hash, plan.initial_state_hash)
        for key in keys for stratum in ("prioritized", "non_prioritized") for arm in ("control", "intervention")
    )


@dataclass(frozen=True)
class PairedEndpointResult:
    key: PairedDrawKey
    station_id: str
    endpoint_month: date
    control_coral_cover_pct: float
    intervention_coral_cover_pct: float
    forcing_content_hash: str
    process_content_hash: str
    initial_state_hash: str
    evidence_kind: str
    causal_claim: bool

    def __post_init__(self) -> None:
        if not isinstance(self.key, PairedDrawKey) or self.station_id not in CANONICAL_STATION_IDS:
            raise ScenarioExperimentValidationError("endpoint requires a plan key and canonical station")
        object.__setattr__(self, "endpoint_month", _month(self.endpoint_month, "endpoint_month", endpoint=True))
        object.__setattr__(self, "control_coral_cover_pct", _finite_cover(self.control_coral_cover_pct, "control_coral_cover_pct"))
        object.__setattr__(self, "intervention_coral_cover_pct", _finite_cover(self.intervention_coral_cover_pct, "intervention_coral_cover_pct"))
        for field in ("forcing_content_hash", "process_content_hash", "initial_state_hash"):
            object.__setattr__(self, field, _hash(getattr(self, field), field))
        if self.evidence_kind != "simulated" or self.causal_claim is not False:
            raise ScenarioExperimentValidationError("endpoint results are simulated and make no causal claim")


@dataclass(frozen=True)
class StationScenarioSummary:
    station_id: str
    control_probability_over_30: float
    intervention_probability_over_30: float
    delta_mean: float
    delta_median: float
    delta_p025: float
    delta_p975: float


@dataclass(frozen=True)
class StratumScenarioSummary:
    stratum: str
    station_count: int
    control_probability_over_30: float
    intervention_probability_over_30: float
    delta_mean: float


@dataclass(frozen=True)
class ScenarioSummary:
    station_summaries: tuple[StationScenarioSummary, ...]
    stratum_summaries: tuple[StratumScenarioSummary, ...]
    intervention_minus_control_mean: float
    prioritized_minus_non_prioritized_delta: float
    percentile_method: str = "linear_interpolation"
    model_based: bool = True
    causal_claim: bool = False

    def __post_init__(self) -> None:
        if self.percentile_method != "linear_interpolation" or self.model_based is not True or self.causal_claim is not False:
            raise ScenarioExperimentValidationError("scenario summaries are non-causal, model-based linear-percentile summaries")
        try:
            stations = tuple(self.station_summaries)
            strata = tuple(self.stratum_summaries)
        except TypeError as error:
            raise ScenarioExperimentValidationError("scenario summaries must be iterable") from error
        if any(not isinstance(item, StationScenarioSummary) for item in stations) or any(not isinstance(item, StratumScenarioSummary) for item in strata):
            raise ScenarioExperimentValidationError("scenario summary values have invalid types")
        object.__setattr__(self, "station_summaries", stations)
        object.__setattr__(self, "stratum_summaries", strata)


def _percentile(sorted_values: tuple[float, ...], probability: float) -> float:
    index = probability * (len(sorted_values) - 1)
    lower = int(math.floor(index))
    upper = int(math.ceil(index))
    return sorted_values[lower] + (sorted_values[upper] - sorted_values[lower]) * (index - lower)


def summarize_paired_endpoints(plan: PairedExperimentPlan, results: Iterable[PairedEndpointResult]) -> ScenarioSummary:
    """Require full pair/station coverage and summarize model-based paired deltas."""

    if not isinstance(plan, PairedExperimentPlan):
        raise ScenarioExperimentValidationError("plan must be a PairedExperimentPlan")
    try:
        supplied = tuple(results)
    except TypeError as error:
        raise ScenarioExperimentValidationError("results must be iterable") from error
    if any(not isinstance(item, PairedEndpointResult) for item in supplied):
        raise ScenarioExperimentValidationError("results must contain PairedEndpointResult values")
    members = {member.forcing_member_id: member for member in plan.forcing_members}
    draws = {draw.process_draw_id: draw for draw in plan.process_draws}
    expected = {(key, station_id) for key in plan.draw_keys for station_id in CANONICAL_STATION_IDS}
    indexed: dict[tuple[PairedDrawKey, str], PairedEndpointResult] = {}
    for result in supplied:
        identity = (result.key, result.station_id)
        if identity in indexed:
            raise ScenarioExperimentValidationError("duplicate pair/station endpoint")
        member, draw = members.get(result.key.forcing_member_id), draws.get(result.key.process_draw_id)
        if member is None or draw is None or result.forcing_content_hash != member.content_hash or result.process_content_hash != draw.content_hash or result.initial_state_hash != plan.initial_state_hash:
            raise ScenarioExperimentValidationError("endpoint hashes or pair key do not match the plan")
        indexed[identity] = result
    if set(indexed) != expected:
        raise ScenarioExperimentValidationError("results must cover every canonical station for every paired draw")
    stations: list[StationScenarioSummary] = []
    for station_id in CANONICAL_STATION_IDS:
        values = tuple(indexed[(key, station_id)] for key in plan.draw_keys)
        deltas = tuple(sorted(item.intervention_coral_cover_pct - item.control_coral_cover_pct for item in values))
        count = len(values)
        stations.append(StationScenarioSummary(
            station_id, sum(item.control_coral_cover_pct > 30.0 for item in values) / count,
            sum(item.intervention_coral_cover_pct > 30.0 for item in values) / count,
            sum(deltas) / count, _percentile(deltas, 0.5), _percentile(deltas, 0.025), _percentile(deltas, 0.975),
        ))
    station_by_id = {item.station_id: item for item in stations}
    strata = tuple(
        _summarize_stratum(name, ids, station_by_id)
        for name, ids in (("prioritized", plan.assignment.prioritized_station_ids), ("non_prioritized", plan.assignment.non_prioritized_station_ids))
    )
    return ScenarioSummary(tuple(stations), strata, sum(item.delta_mean for item in stations) / len(stations), strata[0].delta_mean - strata[1].delta_mean)


def _summarize_stratum(name: str, station_ids: tuple[str, ...], by_id: dict[str, StationScenarioSummary]) -> StratumScenarioSummary:
    summaries = tuple(by_id[station_id] for station_id in station_ids)
    count = len(summaries)
    return StratumScenarioSummary(name, count, sum(item.control_probability_over_30 for item in summaries) / count, sum(item.intervention_probability_over_30 for item in summaries) / count, sum(item.delta_mean for item in summaries) / count)


__all__ = [
    "ExperimentCell", "ForcingEnsembleMember", "PairedDrawKey", "PairedEndpointResult", "PairedExperimentPlan",
    "ProcessDraw", "ScenarioExperimentValidationError", "ScenarioSummary", "StationScenarioSummary",
    "StratumAssignment", "StratumScenarioSummary", "summarize_paired_endpoints",
]
