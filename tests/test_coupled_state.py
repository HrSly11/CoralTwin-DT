"""Contract tests for the deterministic 25-station monthly coupled state."""

from __future__ import annotations

import math
import unittest
from dataclasses import replace
from datetime import date, datetime, timezone

from operational.coupled_state import (
    CANONICAL_STATION_IDS,
    ConnectivityMatrix,
    CoupledStateValidationError,
    MonthlyCoupledState,
    MonthlyForcing,
    MonthlyTransitionParameters,
    project_biological_components,
    step_month,
)


def values(value: float) -> tuple[float, ...]:
    return (value,) * 25


def forcing(month: date = date(2026, 2, 1), *, dhw: float = 0.0) -> MonthlyForcing:
    return MonthlyForcing(month, values(28.0), values(dhw), values(3.5))


def state(month: date = date(2026, 1, 1), *, coral: float = 30.0, macro: float = 20.0) -> MonthlyCoupledState:
    return MonthlyCoupledState(month, CANONICAL_STATION_IDS, values(coral), values(macro), values(0.6), forcing(month))


def parameters(**changes: float) -> MonthlyTransitionParameters:
    defaults = dict(
        coral_growth_per_month=0.04,
        macroalgae_growth_per_month=0.03,
        heat_mortality_per_dhw=0.02,
        grazing_per_month=0.01,
        larval_recruitment_per_month=0.02,
        biodiversity_recovery_per_month=0.03,
        biodiversity_macroalgae_loss_per_month=0.02,
        biodiversity_heat_loss_per_dhw=0.01,
    )
    defaults.update(changes)
    return MonthlyTransitionParameters(**defaults)


class CoupledStateValidationTests(unittest.TestCase):
    def test_canonical_axis_is_exactly_25_stations_in_registry_order(self) -> None:
        self.assertEqual(25, len(CANONICAL_STATION_IDS))
        self.assertEqual("station-01", CANONICAL_STATION_IDS[0])
        self.assertEqual("station-25", CANONICAL_STATION_IDS[-1])
        with self.assertRaises(CoupledStateValidationError):
            replace(state(), station_ids=tuple(reversed(CANONICAL_STATION_IDS)))

    def test_forcing_and_state_reject_invalid_dates_numbers_and_ecological_bounds(self) -> None:
        with self.assertRaises(CoupledStateValidationError):
            forcing(date(2026, 2, 2))
        with self.assertRaises(CoupledStateValidationError):
            MonthlyForcing(date(2026, 2, 1), values(math.nan), values(0), values(3))
        with self.assertRaises(CoupledStateValidationError):
            MonthlyForcing(date(2026, 2, 1), values(28), values(-0.1), values(3))
        with self.assertRaises(CoupledStateValidationError):
            MonthlyForcing(date(2026, 2, 1), values(28), values(0), values(0))
        with self.assertRaises(CoupledStateValidationError):
            state(coral=80, macro=30)
        with self.assertRaises(CoupledStateValidationError):
            MonthlyCoupledState(date(2026, 1, 1), CANONICAL_STATION_IDS, values(30), values(20), values(1.1), forcing(date(2026, 1, 1)))

    def test_forcing_and_state_reject_datetime_values_at_midnight_and_noon(self) -> None:
        for invalid_month in (
            datetime(2026, 2, 1),
            datetime(2026, 2, 1, 12, tzinfo=timezone.utc),
        ):
            with self.subTest(invalid_month=invalid_month):
                with self.assertRaises(CoupledStateValidationError):
                    forcing(invalid_month)
                with self.assertRaises(CoupledStateValidationError):
                    MonthlyCoupledState(invalid_month, CANONICAL_STATION_IDS, values(30), values(20), values(0.6), forcing(date(2026, 1, 1)))

    def test_plain_date_state_and_forcing_can_advance_to_the_following_month(self) -> None:
        initial = state(date(2026, 1, 1))
        result = step_month(initial, forcing(date(2026, 2, 1)), ConnectivityMatrix.default(), parameters())

        self.assertEqual(date(2026, 2, 1), result.month)

    def test_connectivity_requires_canonical_25_square_stochastic_block_matrix(self) -> None:
        identity = ConnectivityMatrix.default()
        self.assertEqual(CANONICAL_STATION_IDS, identity.station_ids)
        self.assertEqual(tuple(1.0 for _ in CANONICAL_STATION_IDS), tuple(sum(row) for row in identity.weights))
        self.assertTrue(all(row[index] == 1.0 for index, row in enumerate(identity.weights)))
        with self.assertRaises(CoupledStateValidationError):
            ConnectivityMatrix(CANONICAL_STATION_IDS[:-1], identity.weights[:-1])
        bad = [list(row) for row in identity.weights]
        bad[0][0] = math.inf
        with self.assertRaises(CoupledStateValidationError):
            ConnectivityMatrix(CANONICAL_STATION_IDS, tuple(tuple(row) for row in bad))
        bad = [list(row) for row in identity.weights]
        bad[0][0], bad[0][1] = 0.9, 0.1  # stations 01 and 02 share a nominal block
        matrix = ConnectivityMatrix(CANONICAL_STATION_IDS, tuple(tuple(row) for row in bad))
        self.assertAlmostEqual(1.0, sum(matrix.weights[0]))
        bad[0][1], bad[0][12] = 0.0, 0.1
        with self.assertRaises(CoupledStateValidationError):
            ConnectivityMatrix(CANONICAL_STATION_IDS, tuple(tuple(row) for row in bad))

    def test_parameters_must_be_finite_and_non_negative(self) -> None:
        with self.assertRaises(CoupledStateValidationError):
            parameters(grazing_per_month=-0.1)
        with self.assertRaises(CoupledStateValidationError):
            parameters(coral_growth_per_month=math.nan)


class MonthlyTransitionTests(unittest.TestCase):
    def test_public_biological_projection_is_finite_and_enforces_the_cmb_bounds(self) -> None:
        self.assertEqual((0.0, 100.0, 1.0), project_biological_components(-2, 200, 4))
        with self.assertRaises(CoupledStateValidationError):
            project_biological_components(math.nan, 1, 0.5)

    def test_step_is_deterministic_advances_december_to_january_and_preserves_bounds(self) -> None:
        initial = state(date(2026, 12, 1), coral=90.0, macro=9.0)
        next_forcing = forcing(date(2027, 1, 1), dhw=50.0)
        result = step_month(initial, next_forcing, ConnectivityMatrix.default(), parameters())

        self.assertEqual(date(2027, 1, 1), result.month)
        self.assertEqual(result, step_month(initial, next_forcing, ConnectivityMatrix.default(), parameters()))
        self.assertTrue(all(0.0 <= coral <= 100.0 for coral in result.coral_cover_pct))
        self.assertTrue(all(0.0 <= macro <= 100.0 for macro in result.macroalgae_cover_pct))
        self.assertTrue(all(coral + macro <= 100.0 for coral, macro in zip(result.coral_cover_pct, result.macroalgae_cover_pct)))
        self.assertTrue(all(0.0 <= biodiversity <= 1.0 for biodiversity in result.biodiversity_index))
        with self.assertRaises(CoupledStateValidationError):
            step_month(initial, forcing(date(2027, 2, 1)), ConnectivityMatrix.default(), parameters())

    def test_intraregional_connectivity_changes_larval_recruitment_only_within_block(self) -> None:
        coral = list(values(0.0))
        coral[0], coral[1] = 100.0, 0.0
        initial = MonthlyCoupledState(date(2026, 1, 1), CANONICAL_STATION_IDS, tuple(coral), values(0.0), values(0.5), forcing(date(2026, 1, 1)))
        weights = [list(row) for row in ConnectivityMatrix.default().weights]
        weights[0][0], weights[0][1] = 0.0, 1.0
        matrix = ConnectivityMatrix(CANONICAL_STATION_IDS, tuple(tuple(row) for row in weights))
        neutral = parameters(coral_growth_per_month=0, macroalgae_growth_per_month=0, heat_mortality_per_dhw=0, grazing_per_month=0, larval_recruitment_per_month=0.5, biodiversity_recovery_per_month=0, biodiversity_macroalgae_loss_per_month=0, biodiversity_heat_loss_per_dhw=0)

        result = step_month(initial, forcing(date(2026, 2, 1)), matrix, neutral)

        self.assertGreater(result.coral_cover_pct[1], 0.0)
        self.assertEqual(0.0, result.coral_cover_pct[12])

    def test_vector_round_trip_is_field_major_and_has_150_values(self) -> None:
        initial = state()
        vector = initial.to_vector()

        self.assertEqual(150, len(vector))
        self.assertEqual(initial.coral_cover_pct[0], vector[0])
        self.assertEqual(initial.macroalgae_cover_pct[0], vector[25])
        self.assertEqual(initial, MonthlyCoupledState.from_vector(initial.month, initial.station_ids, vector))
        with self.assertRaises(CoupledStateValidationError):
            MonthlyCoupledState.from_vector(initial.month, initial.station_ids, vector[:-1])


if __name__ == "__main__":
    unittest.main()
