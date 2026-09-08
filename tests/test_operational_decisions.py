import csv
import math
import tempfile
import unittest
from pathlib import Path

from operational.decisions import (
    DecisionCoverageError,
    DecisionSchemaError,
    DecisionStationNotFoundError,
    StationDecisionSnapshot,
    load_station_decision,
)


CSV_PATH = Path("08_GIS_and_Remote_Sensing/geospatial_outputs/spatial_restoration_priority_ranking.csv")


class DecisionLoaderTests(unittest.TestCase):
    def test_loads_by_canonical_id_and_name_as_immutable_json_safe_snapshot(self):
        by_id = load_station_decision("station-01", CSV_PATH)
        by_name = load_station_decision(by_id.station_name, CSV_PATH)

        self.assertIsInstance(by_id, StationDecisionSnapshot)
        self.assertEqual(by_id, by_name)
        self.assertEqual(by_id.station_name, "Mesoamerican_Fore_01")
        self.assertEqual(by_id.source, "srpi_snapshot_csv")
        self.assertNotIn("\\", by_id.to_dict()["source"])
        self.assertNotIn("/", by_id.to_dict()["source"])
        self.assertIn(by_id.priority_tier, {"Tier_1_High_Priority_Restoration", "Tier_2_Moderate_Priority", "Tier_3_Lower_Priority"})
        self.assertTrue(all(math.isfinite(value) for value in (by_id.macroalgae_cover_pct, by_id.bleaching_severity_pct, by_id.coral_cover_loss_pct, by_id.srpi)))
        with self.assertRaises(AttributeError):
            by_id.srpi = 0.0

    def test_unknown_station_is_explicit(self):
        with self.assertRaises(DecisionStationNotFoundError):
            load_station_decision("not-a-station", CSV_PATH)

    def test_missing_schema_is_typed_error(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "bad.csv"
            path.write_text("Station_Name,Region\nMesoamerican_Fore_01,Caribbean\n", encoding="utf-8")
            with self.assertRaises(DecisionSchemaError):
                load_station_decision("station-01", path)

    def test_duplicate_or_incomplete_canonical_coverage_is_rejected(self):
        rows = list(csv.DictReader(CSV_PATH.open(newline="", encoding="utf-8")))
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "duplicate.csv"
            with path.open("w", newline="", encoding="utf-8") as handle:
                writer = csv.DictWriter(handle, fieldnames=rows[0].keys())
                writer.writeheader()
                writer.writerows(rows + [rows[0]])
            with self.assertRaises(DecisionCoverageError):
                load_station_decision("station-01", path)


if __name__ == "__main__":
    unittest.main()
