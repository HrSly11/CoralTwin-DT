"""Fail-closed reader for the canonical station and data-lineage manifest."""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path, PurePosixPath
from typing import Any, Mapping
from urllib.parse import urlsplit

from .stations import CANONICAL_STATIONS


class ManifestValidationError(ValueError):
    """Raised when the checked-in data manifest is malformed or unsafe."""


DEFAULT_MANIFEST_PATH = (
    Path(__file__).resolve().parents[1] / "03_Data" / "metadata" / "data_source_manifest.json"
)
_LIFECYCLES = frozenset({"active", "archived_legacy"})
_PROVENANCE_KINDS = frozenset({"observed", "derived", "simulated"})


@dataclass(frozen=True)
class CanonicalRegistry:
    version: str
    station_ids: tuple[str, ...]

    @property
    def station_count(self) -> int:
        return len(self.station_ids)


@dataclass(frozen=True)
class LegacyStationMigration:
    legacy_registry_position: int
    legacy_station_name: str
    disposition: str
    canonical_station_id: str | None


@dataclass(frozen=True)
class DataArtifact:
    artifact_id: str
    path: str
    lifecycle: str
    provenance_kind: str
    station_identifiers: tuple[str, ...]
    generated_by: str | None
    external_validation: str


@dataclass(frozen=True)
class DataManifest:
    registry: CanonicalRegistry
    artifacts: tuple[DataArtifact, ...]
    legacy_station_migration: tuple[LegacyStationMigration, ...]


def _fail(message: str) -> None:
    raise ManifestValidationError(message)


def _mapping(value: Any, description: str) -> Mapping[str, Any]:
    if not isinstance(value, Mapping):
        _fail(f"{description} must be an object")
    return value


def _nonempty_string(value: Any, description: str) -> str:
    if not isinstance(value, str) or not value.strip():
        _fail(f"{description} must be a non-empty string")
    return value.strip()


def _relative_path(value: Any, description: str) -> str:
    path = _nonempty_string(value, description)
    parts = path.split("/")
    if (
        "\\" in path
        or path.startswith("/")
        or (len(path) >= 2 and path[0].isalpha() and path[1] == ":")
        or any(part in {"", ".", ".."} for part in parts)
        or str(PurePosixPath(path)) != path
    ):
        _fail(f"{description} must be a safe project-relative POSIX path")
    return path


def _https_url(value: Any, description: str) -> str:
    url = _nonempty_string(value, description)
    parsed = urlsplit(url)
    if parsed.scheme != "https" or not parsed.netloc:
        _fail(f"{description} must use an https URL")
    return url


def _accessed_at(value: Any) -> str:
    timestamp = _nonempty_string(value, "evidence.accessed_at")
    try:
        parsed = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
    except ValueError as error:
        raise ManifestValidationError("evidence.accessed_at must be an ISO-8601 timestamp") from error
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        _fail("evidence.accessed_at must be UTC-aware")
    parsed.astimezone(timezone.utc)
    return timestamp


def _asset_uri(value: Any) -> str:
    uri = _nonempty_string(value, "evidence.asset_uri")
    parsed = urlsplit(uri)
    if parsed.scheme:
        return _https_url(uri, "evidence.asset_uri")
    return _relative_path(uri, "evidence.asset_uri")


def _validate_observed_evidence(value: Any) -> None:
    evidence = _mapping(value, "observed evidence")
    allowed = {"provider", "dataset_id", "accessed_at", "request_url", "asset_uri"}
    unknown = set(evidence).difference(allowed)
    if unknown:
        _fail("observed evidence contains unsupported keys")
    _nonempty_string(evidence.get("provider"), "evidence.provider")
    _nonempty_string(evidence.get("dataset_id"), "evidence.dataset_id")
    _accessed_at(evidence.get("accessed_at"))
    request_url = evidence.get("request_url")
    asset_uri = evidence.get("asset_uri")
    if request_url is None and asset_uri is None:
        _fail("observed evidence requires request_url or asset_uri")
    if request_url is not None:
        _https_url(request_url, "evidence.request_url")
    if asset_uri is not None:
        _asset_uri(asset_uri)


def _string_list(value: Any, description: str) -> tuple[str, ...]:
    if not isinstance(value, list) or not all(isinstance(item, str) and item for item in value):
        _fail(f"{description} must be a non-empty string list")
    return tuple(value)


def _validate_registry(document: Mapping[str, Any]) -> CanonicalRegistry:
    registry = _mapping(document.get("canonical_registry"), "canonical_registry")
    version = _nonempty_string(registry.get("version"), "canonical_registry.version")
    station_ids = _string_list(registry.get("station_ids"), "canonical_registry.station_ids")
    expected = tuple(station.station_id for station in CANONICAL_STATIONS)
    if station_ids != expected:
        _fail("canonical_registry.station_ids must exactly match CANONICAL_STATIONS in order")
    if registry.get("station_count") != len(expected):
        _fail("canonical_registry.station_count must equal the canonical station count")
    return CanonicalRegistry(version=version, station_ids=station_ids)


def _validate_migration(document: Mapping[str, Any]) -> tuple[LegacyStationMigration, ...]:
    entries = document.get("legacy_station_migration")
    if not isinstance(entries, list) or len(entries) != 30:
        _fail("legacy_station_migration must contain exactly 30 entries")

    stations_by_id = {station.station_id: station for station in CANONICAL_STATIONS}
    positions: set[int] = set()
    destination_ids: set[str] = set()
    archive_only = 0
    migration: list[LegacyStationMigration] = []
    for index, value in enumerate(entries, start=1):
        item = _mapping(value, f"legacy_station_migration[{index}]")
        position = item.get("legacy_registry_position")
        if not isinstance(position, int) or position < 1 or position > 30 or position in positions:
            _fail("legacy_station_migration positions must be unique integers from 1 through 30")
        positions.add(position)
        legacy_name = _nonempty_string(item.get("legacy_station_name"), "legacy_station_name")
        disposition = item.get("disposition")
        destination = item.get("canonical_station_id")
        if disposition == "archive_only":
            if destination is not None:
                _fail("archive_only legacy stations cannot have a canonical_station_id")
            archive_only += 1
        elif disposition == "canonical_alias":
            if not isinstance(destination, str) or destination not in stations_by_id:
                _fail("canonical_alias stations must target a canonical station ID")
            if destination in destination_ids:
                _fail("canonical_alias destinations must be unique")
            destination_ids.add(destination)
        else:
            _fail("legacy station disposition must be canonical_alias or archive_only")
        migration.append(LegacyStationMigration(position, legacy_name, disposition, destination))

    expected_ids = set(stations_by_id)
    if positions != set(range(1, 31)) or destination_ids != expected_ids or archive_only != 5:
        _fail("legacy station migration must map 25 canonical stations and archive exactly five entries")
    return tuple(migration)


def _validate_artifacts(document: Mapping[str, Any], registry: CanonicalRegistry) -> tuple[DataArtifact, ...]:
    entries = document.get("artifacts")
    if not isinstance(entries, list) or not entries:
        _fail("artifacts must be a non-empty list")
    artifact_ids: set[str] = set()
    paths: set[str] = set()
    artifacts: list[DataArtifact] = []
    for index, value in enumerate(entries, start=1):
        item = _mapping(value, f"artifacts[{index}]")
        artifact_id = _nonempty_string(item.get("artifact_id"), "artifact_id")
        path = _relative_path(item.get("path"), "artifact path")
        lifecycle = item.get("lifecycle")
        provenance_kind = item.get("provenance_kind")
        identifiers = _string_list(item.get("station_identifiers"), "station_identifiers")
        generated_by = item.get("generated_by")
        if generated_by is not None:
            generated_by = _relative_path(generated_by, "generated_by")
        evidence = item.get("evidence")
        if lifecycle not in _LIFECYCLES:
            _fail("artifact lifecycle must be active or archived_legacy")
        if provenance_kind not in _PROVENANCE_KINDS:
            _fail("artifact provenance_kind must be observed, derived, or simulated")
        if artifact_id in artifact_ids or path in paths:
            _fail("artifact IDs and paths must be unique")
        if provenance_kind == "observed":
            _validate_observed_evidence(evidence)
        if generated_by is not None and provenance_kind == "observed":
            _fail("generated artifacts cannot be declared observed")
        if item.get("external_validation") != "not_claimed":
            _fail("artifacts must declare external_validation as not_claimed")
        if lifecycle == "active" and identifiers != registry.station_ids:
            _fail("active artifacts must use the exact canonical station registry")
        artifact_ids.add(artifact_id)
        paths.add(path)
        artifacts.append(DataArtifact(artifact_id, path, lifecycle, provenance_kind, identifiers, generated_by, "not_claimed"))
    return tuple(artifacts)


def load_data_manifest(path: str | Path | None = None) -> DataManifest:
    """Load the checked-in manifest and reject incompatible provenance declarations."""

    manifest_path = Path(path) if path is not None else DEFAULT_MANIFEST_PATH
    try:
        with manifest_path.open(encoding="utf-8") as handle:
            document = json.load(handle)
    except FileNotFoundError as exc:
        raise ManifestValidationError(f"data manifest is missing at {manifest_path}") from exc
    except (OSError, json.JSONDecodeError) as exc:
        raise ManifestValidationError(f"data manifest cannot be read at {manifest_path}: {exc}") from exc
    document = _mapping(document, "data manifest")
    if document.get("schema_version") != 1:
        _fail("data manifest has an unsupported schema_version")
    registry = _validate_registry(document)
    migration = _validate_migration(document)
    artifacts = _validate_artifacts(document, registry)
    return DataManifest(registry=registry, artifacts=artifacts, legacy_station_migration=migration)


__all__ = [
    "CanonicalRegistry",
    "DEFAULT_MANIFEST_PATH",
    "DataArtifact",
    "DataManifest",
    "LegacyStationMigration",
    "ManifestValidationError",
    "load_data_manifest",
]
