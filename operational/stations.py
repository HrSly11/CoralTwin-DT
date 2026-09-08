"""Canonical operational station registry and deterministic baseline loading."""

from __future__ import annotations

import csv
import math
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import Iterable

from .repository import Station


class StationNotFoundError(LookupError):
    """Raised when a station identifier is not in the canonical registry."""


class BaselineDataError(RuntimeError):
    """Raised when a baseline file cannot provide data for a station."""


class BaselineSchemaError(BaselineDataError):
    """Raised when a baseline CSV does not have the required schema."""


@dataclass(frozen=True)
class StationBaseline:
    """Feature vector and provenance selected for one station."""

    feature_names: tuple[str, ...]
    values: tuple[float, ...]
    source_date: str | None


# This is intentionally the same feature order used by train_models.py.
BASELINE_FEATURES: tuple[str, ...] = (
    "Depth_m",
    "SST_degC",
    "SST_Anomaly_degC",
    "DHW_degC_weeks",
    "pH_total",
    "Aragonite_Saturation_Omega",
    "Turbidity_NTU",
    "PAR_umol_m2_s",
    "Structural_Rugosity",
    "Live_Coral_Cover_Pct",
)

_DEFAULT_BASELINE_PATH = (
    Path(__file__).resolve().parents[1]
    / "03_Data"
    / "processed_data"
    / "coral_environmental_harmonized.csv"
)


# Source of truth: generate_datasets.generate_pilot_stations().  Keep the
# ordered literal here so importing the operational layer never executes the
# data-generation script (which has filesystem and random-number side effects).
_STATION_IDENTITIES: tuple[tuple[str, float, float], ...] = (
    ("Mesoamerican_Fore_01", 18.25, -87.80),
    ("Mesoamerican_Crest_02", 18.28, -87.82),
    ("Mesoamerican_Back_03", 18.31, -87.85),
    ("Mesoamerican_Lagoon_04", 18.35, -87.88),
    ("Belize_Barrier_05", 17.15, -87.90),
    ("Belize_Atoll_06", 17.20, -87.55),
    ("Cozumel_South_07", 20.30, -87.02),
    ("Cozumel_Shallow_08", 20.35, -86.98),
    ("Roatan_North_09", 16.38, -86.50),
    ("Roatan_South_10", 16.32, -86.55),
    ("Florida_Keys_Uppers_11", 25.02, -80.40),
    ("Florida_Keys_Lowers_12", 24.55, -81.45),
    ("GreatBarrier_Northern_13", -14.50, 145.45),
    ("GreatBarrier_Central_14", -18.25, 147.20),
    ("GreatBarrier_Lagoon_15", -18.30, 147.15),
    ("CoralTriangle_RajaAmpat_16", -0.55, 130.50),
    ("CoralTriangle_Misool_17", -1.95, 130.15),
    ("CoralTriangle_Komodo_18", -8.60, 119.55),
    ("CoralTriangle_Sulawesi_19", 1.65, 124.75),
    ("Okinawa_Kerama_20", 26.20, 127.35),
    ("RedSea_Aqaba_21", 29.45, 34.95),
    ("RedSea_Shallow_22", 27.20, 33.85),
    ("Hawaii_Kaneohe_23", 21.45, -157.80),
    ("Hawaii_OahuFore_24", 21.30, -157.70),
    ("Palau_RockIslands_25", 7.30, 134.45),
)

CANONICAL_STATIONS: tuple[Station, ...] = tuple(
    Station(f"station-{index:02d}", name, latitude, longitude)
    for index, (name, latitude, longitude) in enumerate(_STATION_IDENTITIES, start=1)
)
_STATIONS_BY_ID = {station.station_id: station for station in CANONICAL_STATIONS}


def get_station(station_id: str) -> Station:
    """Return a canonical station or raise an explicit lookup error."""

    try:
        return _STATIONS_BY_ID[station_id]
    except (KeyError, TypeError) as exc:
        raise StationNotFoundError(f"Unknown canonical station: {station_id!r}") from exc


def _read_rows(path: Path) -> tuple[tuple[str, ...], list[dict[str, str]]]:
    try:
        with path.open("r", newline="", encoding="utf-8") as handle:
            reader = csv.DictReader(handle)
            fieldnames = tuple(reader.fieldnames or ())
            rows = list(reader)
    except (OSError, UnicodeError, csv.Error) as exc:
        raise BaselineDataError(f"Unable to read baseline CSV {str(path)!r}: {exc}") from exc
    return fieldnames, rows


def _select_row(rows: Iterable[dict[str, str]], has_date: bool) -> tuple[dict[str, str], str | None]:
    candidates = list(rows)
    if not candidates:
        raise BaselineDataError("Baseline CSV contains no data for the requested station")
    if not has_date:
        return candidates[0], None

    dated: list[tuple[date, int, dict[str, str]]] = []
    for index, row in enumerate(candidates):
        raw_date = (row.get("Date") or "").strip()
        try:
            parsed_date = date.fromisoformat(raw_date)
        except ValueError as exc:
            raise BaselineDataError(f"Invalid baseline date {raw_date!r}") from exc
        dated.append((parsed_date, index, row))
    _, _, selected = max(dated, key=lambda item: (item[0], -item[1]))
    return selected, selected["Date"].strip()


def load_station_baseline(station_id: str, csv_path: str | Path | None = None) -> StationBaseline:
    """Load the latest deterministic physical feature row for a station.

    If a CSV has no ``Date`` column, its first matching row is used.  This
    accommodates static snapshots while retaining latest-observation behavior
    for the generated harmonized feed.
    """

    station = get_station(station_id)
    path = Path(csv_path) if csv_path is not None else _DEFAULT_BASELINE_PATH
    fieldnames, rows = _read_rows(path)

    required = {"Station_Name", *BASELINE_FEATURES}
    missing = tuple(sorted(required.difference(fieldnames)))
    if missing:
        raise BaselineSchemaError(
            f"Baseline CSV {str(path)!r} is missing required columns: {', '.join(missing)}"
        )

    matching_rows = [row for row in rows if row.get("Station_Name") == station.name]
    if not matching_rows:
        raise BaselineDataError(
            f"Baseline CSV {str(path)!r} has no data for station {station.station_id} ({station.name})"
        )

    selected, source_date = _select_row(matching_rows, "Date" in fieldnames)
    values: list[float] = []
    for feature in BASELINE_FEATURES:
        raw_value = (selected.get(feature) or "").strip()
        try:
            value = float(raw_value)
        except (TypeError, ValueError) as exc:
            raise BaselineDataError(
                f"Invalid value for feature {feature!r} in station {station.name}: {raw_value!r}"
            ) from exc
        if not math.isfinite(value):
            raise BaselineDataError(
                f"Non-finite value for feature {feature!r} in station {station.name}: {raw_value!r}"
            )
        values.append(value)

    return StationBaseline(BASELINE_FEATURES, tuple(values), source_date)


# Convenient compatibility alias for callers that prefer the shorter name.
Baseline = StationBaseline


__all__ = [
    "BASELINE_FEATURES",
    "Baseline",
    "BaselineDataError",
    "BaselineSchemaError",
    "CANONICAL_STATIONS",
    "Station",
    "StationBaseline",
    "StationNotFoundError",
    "get_station",
    "load_station_baseline",
]
