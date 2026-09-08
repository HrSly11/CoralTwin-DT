"""Shared operational runtime path configuration."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Mapping


DEFAULT_DATABASE_PATH = Path(__file__).resolve().parent / "data" / "coraltwin.db"


def resolve_database_path(
    explicit_path: str | Path | None = None,
    environ: Mapping[str, str] | None = None,
) -> Path:
    """Resolve CLI/API path precedence: explicit value, environment, default."""

    if explicit_path is not None:
        return Path(explicit_path)
    environment = os.environ if environ is None else environ
    configured_path = environment.get("CORALTWIN_DB_PATH")
    return Path(configured_path) if configured_path else DEFAULT_DATABASE_PATH


__all__ = ["DEFAULT_DATABASE_PATH", "resolve_database_path"]
