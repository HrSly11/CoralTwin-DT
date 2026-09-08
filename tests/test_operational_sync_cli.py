"""Offline contract tests for ``python -m operational.sync`` entrypoint."""

from __future__ import annotations

import io
import json
import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import patch

from operational import sync
from operational.noaa_adapter import ProductObservation
from operational.runtime import DEFAULT_DATABASE_PATH


class FakeRepository:
    def __init__(self, path: Path, events: list[tuple[str, object]]) -> None:
        self.path = path
        self.events = events
        self.closed = False
        self.lease_available = True
        self.release_error = None
        self.close_error = None

    def try_acquire_sync_lease(self, lease_name, owner_token, **kwargs) -> bool:
        self.events.append(("acquire_lease", lease_name))
        return self.lease_available

    def release_sync_lease(self, lease_name, owner_token) -> bool:
        self.events.append(("release_lease", lease_name))
        if self.release_error is not None:
            raise self.release_error
        return True

    def renew_sync_lease(self, lease_name, owner_token, **kwargs) -> bool:
        self.events.append(("renew_lease", lease_name))
        return True

    def close(self) -> None:
        self.closed = True
        self.events.append(("close", self.path))
        if self.close_error is not None:
            raise self.close_error


class FakeResult:
    def __init__(self, status: str, payload: dict[str, object]) -> None:
        self.status = status
        self.payload = payload

    def to_dict(self) -> dict[str, object]:
        return {"status": self.status, **self.payload}


class SyncCLITests(unittest.TestCase):
    def run_cli(self, argv: list[str], *, env: dict[str, str] | None = None, status: str = "success", lease_available: bool = True, sync_error: Exception | None = None) -> tuple[int, dict[str, object], list[tuple[str, object]], FakeRepository]:
        events: list[tuple[str, object]] = []
        holder: dict[str, FakeRepository] = {}

        def repository_factory(path: Path) -> FakeRepository:
            events.append(("repository", path))
            holder["repository"] = FakeRepository(path, events)
            holder["repository"].lease_available = lease_available
            return holder["repository"]

        def service_factory(*, stations, adapter, repository, request_delay):
            events.append(("service", tuple(item.station_id for item in stations), request_delay))

            class FakeService:
                def set_lease_guard(self, guard):
                    events.append(("guard", guard))

                def sync_station(self, station_id):
                    events.append(("station", station_id))
                    return FakeResult(status, {"station_id": station_id})

                def sync_all(self):
                    events.append(("all", None))
                    if sync_error is not None:
                        raise sync_error
                    return FakeResult(status, {"stations_total": 25})

            return FakeService()

        output = io.StringIO()
        code = sync.main(
            argv,
            adapter_factory=lambda: object(),
            repository_factory=repository_factory,
            service_factory=service_factory,
            environ=env or {},
            stdout=output,
        )
        return code, json.loads(output.getvalue()), events, holder["repository"]

    def test_station_dispatches_to_injected_service_and_cli_path_wins_over_env(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            cli_path = Path(directory) / "cli" / "sync.sqlite3"
            code, payload, events, repository = self.run_cli(
                ["--database", str(cli_path), "--station", "station-01", "--request-delay", "1.5"],
                env={"CORALTWIN_DB_PATH": str(Path(directory) / "env.sqlite3")},
            )

        self.assertEqual(0, code)
        self.assertEqual("success", payload["status"])
        self.assertIn(("station", "station-01"), events)
        self.assertEqual(1.5, next(event for event in events if event[0] == "service")[2])
        self.assertEqual(cli_path, repository.path)
        self.assertTrue(repository.closed)

    def test_missing_service_lease_protocol_fails_before_sync_work(self) -> None:
        events = []

        class MissingGuardService:
            def sync_station(self, station_id):
                events.append(("station", station_id))

            def sync_all(self):
                events.append(("all", None))

        output = io.StringIO()
        holder = {}

        def repository_factory(path):
            holder["repository"] = FakeRepository(path, events)
            return holder["repository"]

        code = sync.main(
            [],
            adapter_factory=lambda: object(),
            repository_factory=repository_factory,
            service_factory=lambda **kwargs: MissingGuardService(),
            environ={},
            stdout=output,
        )

        self.assertEqual(2, code)
        self.assertEqual("TypeError", json.loads(output.getvalue())["error_type"])
        self.assertFalse(any(event[0] in {"all", "station"} for event in events))
        self.assertTrue(holder["repository"].closed)

    def test_missing_repository_renewal_protocol_fails_before_lease_acquisition(self) -> None:
        events = []

        class MissingRenewRepository(FakeRepository):
            renew_sync_lease = None

        output = io.StringIO()
        holder = {}

        def repository_factory(path):
            holder["repository"] = MissingRenewRepository(path, events)
            return holder["repository"]

        code = sync.main(
            [],
            adapter_factory=lambda: object(),
            repository_factory=repository_factory,
            service_factory=lambda **kwargs: self.fail("service must not be constructed"),
            environ={},
            stdout=output,
        )

        self.assertEqual(2, code)
        self.assertEqual("TypeError", json.loads(output.getvalue())["error_type"])
        self.assertFalse(any(event[0] == "acquire_lease" for event in events))
        self.assertTrue(holder["repository"].closed)

    def test_cli_lease_loss_aborts_before_later_fetch_or_persistence(self) -> None:
        events = []
        output = io.StringIO()
        holder = {}

        class Guard:
            lost = False
            is_alive = False

            def start(self):
                events.append(("guard_start", None))
                return self

            def stop(self):
                events.append(("guard_stop", None))

            def run_if_owned(self, effect):
                if self.lost:
                    raise sync.LeaseLostError("Synchronization lease was lost")
                result = effect()
                if self.lost:
                    raise sync.LeaseLostError("Synchronization lease was lost")
                return result

        guard = Guard()

        class Adapter:
            def fetch(self, station_id, product, latitude, longitude):
                events.append(("fetch", (station_id, product)))
                guard.lost = True
                observed_at = datetime(2026, 1, 1, tzinfo=timezone.utc)
                return ProductObservation(
                    station_id=station_id,
                    product=product,
                    observed_at=observed_at,
                    requested_latitude=latitude,
                    requested_longitude=longitude,
                    returned_latitude=latitude,
                    returned_longitude=longitude,
                    value=29.0,
                    unit="degree_C" if product == "sst" else "degree_Celsius_weeks",
                    source="fake",
                    dataset_id="fake-dataset",
                    request_url="https://fake.invalid",
                    accessed_at=observed_at,
                )

        class RecordingRepository(FakeRepository):
            def upsert_station(self, *args):
                events.append(("upsert", args[0]))

            def start_sync_run(self, station_id, **kwargs):
                events.append(("start_run", station_id))
                return 1

            def save_observation(self, item):
                events.append(("save", item.station_id))

            def record_sync_error(self, *args):
                events.append(("record_error", args[1]))

            def finish_sync_run(self, *args):
                events.append(("finish_run", args[0]))

            def get_sync_run(self, run_id):
                raise AssertionError("lost sync must not finish")

        def repository_factory(path):
            holder["repository"] = RecordingRepository(path, events)
            return holder["repository"]

        with patch.object(sync, "SyncLeaseGuard", return_value=guard):
            code = sync.main(
                ["--station", "station-01", "--request-delay", "0"],
                adapter_factory=Adapter,
                repository_factory=repository_factory,
                environ={},
                stdout=output,
            )

        payload = json.loads(output.getvalue())
        self.assertEqual(2, code)
        self.assertEqual("LeaseLostError", payload["error_type"])
        self.assertEqual([("fetch", ("station-01", "sst"))], [event for event in events if event[0] == "fetch"])
        self.assertFalse(any(event[0] in {"save", "record_error", "finish_run"} for event in events))
        self.assertTrue(holder["repository"].closed)

    def test_cli_cleanup_only_failure_returns_non_success_after_attempting_release_and_close(self) -> None:
        events = []
        output = io.StringIO()
        holder = {}

        class StopFailingGuard:
            lost = False
            is_alive = False

            def start(self):
                return self

            def stop(self):
                events.append(("guard_stop", None))
                raise RuntimeError("stop failed")

        def repository_factory(path):
            repository = FakeRepository(path, events)
            repository.release_error = RuntimeError("release failed")
            holder["repository"] = repository
            return repository

        with patch.object(sync, "SyncLeaseGuard", return_value=StopFailingGuard()):
            code = sync.main(
                [],
                adapter_factory=lambda: object(),
                repository_factory=repository_factory,
                service_factory=lambda **kwargs: type(
                    "Service",
                    (),
                    {
                        "set_lease_guard": lambda self, guard: None,
                        "sync_station": lambda self, station_id: FakeResult("success", {}),
                        "sync_all": lambda self: FakeResult("success", {}),
                    },
                )(),
                environ={},
                stdout=output,
            )

        self.assertEqual(2, code)
        self.assertEqual("CleanupError", json.loads(output.getvalue())["error_type"])
        self.assertIn(("guard_stop", None), events)
        self.assertIn(("release_lease", "operational-noaa-sync"), events)
        self.assertTrue(holder["repository"].closed)

    def test_all_dispatch_uses_environment_path_and_prints_one_json_document(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            env_path = Path(directory) / "nested" / "env.sqlite3"
            output_events: list[tuple[str, object]] = []
            code, payload, events, repository = self.run_cli([], env={"CORALTWIN_DB_PATH": str(env_path)})

        self.assertEqual(0, code)
        self.assertEqual("success", payload["status"])
        self.assertIn(("all", None), events)
        self.assertEqual(env_path, repository.path)
        self.assertTrue(repository.closed)

    def test_invalid_station_returns_json_error_without_creating_repository(self) -> None:
        output = io.StringIO()
        code = sync.main(
            ["--station", "station-99"],
            adapter_factory=lambda: self.fail("adapter must not be created"),
            repository_factory=lambda _path: self.fail("repository must not be created"),
            stdout=output,
        )

        payload = json.loads(output.getvalue())
        self.assertNotEqual(0, code)
        self.assertEqual("error", payload["status"])
        self.assertIn("station", payload["error"].lower())

    def test_total_failure_returns_nonzero_json_and_closes_repository(self) -> None:
        code, payload, _events, repository = self.run_cli([], status="failed")

        self.assertNotEqual(0, code)
        self.assertEqual("failed", payload["status"])
        self.assertTrue(repository.closed)

    def test_cli_default_database_matches_production_runtime_default(self) -> None:
        _code, _payload, _events, repository = self.run_cli([])

        self.assertEqual(DEFAULT_DATABASE_PATH, repository.path)

    def test_busy_lease_returns_one_json_result_without_constructing_service(self) -> None:
        code, payload, events, repository = self.run_cli([], lease_available=False)

        self.assertEqual(3, code)
        self.assertEqual("busy", payload["status"])
        self.assertNotIn(("all", None), events)
        self.assertFalse(any(event[0] == "service" for event in events))
        self.assertTrue(repository.closed)

    def test_cli_releases_lease_after_service_error(self) -> None:
        code, payload, events, repository = self.run_cli([], sync_error=RuntimeError("upstream failure"))

        self.assertEqual(2, code)
        self.assertEqual("error", payload["status"])
        self.assertIn(("release_lease", "operational-noaa-sync"), events)
        self.assertTrue(repository.closed)


if __name__ == "__main__":
    unittest.main()
