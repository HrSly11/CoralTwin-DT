"""Offline contracts for deterministic paired monthly scenarios."""

from __future__ import annotations

import hashlib
import math
import unittest
from datetime import date, datetime, timezone

from operational.coupled_state import CANONICAL_STATION_IDS, ConnectivityMatrix, MonthlyCoupledState, MonthlyForcing, MonthlyTransitionParameters
from operational.monthly_paired_runner import (
    CoralRestorationDose, GrazingDose, InterventionSchedule, LarvalRecruitmentDose,
    MacroalgaeRemovalDose, MonthlyPairedScenarioRunner, PairedRunSpecification,
    ProcessInitialState, ProcessInitialStateSet, ScenarioRunnerValidationError,
)
from operational.scenario_experiment import (
    ForcingEnsembleMember, PairedExperimentPlan, ProcessDraw, StratumAssignment,
    compute_forcing_content_hash, compute_process_content_hash,
    compute_stratum_assignment_content_hash, summarize_paired_endpoints,
)


UTC = timezone.utc
HASH = hashlib.sha256(b"scenario-runner").hexdigest()
JAN = date(2026, 1, 1)


def forcing(month: date) -> MonthlyForcing:
    return MonthlyForcing(month, (28.0,) * 25, (0.0,) * 25, (3.0,) * 25)


def forcings() -> tuple[MonthlyForcing, ...]:
    return tuple(forcing(date(year, month, 1)) for year in range(2026, 2051) for month in range(1, 13))


def process() -> ProcessDraw:
    parameters = MonthlyTransitionParameters(*(0.0,) * 8)
    connectivity = ConnectivityMatrix.default()
    return ProcessDraw("draw-a", parameters, connectivity, compute_process_content_hash("draw-a", parameters, connectivity))


def initial_state() -> MonthlyCoupledState:
    return MonthlyCoupledState(JAN, CANONICAL_STATION_IDS, (30.0,) * 25, (20.0,) * 25, (.5,) * 25, forcing(JAN))


def initial_set(**changes: object) -> ProcessInitialStateSet:
    values: dict[str, object] = {"states": (ProcessInitialState("draw-a", initial_state()),)}
    values.update(changes)
    return ProcessInitialStateSet(**values)


def schedule(arm: str, doses=(), *, placebo: bool = False, **changes: object) -> InterventionSchedule:
    values: dict[str, object] = {"arm": arm, "schedule_id": f"{arm}-schedule", "model_version": "runner-v1", "evidence_id": "doi:10.1/example", "doses": doses, "placebo": placebo}
    values.update(changes)
    return InterventionSchedule(**values)


def plan(initial: ProcessInitialStateSet, control: InterventionSchedule, intervention: InterventionSchedule) -> PairedExperimentPlan:
    member_forcings = forcings()
    member = ForcingEnsembleMember("forcing-a", "model", "grid", "ssp245", compute_forcing_content_hash("forcing-a", "model", "grid", "ssp245", member_forcings), member_forcings)
    assignment = StratumAssignment("assignment", CANONICAL_STATION_IDS[:10], CANONICAL_STATION_IDS[10:], datetime(2025, 12, 1, tzinfo=UTC), "derived", "fixed", compute_stratum_assignment_content_hash("assignment", CANONICAL_STATION_IDS[:10], CANONICAL_STATION_IDS[10:], datetime(2025, 12, 1, tzinfo=UTC), "derived", "fixed"))
    return PairedExperimentPlan((member,), (process(),), assignment, initial.content_hash, "ssp245", control.content_hash, intervention.content_hash)


def specification(control: InterventionSchedule | None = None, intervention: InterventionSchedule | None = None) -> PairedRunSpecification:
    current_initial = initial_set()
    current_control = control or schedule("control")
    current_intervention = intervention or schedule("intervention", placebo=True)
    return PairedRunSpecification(plan(current_initial, current_control, current_intervention), current_initial, current_control, current_intervention)


class MonthlyPairedScenarioRunnerTests(unittest.TestCase):
    def test_hash_linkage_exact_process_mapping_and_control_placebo_are_identical(self) -> None:
        current = specification()
        run = MonthlyPairedScenarioRunner().run(current)
        self.assertEqual((1, 25, 300, 300), (len(run.trajectories), len(run.endpoints), len(run.trajectories[0].control), len(run.trajectories[0].intervention)))
        self.assertEqual(run.trajectories[0].control, run.trajectories[0].intervention)
        self.assertEqual(date(2050, 12, 1), run.endpoints[-1].endpoint_month)
        self.assertTrue(all(endpoint.evidence_kind == "simulated" and endpoint.causal_claim is False for endpoint in run.endpoints))
        self.assertEqual(25, len(summarize_paired_endpoints(current.plan, run.endpoints).station_summaries))
        different = ProcessInitialStateSet((ProcessInitialState("draw-a", MonthlyCoupledState(JAN, CANONICAL_STATION_IDS, (31.0,) * 25, (20.0,) * 25, (.5,) * 25, forcing(JAN))),))
        with self.assertRaises(ScenarioRunnerValidationError):
            PairedRunSpecification(plan(initial_set(), schedule("control"), schedule("intervention", placebo=True)), different, schedule("control"), schedule("intervention", placebo=True))

    def test_schedules_require_explicit_zero_or_intervention_and_canonical_hashes(self) -> None:
        with self.assertRaises(ScenarioRunnerValidationError):
            schedule("control", (MacroalgaeRemovalDose(JAN, "station-01", 1.0, "e"),))
        with self.assertRaises(ScenarioRunnerValidationError):
            schedule("intervention")
        placebo = schedule("intervention", placebo=True)
        self.assertNotEqual(schedule("control").content_hash, placebo.content_hash)
        with self.assertRaises(ScenarioRunnerValidationError):
            type(placebo)(**{**placebo.__dict__, "content_hash": HASH})

    def test_explicit_local_doses_are_bounded_and_order_independent(self) -> None:
        doses = (
            CoralRestorationDose(JAN, "station-01", 10.0, .5, 60.0, "e-rest"),
            MacroalgaeRemovalDose(JAN, "station-01", 3.0, "e-remove"),
            GrazingDose(JAN, JAN, "station-01", .1, "e-g1"),
            GrazingDose(JAN, JAN, "station-01", .2, "e-g2"),
            LarvalRecruitmentDose(JAN, JAN, "station-01", .1, "e-larvae"),
        )
        first = MonthlyPairedScenarioRunner().run(specification(intervention=schedule("intervention", doses)))
        second = MonthlyPairedScenarioRunner().run(specification(intervention=schedule("intervention", tuple(reversed(doses)))))
        state = first.trajectories[0].intervention[0]
        self.assertEqual(first.trajectories, second.trajectories)
        self.assertAlmostEqual(40.276, state.coral_cover_pct[0])
        self.assertAlmostEqual(12.24, state.macroalgae_cover_pct[0])
        self.assertEqual((30.0, 20.0), (state.coral_cover_pct[1], state.macroalgae_cover_pct[1]))
        self.assertTrue(all(c + m <= 100 for c, m in zip(state.coral_cover_pct, state.macroalgae_cover_pct)))

    def test_forcing_and_inputs_are_not_mutated_and_same_member_process_drive_both_arms(self) -> None:
        dose = MacroalgaeRemovalDose(date(2026, 2, 1), "station-01", 2.0, "e")
        current = specification(intervention=schedule("intervention", (dose,)))
        before_forcing = current.plan.forcing_members[0].monthly_forcings
        before_initial = current.initial_states.states[0].state
        run = MonthlyPairedScenarioRunner().run(current)
        trajectory = run.trajectories[0]
        self.assertEqual((before_forcing, before_initial), (current.plan.forcing_members[0].monthly_forcings, current.initial_states.states[0].state))
        self.assertEqual(trajectory.control[1].forcing, trajectory.intervention[1].forcing)
        self.assertEqual(20.0, trajectory.control[1].macroalgae_cover_pct[0])
        self.assertEqual(18.0, trajectory.intervention[1].macroalgae_cover_pct[0])

    def test_bad_dates_ranges_hashes_and_initials_abort_before_a_run(self) -> None:
        invalid = (
            lambda: CoralRestorationDose(date(2025, 12, 1), "station-01", 1, .5, 50, "e"),
            lambda: GrazingDose(JAN, date(2025, 12, 1), "station-01", .1, "e"),
            lambda: LarvalRecruitmentDose(JAN, JAN, "station-01", 1.1, "e"),
            lambda: MacroalgaeRemovalDose(JAN, "station-01", math.nan, "e"),
            lambda: ProcessInitialState("draw-a", MonthlyCoupledState(date(2026, 2, 1), CANONICAL_STATION_IDS, (30.0,) * 25, (20.0,) * 25, (.5,) * 25, forcing(date(2026, 2, 1)))),
        )
        for factory in invalid:
            with self.subTest(factory=factory):
                with self.assertRaises(ScenarioRunnerValidationError):
                    factory()
        with self.assertRaises(ScenarioRunnerValidationError):
            ProcessInitialStateSet(())

    def test_runner_is_deterministic_without_rng_or_external_inputs(self) -> None:
        current = specification()
        runner = MonthlyPairedScenarioRunner()
        self.assertEqual(runner.run(current), runner.run(current))
