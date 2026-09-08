"""Contract tests for the canonical station and data-lineage manifest."""

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from operational.data_manifest import DEFAULT_MANIFEST_PATH, ManifestValidationError, load_data_manifest
from operational.stations import CANONICAL_STATIONS


class DataManifestTests(unittest.TestCase):
    def _document(self) -> dict:
        return json.loads(DEFAULT_MANIFEST_PATH.read_text(encoding="utf-8"))

    def _load_document(self, document: dict) -> object:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "manifest.json"
            path.write_text(json.dumps(document), encoding="utf-8")
            return load_data_manifest(path)

    def _observed_artifact(self, document: dict) -> dict:
        artifact = document["artifacts"][0]
        artifact["provenance_kind"] = "observed"
        artifact.pop("generated_by")
        artifact["evidence"] = {
            "provider": "NOAA CRW",
            "dataset_id": "noaacrwsstDaily",
            "accessed_at": "2026-08-30T00:00:00+00:00",
            "request_url": "https://example.test/query",
        }
        return artifact

    def test_default_manifest_declares_exact_canonical_station_order(self) -> None:
        manifest = load_data_manifest()

        self.assertEqual(tuple(station.station_id for station in CANONICAL_STATIONS), manifest.registry.station_ids)
        self.assertEqual(25, manifest.registry.station_count)
        self.assertEqual(30, len(manifest.legacy_station_migration))
        self.assertEqual(5, sum(item.disposition == "archive_only" for item in manifest.legacy_station_migration))

    def test_rejects_unsafe_paths_and_noncanonical_active_artifacts(self) -> None:
        unsafe = self._document()
        unsafe["artifacts"][0]["path"] = "../outside.csv"
        with self.assertRaisesRegex(ManifestValidationError, "safe project-relative"):
            self._load_document(unsafe)

        noncanonical = self._document()
        noncanonical["artifacts"][0]["station_identifiers"] = ["station-01"]
        with self.assertRaisesRegex(ManifestValidationError, "exact canonical"):
            self._load_document(noncanonical)

    def test_rejects_cross_platform_path_escapes_and_non_normalized_paths(self) -> None:
        for unsafe_path in ("C:/outside.csv", "C:\\outside.csv", "//server/share.csv", "\\\\server\\share.csv", "folder\\file.csv", "folder//file.csv", "folder/./file.csv", "folder/../file.csv"):
            with self.subTest(unsafe_path=unsafe_path):
                document = self._document()
                document["artifacts"][0]["path"] = unsafe_path
                with self.assertRaisesRegex(ManifestValidationError, "safe project-relative"):
                    self._load_document(document)

    def test_rejects_unproven_observed_and_generated_observed_artifacts(self) -> None:
        unproven_observed = self._document()
        artifact = unproven_observed["artifacts"][0]
        artifact["provenance_kind"] = "observed"
        artifact.pop("generated_by")
        with self.assertRaisesRegex(ManifestValidationError, "observed evidence"):
            self._load_document(unproven_observed)

        generated_observed = self._document()
        generated_observed["artifacts"][0]["provenance_kind"] = "observed"
        generated_observed["artifacts"][0]["evidence"] = {
            "provider": "NOAA CRW",
            "dataset_id": "noaacrwsstDaily",
            "accessed_at": "2026-08-30T00:00:00+00:00",
            "request_url": "https://example.test/query",
        }
        with self.assertRaisesRegex(ManifestValidationError, "cannot be declared observed"):
            self._load_document(generated_observed)

    def test_observed_evidence_has_a_strict_schema(self) -> None:
        arbitrary = self._document()
        artifact = self._observed_artifact(arbitrary)
        artifact["evidence"] = {"capture": "source-record"}
        with self.assertRaisesRegex(ManifestValidationError, "unsupported keys"):
            self._load_document(arbitrary)

        for invalid_accessed_at in ("2026-08-30T00:00:00", "not-a-timestamp"):
            with self.subTest(accessed_at=invalid_accessed_at):
                document = self._document()
                artifact = self._observed_artifact(document)
                artifact["evidence"]["accessed_at"] = invalid_accessed_at
                with self.assertRaisesRegex(ManifestValidationError, "accessed_at"):
                    self._load_document(document)

        document = self._document()
        artifact = self._observed_artifact(document)
        artifact["evidence"]["request_url"] = "http://example.test/query"
        with self.assertRaisesRegex(ManifestValidationError, "https"):
            self._load_document(document)

    def test_observed_evidence_accepts_https_request_or_safe_asset_uri(self) -> None:
        request_document = self._document()
        self._observed_artifact(request_document)
        self._load_document(request_document)

        asset_document = self._document()
        artifact = self._observed_artifact(asset_document)
        artifact["evidence"].pop("request_url")
        artifact["evidence"]["asset_uri"] = "raw/noaa/sst.json"
        self._load_document(asset_document)

    def test_generators_only_emit_simulated_provenance_labels(self) -> None:
        root = DEFAULT_MANIFEST_PATH.parents[2]
        for relative_path in ("03_Data/generate_datasets.py", "03_Data/build_final_dataset.py"):
            source = (root / relative_path).read_text(encoding="utf-8")
            self.assertNotIn("Real_Observation", source)
            self.assertIn('"Digital_Twin_Simulated"', source)


if __name__ == "__main__":
    unittest.main()
