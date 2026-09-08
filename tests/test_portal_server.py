"""Contract tests for production API/portal wiring and server startup."""

from __future__ import annotations

import importlib
import os
import sqlite3
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from fastapi.testclient import TestClient


class ProductionWiringTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tempdir = tempfile.TemporaryDirectory()
        self.database_path = Path(self.tempdir.name) / "nested" / "runtime.sqlite"

    def tearDown(self) -> None:
        self.tempdir.cleanup()

    def test_factory_initializes_database_mounts_portal_and_keeps_api_precedence(self) -> None:
        from operational.runtime import create_production_app

        app = create_production_app(self.database_path)
        repository = app.state.repository

        self.assertTrue(self.database_path.exists())
        with TestClient(app) as client:
            portal = client.get("/")
            health = client.get("/api/health")
            stations = client.get("/api/stations")

        self.assertEqual(200, portal.status_code)
        self.assertIn("CoralTwin-DT", portal.text)
        self.assertEqual(200, health.status_code)
        self.assertEqual({"status": "ok"}, health.json())
        self.assertEqual(25, stations.json()["count"])
        self.assertEqual("available", stations.json()["stations"][0]["decision"]["status"])
        with self.assertRaises(sqlite3.ProgrammingError):
            repository.get_latest_sync_run()

    def test_importing_portal_server_does_not_construct_runtime_or_start_work(self) -> None:
        sys.modules.pop("portal.server", None)

        with patch("operational.runtime.create_production_app") as factory:
            importlib.import_module("portal.server")

        factory.assert_not_called()

    def test_run_server_uses_environment_host_port_and_uvicorn_factory_mode(self) -> None:
        server = importlib.import_module("portal.server")

        with patch.dict(os.environ, {"HOST": "0.0.0.0", "PORT": "8123"}, clear=False), patch(
            "portal.server.uvicorn.run"
        ) as run:
            server.run_server()

        run.assert_called_once_with("portal.server:create_app", host="0.0.0.0", port=8123, factory=True)

    def test_production_factory_reads_sync_token_without_exposing_it(self) -> None:
        from operational.runtime import create_production_app

        with patch.dict(os.environ, {"CORALTWIN_SYNC_TOKEN": "production-secret"}, clear=False):
            app = create_production_app(self.database_path)

        self.assertTrue(app.state.sync_token_configured)
        self.assertNotIn("production-secret", repr(app.state.__dict__))
        app.state.repository.close()


if __name__ == "__main__":
    unittest.main()
