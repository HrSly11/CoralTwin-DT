"""Offline contracts for paired SSP2-4.5 scenario endpoints."""

from __future__ import annotations

from datetime import date, datetime, timedelta, timezone
import hashlib
import random
import unittest

from operational.coupled_state import ConnectivityMatrix, MonthlyForcing, MonthlyTransitionParameters
from operational.scenario_experiment import (
    PairedEndpointResult,
    PairedExperimentPlan,
    ProcessDraw,
    ScenarioExperimentValidationError,
    StratumAssignment,
    ForcingEnsembleMember,
    compute_forcing_content_hash,
    compute_process_content_hash,
    compute_stratum_assignment_content_hash,
    summarize_paired_endpoints,
)
from operational.stations import CANONICAL_STATIONS


UTC = timezone.utc
STATION_IDS = tuple(station.station_id for station in CANONICAL_STATIONS)
HASH = hashlib.sha256(b"fixture").hexdigest()


def values(value: float) -> tuple[float, ...]:
    return (value,) * len(STATION_IDS)


def months() -> tuple[MonthlyForcing, ...]:
    return tuple(
        MonthlyForcing(date(year, month, 1), values(28.0), values(0.0), values(3.5))
        for year in range(2026, 2051) for month in range(1, 13)
    )


def parameters() -> MonthlyTransitionParameters:
    return MonthlyTransitionParameters(0.01, 0.01, 0.01, 0.01, 0.01, 0.01, 0.01, 0.01)


def forcing(member_id: str = "member-a", **changes: object) -> ForcingEnsembleMember:
    values_ = dict(forcing_member_id=member_id, source_id="Model-A", grid_id="gn", experiment_id="ssp245", monthly_forcings=months())
    values_.update(changes)
    values_.setdefault("content_hash", compute_forcing_content_hash(**values_))
    return ForcingEnsembleMember(**values_)


def draw(draw_id: str = "draw-a", **changes: object) -> ProcessDraw:
    values_ = dict(process_draw_id=draw_id, parameters=parameters(), connectivity=ConnectivityMatrix.default())
    values_.update(changes)
    values_.setdefault("content_hash", compute_process_content_hash(**values_))
    return ProcessDraw(**values_)


def assignment(**changes: object) -> StratumAssignment:
    values_ = dict(assignment_id="priority-v1", prioritized_station_ids=STATION_IDS[:10], non_prioritized_station_ids=STATION_IDS[10:], assignment_cutoff=datetime(2025, 12, 31, tzinfo=UTC), evidence_kind="derived", rationale="pre-specified vulnerability ranking")
    values_.update(changes)
    values_.setdefault("content_hash", compute_stratum_assignment_content_hash(**values_))
    return StratumAssignment(**values_)


def plan(**changes: object) -> PairedExperimentPlan:
    values_ = dict(forcing_members=(forcing(),), process_draws=(draw(),), assignment=assignment(), initial_state_hash=HASH, climate_pathway="ssp245", control_dose_hash=HASH, intervention_dose_hash=HASH)
    values_.update(changes)
    return PairedExperimentPlan(**values_)


def endpoints(current: PairedExperimentPlan, *, control: float = 29.0, intervention: float = 35.0) -> tuple[PairedEndpointResult, ...]:
    return tuple(
        PairedEndpointResult(key=key, station_id=station_id, endpoint_month=date(2050, 12, 1), control_coral_cover_pct=control, intervention_coral_cover_pct=intervention, forcing_content_hash=next(member.content_hash for member in current.forcing_members if member.forcing_member_id == key.forcing_member_id), process_content_hash=next(draw_.content_hash for draw_ in current.process_draws if draw_.process_draw_id == key.process_draw_id), initial_state_hash=current.initial_state_hash, evidence_kind="simulated", causal_claim=False)
        for key in current.draw_keys for station_id in STATION_IDS
    )


class PairedScenarioExperimentTests(unittest.TestCase):
    def test_content_hash_helpers_are_deterministic_and_bind_execution_inputs(self) -> None:
        member = forcing()
        self.assertEqual(member.content_hash, compute_forcing_content_hash(member.forcing_member_id, member.source_id, member.grid_id, member.experiment_id, member.monthly_forcings))
        changed_sst = list(member.monthly_forcings)
        changed_sst[0] = MonthlyForcing(changed_sst[0].month, values(28.1), values(0.0), values(3.5))
        with self.assertRaises(ScenarioExperimentValidationError):
            ForcingEnsembleMember(member.forcing_member_id, member.source_id, member.grid_id, member.experiment_id, member.content_hash, tuple(changed_sst))
        with self.assertRaises(ScenarioExperimentValidationError):
            ForcingEnsembleMember(member.forcing_member_id, member.source_id, member.grid_id, member.experiment_id, member.content_hash, member.monthly_forcings[1:] + member.monthly_forcings[:1])

        process = draw()
        self.assertEqual(process.content_hash, compute_process_content_hash(process.process_draw_id, process.parameters, process.connectivity))
        with self.assertRaises(ScenarioExperimentValidationError):
            ProcessDraw(process.process_draw_id, MonthlyTransitionParameters(0.02, *(0.01,) * 7), process.connectivity, process.content_hash)
        weights = [list(row) for row in process.connectivity.weights]
        weights[0][0], weights[0][1] = 0.5, 0.5
        changed_connectivity = ConnectivityMatrix(process.connectivity.station_ids, tuple(tuple(row) for row in weights))
        with self.assertRaises(ScenarioExperimentValidationError):
            ProcessDraw(process.process_draw_id, process.parameters, changed_connectivity, process.content_hash)

        strata = assignment()
        self.assertEqual(strata.content_hash, compute_stratum_assignment_content_hash(strata.assignment_id, strata.prioritized_station_ids, strata.non_prioritized_station_ids, strata.assignment_cutoff, strata.evidence_kind, strata.rationale))
        with self.assertRaises(ScenarioExperimentValidationError):
            StratumAssignment(strata.assignment_id, strata.prioritized_station_ids, strata.non_prioritized_station_ids, strata.assignment_cutoff, strata.evidence_kind, "changed rationale", strata.content_hash)
        with self.assertRaises(ScenarioExperimentValidationError):
            StratumAssignment(strata.assignment_id, strata.prioritized_station_ids[:-1] + strata.non_prioritized_station_ids[:1], (strata.prioritized_station_ids[-1],) + strata.non_prioritized_station_ids[1:], strata.assignment_cutoff, strata.evidence_kind, strata.rationale, strata.content_hash)

    def test_forcing_requires_exact_ssp245_hash_axis_and_contiguous_months(self) -> None:
        self.assertEqual(300, len(forcing().monthly_forcings))
        for changes in ({"experiment_id": "ssp370"}, {"content_hash": "no"}, {"monthly_forcings": months()[:-1]}, {"monthly_forcings": months()[1:]}, {"monthly_forcings": (object(),) * 300}):
            with self.subTest(changes=changes):
                with self.assertRaises(ScenarioExperimentValidationError):
                    forcing(**changes)

    def test_assignment_is_an_exact_frozen_partition_with_safe_evidence(self) -> None:
        self.assertEqual(STATION_IDS[:10], assignment().prioritized_station_ids)
        for changes in (
            {"prioritized_station_ids": STATION_IDS[:10] + STATION_IDS[:1]}, {"non_prioritized_station_ids": ()},
            {"evidence_kind": "simulated"}, {"assignment_cutoff": datetime(2025, 12, 31)},
            {"assignment_cutoff": datetime(2026, 1, 1, tzinfo=UTC)},
            {"assignment_cutoff": datetime(2050, 1, 1, tzinfo=UTC)},
            {"assignment_cutoff": datetime(2025, 12, 31, 19, tzinfo=timezone(timedelta(hours=-5)))},
        ):
            with self.subTest(changes=changes):
                with self.assertRaises(ScenarioExperimentValidationError):
                    assignment(**changes)
        with self.assertRaises(Exception):
            assignment().rationale = "changed"  # type: ignore[misc]
        offset = assignment(assignment_cutoff=datetime(2025, 12, 31, 18, tzinfo=timezone(timedelta(hours=-5))))
        self.assertEqual(datetime(2025, 12, 31, 23, tzinfo=UTC), offset.assignment_cutoff)

    def test_plan_builds_four_cells_for_each_cartesian_pair_and_no_implicit_dose(self) -> None:
        current = plan(forcing_members=(forcing("z"), forcing("a")), process_draws=(draw("z"), draw("a")))
        self.assertEqual(("a", "a"), (current.draw_keys[0].forcing_member_id, current.draw_keys[0].process_draw_id))
        self.assertEqual(16, len(current.cells))
        for cell in current.cells:
            self.assertEqual(current.initial_state_hash, cell.initial_state_hash)
        with self.assertRaises(ScenarioExperimentValidationError):
            plan(control_dose_hash="bad")
        with self.assertRaises(ScenarioExperimentValidationError):
            draw(content_hash="bad")

    def test_endpoint_contract_rejects_bounds_endpoint_and_non_simulated_claims(self) -> None:
        current = plan()
        base = endpoints(current)[0]
        for changes in ({"endpoint_month": date(2050, 11, 1)}, {"control_coral_cover_pct": 101.0}, {"evidence_kind": "derived"}, {"causal_claim": True}):
            with self.subTest(changes=changes):
                with self.assertRaises(ScenarioExperimentValidationError):
                    PairedEndpointResult(**{**base.__dict__, **changes})

    def test_results_require_complete_unique_axis_and_matching_hashes(self) -> None:
        current = plan()
        source = endpoints(current)
        for results in (source[:-1], source + source[:1], tuple(PairedEndpointResult(**{**source[0].__dict__, "forcing_content_hash": hashlib.sha256(b"other").hexdigest()}) if index == 0 else item for index, item in enumerate(source))):
            with self.subTest(size=len(results)):
                with self.assertRaises(ScenarioExperimentValidationError):
                    summarize_paired_endpoints(current, results)

    def test_summary_is_paired_strict_threshold_deterministic_and_noncausal(self) -> None:
        current = plan(forcing_members=(forcing("a"), forcing("b")))
        results = endpoints(current, control=30.0, intervention=35.0)
        first = summarize_paired_endpoints(current, results)
        second = summarize_paired_endpoints(current, tuple(reversed(results)))
        self.assertEqual(first, second)
        station = first.station_summaries[0]
        self.assertEqual((0.0, 1.0, 5.0, 5.0, 5.0, 5.0), (station.control_probability_over_30, station.intervention_probability_over_30, station.delta_mean, station.delta_median, station.delta_p025, station.delta_p975))
        self.assertTrue(first.model_based)
        self.assertFalse(first.causal_claim)
        with self.assertRaises(ScenarioExperimentValidationError):
            type(first)(first.station_summaries, first.stratum_summaries, first.intervention_minus_control_mean, first.prioritized_minus_non_prioritized_delta, model_based=False)

    def test_group_metrics_weight_stations_equally_and_identical_arms_falsify(self) -> None:
        current = plan(forcing_members=(forcing("a"), forcing("b"), forcing("c")))
        source = list(endpoints(current, control=10.0, intervention=10.0))
        for index, result in enumerate(source):
            if result.station_id == STATION_IDS[0] and result.key.forcing_member_id == "a":
                source[index] = PairedEndpointResult(**{**result.__dict__, "control_coral_cover_pct": 20.0, "intervention_coral_cover_pct": 20.0})
        summary = summarize_paired_endpoints(current, source)
        self.assertEqual(0.0, summary.intervention_minus_control_mean)
        self.assertEqual(0.0, summary.prioritized_minus_non_prioritized_delta)
        self.assertAlmostEqual(0.0, summary.stratum_summaries[0].delta_mean)

    def test_module_is_pure_frozen_and_does_not_use_random_or_disk(self) -> None:
        before = random.getstate()
        current = plan()
        summarize_paired_endpoints(current, endpoints(current))
        self.assertEqual(before, random.getstate())
        with self.assertRaises(Exception):
            current.cells = ()  # type: ignore[misc]
        summaries = list(summarize_paired_endpoints(current, endpoints(current)).station_summaries)
        summary = summarize_paired_endpoints(current, endpoints(current))
        self.assertIsInstance(type(summary)(summaries, summary.stratum_summaries, summary.intervention_minus_control_mean, summary.prioritized_minus_non_prioritized_delta).station_summaries, tuple)
