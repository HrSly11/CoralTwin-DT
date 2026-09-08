import json
import math
import sqlite3
import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import patch

from operational.noaa_adapter import ProductObservation
from operational.observations import CanonicalObservation, ObservationValidationError
from operational.repository import SQLiteOperationalRepository


UTC = timezone.utc


def noaa(product: str = "sst", value: float = 29.1) -> ProductObservation:
    return ProductObservation(
        station_id="station-01",
        product=product,
        observed_at=datetime(2026, 1, 1, tzinfo=UTC),
        requested_latitude=18.25,
        requested_longitude=-87.8,
        returned_latitude=18.3,
        returned_longitude=-87.75,
        value=value,
        unit="degree_C" if product == "sst" else "degree_Celsius_weeks",
        source="noaa_crw_erddap",
        dataset_id="noaacrwsstDaily" if product == "sst" else "noaacrwdhwDaily",
        request_url="https://example.test/noaa",
        accessed_at=datetime(2026, 1, 2, tzinfo=UTC),
    )


class CanonicalObservationTests(unittest.TestCase):
    def test_observed_requires_complete_source_evidence(self):
        with self.assertRaises(ObservationValidationError):
            CanonicalObservation(
                station_id="station-01", metric="sst", observed_at=datetime(2026, 1, 1, tzinfo=UTC),
                unit="degree_C", value=29.1, provenance_kind="observed", provider="NOAA",
                dataset_id="dataset", accessed_at=datetime(2026, 1, 2, tzinfo=UTC),
            )

    def test_derived_and_simulated_require_their_respective_lineage(self):
        with self.assertRaises(ObservationValidationError):
            CanonicalObservation("station-01", "stress", datetime(2026, 1, 1, tzinfo=UTC), "1", 1.0, "derived")
        with self.assertRaises(ObservationValidationError):
            CanonicalObservation("station-01", "cover", datetime(2026, 1, 1, tzinfo=UTC), "%", 30.0, "simulated")

    def test_provenance_kinds_reject_mixed_evidence_fields(self):
        observed = noaa()
        with self.assertRaisesRegex(ObservationValidationError, "observed.*derivation"):
            CanonicalObservation.from_noaa(observed).__class__(
                **{**CanonicalObservation.from_noaa(observed).__dict__, "derivation_method": "aggregate", "input_lineage": ("raw",)}
            )
        with self.assertRaisesRegex(ObservationValidationError, "derived.*observational"):
            CanonicalObservation(
                "station-01", "stress", datetime(2026, 1, 1, tzinfo=UTC), "1", 1.0, "derived",
                logical_observation_id="derived:station-01:stress:20260101", derivation_method="aggregate", input_lineage=("raw",), provider="NOAA",
            )
        with self.assertRaisesRegex(ObservationValidationError, "simulated.*derivation"):
            CanonicalObservation(
                "station-01", "cover", datetime(2026, 1, 1, tzinfo=UTC), "%", 30.0, "simulated",
                logical_observation_id="simulated:station-01:cover:20260101", model_version="v1", scenario_id="ssp245", derivation_method="aggregate",
            )

    def test_nested_lineage_is_deeply_immutable_and_serializes_deterministically(self):
        source = {"inputs": [{"station": "station-01"}]}
        item = CanonicalObservation(
            "station-01", "stress", datetime(2026, 1, 1, tzinfo=UTC), "1", 1.0, "derived",
            logical_observation_id="derived:station-01:stress:20260101", derivation_method="aggregate", input_lineage=(source,),
        )
        source["inputs"][0]["station"] = "mutated"
        with self.assertRaises(TypeError):
            item.input_lineage[0]["inputs"] = ()

        self.assertEqual("station-01", item.to_dict()["input_lineage"][0]["inputs"][0]["station"])
        self.assertEqual(item.json_columns(), item.json_columns())

    def test_unknown_provenance_and_non_finite_values_are_rejected(self):
        for provenance in ("real", "calibrated real", ""):
            with self.subTest(provenance=provenance):
                with self.assertRaises(ObservationValidationError):
                    CanonicalObservation("station-01", "sst", datetime(2026, 1, 1, tzinfo=UTC), "degree_C", 29.1, provenance)
        with self.assertRaises(ObservationValidationError):
            CanonicalObservation("station-01", "sst", datetime(2026, 1, 1, tzinfo=UTC), "degree_C", math.nan, "simulated", model_version="v1", scenario_id="ssp245")

    def test_noaa_mapping_is_observed_and_json_safe(self):
        item = CanonicalObservation.from_noaa(noaa())

        self.assertEqual("observed", item.provenance_kind)
        self.assertEqual("noaa_crw_erddap", item.provider)
        self.assertEqual("sst", item.metric)
        self.assertEqual("https://example.test/noaa", item.request_url)
        self.assertEqual("noaa-crw:station-01:sst:20260101T000000Z", item.logical_observation_id)
        self.assertEqual(item.to_dict(), json.loads(json.dumps(item.to_dict(), allow_nan=False)))


class CanonicalLedgerRepositoryTests(unittest.TestCase):
    def setUp(self):
        self.tempdir = tempfile.TemporaryDirectory()
        self.path = Path(self.tempdir.name) / "ledger.sqlite"
        self.repository = SQLiteOperationalRepository(self.path)
        self.repository.upsert_station("station-01", "Station", 18.25, -87.8)

    def tearDown(self):
        self.repository.close()
        self.tempdir.cleanup()

    def test_save_is_idempotent_and_same_timestamp_corrections_append_a_revision(self):
        self.assertTrue(self.repository.save_observation(noaa(value=29.1)))
        self.assertFalse(self.repository.save_observation(noaa(value=29.1)))
        self.assertTrue(self.repository.save_observation(noaa(value=29.4)))

        records = self.repository.list_canonical_observations("station-01", "sst")
        self.assertEqual(2, len(records))
        self.assertEqual([29.1, 29.4], [record["value"] for record in records])
        self.assertEqual(1, records[1]["supersedes_revision"])
        self.assertGreater(records[1]["revision"], records[0]["revision"])
        self.assertEqual(records[1], self.repository.get_latest_canonical_observation("station-01", "sst"))

    def test_provider_and_dataset_correction_stays_in_one_logical_chain(self):
        original = noaa()
        corrected = ProductObservation(**{**original.__dict__, "source": "noaa_crw_corrected", "dataset_id": "noaacrwsstDaily-v2"})
        self.repository.save_observation(original)
        self.repository.save_observation(corrected)

        records = self.repository.list_canonical_observations("station-01", "sst")
        self.assertEqual(2, len(records))
        self.assertEqual(records[0]["logical_observation_id"], records[1]["logical_observation_id"])
        self.assertEqual(records[0]["revision"], records[1]["supersedes_revision"])

    def test_distinct_logical_ids_for_sources_at_same_time_do_not_mix(self):
        first = CanonicalObservation(
            "station-01", "sst", datetime(2026, 1, 1, tzinfo=UTC), "degree_C", 29.1, "observed",
            logical_observation_id="field-a:station-01:sst:20260101", provider="provider-a", dataset_id="a",
            accessed_at=datetime(2026, 1, 2, tzinfo=UTC), request_url="https://example.test/a",
        )
        second = CanonicalObservation(
            "station-01", "sst", datetime(2026, 1, 1, tzinfo=UTC), "degree_C", 28.9, "observed",
            logical_observation_id="field-b:station-01:sst:20260101", provider="provider-b", dataset_id="b",
            accessed_at=datetime(2026, 1, 2, tzinfo=UTC), request_url="https://example.test/b",
        )
        self.repository.save_canonical_observation(first)
        self.repository.save_canonical_observation(second)

        records = self.repository.list_canonical_observations("station-01", "sst")
        self.assertEqual(2, len(records))
        self.assertEqual({"field-a:station-01:sst:20260101", "field-b:station-01:sst:20260101"}, {item["logical_observation_id"] for item in records})
        self.assertTrue(all(item["supersedes_revision"] is None for item in records))

    def test_reusing_logical_id_for_another_axis_fails_before_a_write(self):
        original = CanonicalObservation(
            "station-01", "sst", datetime(2026, 1, 1, tzinfo=UTC), "degree_C", 29.1, "observed",
            logical_observation_id="field-a:station-01:sst:20260101", provider="provider-a", dataset_id="a",
            accessed_at=datetime(2026, 1, 2, tzinfo=UTC), request_url="https://example.test/a",
        )
        changed_axis = CanonicalObservation(
            "station-01", "dhw", datetime(2026, 1, 1, tzinfo=UTC), "degree_Celsius_weeks", 1.0, "observed",
            logical_observation_id="field-a:station-01:sst:20260101", provider="provider-a", dataset_id="a",
            accessed_at=datetime(2026, 1, 2, tzinfo=UTC), request_url="https://example.test/a",
        )
        self.repository.save_canonical_observation(original)
        with self.assertRaisesRegex(ObservationValidationError, "logical_observation_id.*axis"):
            self.repository.save_canonical_observation(changed_axis)
        self.assertEqual(1, len(self.repository.list_canonical_observations("station-01")))

    def test_sst_and_dhw_keep_independent_lineage(self):
        self.repository.save_observation(noaa("sst"))
        self.repository.save_observation(noaa("dhw", 3.0))

        self.assertEqual("noaacrwsstDaily", self.repository.get_latest_canonical_observation("station-01", "sst")["dataset_id"])
        self.assertEqual("noaacrwdhwDaily", self.repository.get_latest_canonical_observation("station-01", "dhw")["dataset_id"])

    def test_invalid_source_record_fails_before_any_database_write(self):
        invalid = noaa()
        invalid = ProductObservation(**{**invalid.__dict__, "source": ""})
        with self.assertRaises(ObservationValidationError):
            self.repository.save_observation(invalid)
        self.assertEqual([], self.repository.list_canonical_observations("station-01"))
        self.assertIsNone(self.repository.get_latest_state("station-01").sst)

    def test_legacy_cache_rolls_back_when_ledger_mirroring_fails(self):
        with patch.object(self.repository, "_upsert_canonical_observation", side_effect=sqlite3.IntegrityError("ledger failed")):
            with self.assertRaises(sqlite3.IntegrityError):
                self.repository.save_observation(noaa())

        self.assertIsNone(self.repository.get_latest_state("station-01").sst)
        self.assertEqual([], self.repository.list_canonical_observations("station-01"))

    def test_schema_backfills_legacy_noaa_rows_idempotently(self):
        self.repository.close()
        connection = sqlite3.connect(self.path)
        connection.execute(
            """INSERT INTO product_observations(station_id, product, observed_at, requested_latitude, requested_longitude,
               returned_latitude, returned_longitude, value, unit, source, dataset_id, request_url, accessed_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            ("station-01", "sst", "2026-01-01T00:00:00+00:00", 18.25, -87.8, 18.3, -87.75, 29.1,
             "degree_C", "noaa_crw_erddap", "noaacrwsstDaily", "https://example.test/noaa", "2026-01-02T00:00:00+00:00"),
        )
        connection.commit()
        connection.close()
        self.repository = SQLiteOperationalRepository(self.path)

        self.assertEqual(1, len(self.repository.list_canonical_observations("station-01", "sst")))
        self.repository.close()
        self.repository = SQLiteOperationalRepository(self.path)
        self.assertEqual(1, len(self.repository.list_canonical_observations("station-01", "sst")))

    def test_migrates_v1_ledger_rows_without_losing_their_content(self):
        self.repository.close()
        connection = sqlite3.connect(self.path)
        connection.execute("DROP TABLE canonical_observations")
        connection.execute(
            """CREATE TABLE canonical_observations (
                identity TEXT PRIMARY KEY, station_id TEXT NOT NULL, metric TEXT NOT NULL, observed_at TEXT NOT NULL,
                unit TEXT NOT NULL, value REAL NOT NULL, provenance_kind TEXT NOT NULL, provider TEXT,
                dataset_id TEXT, accessed_at TEXT, request_url TEXT, requested_latitude REAL,
                requested_longitude REAL, returned_latitude REAL, returned_longitude REAL,
                quality_flags_json TEXT NOT NULL, uncertainty REAL, derivation_method TEXT,
                input_lineage_json TEXT NOT NULL, model_version TEXT, scenario_id TEXT,
                source_evidence_json TEXT NOT NULL)"""
        )
        record = CanonicalObservation.from_noaa(noaa())
        flags, lineage, evidence = record.json_columns()
        connection.execute(
            """INSERT INTO canonical_observations VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (record.identity, record.station_id, record.metric, record.observed_at.isoformat(), record.unit, record.value,
             record.provenance_kind, record.provider, record.dataset_id, record.accessed_at.isoformat(), record.request_url,
             record.requested_latitude, record.requested_longitude, record.returned_latitude, record.returned_longitude,
             flags, record.uncertainty, record.derivation_method, lineage, record.model_version, record.scenario_id, evidence),
        )
        connection.commit()
        connection.close()
        self.repository = SQLiteOperationalRepository(self.path)

        migrated = self.repository.list_canonical_observations("station-01", "sst")
        self.assertEqual(1, len(migrated))
        self.assertEqual((1, 29.1, None), (migrated[0]["revision"], migrated[0]["value"], migrated[0]["supersedes_revision"]))

    def test_migrates_partial_append_only_schema_to_logical_id_chain(self):
        self.repository.close()
        connection = sqlite3.connect(self.path)
        connection.execute("DROP TABLE canonical_observation_axes")
        connection.execute("DROP TABLE canonical_observations")
        connection.execute(
            """CREATE TABLE canonical_observations (
                revision INTEGER PRIMARY KEY AUTOINCREMENT, identity TEXT NOT NULL, content_hash TEXT NOT NULL,
                supersedes_revision INTEGER, station_id TEXT NOT NULL, metric TEXT NOT NULL, observed_at TEXT NOT NULL,
                unit TEXT NOT NULL, value REAL NOT NULL, provenance_kind TEXT NOT NULL, provider TEXT, dataset_id TEXT,
                accessed_at TEXT, request_url TEXT, requested_latitude REAL, requested_longitude REAL,
                returned_latitude REAL, returned_longitude REAL, quality_flags_json TEXT NOT NULL, uncertainty REAL,
                derivation_method TEXT, input_lineage_json TEXT NOT NULL, model_version TEXT, scenario_id TEXT,
                source_evidence_json TEXT NOT NULL, UNIQUE(identity, content_hash))"""
        )
        record = CanonicalObservation.from_noaa(noaa())
        flags, lineage, evidence = record.json_columns()
        connection.execute(
            """INSERT INTO canonical_observations(
                identity, content_hash, station_id, metric, observed_at, unit, value, provenance_kind, provider,
                dataset_id, accessed_at, request_url, requested_latitude, requested_longitude, returned_latitude,
                returned_longitude, quality_flags_json, uncertainty, derivation_method, input_lineage_json,
                model_version, scenario_id, source_evidence_json
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (record.identity, record.content_hash, record.station_id, record.metric, record.observed_at.isoformat(),
             record.unit, record.value, record.provenance_kind, record.provider, record.dataset_id,
             record.accessed_at.isoformat(), record.request_url, record.requested_latitude, record.requested_longitude,
             record.returned_latitude, record.returned_longitude, flags, record.uncertainty,
             record.derivation_method, lineage, record.model_version, record.scenario_id, evidence),
        )
        connection.commit()
        connection.close()
        self.repository = SQLiteOperationalRepository(self.path)

        migrated = self.repository.get_latest_canonical_observation("station-01", "sst")
        self.assertEqual("noaa-crw:station-01:sst:20260101T000000Z", migrated["logical_observation_id"])


if __name__ == "__main__":
    unittest.main()
