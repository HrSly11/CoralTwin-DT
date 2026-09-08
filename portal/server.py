"""Uvicorn entrypoint for the operational API and static portal."""

from __future__ import annotations

import os
import sys
from pathlib import Path

import uvicorn

if __package__ in (None, ""):
    project_root = str(Path(__file__).resolve().parents[1])
    if project_root not in sys.path:
        sys.path.insert(0, project_root)

from operational.runtime import create_production_app


def create_app():
    """Uvicorn factory target; construction is deferred until server startup."""

    return create_production_app()


def run_server() -> None:
    host = os.environ.get("HOST", "127.0.0.1")
    port = int(os.environ.get("PORT", "8000"))
    uvicorn.run("portal.server:create_app", host=host, port=port, factory=True)


if __name__ == "__main__":
    run_server()
