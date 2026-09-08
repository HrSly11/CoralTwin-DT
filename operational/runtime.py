"""Production dependency wiring for the operational CoralTwin API."""

from __future__ import annotations

import os
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from .api import create_app
from .config import DEFAULT_DATABASE_PATH, resolve_database_path
from .decisions import load_station_decision
from .inference import InferenceEngine
from .noaa_adapter import NOAAErddapAdapter
from .repository import SQLiteOperationalRepository
from .stations import CANONICAL_STATIONS, load_station_baseline
from .sync import SyncService


DEFAULT_REQUEST_DELAY = 1.0
PORTAL_DIRECTORY = Path(__file__).resolve().parents[1] / "portal"


def _database_path(database_path: str | Path | None) -> Path:
    return resolve_database_path(database_path)


def _request_delay() -> float:
    raw_value = os.environ.get("CORALTWIN_REQUEST_DELAY")
    if raw_value is None:
        return DEFAULT_REQUEST_DELAY
    try:
        delay = float(raw_value)
    except ValueError as error:
        raise ValueError("CORALTWIN_REQUEST_DELAY must be numeric") from error
    if delay < 0:
        raise ValueError("CORALTWIN_REQUEST_DELAY must be non-negative")
    return delay


def create_production_app(database_path: str | Path | None = None) -> FastAPI:
    """Build the production API and mount the existing portal after API routes."""

    resolved_database_path = _database_path(database_path)
    resolved_database_path.parent.mkdir(parents=True, exist_ok=True)
    repository = SQLiteOperationalRepository(resolved_database_path)
    adapter = NOAAErddapAdapter()
    sync_service = SyncService(
        stations=CANONICAL_STATIONS,
        adapter=adapter,
        repository=repository,
        request_delay=_request_delay(),
    )
    inference_engine = InferenceEngine()
    app = create_app(
        repository=repository,
        sync_service=sync_service,
        inference_engine=inference_engine,
        stations=CANONICAL_STATIONS,
        baseline_loader=load_station_baseline,
        decision_loader=load_station_decision,
        sync_token=os.environ.get("CORALTWIN_SYNC_TOKEN"),
    )
    app.state.repository = repository
    app.state.adapter = adapter
    app.state.sync_service = sync_service
    app.state.inference_engine = inference_engine

    @asynccontextmanager
    async def lifespan(_: FastAPI):
        try:
            yield
        finally:
            repository.close()

    app.router.lifespan_context = lifespan
    app.mount("/", StaticFiles(directory=str(PORTAL_DIRECTORY), html=True), name="portal")
    return app


__all__ = ["create_production_app"]
