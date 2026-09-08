"""SQLite persistence for NOAA observations and synchronization evidence."""

from __future__ import annotations

import sqlite3
import json
import threading
import uuid
import math
import re
import time
from dataclasses import dataclass
from datetime import date, datetime, timedelta, timezone
from functools import wraps
from pathlib import Path
from typing import Any, Callable, Mapping, TypeVar

from .noaa_adapter import ProductObservation, SOURCE as NOAA_SOURCE
from .observations import CanonicalObservation, ObservationValidationError


_RepositoryMethod = TypeVar("_RepositoryMethod", bound=Callable[..., Any])
SYNC_LEASE_NAME = "operational-noaa-sync"
_SAFE_METRIC = re.compile(r"^[A-Za-z][A-Za-z0-9_.:-]{0,127}$")


def _synchronized(method: _RepositoryMethod) -> _RepositoryMethod:
    """Serialize connection access while allowing nested repository reads."""

    @wraps(method)
    def synchronized(self: "SQLiteOperationalRepository", *args: Any, **kwargs: Any) -> Any:
        with self._lock:
            return method(self, *args, **kwargs)

    return synchronized  # type: ignore[return-value]


def _as_timestamp(value: datetime) -> str:
    timestamp = value if value.tzinfo else value.replace(tzinfo=timezone.utc)
    return timestamp.astimezone(timezone.utc).isoformat()


def _as_utc_datetime(value: datetime) -> datetime:
    return (value if value.tzinfo else value.replace(tzinfo=timezone.utc)).astimezone(timezone.utc)


def _from_timestamp(value: str) -> datetime:
    return datetime.fromisoformat(value).astimezone(timezone.utc)


def _now_timestamp() -> str:
    return datetime.now(timezone.utc).isoformat()


def _utc_month_bounds(month: date) -> tuple[datetime, datetime]:
    if type(month) is not date or month.day != 1:
        raise ValueError("month must be a calendar month represented by its first day")
    start = datetime(month.year, month.month, 1, tzinfo=timezone.utc)
    if month.month == 12:
        return start, datetime(month.year + 1, 1, 1, tzinfo=timezone.utc)
    return start, datetime(month.year, month.month + 1, 1, tzinfo=timezone.utc)


def _as_as_of_cutoff(value: datetime) -> datetime:
    if not isinstance(value, datetime) or value.tzinfo is None or value.utcoffset() != timedelta(0):
        raise ValueError("cutoff must be a timezone-aware UTC datetime")
    return value.astimezone(timezone.utc)


@dataclass(frozen=True)
class Station:
    station_id: str
    name: str
    latitude: float
    longitude: float


@dataclass(frozen=True)
class LatestState:
    station: Station
    sst: ProductObservation | None
    dhw: ProductObservation | None


@dataclass(frozen=True)
class SyncRun:
    run_id: int
    station_id: str
    started_at: datetime
    finished_at: datetime | None
    status: str


@dataclass(frozen=True)
class SyncError:
    error_id: int
    run_id: int
    product: str
    error_type: str
    message: str
    occurred_at: datetime


class SQLiteOperationalRepository:
    """A lightweight, foreign-key-enforced store with append-only observations."""

    def __init__(self, database_path: str | Path, *, clock: Callable[[], datetime] | None = None) -> None:
        self._lock = threading.RLock()
        self._clock = clock or (lambda: datetime.now(timezone.utc))
        self._connection = sqlite3.connect(str(database_path), check_same_thread=False)
        self._connection.row_factory = sqlite3.Row
        with self._lock:
            self._connection.execute("PRAGMA foreign_keys = ON")
        try:
            self._initialize_schema()
        except Exception:
            self._connection.close()
            raise

    @_synchronized
    def close(self) -> None:
        self._connection.close()

    @_synchronized
    def _initialize_schema(self) -> None:
        self._connection.executescript(
            """
            CREATE TABLE IF NOT EXISTS stations (
                station_id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                latitude REAL NOT NULL,
                longitude REAL NOT NULL
            );
            CREATE TABLE IF NOT EXISTS product_observations (
                observation_id INTEGER PRIMARY KEY,
                station_id TEXT NOT NULL REFERENCES stations(station_id),
                product TEXT NOT NULL,
                observed_at TEXT NOT NULL,
                requested_latitude REAL NOT NULL,
                requested_longitude REAL NOT NULL,
                returned_latitude REAL NOT NULL,
                returned_longitude REAL NOT NULL,
                value REAL NOT NULL,
                unit TEXT NOT NULL,
                source TEXT NOT NULL,
                dataset_id TEXT NOT NULL,
                request_url TEXT NOT NULL,
                accessed_at TEXT NOT NULL,
                UNIQUE(station_id, product, observed_at, source)
            );
            CREATE TABLE IF NOT EXISTS sync_runs (
                run_id INTEGER PRIMARY KEY,
                station_id TEXT NOT NULL REFERENCES stations(station_id),
                started_at TEXT NOT NULL,
                finished_at TEXT,
                status TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS sync_errors (
                error_id INTEGER PRIMARY KEY,
                run_id INTEGER NOT NULL REFERENCES sync_runs(run_id),
                product TEXT NOT NULL,
                error_type TEXT NOT NULL,
                message TEXT NOT NULL,
                occurred_at TEXT NOT NULL
            );
            CREATE INDEX IF NOT EXISTS idx_product_observations_latest
                ON product_observations(station_id, product, observed_at DESC);
            CREATE TABLE IF NOT EXISTS canonical_observations (
                revision INTEGER PRIMARY KEY AUTOINCREMENT,
                identity TEXT NOT NULL,
                logical_observation_id TEXT NOT NULL,
                content_hash TEXT NOT NULL,
                supersedes_revision INTEGER REFERENCES canonical_observations(revision),
                station_id TEXT NOT NULL REFERENCES stations(station_id),
                metric TEXT NOT NULL,
                observed_at TEXT NOT NULL,
                unit TEXT NOT NULL,
                value REAL NOT NULL,
                provenance_kind TEXT NOT NULL CHECK(provenance_kind IN ('observed', 'derived', 'simulated')),
                provider TEXT,
                dataset_id TEXT,
                accessed_at TEXT,
                available_at TEXT,
                request_url TEXT,
                requested_latitude REAL,
                requested_longitude REAL,
                returned_latitude REAL,
                returned_longitude REAL,
                quality_flags_json TEXT NOT NULL,
                uncertainty REAL,
                derivation_method TEXT,
                input_lineage_json TEXT NOT NULL,
                model_version TEXT,
                scenario_id TEXT,
                source_evidence_json TEXT NOT NULL,
                CHECK(json_valid(quality_flags_json)),
                CHECK(json_valid(input_lineage_json)),
                CHECK(json_valid(source_evidence_json)),
                UNIQUE(logical_observation_id, content_hash)
            );
            CREATE TABLE IF NOT EXISTS canonical_observation_axes (
                logical_observation_id TEXT PRIMARY KEY,
                station_id TEXT NOT NULL,
                metric TEXT NOT NULL,
                observed_at TEXT NOT NULL
            );
            CREATE INDEX IF NOT EXISTS idx_canonical_observations_station_metric_time
                ON canonical_observations(station_id, metric, observed_at DESC);
            CREATE INDEX IF NOT EXISTS idx_sync_errors_run ON sync_errors(run_id);
            CREATE TABLE IF NOT EXISTS sync_leases (
                lease_name TEXT PRIMARY KEY,
                owner_token TEXT NOT NULL,
                acquired_at TEXT NOT NULL,
                expires_at TEXT NOT NULL
            );
            """
        )
        self._connection.execute("BEGIN IMMEDIATE")
        try:
            self._migrate_canonical_ledger_if_needed()
            self._ensure_canonical_available_at_column()
            self._ensure_canonical_revision_index()
            self._backfill_legacy_noaa_observations()
            self._connection.commit()
        except Exception:
            self._connection.rollback()
            raise

    def _ensure_canonical_revision_index(self) -> None:
        columns = {row["name"] for row in self._connection.execute("PRAGMA table_info(canonical_observations)")}
        if "revision" not in columns:
            return
        self._connection.execute("DROP INDEX IF EXISTS idx_canonical_observations_station_metric_time")
        self._connection.execute(
            "CREATE INDEX idx_canonical_observations_station_metric_time "
            "ON canonical_observations(station_id, metric, observed_at DESC, revision DESC)"
        )
        self._connection.execute(
            "CREATE INDEX IF NOT EXISTS idx_canonical_observations_as_of "
            "ON canonical_observations(station_id, metric, observed_at, available_at, revision DESC)"
        )

    def _ensure_canonical_available_at_column(self) -> None:
        """Add availability metadata without fabricating it for historical rows."""

        columns = {row["name"] for row in self._connection.execute("PRAGMA table_info(canonical_observations)")}
        if "available_at" not in columns:
            self._connection.execute("ALTER TABLE canonical_observations ADD COLUMN available_at TEXT")

    def _migrate_canonical_ledger_if_needed(self) -> None:
        """Upgrade pre-logical-id ledger schemas into immutable logical chains."""

        columns = {row["name"] for row in self._connection.execute("PRAGMA table_info(canonical_observations)")}
        if "logical_observation_id" in columns:
            return
        legacy_rows = self._connection.execute("SELECT * FROM canonical_observations ORDER BY rowid").fetchall()
        self._connection.execute("ALTER TABLE canonical_observations RENAME TO canonical_observations_legacy")
        self._connection.execute("DROP INDEX IF EXISTS idx_canonical_observations_station_metric_time")
        self._connection.execute(
            """CREATE TABLE canonical_observations (
                revision INTEGER PRIMARY KEY AUTOINCREMENT, identity TEXT NOT NULL,
                logical_observation_id TEXT NOT NULL, content_hash TEXT NOT NULL,
                supersedes_revision INTEGER REFERENCES canonical_observations(revision),
                station_id TEXT NOT NULL REFERENCES stations(station_id), metric TEXT NOT NULL,
                observed_at TEXT NOT NULL, unit TEXT NOT NULL, value REAL NOT NULL,
                provenance_kind TEXT NOT NULL CHECK(provenance_kind IN ('observed', 'derived', 'simulated')),
                provider TEXT, dataset_id TEXT, accessed_at TEXT, available_at TEXT, request_url TEXT,
                requested_latitude REAL, requested_longitude REAL, returned_latitude REAL,
                returned_longitude REAL, quality_flags_json TEXT NOT NULL, uncertainty REAL,
                derivation_method TEXT, input_lineage_json TEXT NOT NULL, model_version TEXT,
                scenario_id TEXT, source_evidence_json TEXT NOT NULL,
                CHECK(json_valid(quality_flags_json)), CHECK(json_valid(input_lineage_json)),
                CHECK(json_valid(source_evidence_json)), UNIQUE(logical_observation_id, content_hash)
            )"""
        )
        self._connection.execute(
            """CREATE TABLE IF NOT EXISTS canonical_observation_axes (
                logical_observation_id TEXT PRIMARY KEY, station_id TEXT NOT NULL,
                metric TEXT NOT NULL, observed_at TEXT NOT NULL
            )"""
        )
        self._connection.execute(
            "CREATE INDEX idx_canonical_observations_station_metric_time "
            "ON canonical_observations(station_id, metric, observed_at DESC, revision DESC)"
        )
        for row in legacy_rows:
            evidence = json.loads(row["source_evidence_json"])
            record = CanonicalObservation(
                station_id=row["station_id"], metric=row["metric"], observed_at=_from_timestamp(row["observed_at"]),
                unit=row["unit"], value=row["value"], provenance_kind=row["provenance_kind"],
                logical_observation_id=self._legacy_logical_observation_id(row),
                provider=row["provider"], dataset_id=row["dataset_id"],
                accessed_at=_from_timestamp(row["accessed_at"]) if row["accessed_at"] else None,
                request_url=row["request_url"], asset_id=evidence.get("asset_id"), asset_href=evidence.get("asset_href"),
                requested_latitude=row["requested_latitude"], requested_longitude=row["requested_longitude"],
                returned_latitude=row["returned_latitude"], returned_longitude=row["returned_longitude"],
                quality_flags=tuple(json.loads(row["quality_flags_json"])),
                uncertainty=row["uncertainty"], derivation_method=row["derivation_method"],
                input_lineage=tuple(json.loads(row["input_lineage_json"])),
                model_version=row["model_version"], scenario_id=row["scenario_id"],
            )
            self._upsert_canonical_observation(record, assign_available_at=False)
        self._connection.execute("DROP TABLE canonical_observations_legacy")

    @staticmethod
    def _legacy_logical_observation_id(row: sqlite3.Row) -> str:
        observed_at = _from_timestamp(row["observed_at"])
        if row["provenance_kind"] == "observed" and row["provider"] == NOAA_SOURCE:
            return CanonicalObservation.noaa_logical_observation_id(row["station_id"], row["metric"], observed_at)
        return f"legacy:{row['identity']}"

    def _backfill_legacy_noaa_observations(self) -> None:
        """Add provenance-preserving canonical records for legacy NOAA cache rows only."""

        rows = self._connection.execute(
            """
            SELECT station_id, product, observed_at, requested_latitude, requested_longitude,
                   returned_latitude, returned_longitude, value, unit, source, dataset_id,
                   request_url, accessed_at
            FROM product_observations WHERE source = ?
            """,
            (NOAA_SOURCE,),
        ).fetchall()
        for row in rows:
            try:
                record = CanonicalObservation.from_noaa(
                    ProductObservation(
                        station_id=row["station_id"], product=row["product"], observed_at=_from_timestamp(row["observed_at"]),
                        requested_latitude=row["requested_latitude"], requested_longitude=row["requested_longitude"],
                        returned_latitude=row["returned_latitude"], returned_longitude=row["returned_longitude"],
                        value=row["value"], unit=row["unit"], source=row["source"], dataset_id=row["dataset_id"],
                        request_url=row["request_url"], accessed_at=_from_timestamp(row["accessed_at"]),
                    )
                )
            except (ObservationValidationError, TypeError, ValueError):
                # A legacy row without valid source evidence is deliberately not relabelled.
                continue
            self._upsert_canonical_observation(record)

    @_synchronized
    def upsert_station(self, station_id: str, name: str, latitude: float, longitude: float) -> Station:
        self._connection.execute(
            """
            INSERT INTO stations(station_id, name, latitude, longitude) VALUES (?, ?, ?, ?)
            ON CONFLICT(station_id) DO UPDATE SET name = excluded.name, latitude = excluded.latitude,
                longitude = excluded.longitude
            """,
            (station_id, name, latitude, longitude),
        )
        self._connection.commit()
        return Station(station_id, name, float(latitude), float(longitude))

    @_synchronized
    def save_observation(self, observation: ProductObservation) -> bool:
        """Atomically mirror a validated adapter result to cache and evidence ledger."""

        if not isinstance(observation, ProductObservation):
            raise TypeError("observation must be a ProductObservation")
        canonical = CanonicalObservation.from_noaa(observation)
        self._connection.execute("BEGIN")
        try:
            legacy_changed = self._save_product_observation(observation)
            ledger_changed = self._upsert_canonical_observation(canonical)
            self._connection.commit()
            return legacy_changed or ledger_changed
        except Exception:
            self._connection.rollback()
            raise

    def _save_product_observation(self, observation: ProductObservation) -> bool:
        cursor = self._connection.execute(
            """
            INSERT INTO product_observations(
                station_id, product, observed_at, requested_latitude, requested_longitude,
                returned_latitude, returned_longitude, value, unit, source, dataset_id,
                request_url, accessed_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(station_id, product, observed_at, source) DO UPDATE SET
                requested_latitude = excluded.requested_latitude,
                requested_longitude = excluded.requested_longitude,
                returned_latitude = excluded.returned_latitude,
                returned_longitude = excluded.returned_longitude,
                value = excluded.value,
                unit = excluded.unit,
                dataset_id = excluded.dataset_id,
                request_url = excluded.request_url,
                accessed_at = excluded.accessed_at
            WHERE product_observations.requested_latitude IS NOT excluded.requested_latitude
               OR product_observations.requested_longitude IS NOT excluded.requested_longitude
               OR product_observations.returned_latitude IS NOT excluded.returned_latitude
               OR product_observations.returned_longitude IS NOT excluded.returned_longitude
               OR product_observations.value IS NOT excluded.value
               OR product_observations.unit IS NOT excluded.unit
               OR product_observations.dataset_id IS NOT excluded.dataset_id
               OR product_observations.request_url IS NOT excluded.request_url
               OR product_observations.accessed_at IS NOT excluded.accessed_at
            """,
            (
                observation.station_id, observation.product, _as_timestamp(observation.observed_at),
                observation.requested_latitude, observation.requested_longitude, observation.returned_latitude,
                observation.returned_longitude, observation.value, observation.unit, observation.source,
                observation.dataset_id, observation.request_url, _as_timestamp(observation.accessed_at),
            ),
        )
        return cursor.rowcount == 1

    @_synchronized
    def save_canonical_observation(self, observation: CanonicalObservation) -> bool:
        if not isinstance(observation, CanonicalObservation):
            raise TypeError("observation must be a CanonicalObservation")
        self._connection.execute("BEGIN")
        try:
            changed = self._upsert_canonical_observation(observation)
            self._connection.commit()
            return changed
        except Exception:
            self._connection.rollback()
            raise

    def _upsert_canonical_observation(
        self, observation: CanonicalObservation, *, assign_available_at: bool = True
    ) -> bool:
        observation = observation.validated_copy()
        quality_flags_json, input_lineage_json, source_evidence_json = observation.json_columns()
        axis = self._connection.execute(
            "SELECT station_id, metric, observed_at FROM canonical_observation_axes WHERE logical_observation_id = ?",
            (observation.logical_observation_id,),
        ).fetchone()
        expected_axis = (observation.station_id, observation.metric, _as_timestamp(observation.observed_at))
        if axis is not None and (axis["station_id"], axis["metric"], axis["observed_at"]) != expected_axis:
            raise ObservationValidationError("logical_observation_id cannot change its immutable station, metric, or observed_at axis")
        existing = self._connection.execute(
            "SELECT revision FROM canonical_observations WHERE logical_observation_id = ? AND content_hash = ?",
            (observation.logical_observation_id, observation.content_hash),
        ).fetchone()
        if existing is not None:
            return False
        if axis is None:
            self._connection.execute(
                "INSERT INTO canonical_observation_axes(logical_observation_id, station_id, metric, observed_at) VALUES (?, ?, ?, ?)",
                (observation.logical_observation_id, *expected_axis),
            )
        current = self._connection.execute(
            "SELECT revision FROM canonical_observations WHERE logical_observation_id = ? ORDER BY revision DESC LIMIT 1",
            (observation.logical_observation_id,),
        ).fetchone()
        available_at = _as_timestamp(_as_utc_datetime(self._clock())) if assign_available_at else None
        cursor = self._connection.execute(
            """
            INSERT INTO canonical_observations(
                identity, logical_observation_id, content_hash, supersedes_revision, station_id, metric, observed_at, unit, value, provenance_kind, provider,
                dataset_id, accessed_at, available_at, request_url, requested_latitude, requested_longitude,
                returned_latitude, returned_longitude, quality_flags_json, uncertainty,
                derivation_method, input_lineage_json, model_version, scenario_id, source_evidence_json
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                observation.identity, observation.logical_observation_id, observation.content_hash, current["revision"] if current else None,
                observation.station_id, observation.metric, _as_timestamp(observation.observed_at),
                observation.unit, observation.value, observation.provenance_kind, observation.provider,
                observation.dataset_id, _as_timestamp(observation.accessed_at) if observation.accessed_at else None, available_at,
                observation.request_url, observation.requested_latitude, observation.requested_longitude,
                observation.returned_latitude, observation.returned_longitude, quality_flags_json,
                observation.uncertainty, observation.derivation_method, input_lineage_json,
                observation.model_version, observation.scenario_id, source_evidence_json,
            ),
        )
        return cursor.rowcount == 1

    @_synchronized
    def list_canonical_observations(
        self, station_id: str, metric: str | None = None
    ) -> list[dict[str, Any]]:
        query = "SELECT * FROM canonical_observations WHERE station_id = ?"
        parameters: tuple[str, ...] = (station_id,)
        if metric is not None:
            query += " AND metric = ?"
            parameters += (metric,)
        query += " ORDER BY observed_at, revision"
        return [self._canonical_row_to_dict(row) for row in self._connection.execute(query, parameters).fetchall()]

    @_synchronized
    def list_canonical_observations_as_of(
        self,
        month: date,
        cutoff: datetime,
        *,
        station_ids: tuple[str, ...] | None = None,
        metrics: tuple[str, ...] | None = None,
    ) -> list[dict[str, Any]]:
        """Return only the latest observed revision knowable at one UTC cutoff.

        Historical rows without ``available_at`` intentionally remain invisible:
        assigning availability during migration would fabricate availability time.
        """

        from .stations import CANONICAL_STATIONS

        start, end = _utc_month_bounds(month)
        as_of = _as_as_of_cutoff(cutoff)
        expected_station_ids = tuple(station.station_id for station in CANONICAL_STATIONS)
        if station_ids is None:
            raise ValueError("station_ids must exactly match the ordered 25-station canonical registry")
        normalized_station_ids = tuple(station_ids)
        if normalized_station_ids != expected_station_ids:
            raise ValueError("station_ids must exactly match the ordered 25-station canonical registry")
        if metrics is None or isinstance(metrics, (str, bytes, Mapping)):
            raise ValueError("metrics must be a non-empty unique sequence")
        normalized_metrics = tuple(metrics)
        if not normalized_metrics or len(set(normalized_metrics)) != len(normalized_metrics):
            raise ValueError("metrics must be a non-empty unique sequence")
        if any(not isinstance(metric, str) or not _SAFE_METRIC.fullmatch(metric) for metric in normalized_metrics):
            raise ValueError("metrics must contain safe non-empty metric identifiers")
        query = """
            SELECT current.* FROM canonical_observations AS current
            WHERE current.provenance_kind = 'observed'
              AND current.observed_at >= ? AND current.observed_at < ?
              AND current.available_at IS NOT NULL AND current.available_at <= ?
              AND current.accessed_at IS NOT NULL AND current.accessed_at <= ?
              AND current.revision = (
                    SELECT MAX(visible.revision) FROM canonical_observations AS visible
                    WHERE visible.logical_observation_id = current.logical_observation_id
                      AND visible.available_at IS NOT NULL AND visible.available_at <= ?
                      AND COALESCE(visible.accessed_at, visible.available_at) <= ?
              )
        """
        parameters: list[str] = [
            _as_timestamp(start), _as_timestamp(end), _as_timestamp(as_of), _as_timestamp(as_of),
            _as_timestamp(as_of), _as_timestamp(as_of),
        ]
        query += f" AND current.station_id IN ({','.join('?' for _ in normalized_station_ids)})"
        parameters.extend(normalized_station_ids)
        query += f" AND current.metric IN ({','.join('?' for _ in normalized_metrics)})"
        parameters.extend(normalized_metrics)
        query += " ORDER BY current.metric, current.station_id, current.observed_at, current.logical_observation_id, current.revision"
        return [self._canonical_row_to_dict(row) for row in self._connection.execute(query, parameters).fetchall()]

    @_synchronized
    def get_latest_canonical_observation(self, station_id: str, metric: str) -> dict[str, Any] | None:
        row = self._connection.execute(
            """SELECT * FROM canonical_observations WHERE station_id = ? AND metric = ?
               ORDER BY observed_at DESC, revision DESC LIMIT 1""",
            (station_id, metric),
        ).fetchone()
        return self._canonical_row_to_dict(row) if row else None

    @staticmethod
    def _canonical_row_to_dict(row: sqlite3.Row) -> dict[str, Any]:
        evidence = json.loads(row["source_evidence_json"])
        return {
            "revision": int(row["revision"]), "identity": row["identity"],
            "logical_observation_id": row["logical_observation_id"],
            "content_hash": row["content_hash"], "supersedes_revision": row["supersedes_revision"],
            "station_id": row["station_id"], "metric": row["metric"],
            "observed_at": _from_timestamp(row["observed_at"]).isoformat(), "unit": row["unit"],
            "value": float(row["value"]), "provenance_kind": row["provenance_kind"], "provider": row["provider"],
            "dataset_id": row["dataset_id"], "accessed_at": _from_timestamp(row["accessed_at"]).isoformat() if row["accessed_at"] else None,
            "available_at": _from_timestamp(row["available_at"]).isoformat() if row["available_at"] else None,
            "request_url": row["request_url"], "asset_id": evidence.get("asset_id"), "asset_href": evidence.get("asset_href"),
            "requested_latitude": row["requested_latitude"], "requested_longitude": row["requested_longitude"],
            "returned_latitude": row["returned_latitude"], "returned_longitude": row["returned_longitude"],
            "quality_flags": json.loads(row["quality_flags_json"]), "uncertainty": row["uncertainty"],
            "derivation_method": row["derivation_method"], "input_lineage": json.loads(row["input_lineage_json"]),
            "model_version": row["model_version"], "scenario_id": row["scenario_id"],
        }

    @_synchronized
    def start_sync_run(self, station_id: str, started_at: datetime | None = None) -> int:
        cursor = self._connection.execute(
            "INSERT INTO sync_runs(station_id, started_at, status) VALUES (?, ?, ?)",
            (station_id, _as_timestamp(started_at) if started_at else _now_timestamp(), "running"),
        )
        self._connection.commit()
        return int(cursor.lastrowid)

    @_synchronized
    def finish_sync_run(self, run_id: int, status: str, finished_at: datetime | None = None) -> None:
        self._connection.execute(
            "UPDATE sync_runs SET status = ?, finished_at = ? WHERE run_id = ?",
            (status, _as_timestamp(finished_at) if finished_at else _now_timestamp(), run_id),
        )
        self._connection.commit()

    @_synchronized
    def record_sync_error(
        self,
        run_id: int,
        product: str,
        error_type: str,
        message: str,
        occurred_at: datetime | None = None,
    ) -> int:
        cursor = self._connection.execute(
            """
            INSERT INTO sync_errors(run_id, product, error_type, message, occurred_at)
            VALUES (?, ?, ?, ?, ?)
            """,
            (run_id, product, error_type, message, _as_timestamp(occurred_at) if occurred_at else _now_timestamp()),
        )
        self._connection.commit()
        return int(cursor.lastrowid)

    @_synchronized
    def list_stations(self) -> list[dict[str, str | float]]:
        """Return all persisted stations in deterministic, JSON-safe form."""

        rows = self._connection.execute(
            "SELECT station_id, name, latitude, longitude FROM stations ORDER BY station_id"
        ).fetchall()
        return [
            {
                "station_id": row["station_id"],
                "name": row["name"],
                "latitude": float(row["latitude"]),
                "longitude": float(row["longitude"]),
            }
            for row in rows
        ]

    @_synchronized
    def get_latest_sync_run(self, station_id: str | None = None) -> dict[str, int | str | None] | None:
        """Return the latest sync run globally or for one station as JSON-safe data."""

        if station_id is None:
            row = self._connection.execute(
                """
                SELECT run_id, station_id, started_at, finished_at, status
                FROM sync_runs
                ORDER BY started_at DESC, run_id DESC
                LIMIT 1
                """
            ).fetchone()
        else:
            row = self._connection.execute(
                """
                SELECT run_id, station_id, started_at, finished_at, status
                FROM sync_runs
                WHERE station_id = ?
                ORDER BY started_at DESC, run_id DESC
                LIMIT 1
                """,
                (station_id,),
            ).fetchone()
        if row is None:
            return None
        return {
            "run_id": int(row["run_id"]),
            "station_id": row["station_id"],
            "started_at": _from_timestamp(row["started_at"]).isoformat(),
            "finished_at": _from_timestamp(row["finished_at"]).isoformat() if row["finished_at"] else None,
            "status": row["status"],
        }

    @_synchronized
    def get_latest_state(self, station_id: str) -> LatestState | None:
        station_row = self._connection.execute(
            "SELECT station_id, name, latitude, longitude FROM stations WHERE station_id = ?", (station_id,)
        ).fetchone()
        if station_row is None:
            return None
        station = Station(
            station_id=station_row["station_id"],
            name=station_row["name"],
            latitude=station_row["latitude"],
            longitude=station_row["longitude"],
        )
        return LatestState(
            station=station,
            sst=self._latest_observation(station_id, "sst"),
            dhw=self._latest_observation(station_id, "dhw"),
        )

    @_synchronized
    def _latest_observation(self, station_id: str, product: str) -> ProductObservation | None:
        row = self._connection.execute(
            """
            SELECT station_id, product, observed_at, requested_latitude, requested_longitude,
                   returned_latitude, returned_longitude, value, unit, source, dataset_id,
                   request_url, accessed_at
            FROM product_observations
            WHERE station_id = ? AND product = ?
            ORDER BY observed_at DESC, observation_id DESC LIMIT 1
            """,
            (station_id, product),
        ).fetchone()
        if row is None:
            return None
        return ProductObservation(
            station_id=row["station_id"],
            product=row["product"],
            observed_at=_from_timestamp(row["observed_at"]),
            requested_latitude=row["requested_latitude"],
            requested_longitude=row["requested_longitude"],
            returned_latitude=row["returned_latitude"],
            returned_longitude=row["returned_longitude"],
            value=row["value"],
            unit=row["unit"],
            source=row["source"],
            dataset_id=row["dataset_id"],
            request_url=row["request_url"],
            accessed_at=_from_timestamp(row["accessed_at"]),
        )

    @_synchronized
    def get_sync_run(self, run_id: int) -> SyncRun | None:
        row = self._connection.execute(
            "SELECT run_id, station_id, started_at, finished_at, status FROM sync_runs WHERE run_id = ?", (run_id,)
        ).fetchone()
        if row is None:
            return None
        return SyncRun(
            run_id=row["run_id"],
            station_id=row["station_id"],
            started_at=_from_timestamp(row["started_at"]),
            finished_at=_from_timestamp(row["finished_at"]) if row["finished_at"] else None,
            status=row["status"],
        )

    @_synchronized
    def list_sync_errors(self, run_id: int) -> tuple[SyncError, ...]:
        rows = self._connection.execute(
            """
            SELECT error_id, run_id, product, error_type, message, occurred_at
            FROM sync_errors WHERE run_id = ? ORDER BY error_id
            """,
            (run_id,),
        ).fetchall()
        return tuple(
            SyncError(
                error_id=row["error_id"],
                run_id=row["run_id"],
                product=row["product"],
                error_type=row["error_type"],
                message=row["message"],
                occurred_at=_from_timestamp(row["occurred_at"]),
            )
            for row in rows
        )

    @_synchronized
    def try_acquire_sync_lease(
        self,
        lease_name: str = SYNC_LEASE_NAME,
        owner_token: str | None = None,
        *,
        now: datetime | None = None,
        lease_seconds: float = 300.0,
    ) -> bool:
        if not math.isfinite(lease_seconds) or lease_seconds <= 0:
            raise ValueError("lease_seconds must be positive and finite")
        owner = owner_token or uuid.uuid4().hex
        current = _as_utc_datetime(now or datetime.now(timezone.utc))
        expires = current.timestamp() + lease_seconds
        acquired_at = _as_timestamp(current)
        expires_at = datetime.fromtimestamp(expires, timezone.utc)
        self._connection.execute("BEGIN IMMEDIATE")
        try:
            row = self._connection.execute(
                "SELECT owner_token, expires_at FROM sync_leases WHERE lease_name = ?", (lease_name,)
            ).fetchone()
            if row is not None and _from_timestamp(row["expires_at"]) > current:
                self._connection.rollback()
                return False
            self._connection.execute(
                "INSERT INTO sync_leases(lease_name, owner_token, acquired_at, expires_at) VALUES (?, ?, ?, ?) "
                "ON CONFLICT(lease_name) DO UPDATE SET owner_token=excluded.owner_token, acquired_at=excluded.acquired_at, expires_at=excluded.expires_at",
                (lease_name, owner, acquired_at, _as_timestamp(expires_at)),
            )
            self._connection.commit()
            return True
        except Exception:
            self._connection.rollback()
            raise

    @_synchronized
    def release_sync_lease(self, lease_name: str = SYNC_LEASE_NAME, owner_token: str = "") -> bool:
        cursor = self._connection.execute(
            "DELETE FROM sync_leases WHERE lease_name = ? AND owner_token = ?", (lease_name, owner_token)
        )
        self._connection.commit()
        return cursor.rowcount == 1

    @_synchronized
    def renew_sync_lease(
        self, lease_name: str = SYNC_LEASE_NAME, owner_token: str = "", *, now: datetime | None = None, lease_seconds: float = 300.0
    ) -> bool:
        if not math.isfinite(lease_seconds) or lease_seconds <= 0:
            raise ValueError("lease_seconds must be positive and finite")
        current = _as_utc_datetime(now or datetime.now(timezone.utc))
        expires_at = _as_timestamp(datetime.fromtimestamp(current.timestamp() + lease_seconds, timezone.utc))
        cursor = self._connection.execute(
            "UPDATE sync_leases SET acquired_at = ?, expires_at = ? WHERE lease_name = ? AND owner_token = ? AND expires_at > ?",
            (_as_timestamp(current), expires_at, lease_name, owner_token, _as_timestamp(current)),
        )
        self._connection.commit()
        return cursor.rowcount == 1


class SyncLeaseGuard:
    """Daemon heartbeat that keeps an owned lease alive until stopped."""

    def __init__(
        self,
        repository: SQLiteOperationalRepository,
        lease_name: str,
        owner_token: str,
        *,
        lease_seconds: float = 300.0,
        heartbeat_interval: float | None = None,
        sleeper: Callable[[float], None] = time.sleep,
        shutdown_timeout: float = 10.0,
    ) -> None:
        self._repository = repository
        self._lease_name = lease_name
        self._owner_token = owner_token
        self._lease_seconds = lease_seconds
        self._interval = heartbeat_interval if heartbeat_interval is not None else lease_seconds / 3
        if not math.isfinite(self._lease_seconds) or self._lease_seconds <= 0:
            raise ValueError("lease_seconds must be positive and finite")
        if not math.isfinite(self._interval) or self._interval <= 0 or self._interval >= self._lease_seconds:
            raise ValueError("heartbeat_interval must be positive, finite, and less than lease_seconds")
        if not math.isfinite(shutdown_timeout) or shutdown_timeout <= 0:
            raise ValueError("shutdown_timeout must be positive and finite")
        self._sleeper = sleeper
        self._shutdown_timeout = shutdown_timeout
        self._stop = threading.Event()
        self._lost = threading.Event()
        self._gate = threading.RLock()
        self._thread: threading.Thread | None = None

    @property
    def lost(self) -> bool:
        return self._lost.is_set()

    @property
    def is_alive(self) -> bool:
        return self._thread is not None and self._thread.is_alive()

    def start(self) -> "SyncLeaseGuard":
        self._thread = threading.Thread(target=self._run, name="sync-lease-heartbeat", daemon=True)
        self._thread.start()
        return self

    def _run(self) -> None:
        while not self._stop.is_set():
            if self._sleeper is time.sleep:
                self._stop.wait(self._interval)
            else:
                self._sleeper(self._interval)
            if self._stop.is_set():
                break
            with self._gate:
                if self._stop.is_set():
                    break
                try:
                    renewed = self._repository.renew_sync_lease(
                        self._lease_name,
                        self._owner_token,
                        lease_seconds=self._lease_seconds,
                    )
                except Exception:
                    self._lost.set()
                    break
                if not renewed:
                    self._lost.set()
                    break

    def run_if_owned(self, effect: Callable[[], object]) -> object:
        """Renew ownership and run one bounded effect under the heartbeat gate."""

        from .sync import LeaseLostError

        if not callable(effect):
            raise TypeError("effect must be callable")
        with self._gate:
            if self._lost.is_set():
                raise LeaseLostError("Synchronization lease was lost")
            try:
                renewed = self._repository.renew_sync_lease(
                    self._lease_name,
                    self._owner_token,
                    lease_seconds=self._lease_seconds,
                )
            except Exception as error:
                self._lost.set()
                raise LeaseLostError("Synchronization lease renewal failed") from error
            if not renewed:
                self._lost.set()
                raise LeaseLostError("Synchronization lease was lost")
            return effect()

    def stop(self) -> None:
        self._stop.set()
        if self._thread is not None:
            self._thread.join(timeout=self._shutdown_timeout)
            if self._thread.is_alive():
                raise RuntimeError("Synchronization lease heartbeat did not stop")
