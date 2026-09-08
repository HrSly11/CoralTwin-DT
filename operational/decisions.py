"""Deterministic SRPI decision snapshots from the canonical GIS export."""

from __future__ import annotations

import csv
import math
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from .stations import CANONICAL_STATIONS


class DecisionDataError(RuntimeError):
    """Base error for invalid decision snapshot data."""


class DecisionSchemaError(DecisionDataError):
    """The decision CSV does not satisfy its required schema."""


class DecisionCoverageError(DecisionDataError):
    """The decision CSV does not cover each canonical station exactly once."""


class DecisionStationNotFoundError(LookupError):
    """The requested station is not canonical."""


_DEFAULT_PATH = Path(__file__).resolve().parents[1] / "08_GIS_and_Remote_Sensing" / "geospatial_outputs" / "spatial_restoration_priority_ranking.csv"
_REQUIRED = {"Station_Name", "Region", "Reef_Zone", "Macroalgae_Cover_Pct", "Bleaching_Severity_Pct", "Coral_Cover_Loss_Pct", "Spatial_Restoration_Priority_Index_SRPI", "Priority_Tier"}
_TIERS = {"Tier_1_High_Priority_Restoration", "Tier_2_Secondary_Conservation", "Tier_3_Low_Monitoring"}


@dataclass(frozen=True)
class StationDecisionSnapshot:
    station_name: str
    region: str
    reef_zone: str
    macroalgae_cover_pct: float
    bleaching_severity_pct: float
    coral_cover_loss_pct: float
    srpi: float
    priority_tier: str
    source: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def _station_name(value: str) -> str:
    for station in CANONICAL_STATIONS:
        if value in (station.station_id, station.name):
            return station.name
    raise DecisionStationNotFoundError(f"Unknown canonical station: {value!r}")


def load_station_decision(station_id_or_station_name: str, csv_path: str | Path | None = None) -> StationDecisionSnapshot:
    station_name = _station_name(station_id_or_station_name)
    path = Path(csv_path) if csv_path is not None else _DEFAULT_PATH
    try:
        with path.open("r", newline="", encoding="utf-8") as handle:
            reader = csv.DictReader(handle)
            fieldnames = set(reader.fieldnames or ())
            missing = sorted(_REQUIRED - fieldnames)
            if missing:
                raise DecisionSchemaError(f"Decision CSV is missing required columns: {', '.join(missing)}")
            rows = list(reader)
    except DecisionDataError:
        raise
    except (OSError, UnicodeError, csv.Error) as error:
        raise DecisionDataError(f"Unable to read decision CSV {str(path)!r}: {error}") from error

    names = [row.get("Station_Name", "") for row in rows]
    canonical = {station.name for station in CANONICAL_STATIONS}
    if len(names) != len(set(names)) or set(names) != canonical:
        raise DecisionCoverageError("Decision CSV must contain each canonical station exactly once")
    row = next(row for row in rows if row["Station_Name"] == station_name)
    numeric_fields = {
        "Macroalgae_Cover_Pct": "macroalgae_cover_pct",
        "Bleaching_Severity_Pct": "bleaching_severity_pct",
        "Coral_Cover_Loss_Pct": "coral_cover_loss_pct",
        "Spatial_Restoration_Priority_Index_SRPI": "srpi",
    }
    values = {}
    try:
        for source_name, target_name in numeric_fields.items():
            value = float(row[source_name])
            if not math.isfinite(value):
                raise ValueError(f"{source_name} is not finite")
            values[target_name] = value
    except (KeyError, TypeError, ValueError) as error:
        raise DecisionSchemaError(f"Invalid numeric decision value for {station_name}: {error}") from error
    tier = row["Priority_Tier"]
    if tier not in _TIERS:
        raise DecisionSchemaError(f"Invalid priority tier {tier!r}")
    return StationDecisionSnapshot(station_name, row["Region"], row["Reef_Zone"], priority_tier=tier, source="srpi_snapshot_csv", **values)


__all__ = ["DecisionCoverageError", "DecisionDataError", "DecisionSchemaError", "DecisionStationNotFoundError", "StationDecisionSnapshot", "load_station_decision"]
