"""Contract tests for the canonical station registry and static baselines."""

from __future__ import annotations

import csv
import tempfile
import unittest
from pathlib import Path

from operational.stations import (
    BASELINE_FEATURES,
    BaselineDataError,
    BaselineSchemaError,
    CANONICAL_STATIONS,
    StationNotFoundError,
    get_station,
    load_station_baseline,
)


def write_csv(rows: list[dict[str, str]], fieldnames: list[str] | None = None) -> str:
    temporary = tempfile.NamedTemporaryFile(mode="w", newline="", suffix=".csv", delete=False, encoding="utf-8")
    columns = fieldnames or list(rows[0])
    with temporary:
        writer = csv.DictWriter(temporary, fieldnames=columns)
        writer.writeheader()
        writer.writerows(rows)
    return temporary.name


def baseline_row(*, station_name: str = "Mesoamerican_Fore_01", date: str = "2024-01-01", sst: str = "28.1") -> dict[str, str]:
    return {
        "Station_Name": station_name,
        "Date": date,
        "Depth_m": "12.5",
        "SST_degC": sst,
        "SST_Anomaly_degC": "0.4",
        "DHW_degC_weeks": "1.0",
        "pH_total": "8.1",
        "Aragonite_Saturation_Omega": "3.8",
        "Turbidity_NTU": "0.7",
        "PAR_umol_m2_s": "1000.0",
        "Structural_Rugosity": "2.5",
        "Live_Coral_Cover_Pct": "35.0",
    }


class CanonicalStationRegistryTests(unittest.TestCase):
    def test_contains_exactly_the_25_source_identities_with_stable_ids(self) -> None:
        self.assertEqual(25, len(CANONICAL_STATIONS))
        first = get_station("station-01")
        last = get_station("station-25")
        self.assertEqual(("Mesoamerican_Fore_01", 18.25, -87.80), (first.name, first.latitude, first.longitude))
        self.assertEqual(("Palau_RockIslands_25", 7.30, 134.45), (last.name, last.latitude, last.longitude))
        self.assertEqual(tuple(f"station-{number:02d}" for number in range(1, 26)), tuple(item.station_id for item in CANONICAL_STATIONS))

    def test_rejects_an_unknown_station_id(self) -> None:
        with self.assertRaises(StationNotFoundError):
            get_station("station-99")


class StationBaselineLoaderTests(unittest.TestCase):
    def tearDown(self) -> None:
        for path in getattr(self, "paths", []):
            Path(path).unlink(missing_ok=True)

    def test_uses_the_latest_dated_row_and_the_exact_feature_order(self) -> None:
        self.paths = [
            write_csv(
                [
                    baseline_row(date="2023-10-01", sst="27.1"),
                    baseline_row(date="2024-10-01", sst="29.3"),
                ]
            )
        ]

        baseline = load_station_baseline("station-01", self.paths[0])

        self.assertEqual(BASELINE_FEATURES, baseline.feature_names)
        self.assertEqual("2024-10-01", baseline.source_date)
        self.assertEqual((12.5, 29.3, 0.4, 1.0, 8.1, 3.8, 0.7, 1000.0, 2.5, 35.0), baseline.values)

    def test_uses_the_first_matching_physical_row_when_no_date_column_exists(self) -> None:
        first = baseline_row(sst="27.1")
        second = baseline_row(sst="29.3")
        first.pop("Date")
        second.pop("Date")
        self.paths = [write_csv([first, second])]

        baseline = load_station_baseline("station-01", self.paths[0])

        self.assertIsNone(baseline.source_date)
        self.assertEqual(27.1, baseline.values[1])

    def test_fails_explicitly_for_missing_schema_file_or_station_data(self) -> None:
        missing_feature = baseline_row()
        missing_feature.pop("pH_total")
        self.paths = [write_csv([missing_feature])]

        with self.assertRaises(BaselineSchemaError):
            load_station_baseline("station-01", self.paths[0])
        with self.assertRaises(BaselineDataError):
            load_station_baseline("station-01", "does-not-exist.csv")
        other_station = write_csv([baseline_row(station_name="Belize_Barrier_05")])
        self.paths.append(other_station)
        with self.assertRaises(BaselineDataError):
            load_station_baseline("station-01", other_station)


if __name__ == "__main__":
    unittest.main()
