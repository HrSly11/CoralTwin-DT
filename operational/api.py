"""Dependency-injected HTTP boundary for the operational digital twin."""

from __future__ import annotations

from dataclasses import asdict, is_dataclass
from datetime import datetime, timezone
import hmac
import math
import threading
import uuid
from typing import Any, Callable, Iterable, Mapping

from fastapi import Body, FastAPI, Header, HTTPException

from .repository import SYNC_LEASE_NAME, LatestState, SQLiteOperationalRepository, Station, SyncLeaseGuard
from .sync import LeaseLostError, require_sync_lease_repository, require_sync_service
from .stations import CANONICAL_STATIONS, StationNotFoundError


def _json_safe(value: Any) -> Any:
    """Convert operational dataclasses and timestamps into JSON primitives."""

    if isinstance(value, datetime):
        return value.isoformat()
    to_dict = getattr(value, "to_dict", None)
    if callable(to_dict):
        return _json_safe(to_dict())
    if is_dataclass(value):
        return _json_safe(asdict(value))
    if isinstance(value, Mapping):
        return {str(key): _json_safe(item) for key, item in value.items()}
    if isinstance(value, (tuple, list)):
        return [_json_safe(item) for item in value]
    if isinstance(value, (str, int, float, bool)) or value is None:
        return value
    return str(value)


def _station_payload(station: Station) -> dict[str, Any]:
    return {
        "station_id": station.station_id,
        "name": station.name,
        "latitude": float(station.latitude),
        "longitude": float(station.longitude),
    }


def _utc_now(clock: Callable[[], datetime] | None) -> str:
    value = clock() if clock is not None else datetime.now(timezone.utc)
    if value.tzinfo is None:
        value = value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc).isoformat()


def _product_summary(observation: Any) -> dict[str, Any] | None:
    if observation is None:
        return None
    return {
        "product": observation.product,
        "value": float(observation.value),
        "observed_at": observation.observed_at.isoformat(),
        "unit": observation.unit,
        "source": observation.source,
        "dataset_id": observation.dataset_id,
        "requested_latitude": float(observation.requested_latitude),
        "requested_longitude": float(observation.requested_longitude),
        "returned_latitude": float(observation.returned_latitude),
        "returned_longitude": float(observation.returned_longitude),
        "request_url": observation.request_url,
        "accessed_at": observation.accessed_at.isoformat(),
    }


def _baseline_payload(station_id: str, loader: Callable[[str], Any] | None) -> tuple[dict[str, Any], Any]:
    """Load and expose processed baseline data without conflating it with live state."""
    if loader is None:
        return {"status": "unavailable", "reason": "Baseline loader is not configured"}, None
    try:
        baseline = loader(station_id)
        feature_names = tuple(getattr(baseline, "feature_names"))
        values = tuple(getattr(baseline, "values"))
        if len(feature_names) != len(values):
            raise ValueError("Baseline feature names and values have different lengths")
        features = {}
        for name, value in zip(feature_names, values):
            numeric = float(value)
            if not math.isfinite(numeric):
                raise ValueError(f"Baseline feature {name!r} is not finite")
            features[str(name)] = numeric
        return {
            "status": "available",
            "source": "processed_harmonized_csv",
            "source_date": getattr(baseline, "source_date", None),
            "features": features,
        }, baseline
    except Exception as error:
        return {"status": "unavailable", "reason": str(error)}, None


def _decision_payload(station_id: str, loader: Callable[[str], Any] | None) -> dict[str, Any]:
    if loader is None:
        return {"status": "unavailable", "reason": "Decision loader is not configured"}
    try:
        value = loader(station_id)
        payload = value.to_dict() if hasattr(value, "to_dict") else _json_safe(value)
        return {"status": "available", **payload}
    except Exception as error:
        return {"status": "unavailable", "reason": str(error)}


def create_app(
    repository: SQLiteOperationalRepository,
    sync_service: Any | None = None,
    inference_engine: Any | None = None,
    *,
    stations: Iterable[Station] = CANONICAL_STATIONS,
    baseline_loader: Callable[[str], Any] | None = None,
    decision_loader: Callable[[str], Any] | None = None,
    sync_lease_seconds: float = 300.0,
    sync_heartbeat_interval: float | None = None,
    sync_max_effect_seconds: float = 46.5,
    clock: Callable[[], datetime] | None = None,
    sync_token: str | None = None,
) -> FastAPI:
    """Build the API with all external dependencies supplied by the caller."""

    app = FastAPI(title="CoralTwin-DT Operational API")
    require_sync_lease_repository(repository)
    if sync_service is not None:
        require_sync_service(sync_service)
    if not math.isfinite(sync_max_effect_seconds) or sync_max_effect_seconds <= 0:
        raise ValueError("sync_max_effect_seconds must be positive and finite")
    if not math.isfinite(sync_lease_seconds) or sync_lease_seconds <= sync_max_effect_seconds:
        raise ValueError("sync_lease_seconds must be finite and longer than sync_max_effect_seconds")
    configured_stations = tuple(stations)
    stations_by_id = {station.station_id: station for station in configured_stations}
    configured_sync_token = sync_token if isinstance(sync_token, str) and sync_token else None
    sync_lock = threading.Lock()
    app.state.sync_token_configured = configured_sync_token is not None
    app.state.sync_lock = sync_lock

    def station_for(station_id: str) -> Station:
        try:
            return stations_by_id[station_id]
        except KeyError as error:
            raise HTTPException(status_code=404, detail=f"Unknown canonical station: {station_id!r}") from error

    def state_payload(station: Station) -> dict[str, Any]:
        state: LatestState | None = repository.get_latest_state(station.station_id)
        latest = state or LatestState(station=station, sst=None, dhw=None)
        baseline_payload, baseline = _baseline_payload(station.station_id, baseline_loader)
        decision = _decision_payload(station.station_id, decision_loader)
        inference: Any = None
        if inference_engine is not None:
            try:
                inference = inference_engine.infer(baseline, state)
            except Exception as error:
                inference = {"status": "unavailable", "reason": str(error)}
        return {
            "station": _station_payload(latest.station),
            "sst": _product_summary(latest.sst),
            "dhw": _product_summary(latest.dhw),
            "baseline": baseline_payload,
            "decision": decision,
            "latest_sync_run": repository.get_latest_sync_run(station.station_id),
            "inference": _json_safe(inference),
            "retrieved_at": _utc_now(clock),
        }

    @app.get("/api/health")
    def health() -> dict[str, str]:
        return {"status": "ok"}

    @app.get("/api/stations")
    def list_stations() -> dict[str, Any]:
        retrieved_at = _utc_now(clock)
        summaries = []
        for station in configured_stations:
            state: LatestState | None = repository.get_latest_state(station.station_id)
            latest = state or LatestState(station=station, sst=None, dhw=None)
            baseline, _ = _baseline_payload(station.station_id, baseline_loader)
            decision = _decision_payload(station.station_id, decision_loader)
            summaries.append(
                {
                    **_station_payload(station),
                    "sst": _product_summary(latest.sst),
                    "dhw": _product_summary(latest.dhw),
                    "baseline": baseline,
                    "decision": decision,
                }
            )
        return {"stations": summaries, "count": len(summaries), "retrieved_at": retrieved_at}

    @app.get("/api/stations/{station_id}/state")
    def station_state(station_id: str) -> dict[str, Any]:
        return state_payload(station_for(station_id))

    @app.post("/api/sync")
    def sync(
        payload: dict[str, Any] | None = Body(default=None),
        supplied_token: str | None = Header(default=None, alias="X-CoralTwin-Sync-Token"),
    ) -> Any:
        if configured_sync_token is None:
            raise HTTPException(status_code=503, detail="HTTP synchronization is not configured")
        if supplied_token is None:
            raise HTTPException(status_code=401, detail="Synchronization token is required")
        if not hmac.compare_digest(supplied_token, configured_sync_token):
            raise HTTPException(status_code=403, detail="Synchronization token is invalid")
        supplied_station_id = payload is not None and "station_id" in payload
        station_id = payload.get("station_id") if supplied_station_id else None
        if supplied_station_id and (not isinstance(station_id, str) or not station_id.strip()):
            raise HTTPException(status_code=422, detail="station_id must be a non-empty string")
        if sync_service is None:
            raise HTTPException(status_code=503, detail="Synchronization service is not configured")
        if not sync_lock.acquire(blocking=False):
            raise HTTPException(status_code=409, detail="Synchronization is already in progress")
        owner_token: str | None = None
        lease_acquired = False
        lease_guard = None
        result = None
        primary_error: Exception | None = None
        cleanup_errors: list[Exception] = []
        try:
            owner_token = uuid.uuid4().hex
            lease_acquired = repository.try_acquire_sync_lease(SYNC_LEASE_NAME, owner_token, lease_seconds=sync_lease_seconds)
            if not lease_acquired:
                raise HTTPException(status_code=409, detail="Synchronization is already in progress")
            lease_guard = SyncLeaseGuard(repository, SYNC_LEASE_NAME, owner_token, lease_seconds=sync_lease_seconds, heartbeat_interval=sync_heartbeat_interval).start()
            sync_service.set_lease_guard(lease_guard)
            result = sync_service.sync_station(station_id) if supplied_station_id else sync_service.sync_all()
        except StationNotFoundError as error:
            primary_error = HTTPException(status_code=404, detail=str(error))
        except LeaseLostError as error:
            primary_error = HTTPException(status_code=409, detail=str(error))
        except Exception as error:
            primary_error = error
        finally:
            if lease_guard is not None:
                try:
                    lease_guard.stop()
                except Exception as error:
                    cleanup_errors.append(error)
            if lease_acquired and owner_token is not None:
                try:
                    repository.release_sync_lease(SYNC_LEASE_NAME, owner_token)
                except Exception as error:
                    cleanup_errors.append(error)
            try:
                sync_lock.release()
            except Exception as error:
                cleanup_errors.append(error)

        if primary_error is not None:
            raise primary_error
        if lease_guard is not None and lease_guard.lost:
            raise HTTPException(status_code=409, detail="Synchronization lease was lost")
        if cleanup_errors:
            raise HTTPException(
                status_code=500,
                detail="Synchronization cleanup failed: "
                + "; ".join(str(error) for error in cleanup_errors),
            )
        return _json_safe(result.to_dict() if hasattr(result, "to_dict") else result)

    @app.get("/api/sync-runs/latest")
    def latest_sync_run() -> Any:
        return _json_safe(repository.get_latest_sync_run())

    return app


__all__ = ["create_app"]
