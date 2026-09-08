"""Contract tests for monthly, as-of observation batches."""

from __future__ import annotations

import sqlite3
import tempfile
import unittest
from dataclasses import replace
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

from operational.monthly_observations import (
    AssimilationInputs,
    MetricAggregationPolicy,
    MonthlyObservationBatch,
    SimulatedBootstrapValue,
    SourceKey,
    build_monthly_observation_batch,
)
from operational.observations import CanonicalObservation
from operational.repository import SQLiteOperationalRepository
from operational.stations import CANONICAL_STATIONS


UTC = timezone.utc


class MutableClock:
    def __init__(self, value: datetime) -> None:
        self.value = value
        self.calls = 0

    def __call__(self) -> datetime:
        self.calls += 1
        return self.value


def observed(
    station_id: str,
    metric: str,
    value: float,
    *,
    logical_id: str,
    provider: str = "provider-a",
    dataset_id: str = "dataset-a",
    observed_at: datetime = datetime(2026, 1, 15, tzinfo=UTC),
    accessed_at: datetime = datetime(2026, 1, 16, tzinfo=UTC),
    unit: str = "degree_C",
    flags: tuple[str, ...] = (),
    uncertainty: float | None = 0.5,
) -> CanonicalObservation:
    return CanonicalObservation(
        station_id=station_id,
        metric=metric,
        observed_at=observed_at,
        unit=unit,
        value=value,
        provenance_kind="observed",
        logical_observation_id=logical_id,
        provider=provider,
        dataset_id=dataset_id,
        accessed_at=accessed_at,
        request_url="https://example.test/observation",
        quality_flags=flags,
        uncertainty=uncertainty,
    )


def policy(*, providers: tuple[SourceKey, ...] = (SourceKey("provider-a", "dataset-a"),)) -> MetricAggregationPolicy:
    return MetricAggregationPolicy(
        metric="sst",
        unit="degree_C",
        accepted_quality_flags=frozenset({"good"}),
        max_uncertainty=1.0,
        fallback_uncertainty=0.8,
        minimum_samples=1,
        provider_priority=providers,
    )


class MonthlyObservationRepositoryTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tempdir = tempfile.TemporaryDirectory()
        self.path = Path(self.tempdir.name) / "monthly.sqlite"
        self.clock = MutableClock(datetime(2026, 2, 1, 12, tzinfo=UTC))
        self.repository = SQLiteOperationalRepository(self.path, clock=self.clock)
        for station in CANONICAL_STATIONS:
            self.repository.upsert_station(station.station_id, station.name, station.latitude, station.longitude)

    def tearDown(self) -> None:
        self.repository.close()
        self.tempdir.cleanup()

    def test_available_at_is_clock_assigned_only_for_insert_and_idempotent_saves_do_not_advance_it(self) -> None:
        record = observed("station-01", "sst", 29.0, logical_id="field:station-01:sst:20260115")

        self.assertTrue(self.repository.save_canonical_observation(record))
        self.assertEqual(1, self.clock.calls)
        self.assertFalse(self.repository.save_canonical_observation(record))
        self.assertEqual(1, self.clock.calls)
        row = self.repository.list_canonical_observations("station-01", "sst")[0]
        self.assertEqual("2026-02-01T12:00:00+00:00", row["available_at"])

    def test_as_of_excludes_future_corrections_and_legacy_null_availability(self) -> None:
        original = observed("station-01", "sst", 29.0, logical_id="field:station-01:sst:20260115")
        self.repository.save_canonical_observation(original)
        self.clock.value = datetime(2026, 2, 10, tzinfo=UTC)
        correction = replace(original, value=30.0, accessed_at=datetime(2026, 1, 20, tzinfo=UTC))
        self.repository.save_canonical_observation(correction)

        station_ids = tuple(station.station_id for station in CANONICAL_STATIONS)
        early = self.repository.list_canonical_observations_as_of(
            date(2026, 1, 1), datetime(2026, 2, 5, tzinfo=UTC), station_ids=station_ids, metrics=("sst",)
        )
        late = self.repository.list_canonical_observations_as_of(
            date(2026, 1, 1), datetime(2026, 2, 11, tzinfo=UTC), station_ids=station_ids, metrics=("sst",)
        )
        self.assertEqual([29.0], [row["value"] for row in early])
        self.assertEqual([30.0], [row["value"] for row in late])

        self.repository._connection.execute(
            "UPDATE canonical_observations SET available_at = NULL WHERE logical_observation_id = ?",
            (late[0]["logical_observation_id"],),
        )
        self.repository._connection.commit()
        self.assertEqual([], self.repository.list_canonical_observations_as_of(
            date(2026, 1, 1), datetime(2026, 2, 11, tzinfo=UTC), station_ids=station_ids, metrics=("sst",)
        ))

    def test_available_at_migration_is_additive_and_legacy_rows_remain_null(self) -> None:
        self.repository.close()
        connection = sqlite3.connect(self.path)
        connection.execute("DROP TABLE canonical_observations")
        connection.execute(
            """CREATE TABLE canonical_observations (
                revision INTEGER PRIMARY KEY AUTOINCREMENT, identity TEXT NOT NULL,
                logical_observation_id TEXT NOT NULL, content_hash TEXT NOT NULL,
                supersedes_revision INTEGER, station_id TEXT NOT NULL, metric TEXT NOT NULL,
                observed_at TEXT NOT NULL, unit TEXT NOT NULL, value REAL NOT NULL,
                provenance_kind TEXT NOT NULL, provider TEXT, dataset_id TEXT, accessed_at TEXT,
                request_url TEXT, requested_latitude REAL, requested_longitude REAL,
                returned_latitude REAL, returned_longitude REAL, quality_flags_json TEXT NOT NULL,
                uncertainty REAL, derivation_method TEXT, input_lineage_json TEXT NOT NULL,
                model_version TEXT, scenario_id TEXT, source_evidence_json TEXT NOT NULL,
                UNIQUE(logical_observation_id, content_hash))"""
        )
        source = observed("station-01", "sst", 29.0, logical_id="field:station-01:sst:20260115")
        flags, lineage, evidence = source.json_columns()
        connection.execute(
            """INSERT INTO canonical_observations(
                identity, logical_observation_id, content_hash, station_id, metric, observed_at, unit, value,
                provenance_kind, provider, dataset_id, accessed_at, request_url, quality_flags_json,
                uncertainty, input_lineage_json, source_evidence_json
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (source.identity, source.logical_observation_id, source.content_hash, source.station_id, source.metric,
             source.observed_at.isoformat(), source.unit, source.value, source.provenance_kind, source.provider,
             source.dataset_id, source.accessed_at.isoformat(), source.request_url, flags, source.uncertainty,
             lineage, evidence),
        )
        connection.commit()
        connection.close()
        self.repository = SQLiteOperationalRepository(self.path, clock=self.clock)

        rows = self.repository.list_canonical_observations("station-01", "sst")
        self.assertEqual(1, len(rows))
        self.assertIsNone(rows[0]["available_at"])
        self.assertEqual([], self.repository.list_canonical_observations_as_of(
            date(2026, 1, 1), datetime(2026, 3, 1, tzinfo=UTC),
            station_ids=tuple(station.station_id for station in CANONICAL_STATIONS), metrics=("sst",),
        ))

    def test_as_of_never_revives_observed_when_latest_visible_revision_is_derived_or_simulated(self) -> None:
        original = observed("station-01", "sst", 29.0, logical_id="field:station-01:sst:20260115")
        self.repository.save_canonical_observation(original)
        self.clock.value = datetime(2026, 2, 2, tzinfo=UTC)
        derived = CanonicalObservation(
            "station-01", "sst", original.observed_at, "degree_C", 29.2, "derived",
            logical_observation_id=original.logical_observation_id, derivation_method="bias-correction", input_lineage=("raw",),
        )
        self.repository.save_canonical_observation(derived)
        kwargs = {"station_ids": tuple(station.station_id for station in CANONICAL_STATIONS), "metrics": ("sst",)}
        self.assertEqual([], self.repository.list_canonical_observations_as_of(date(2026, 1, 1), datetime(2026, 2, 3, tzinfo=UTC), **kwargs))

        self.clock.value = datetime(2026, 2, 4, tzinfo=UTC)
        simulated = CanonicalObservation(
            "station-01", "sst", original.observed_at, "degree_C", 29.3, "simulated",
            logical_observation_id=original.logical_observation_id, model_version="v1", scenario_id="ssp245",
        )
        self.repository.save_canonical_observation(simulated)
        self.assertEqual([], self.repository.list_canonical_observations_as_of(date(2026, 1, 1), datetime(2026, 2, 5, tzinfo=UTC), **kwargs))

    def test_as_of_ignores_a_future_accessed_correction_and_keeps_prior_visible_observed_revision(self) -> None:
        original = observed("station-01", "sst", 29.0, logical_id="field:station-01:sst:20260115")
        self.repository.save_canonical_observation(original)
        self.clock.value = datetime(2026, 2, 2, tzinfo=UTC)
        future_accessed = replace(original, value=30.0, accessed_at=datetime(2026, 3, 1, tzinfo=UTC))
        self.repository.save_canonical_observation(future_accessed)

        result = self.repository.list_canonical_observations_as_of(
            date(2026, 1, 1), datetime(2026, 2, 3, tzinfo=UTC),
            station_ids=tuple(station.station_id for station in CANONICAL_STATIONS), metrics=("sst",),
        )
        self.assertEqual([29.0], [row["value"] for row in result])

    def test_as_of_rejects_noncanonical_axes_invalid_metrics_and_non_utc_cutoffs_before_query(self) -> None:
        kwargs = {"station_ids": tuple(station.station_id for station in CANONICAL_STATIONS), "metrics": ("sst",)}
        invalid = (
            {"station_ids": None},
            {"station_ids": kwargs["station_ids"][:-1]},
            {"station_ids": tuple(reversed(kwargs["station_ids"]))},
            {"metrics": ()},
            {"metrics": "sst"},
            {"metrics": b"sst"},
            {"metrics": {"sst": "value"}},
            {"metrics": ("sst", "sst")},
            {"metrics": ("sst;drop",)},
            {"month": datetime(2026, 1, 1, tzinfo=UTC)},
            {"cutoff": datetime(2026, 2, 1)},
            {"cutoff": datetime(2026, 2, 1, tzinfo=timezone(timedelta(hours=-5)))},
        )
        for changes in invalid:
            with self.subTest(changes=changes):
                values = {"month": date(2026, 1, 1), "cutoff": datetime(2026, 2, 1, tzinfo=UTC), **kwargs, **changes}
                with self.assertRaises(ValueError):
                    self.repository.list_canonical_observations_as_of(**values)

    def test_available_at_migration_rolls_back_column_and_index_when_initialization_fails(self) -> None:
        self.repository.close()
        connection = sqlite3.connect(self.path)
        connection.execute("DROP INDEX IF EXISTS idx_canonical_observations_as_of")
        connection.execute("DROP TABLE canonical_observations")
        connection.execute(
            """CREATE TABLE canonical_observations (
                revision INTEGER PRIMARY KEY AUTOINCREMENT, identity TEXT NOT NULL, logical_observation_id TEXT NOT NULL,
                content_hash TEXT NOT NULL, supersedes_revision INTEGER, station_id TEXT NOT NULL, metric TEXT NOT NULL,
                observed_at TEXT NOT NULL, unit TEXT NOT NULL, value REAL NOT NULL, provenance_kind TEXT NOT NULL,
                provider TEXT, dataset_id TEXT, accessed_at TEXT, request_url TEXT, requested_latitude REAL,
                requested_longitude REAL, returned_latitude REAL, returned_longitude REAL, quality_flags_json TEXT NOT NULL,
                uncertainty REAL, derivation_method TEXT, input_lineage_json TEXT NOT NULL, model_version TEXT,
                scenario_id TEXT, source_evidence_json TEXT NOT NULL)"""
        )
        connection.commit()
        connection.close()

        class FailingRepository(SQLiteOperationalRepository):
            def _ensure_canonical_revision_index(self) -> None:
                raise RuntimeError("injected migration failure")

        with self.assertRaisesRegex(RuntimeError, "injected"):
            FailingRepository(self.path, clock=self.clock)
        check = sqlite3.connect(self.path)
        try:
            columns = {row[1] for row in check.execute("PRAGMA table_info(canonical_observations)")}
            indexes = {row[1] for row in check.execute("PRAGMA index_list(canonical_observations)")}
        finally:
            check.close()
        self.assertNotIn("available_at", columns)
        self.assertNotIn("idx_canonical_observations_as_of", indexes)


class MonthlyObservationBatchTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tempdir = tempfile.TemporaryDirectory()
        self.clock = MutableClock(datetime(2026, 2, 1, tzinfo=UTC))
        self.repository = SQLiteOperationalRepository(Path(self.tempdir.name) / "monthly.sqlite", clock=self.clock)
        for station in CANONICAL_STATIONS:
            self.repository.upsert_station(station.station_id, station.name, station.latitude, station.longitude)

    def tearDown(self) -> None:
        self.repository.close()
        self.tempdir.cleanup()

    def test_batch_is_metric_major_station_major_with_exact_25_station_axis(self) -> None:
        for station in CANONICAL_STATIONS:
            self.repository.save_canonical_observation(
                observed(station.station_id, "sst", 28.0, logical_id=f"field:{station.station_id}:sst:20260115")
            )

        batch = build_monthly_observation_batch(
            self.repository, date(2026, 1, 1), datetime(2026, 2, 2, tzinfo=UTC), (policy(),)
        )

        self.assertEqual(tuple(station.station_id for station in CANONICAL_STATIONS), batch.station_ids)
        self.assertEqual(25, len(batch.observations))
        self.assertTrue(all(item.assimilation_mask for item in batch.observations))
        self.assertEqual(["station-01", "station-02"], [item.station_id for item in batch.observations[:2]])

    def test_provider_priority_prevents_mixed_streams_and_ambiguous_sources_are_missing(self) -> None:
        first = observed("station-01", "sst", 28.0, logical_id="a:station-01:sst:20260115")
        second = observed(
            "station-01", "sst", 30.0, logical_id="b:station-01:sst:20260115", provider="provider-b", dataset_id="dataset-b"
        )
        self.repository.save_canonical_observation(first)
        self.repository.save_canonical_observation(second)

        ambiguous = build_monthly_observation_batch(
            self.repository, date(2026, 1, 1), datetime(2026, 2, 2, tzinfo=UTC), (policy(providers=()),)
        ).observations[0]
        selected = build_monthly_observation_batch(
            self.repository, date(2026, 1, 1), datetime(2026, 2, 2, tzinfo=UTC), (policy(),)
        ).observations[0]
        self.assertEqual("missing_ambiguous", ambiguous.status)
        self.assertFalse(ambiguous.assimilation_mask)
        self.assertEqual((28.0, 0.5), (selected.value, selected.uncertainty))

    def test_qc_unit_and_uncertainty_are_enforced_without_reviving_an_invalid_superseded_revision(self) -> None:
        original = observed("station-01", "sst", 28.0, logical_id="a:station-01:sst:20260115")
        self.repository.save_canonical_observation(original)
        self.clock.value = datetime(2026, 2, 2, tzinfo=UTC)
        invalid_correction = replace(original, value=30.0, quality_flags=("bad",))
        self.repository.save_canonical_observation(invalid_correction)
        wrong_unit = observed("station-02", "sst", 30.0, logical_id="a:station-02:sst:20260115", unit="kelvin")
        too_uncertain = observed("station-03", "sst", 30.0, logical_id="a:station-03:sst:20260115", uncertainty=2.0)
        self.repository.save_canonical_observation(wrong_unit)
        self.repository.save_canonical_observation(too_uncertain)

        items = build_monthly_observation_batch(
            self.repository, date(2026, 1, 1), datetime(2026, 2, 3, tzinfo=UTC), (policy(),)
        ).observations
        self.assertEqual(("missing_qc", None), (items[0].status, items[0].value))
        self.assertEqual("missing_unit", items[1].status)
        self.assertEqual("missing_uncertainty", items[2].status)

    def test_mean_and_independent_uncertainty_are_aggregated_within_the_selected_stream(self) -> None:
        self.repository.save_canonical_observation(observed("station-01", "sst", 28.0, logical_id="a:station-01:sst:20260115", uncertainty=0.6))
        self.repository.save_canonical_observation(
            observed("station-01", "sst", 30.0, logical_id="b:station-01:sst:20260120", uncertainty=0.8)
        )
        item = build_monthly_observation_batch(
            self.repository, date(2026, 1, 1), datetime(2026, 2, 2, tzinfo=UTC), (policy(),)
        ).observations[0]
        self.assertEqual(29.0, item.value)
        self.assertAlmostEqual(0.5, item.uncertainty)
        self.assertEqual(2, item.sample_count)

    def test_bootstrap_is_opt_in_simulated_and_never_sets_assimilation_mask(self) -> None:
        bootstrap = SimulatedBootstrapValue("station-01", "sst", date(2026, 1, 1), "degree_C", 27.5, 0.7)
        no_bootstrap = build_monthly_observation_batch(
            self.repository, date(2026, 1, 1), datetime(2026, 2, 2, tzinfo=UTC), (policy(),)
        ).observations[0]
        with_bootstrap = build_monthly_observation_batch(
            self.repository, date(2026, 1, 1), datetime(2026, 2, 2, tzinfo=UTC), (policy(),), bootstrap_values=(bootstrap,)
        ).observations[0]
        self.assertEqual("missing", no_bootstrap.status)
        self.assertEqual(("simulated_bootstrap", 27.5, False), (with_bootstrap.status, with_bootstrap.value, with_bootstrap.assimilation_mask))

    def test_assimilation_inputs_are_metric_major_and_hide_missing_or_bootstrap_numbers(self) -> None:
        self.repository.save_canonical_observation(observed("station-01", "sst", 28.0, logical_id="a:station-01:sst:20260115"))
        bootstrap = SimulatedBootstrapValue("station-02", "sst", date(2026, 1, 1), "degree_C", 27.5, 0.7)
        batch = build_monthly_observation_batch(
            self.repository, date(2026, 1, 1), datetime(2026, 2, 2, tzinfo=UTC), (policy(),), bootstrap_values=(bootstrap,)
        )

        inputs = batch.assimilation_inputs()
        self.assertIsInstance(inputs, AssimilationInputs)
        self.assertEqual((("sst", "station-01"), ("sst", "station-02")), inputs.keys[:2])
        self.assertEqual((28.0, None, None), inputs.values[:3])
        self.assertEqual((0.5, None, None), inputs.uncertainties[:3])
        self.assertEqual((True, False, False), inputs.mask[:3])
        with self.assertRaises(ValueError):
            AssimilationInputs((("sst", "station-01"),), (27.0,), (0.5,), (False,))

    def test_monthly_values_are_deeply_immutable_and_batch_axis_validation_is_fail_closed(self) -> None:
        source = SourceKey("provider-a", "dataset-a")
        with self.assertRaises((AttributeError, TypeError)):
            source.provider = "changed"  # type: ignore[misc]
        with self.assertRaises(ValueError):
            MonthlyObservationBatch(date(2026, 1, 1), tuple(reversed(tuple(station.station_id for station in CANONICAL_STATIONS))), ("sst",), ())


if __name__ == "__main__":
    unittest.main()
