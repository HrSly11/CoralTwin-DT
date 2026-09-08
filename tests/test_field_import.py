"""Offline contracts for auditable field-observation imports."""

from __future__ import annotations

import csv
import io
import json
import math
import unittest
from datetime import datetime, timezone

from operational.field_import import FieldImportPolicy, FieldObservationImporter


UTC = timezone.utc


def policy(**changes: object) -> FieldImportPolicy:
    values: dict[str, object] = {
        "max_station_distance_m": 500.0,
        "cover_sum_tolerance_pct": 0.1,
        "allowed_licenses": frozenset({"CC-BY-4.0"}),
        "allowed_consent_codes": frozenset({"research-approved"}),
        "allowed_qc_flags": frozenset({"verified", "accepted"}),
        "forbidden_generated_markers": frozenset({"synthetic", "simulated", "digital_twin_simulated", "prototype", "computational"}),
        "allow_day_precision": True,
        "max_input_bytes": 20_000,
        "max_rows": 100,
    }
    values.update(changes)
    return FieldImportPolicy(**values)


def row(**changes: object) -> dict[str, object]:
    values: dict[str, object] = {
        "dataset_kind": "field_observed",
        "dataset_id": "reef-survey-2026",
        "record_id": "cover-1",
        "record_version": 1,
        "survey_id": "survey-a",
        "observed_at": "2026-03-02T10:00:00Z",
        "time_precision": "instant",
        "station_id": "station-01",
        "latitude": 18.25,
        "longitude": -87.80,
        "method": "belt_transect",
        "protocol": "AGRRA-v5",
        "observer_id": "observer-007",
        "organization": "Reef Field Lab",
        "source_url": "https://doi.org/10.1234/reef.2026",
        "measurement_type": "coral_cover_pct",
        "unit": "percent",
        "value": 42.0,
        "uncertainty": 2.0,
        "sample_size": 12,
        "license": "CC-BY-4.0",
        "consent": "research-approved",
        "qc_flags": ["verified"],
    }
    values.update(changes)
    return values


class FieldObservationImporterTests(unittest.TestCase):
    def importer(self) -> FieldObservationImporter:
        return FieldObservationImporter(clock=lambda: datetime(2026, 4, 1, 12, tzinfo=UTC))

    def import_rows(self, *rows: dict[str, object], **changes: object):
        return self.importer().import_records(rows, policy=policy(**changes))

    def test_json_records_and_csv_text_or_bytes_map_to_observed_evidence_without_writes(self) -> None:
        expected = self.import_rows(row())
        csv_text = io.StringIO()
        writer = csv.DictWriter(csv_text, fieldnames=list(row()))
        writer.writeheader()
        csv_row = row(qc_flags=json.dumps(["verified"]))
        writer.writerow(csv_row)

        for raw in (csv_text.getvalue(), csv_text.getvalue().encode("utf-8")):
            with self.subTest(raw_type=type(raw).__name__):
                result = self.importer().import_csv(raw, policy=policy())
                self.assertTrue(result.ready_for_persistence)
                self.assertEqual(expected.candidates[0].to_dict(), result.candidates[0].to_dict())

        item = expected.candidates[0]
        self.assertEqual(("observed", "Reef Field Lab", "reef-survey-2026", "percent", 42.0),
                         (item.provenance_kind, item.provider, item.dataset_id, item.unit, item.value))
        self.assertEqual(datetime(2026, 4, 1, 12, tzinfo=UTC), item.accessed_at)
        self.assertEqual((18.25, -87.8, 18.25, -87.8), (item.requested_latitude, item.requested_longitude, item.returned_latitude, item.returned_longitude))
        self.assertIn("observer:observer-007", item.quality_flags)

    def test_invalid_row_makes_entire_result_atomic_and_rejections_deterministic(self) -> None:
        result = self.import_rows(row(record_id="valid"), row(record_id="bad", value=math.nan))
        self.assertFalse(result.ready_for_persistence)
        self.assertEqual((), result.candidates)
        self.assertEqual(((1, "invalid_value", "bad"),), tuple((r.row_index, r.reason, r.record_id) for r in result.rejected))

    def test_policy_rejects_implicit_or_ambiguous_values(self) -> None:
        invalid = (
            {"max_station_distance_m": True}, {"max_station_distance_m": "500"},
            {"cover_sum_tolerance_pct": -1.0}, {"allowed_licenses": "CC-BY-4.0"},
            {"allowed_qc_flags": ["verified", 1]}, {"allow_day_precision": 1},
            {"max_input_bytes": True}, {"max_input_bytes": 0}, {"max_rows": 1.0}, {"max_rows": 0},
        )
        for changes in invalid:
            with self.subTest(changes=changes):
                with self.assertRaises(ValueError):
                    policy(**changes)

    def test_requires_complete_strict_fields_and_safe_dates(self) -> None:
        invalid = (
            {"dataset_kind": "observed"}, {"record_version": 0}, {"observer_id": "Jane Doe"},
            {"source_url": "http://example.test/a"}, {"observed_at": "2026-03-02T10:00:00", "time_precision": "instant"},
            {"observed_at": "2026-03", "time_precision": "day"}, {"time_precision": "day", "observed_at": "2026-03-02"},
        )
        for changes in invalid:
            with self.subTest(changes=changes):
                result = self.import_rows(row(**changes), allow_day_precision=False if changes.get("time_precision") == "day" else True)
                self.assertFalse(result.ready_for_persistence)
                self.assertEqual((), result.candidates)

        day = self.import_rows(row(observed_at="2026-03-02", time_precision="day"))
        self.assertEqual(datetime(2026, 3, 2, tzinfo=UTC), day.candidates[0].observed_at)

    def test_station_resolution_requires_unique_nearby_canonical_location_and_matching_id(self) -> None:
        coordinate_only = self.import_rows(row(station_id="", latitude=18.25, longitude=-87.80))
        self.assertTrue(coordinate_only.ready_for_persistence)
        self.assertEqual("station-01", coordinate_only.candidates[0].station_id)
        for changes in (
            {"station_id": "station-01", "latitude": 0.0, "longitude": 0.0},
            {"station_id": "", "latitude": 95.0, "longitude": 0.0},
            {"station_id": "", "latitude": 0.0, "longitude": 0.0},
        ):
            with self.subTest(changes=changes):
                self.assertFalse(self.import_rows(row(**changes)).ready_for_persistence)
        self.assertFalse(self.import_rows(row(station_id=9), max_station_distance_m=30_000_000).ready_for_persistence)
        self.assertFalse(self.import_rows(row(station_id="", latitude=0.0, longitude=0.0), max_station_distance_m=30_000_000).ready_for_persistence)

    def test_measurement_units_bounds_cover_sum_and_taxon_requirements(self) -> None:
        invalid = (
            {"measurement_type": "coral_cover_pct", "unit": "%"},
            {"measurement_type": "macroalgae_cover_pct", "value": 101.0},
            {"uncertainty": -0.1}, {"sample_size": 0}, {"qc_flags": ["unknown"]},
            {"license": "CC0"}, {"consent": "no"},
            {"measurement_type": "taxon_abundance", "unit": "count", "taxon_id": "", "survey_complete": True},
            {"measurement_type": "taxon_abundance", "unit": "count", "taxon_id": "taxon:1", "survey_complete": "true"},
            {"measurement_type": "taxon_abundance", "unit": "count", "value": 1.5, "taxon_id": "taxon:1", "survey_complete": True},
        )
        for changes in invalid:
            with self.subTest(changes=changes):
                self.assertFalse(self.import_rows(row(**changes)).ready_for_persistence)
        self.assertFalse(self.import_rows(row(value=60), row(record_id="macro", measurement_type="macroalgae_cover_pct", value=41)).ready_for_persistence)

    def test_generated_markers_reject_the_whole_batch_case_insensitively(self) -> None:
        result = self.import_rows(row(record_id="good"), row(record_id="bad", organization="Digital_Twin_Simulated Lab"))
        self.assertFalse(result.ready_for_persistence)
        self.assertEqual((), result.candidates)
        self.assertEqual("forbidden_generated_marker", result.rejected[0].reason)
        self.assertFalse(self.import_rows(row(dataset_id="Prototype-field-run")).ready_for_persistence)
        self.assertFalse(self.import_rows(row(method="computational_transect")).ready_for_persistence)
        for evasion in ("Digital Twin Simulated", "digital-twin.simulated", "Ｄｉｇｉｔａｌ　Ｔｗｉｎ—Ｓｉｍｕｌａｔｅｄ"):
            with self.subTest(evasion=evasion):
                self.assertFalse(self.import_rows(row(organization=evasion)).ready_for_persistence)

    def test_dedupes_identical_versions_and_only_allows_same_axis_higher_version_corrections(self) -> None:
        same = self.import_rows(row(), row())
        self.assertTrue(same.ready_for_persistence)
        self.assertEqual(1, len(same.candidates))
        corrected = self.import_rows(row(value=40, record_version=1), row(value=41, record_version=2))
        self.assertTrue(corrected.ready_for_persistence)
        self.assertEqual(41.0, corrected.candidates[0].value)
        self.assertEqual(self.import_rows(row()).candidates[0].logical_observation_id, corrected.candidates[0].logical_observation_id)
        for second in (row(value=41), row(value=41, record_version=2, station_id="station-02", latitude=18.28, longitude=-87.82)):
            with self.subTest(second=second):
                result = self.import_rows(row(value=40), second)
                self.assertFalse(result.ready_for_persistence)
                self.assertEqual((), result.candidates)

    def test_record_anchor_prevents_metric_or_taxon_parallel_revision_chains(self) -> None:
        changed_metric = self.import_rows(row(value=40), row(record_version=2, measurement_type="macroalgae_cover_pct", value=41))
        self.assertFalse(changed_metric.ready_for_persistence)
        self.assertEqual("correction_axis_changed", changed_metric.rejected[0].reason)
        first = row(record_id="taxon", measurement_type="taxon_abundance", unit="count", value=2, taxon_id="taxon:a", survey_complete=False)
        changed_taxon = self.import_rows(first, row(**{**first, "record_version": 2, "taxon_id": "taxon:b", "value": 3}))
        self.assertFalse(changed_taxon.ready_for_persistence)
        self.assertEqual("correction_axis_changed", changed_taxon.rejected[0].reason)

    def test_complete_taxon_survey_derives_richness_and_shannon_with_lineage_only(self) -> None:
        first = row(record_id="taxon-a", measurement_type="taxon_abundance", unit="count", value=10, taxon_id="taxon:a", survey_complete=True)
        second = row(record_id="taxon-b", measurement_type="taxon_abundance", unit="count", value=30, taxon_id="taxon:b", survey_complete=True)
        result = self.import_rows(first, second)
        self.assertTrue(result.ready_for_persistence)
        derived = {item.metric: item for item in result.candidates if item.provenance_kind == "derived"}
        self.assertEqual(2.0, derived["species_richness"].value)
        self.assertAlmostEqual(-(.25 * math.log(.25) + .75 * math.log(.75)), derived["shannon_diversity_h"].value)
        self.assertEqual("field-taxonomy-shannon-v1", derived["shannon_diversity_h"].derivation_method)
        self.assertIsNone(derived["shannon_diversity_h"].provider)
        self.assertEqual(2, len(derived["shannon_diversity_h"].input_lineage))
        zero = self.import_rows(row(record_id="zero", measurement_type="taxon_abundance", unit="count", value=0, taxon_id="taxon:zero", survey_complete=True))
        self.assertFalse(zero.ready_for_persistence)
        self.assertEqual("zero_total_abundance", zero.rejected[0].reason)
        duplicate_taxon = self.import_rows(first, row(record_id="taxon-a-repeat", measurement_type="taxon_abundance", unit="count", value=3, taxon_id="taxon:a", survey_complete=True))
        self.assertFalse(duplicate_taxon.ready_for_persistence)

    def test_result_and_policy_are_frozen_and_json_records_are_not_mutated(self) -> None:
        source = row(qc_flags=["verified"])
        result = self.import_rows(source)
        source["qc_flags"].append("accepted")  # type: ignore[index]
        self.assertEqual(("verified",), tuple(sorted(flag.split(":", 1)[1] for flag in result.candidates[0].quality_flags if flag.startswith("qc:"))))
        with self.assertRaises(Exception):
            result.candidates = ()  # type: ignore[misc]
        with self.assertRaises(Exception):
            policy().max_station_distance_m = 1  # type: ignore[misc]

    def test_csv_headers_source_urls_and_input_bounds_fail_closed_before_partial_candidates(self) -> None:
        duplicate_header = "value,value\n1,2\n"
        empty_header = ",dataset_id\n1,reef\n"
        non_normalized_header = "ｖａｌｕｅ,dataset_id\n1,reef\n"
        for text in (duplicate_header, empty_header, non_normalized_header):
            with self.subTest(text=text):
                result = self.importer().import_csv(text, policy=policy())
                self.assertFalse(result.ready_for_persistence)
                self.assertEqual("invalid_csv_header", result.rejected[0].reason)
        for source_url in (
            "https://doi.org/10.1234/reef?token=secret", "https://doi.org/10.1234/reef#email@example.org",
            "https://user:token@doi.org/10.1234/reef", "https://doi.org/10.1234/reef?",
            "https://doi.org/10.1234/reef#", "https://[bad",
        ):
            with self.subTest(source_url=source_url):
                result = self.import_rows(row(source_url=source_url))
                self.assertFalse(result.ready_for_persistence)
                self.assertEqual(((), "invalid_source_url"), (result.candidates, result.rejected[0].reason))
        source = "\n".join((",".join(row().keys()), ",".join(json.dumps(value) if isinstance(value, list) else str(value) for value in row().values())))
        self.assertFalse(self.importer().import_csv(source, policy=policy(max_input_bytes=1)).ready_for_persistence)
        result = self.import_rows(row(record_id="one"), row(record_id="two"), max_rows=1)
        self.assertFalse(result.ready_for_persistence)
        self.assertEqual("max_rows_exceeded", result.rejected[0].reason)

        consumed = 0

        def unbounded_records():
            nonlocal consumed
            while True:
                consumed += 1
                yield row(record_id=f"row-{consumed}")

        result = self.importer().import_records(unbounded_records(), policy=policy(max_rows=2))
        self.assertFalse(result.ready_for_persistence)
        self.assertEqual(("max_rows_exceeded", 3), (result.rejected[0].reason, consumed))
