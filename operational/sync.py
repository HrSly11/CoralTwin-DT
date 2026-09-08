"""Bounded synchronization service for canonical NOAA station telemetry."""

from __future__ import annotations

import time
import argparse
import json
import math
import sys
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Iterable, Mapping

from .noaa_adapter import NOAAErddapAdapter, ProductObservation
from .config import DEFAULT_DATABASE_PATH, resolve_database_path
from .repository import SYNC_LEASE_NAME, SQLiteOperationalRepository, Station, SyncLeaseGuard
from .stations import CANONICAL_STATIONS, StationNotFoundError


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


@dataclass(frozen=True)
class ProductSyncResult:
    product: str
    status: str
    error_type: str | None = None
    error_message: str | None = None

    def to_dict(self) -> dict[str, str | None]:
        return {
            "product": self.product,
            "status": self.status,
            "error_type": self.error_type,
            "error_message": self.error_message,
        }


class LeaseLostError(RuntimeError):
    """Raised when synchronization no longer owns its cross-process lease."""


def require_sync_lease_repository(repository: Any) -> Any:
    """Validate the cross-process lease contract before synchronization starts."""

    required = (
        "try_acquire_sync_lease",
        "renew_sync_lease",
        "release_sync_lease",
        "close",
    )
    missing = [name for name in required if not callable(getattr(repository, name, None))]
    if missing:
        raise TypeError(
            "Synchronization repository must implement callable lease methods: "
            + ", ".join(missing)
        )
    return repository


def require_sync_service(service: Any) -> Any:
    """Validate the service lease-control contract before dispatching work."""

    required = ("set_lease_guard", "sync_station", "sync_all")
    missing = [name for name in required if not callable(getattr(service, name, None))]
    if missing:
        raise TypeError(
            "Synchronization service must implement callable methods: "
            + ", ".join(missing)
        )
    return service


@dataclass(frozen=True)
class StationSyncResult:
    station_id: str
    status: str
    run_id: int | None
    started_at: datetime
    finished_at: datetime
    products_succeeded: int
    products_failed: int
    product_results: Mapping[str, ProductSyncResult]

    def to_dict(self) -> dict[str, object]:
        return {
            "station_id": self.station_id,
            "status": self.status,
            "run_id": self.run_id,
            "started_at": self.started_at.isoformat(),
            "finished_at": self.finished_at.isoformat(),
            "products_succeeded": self.products_succeeded,
            "products_failed": self.products_failed,
            "product_results": {product: result.to_dict() for product, result in self.product_results.items()},
        }


@dataclass(frozen=True)
class SyncAllResult:
    status: str
    stations_total: int
    stations_succeeded: int
    stations_partial: int
    stations_failed: int
    products_succeeded: int
    products_failed: int
    stations: tuple[StationSyncResult, ...]

    def to_dict(self) -> dict[str, object]:
        return {
            "status": self.status,
            "stations_total": self.stations_total,
            "stations_succeeded": self.stations_succeeded,
            "stations_partial": self.stations_partial,
            "stations_failed": self.stations_failed,
            "products_succeeded": self.products_succeeded,
            "products_failed": self.products_failed,
            "stations": [station.to_dict() for station in self.stations],
        }


class SyncService:
    """Synchronize SST and DHW independently while preserving good state."""

    def __init__(
        self,
        stations: Iterable[Station],
        adapter: NOAAErddapAdapter,
        repository: SQLiteOperationalRepository,
        sleeper: Callable[[float], None] | None = None,
        request_delay: float = 0.0,
        clock: Callable[[], datetime] | None = None,
    ) -> None:
        if request_delay < 0:
            raise ValueError("request_delay must be non-negative")
        self._stations = tuple(stations)
        self._stations_by_id = {station.station_id: station for station in self._stations}
        self._adapter = adapter
        self._repository = repository
        self._sleeper = sleeper or time.sleep
        self._request_delay = request_delay
        self._clock = clock or _utc_now
        self._lease_guard: SyncLeaseGuard | None = None

    def set_lease_guard(self, guard: SyncLeaseGuard) -> None:
        if not callable(getattr(guard, "run_if_owned", None)):
            raise TypeError("Synchronization lease guard must implement callable run_if_owned")
        self._lease_guard = guard

    def _run_if_owned(self, effect: Callable[[], Any]) -> Any:
        if self._lease_guard is None:
            return effect()
        return self._lease_guard.run_if_owned(effect)

    def _station_for(self, station_id: str) -> Station:
        try:
            return self._stations_by_id[station_id]
        except (KeyError, TypeError) as error:
            raise StationNotFoundError(f"Unknown synchronization station: {station_id!r}") from error

    def _finish_result(
        self,
        station: Station,
        run_id: int,
        started_at: datetime,
        product_results: Mapping[str, ProductSyncResult],
    ) -> StationSyncResult:
        succeeded = sum(item.status == "success" for item in product_results.values())
        failed = len(product_results) - succeeded
        status = "success" if failed == 0 else ("failed" if succeeded == 0 else "partial")
        self._run_if_owned(lambda: self._repository.finish_sync_run(run_id, status))
        run = self._run_if_owned(lambda: self._repository.get_sync_run(run_id))
        finished_at = run.finished_at if run and run.finished_at else started_at
        return StationSyncResult(
            station_id=station.station_id,
            status=status,
            run_id=run_id,
            started_at=started_at,
            finished_at=finished_at,
            products_succeeded=succeeded,
            products_failed=failed,
            product_results=dict(product_results),
        )

    def sync_station(self, station_id: str) -> StationSyncResult:
        """Synchronize one known station; unknown IDs fail before any DB write."""

        station = self._station_for(station_id)
        started_at = self._clock()
        self._run_if_owned(
            lambda: self._repository.upsert_station(
                station.station_id,
                station.name,
                station.latitude,
                station.longitude,
            )
        )
        run_id = self._run_if_owned(
            lambda: self._repository.start_sync_run(station.station_id, started_at=started_at)
        )
        product_results: dict[str, ProductSyncResult] = {}

        for index, product in enumerate(("sst", "dhw")):
            try:
                observation = self._run_if_owned(
                    lambda: self._adapter.fetch(
                        station.station_id,
                        product,
                        station.latitude,
                        station.longitude,
                    )
                )
                if not isinstance(observation, ProductObservation):
                    raise TypeError("adapter returned a non-ProductObservation value")
                self._run_if_owned(lambda: self._repository.save_observation(observation))
                product_results[product] = ProductSyncResult(product, "success")
            except LeaseLostError:
                raise
            except Exception as error:
                self._run_if_owned(
                    lambda: self._repository.record_sync_error(
                        run_id,
                        product,
                        type(error).__name__,
                        str(error),
                    )
                )
                product_results[product] = ProductSyncResult(
                    product,
                    "failed",
                    type(error).__name__,
                    str(error),
                )
            if index == 0:
                self._sleeper(self._request_delay)

        return self._finish_result(station, run_id, started_at, product_results)

    def sync_all(self) -> SyncAllResult:
        """Attempt every configured station and aggregate JSON-safe outcomes."""

        results: list[StationSyncResult] = []
        for station in self._stations:
            try:
                results.append(self.sync_station(station.station_id))
            except LeaseLostError:
                raise
            except Exception as error:
                # A station-level failure must not prevent later stations from syncing.
                now = self._clock()
                failed_products = {
                    product: ProductSyncResult(product, "failed", type(error).__name__, str(error))
                    for product in ("sst", "dhw")
                }
                results.append(
                    StationSyncResult(
                        station_id=station.station_id,
                        status="failed",
                        run_id=None,
                        started_at=now,
                        finished_at=now,
                        products_succeeded=0,
                        products_failed=2,
                        product_results=failed_products,
                    )
                )

        stations_succeeded = sum(item.status == "success" for item in results)
        stations_partial = sum(item.status == "partial" for item in results)
        stations_failed = sum(item.status == "failed" for item in results)
        products_succeeded = sum(item.products_succeeded for item in results)
        products_failed = sum(item.products_failed for item in results)
        if stations_failed and not stations_succeeded and not stations_partial:
            status = "failed"
        elif stations_failed or stations_partial:
            status = "partial"
        else:
            status = "success"
        return SyncAllResult(
            status=status,
            stations_total=len(results),
            stations_succeeded=stations_succeeded,
            stations_partial=stations_partial,
            stations_failed=stations_failed,
            products_succeeded=products_succeeded,
            products_failed=products_failed,
            stations=tuple(results),
        )


SyncResult = StationSyncResult
SyncAggregateResult = SyncAllResult


class _CLIArgumentParser(argparse.ArgumentParser):
    """Argument parser that lets main emit one JSON error document."""

    def error(self, message: str) -> None:
        raise ValueError(message)


def _default_database_path() -> Path:
    return DEFAULT_DATABASE_PATH


def _result_payload(result: object) -> dict[str, object]:
    if hasattr(result, "to_dict"):
        payload = result.to_dict()
    elif isinstance(result, Mapping):
        payload = dict(result)
    else:
        payload = {"status": getattr(result, "status", "unknown"), "result": str(result)}
    if not isinstance(payload, dict):
        raise TypeError("sync result to_dict() must return an object")
    return payload


def main(
    argv: Iterable[str] | None = None,
    *,
    adapter_factory: Callable[[], NOAAErddapAdapter] | None = None,
    repository_factory: Callable[[str | Path], SQLiteOperationalRepository] | None = None,
    service_factory: Callable[..., SyncService] | None = None,
    environ: Mapping[str, str] | None = None,
    stdout: object | None = None,
) -> int:
    """Run a manual synchronization and print exactly one JSON result."""

    parser = _CLIArgumentParser(prog="python -m operational.sync", add_help=True)
    parser.add_argument("--database", help="SQLite database path")
    parser.add_argument("--station", help="sync one canonical station id")
    parser.add_argument("--request-delay", type=float, default=2.5, help="seconds between SST and DHW requests")
    output = stdout or sys.stdout
    repository: SQLiteOperationalRepository | None = None
    lease_owner: str | None = None
    lease_acquired = False
    lease_guard = None
    payload: dict[str, object] | None = None
    exit_code = 2
    primary_error: Exception | None = None
    cleanup_errors: list[Exception] = []

    try:
        args = parser.parse_args(list(argv) if argv is not None else None)
        if not math.isfinite(args.request_delay) or args.request_delay < 0:
            raise ValueError("--request-delay must be a finite non-negative number")

        stations_by_id = {station.station_id: station for station in CANONICAL_STATIONS}
        if args.station is not None:
            try:
                selected_station = stations_by_id[args.station]
            except KeyError as error:
                raise StationNotFoundError(f"Unknown canonical station: {args.station!r}") from error
            stations = (selected_station,)
        else:
            stations = CANONICAL_STATIONS

        database_path = resolve_database_path(args.database, environ)
        database_path.parent.mkdir(parents=True, exist_ok=True)

        adapter = (adapter_factory or NOAAErddapAdapter)()
        repository = (repository_factory or SQLiteOperationalRepository)(database_path)
        require_sync_lease_repository(repository)
        lease_owner = uuid.uuid4().hex
        lease_acquired = repository.try_acquire_sync_lease(SYNC_LEASE_NAME, lease_owner)
        if not lease_acquired:
            payload = {"status": "busy", "error": "Synchronization is already in progress"}
            exit_code = 3
        else:
            service = require_sync_service((service_factory or SyncService)(
                stations=stations,
                adapter=adapter,
                repository=repository,
                request_delay=args.request_delay,
            ))
            lease_guard = SyncLeaseGuard(repository, SYNC_LEASE_NAME, lease_owner, lease_seconds=300.0).start()
            service.set_lease_guard(lease_guard)
            result = service.sync_station(args.station) if args.station is not None else service.sync_all()
            payload = _result_payload(result)
            exit_code = 0 if payload.get("status") in {"success", "partial"} else 1
    except Exception as error:
        primary_error = error
        payload = {"status": "error", "error": str(error), "error_type": type(error).__name__}
        exit_code = 2
    finally:
        if repository is not None:
            if lease_guard is not None:
                try:
                    lease_guard.stop()
                except Exception as error:
                    cleanup_errors.append(error)
            if lease_acquired and lease_owner is not None:
                try:
                    repository.release_sync_lease(SYNC_LEASE_NAME, lease_owner)
                except Exception as error:
                    cleanup_errors.append(error)
            heartbeat_alive = lease_guard is not None and bool(getattr(lease_guard, "is_alive", True))
            if not heartbeat_alive:
                try:
                    repository.close()
                except Exception as error:
                    cleanup_errors.append(error)

    if primary_error is None and lease_guard is not None and lease_guard.lost:
        error = LeaseLostError("Synchronization lease was lost")
        payload = {"status": "error", "error": str(error), "error_type": type(error).__name__}
        exit_code = 2
    elif primary_error is None and cleanup_errors:
        payload = {
            "status": "error",
            "error": "; ".join(str(error) for error in cleanup_errors),
            "error_type": "CleanupError",
        }
        exit_code = 2

    if payload is None:
        payload = {"status": "error", "error": "Synchronization produced no result", "error_type": "RuntimeError"}
        exit_code = 2
    print(json.dumps(payload, sort_keys=True, ensure_ascii=False), file=output)
    return exit_code


__all__ = [
    "LeaseLostError",
    "ProductSyncResult",
    "StationSyncResult",
    "SyncAggregateResult",
    "SyncAllResult",
    "SyncResult",
    "SyncService",
    "require_sync_lease_repository",
    "require_sync_service",
    "main",
]


if __name__ == "__main__":
    raise SystemExit(main())
