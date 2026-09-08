"""Contract tests for the bounded, biological-only monthly EnKF."""

from __future__ import annotations

import math
import random
import unittest
from dataclasses import replace
from datetime import date

from operational.coupled_state import (
    CANONICAL_STATION_IDS,
    ConnectivityMatrix,
    MonthlyCoupledState,
    MonthlyForcing,
)
from operational.enkf import (
    EnKFConfig,
    EnKFValidationError,
    MonthlyStateEnsemble,
    ObservationTarget,
    analyze_month,
)
from operational.monthly_observations import MonthlyObservation, MonthlyObservationBatch


MONTH = date(2026, 3, 1)


def values(value: float) -> tuple[float, ...]:
    return (value,) * len(CANONICAL_STATION_IDS)


def forcing(*, sst: float = 28.0) -> MonthlyForcing:
    return MonthlyForcing(MONTH, values(sst), values(0.0), values(3.5))


def state(*, coral_first: float, coral_second: float = 30.0, macro_first: float = 20.0, biodiversity_first: float = 0.6, current_forcing: MonthlyForcing | None = None) -> MonthlyCoupledState:
    coral = list(values(30.0))
    macro = list(values(20.0))
    biodiversity = list(values(0.6))
    coral[0], coral[1], macro[0], biodiversity[0] = coral_first, coral_second, macro_first, biodiversity_first
    return MonthlyCoupledState(MONTH, CANONICAL_STATION_IDS, tuple(coral), tuple(macro), tuple(biodiversity), current_forcing or forcing())


def ensemble(*, current_forcing: MonthlyForcing | None = None) -> MonthlyStateEnsemble:
    shared_forcing = current_forcing or forcing()
    return MonthlyStateEnsemble(tuple(state(coral_first=value, current_forcing=shared_forcing) for value in (20.0, 30.0, 40.0)))


def batch(*, observed: bool = True, metric: str = "coral_observed", unit: str = "percent", value: float = 80.0, sigma: float = 2.0, status: str | None = None) -> MonthlyObservationBatch:
    actual_status = status or ("observed" if observed else "missing")
    items = []
    for index, station_id in enumerate(CANONICAL_STATION_IDS):
        enabled = observed and index == 0
        items.append(MonthlyObservation(
            MONTH, station_id, metric, unit, value if enabled else None, sigma if enabled else None,
            1 if enabled else 0, (), (), actual_status if index == 0 else "missing", enabled,
        ))
    return MonthlyObservationBatch(MONTH, CANONICAL_STATION_IDS, (metric,), tuple(items))


def config(*, target: ObservationTarget | None = None, connectivity: ConnectivityMatrix | None = None, inflation: float = 1.0, floor: float = 0.1, minimum_members: int = 3, seed: int = 7) -> EnKFConfig:
    return EnKFConfig(
        (target or ObservationTarget("coral_observed", "coral_cover_pct", "percent"),), connectivity or ConnectivityMatrix.default(),
        inflation, floor, minimum_members, seed,
    )


class EnKFValidationTests(unittest.TestCase):
    def test_config_rejects_ambiguous_types_invalid_values_and_duplicate_target_metrics(self) -> None:
        with self.assertRaises(EnKFValidationError):
            ObservationTarget("coral_observed", "sst_deg_c", "percent")
        with self.assertRaises(EnKFValidationError):
            EnKFConfig((ObservationTarget("x", "coral_cover_pct", "percent"), ObservationTarget("x", "biodiversity_index", "index")), ConnectivityMatrix.default(), 1, 1, 3, 1)
        with self.assertRaises(EnKFValidationError):
            EnKFConfig((ObservationTarget("x", "coral_cover_pct", "percent"), ObservationTarget("y", "coral_cover_pct", "percent")), ConnectivityMatrix.default(), 1, 1, 3, 1)
        with self.assertRaises(EnKFValidationError):
            ObservationTarget("coral_observed", "coral_cover_pct", " ")
        for changes in ({"inflation": 0.9}, {"floor": 0.0}, {"minimum_members": True}, {"seed": True}):
            with self.subTest(changes=changes):
                with self.assertRaises(EnKFValidationError):
                    config(**changes)

    def test_ensemble_requires_same_month_axis_and_forcing(self) -> None:
        with self.assertRaises(EnKFValidationError):
            MonthlyStateEnsemble((state(coral_first=20), state(coral_first=30, current_forcing=forcing(sst=29))))
        with self.assertRaises(EnKFValidationError):
            analyze_month(ensemble(), batch(), replace(config(), minimum_members=4))
        wrong_month = MonthlyObservationBatch(date(2026, 4, 1), CANONICAL_STATION_IDS, ("coral_observed",), tuple(
            MonthlyObservation(date(2026, 4, 1), station_id, "coral_observed", "percent", None, None, 0, (), (), "missing", False)
            for station_id in CANONICAL_STATION_IDS
        ))
        with self.assertRaises(EnKFValidationError):
            analyze_month(ensemble(), wrong_month, config())


class EnKFAssimilationTests(unittest.TestCase):
    def test_target_unit_must_match_exactly_and_biodiversity_requires_its_own_unit(self) -> None:
        forecast = ensemble()
        mismatch = analyze_month(forecast, batch(unit="degree_Celsius"), config())
        self.assertEqual(forecast, mismatch.analysis)
        self.assertIn((("coral_observed", "station-01"), "unit_mismatch"), mismatch.diagnostics.skipped)
        biodiversity_forecast = MonthlyStateEnsemble(tuple(
            state(coral_first=30.0, biodiversity_first=value, current_forcing=forcing()) for value in (0.4, 0.6, 0.8)
        ))
        biodiversity = analyze_month(
            biodiversity_forecast, batch(metric="biodiversity_observed", unit="index", value=0.8),
            config(target=ObservationTarget("biodiversity_observed", "biodiversity_index", "index")),
        )
        self.assertNotEqual(biodiversity_forecast.members[0].biodiversity_index[0], biodiversity.analysis.members[0].biodiversity_index[0])

    def test_overflow_prone_uncertainty_is_skipped_and_impossible_inflation_fails_closed(self) -> None:
        forecast = ensemble()
        skipped = analyze_month(forecast, batch(sigma=1e308), config(floor=1e308))
        self.assertEqual(forecast, skipped.analysis)
        self.assertIn((("coral_observed", "station-01"), "uncertainty_overflow"), skipped.diagnostics.skipped)
        with self.assertRaises(EnKFValidationError):
            config(inflation=1e308)

    def test_seed_is_reproducible_but_different_seed_changes_perturbed_analysis(self) -> None:
        forecast = ensemble()
        self.assertEqual(analyze_month(forecast, batch(), config(seed=11)), analyze_month(forecast, batch(), config(seed=11)))
        self.assertNotEqual(analyze_month(forecast, batch(), config(seed=11)).analysis, analyze_month(forecast, batch(), config(seed=12)).analysis)

    def test_only_observed_masked_finite_positive_sigma_inputs_enter_and_no_inputs_is_identity(self) -> None:
        forecast = ensemble()
        no_observations = batch(observed=False, status="simulated_bootstrap")
        result = analyze_month(forecast, no_observations, config())
        self.assertEqual(forecast, result.analysis)
        self.assertEqual(0, result.diagnostics.assimilated_count)
        self.assertIn((("coral_observed", "station-01"), "simulated_bootstrap"), result.diagnostics.skipped)
        self.assertIn((("coral_observed", "station-02"), "missing"), result.diagnostics.skipped)

    def test_identity_localization_blocks_remote_same_component_updates(self) -> None:
        forecast = ensemble()
        result = analyze_month(forecast, batch(), config())
        self.assertNotEqual(forecast.members[0].coral_cover_pct[0], result.analysis.members[0].coral_cover_pct[0])
        self.assertEqual(forecast.members[0].coral_cover_pct[1], result.analysis.members[0].coral_cover_pct[1])
        self.assertEqual(forecast.members[0].macroalgae_cover_pct, result.analysis.members[0].macroalgae_cover_pct)

    def test_valid_intraregional_weight_updates_only_the_target_component_and_destination(self) -> None:
        weights = [list(row) for row in ConnectivityMatrix.default().weights]
        weights[0][0], weights[0][1] = 0.5, 0.5
        forecast = MonthlyStateEnsemble(tuple(state(coral_first=value, coral_second=value, current_forcing=forcing()) for value in (20.0, 30.0, 40.0)))
        result = analyze_month(forecast, batch(), config(connectivity=ConnectivityMatrix(CANONICAL_STATION_IDS, tuple(tuple(row) for row in weights))))
        self.assertNotEqual(forecast.members[0].coral_cover_pct[1], result.analysis.members[0].coral_cover_pct[1])
        self.assertEqual(forecast.members[0].coral_cover_pct[5], result.analysis.members[0].coral_cover_pct[5])
        self.assertEqual(forecast.members[0].biodiversity_index, result.analysis.members[0].biodiversity_index)

    def test_variance_floor_and_inflation_change_the_gain_and_projection_preserves_bounds(self) -> None:
        forecast = MonthlyStateEnsemble(tuple(state(coral_first=value, macro_first=90.0, biodiversity_first=0.9) for value in (1.0, 5.0, 9.0)))
        low_floor = analyze_month(forecast, batch(value=100.0, sigma=0.01), config(floor=0.0001))
        high_floor = analyze_month(forecast, batch(value=100.0, sigma=0.01), config(floor=1000.0))
        inflated = analyze_month(forecast, batch(value=100.0, sigma=0.01), config(inflation=2.0, floor=0.0001))
        self.assertNotEqual(low_floor.analysis, high_floor.analysis)
        self.assertNotEqual(low_floor.analysis, inflated.analysis)
        for member in low_floor.analysis.members:
            self.assertTrue(all(0 <= coral and 0 <= macro and coral + macro <= 100 for coral, macro in zip(member.coral_cover_pct, member.macroalgae_cover_pct)))
            self.assertTrue(all(0 <= biodiversity <= 1 for biodiversity in member.biodiversity_index))

    def test_forcing_is_never_updated_and_global_rng_is_untouched(self) -> None:
        forecast = ensemble()
        random.seed(991)
        before = random.getstate()
        result = analyze_month(forecast, batch(), config())
        self.assertEqual(before, random.getstate())
        self.assertTrue(all(member.forcing == forecast.members[0].forcing for member in result.analysis.members))
        self.assertEqual(tuple(forecast.members[0].forcing.sst_deg_c), tuple(result.analysis.members[0].forcing.sst_deg_c))

    def test_result_and_diagnostics_are_immutable_and_ordered(self) -> None:
        result = analyze_month(ensemble(), batch(metric="unmapped"), config())
        self.assertEqual((), result.diagnostics.assimilated_keys)
        self.assertEqual((("unmapped", "station-01"), "unmapped_metric"), result.diagnostics.skipped[0])
        with self.assertRaises(AttributeError):
            result.diagnostics.seed = 4


if __name__ == "__main__":
    unittest.main()
