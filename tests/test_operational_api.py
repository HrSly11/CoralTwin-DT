"""Contract tests for the dependency-injected operational FastAPI surface."""

from __future__ import annotations

import tempfile
import threading
import time
import unittest
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import patch

from fastapi.testclient import TestClient

from operational.api import create_app
from operational.noaa_adapter import ProductObservation
from operational.repository import SYNC_LEASE_NAME, SQLiteOperationalRepository
from operational.stations import CANONICAL_STATIONS
from operational.stations import BASELINE_FEATURES, StationBaseline
from operational.decisions import StationDecisionSnapshot
from operational.stations import StationNotFoundError
from operational.sync import SyncService


class _Result:
    def __init__(self, payload: dict):
        self.payload = payload

    def to_dict(self) -> dict:
        return self.payload


class _FakeSyncService:
    def __init__(self):
        self.station_calls: list[str] = []
        self.all_calls = 0
        self.guard = None

    def set_lease_guard(self, guard) -> None:
        self.guard = guard

    def sync_station(self, station_id: str) -> _Result:
        self.station_calls.append(station_id)
        if station_id == "station-99":
            raise StationNotFoundError(station_id)
        return _Result({"status": "success", "station_id": station_id, "products_succeeded": 2})

    def sync_all(self) -> _Result:
        self.all_calls += 1
        return _Result({"stations_total": 25, "stations_succeeded": 25, "products_succeeded": 50})


class _FakeInferenceEngine:
    def infer(self, baseline, latest_state) -> _Result:
        return _Result(
            {
                "status": "ok",
                "classification": "Low",
                "confidence": 0.9,
                "coral_cover_loss_pct": 4.2,
                "input_provenance": {"SST_degC": {"source": "noaa_crw_erddap"}},
            }
        )


class _CountingBaselineLoader:
    def __init__(self, fail=False):
        self.calls = []
        self.fail = fail

    def __call__(self, station_id):
        self.calls.append(station_id)
        if self.fail:
            raise ValueError("baseline schema unavailable")
        return StationBaseline(BASELINE_FEATURES, tuple(float(index) for index in range(1, 11)), "2026-08-28")


class _CountingDecisionLoader:
    def __init__(self, fail=False):
        self.calls = []
        self.fail = fail

    def __call__(self, station_id):
        self.calls.append(station_id)
        if self.fail:
            raise ValueError("decision snapshot unavailable")
        return StationDecisionSnapshot("Mesoamerican_Fore_01", "Caribbean", "Fore Reef", 30.5, 13.8, 11.2, 0.682, "Tier_1_High_Priority_Restoration", "snapshot.csv")


def observation(station_id: str, product: str, value: float, observed_at: datetime) -> ProductObservation:
    station = next(item for item in CANONICAL_STATIONS if item.station_id == station_id)
    return ProductObservation(
        station_id=station_id,
        product=product,
        observed_at=observed_at,
        requested_latitude=station.latitude,
        requested_longitude=station.longitude,
        returned_latitude=station.latitude,
        returned_longitude=station.longitude,
        value=value,
        unit="degree_C" if product == "sst" else "degree_Celsius_weeks",
        source="fake",
        dataset_id="fake-dataset",
        request_url="https://fake.invalid",
        accessed_at=observed_at,
    )


class OperationalApiTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tempdir = tempfile.TemporaryDirectory()
        self.database_path = Path(self.tempdir.name) / "api.sqlite"
        self.repository = SQLiteOperationalRepository(self.database_path)
        for station in CANONICAL_STATIONS:
            self.repository.upsert_station(station.station_id, station.name, station.latitude, station.longitude)
        self.repository.save_observation(
            observation("station-01", "sst", 29.1, datetime(2026, 8, 27, tzinfo=timezone.utc))
        )
        self.repository.save_observation(
            observation("station-01", "dhw", 3.2, datetime(2026, 8, 28, tzinfo=timezone.utc))
        )
        run_id = self.repository.start_sync_run(
            "station-01", datetime(2026, 8, 29, 12, tzinfo=timezone.utc)
        )
        self.repository.finish_sync_run(run_id, "success", datetime(2026, 8, 29, 12, 1, tzinfo=timezone.utc))
        self.sync_service = _FakeSyncService()
        self.baseline_loader = _CountingBaselineLoader()
        self.decision_loader = _CountingDecisionLoader()
        self.clock = lambda: datetime(2026, 8, 29, 13, tzinfo=timezone.utc)
        self.client = TestClient(
            create_app(
                repository=self.repository,
                stations=CANONICAL_STATIONS,
                sync_service=self.sync_service,
                inference_engine=_FakeInferenceEngine(),
                baseline_loader=self.baseline_loader,
                decision_loader=self.decision_loader,
                clock=self.clock,
            )
        )

    def tearDown(self) -> None:
        self.repository.close()
        self.tempdir.cleanup()

    def test_health_is_same_origin_json_endpoint(self) -> None:
        response = self.client.get("/api/health")

        self.assertEqual(200, response.status_code)
        self.assertEqual({"status": "ok"}, response.json())

    def test_station_listing_contains_exact_canonical_registry_and_product_summaries(self) -> None:
        response = self.client.get("/api/stations")

        self.assertEqual(200, response.status_code)
        payload = response.json()
        self.assertEqual(25, payload["count"])
        self.assertEqual([station.station_id for station in CANONICAL_STATIONS], [item["station_id"] for item in payload["stations"]])
        station = payload["stations"][0]
        self.assertEqual(
            {
                "station_id": "station-01",
                "name": "Mesoamerican_Fore_01",
                "latitude": 18.25,
                "longitude": -87.8,
                "sst": {
                    "product": "sst",
                    "value": 29.1,
                    "observed_at": "2026-08-27T00:00:00+00:00",
                    "unit": "degree_C",
                    "source": "fake",
                    "dataset_id": "fake-dataset",
                    "requested_latitude": 18.25,
                    "requested_longitude": -87.8,
                    "returned_latitude": 18.25,
                    "returned_longitude": -87.8,
                    "request_url": "https://fake.invalid",
                    "accessed_at": "2026-08-27T00:00:00+00:00",
                },
                "dhw": {
                    "product": "dhw",
                    "value": 3.2,
                    "observed_at": "2026-08-28T00:00:00+00:00",
                    "unit": "degree_Celsius_weeks",
                    "source": "fake",
                    "dataset_id": "fake-dataset",
                    "requested_latitude": 18.25,
                    "requested_longitude": -87.8,
                    "returned_latitude": 18.25,
                    "returned_longitude": -87.8,
                    "request_url": "https://fake.invalid",
                    "accessed_at": "2026-08-28T00:00:00+00:00",
                },
                "baseline": {"status": "available", "source": "processed_harmonized_csv", "source_date": "2026-08-28", "features": {name: float(index) for index, name in enumerate(BASELINE_FEATURES, 1)}},
                "decision": {"status": "available", "station_name": "Mesoamerican_Fore_01", "region": "Caribbean", "reef_zone": "Fore Reef", "macroalgae_cover_pct": 30.5, "bleaching_severity_pct": 13.8, "coral_cover_loss_pct": 11.2, "srpi": 0.682, "priority_tier": "Tier_1_High_Priority_Restoration", "source": "snapshot.csv"},
            },
            station,
        )
        self.assertEqual(payload["retrieved_at"], "2026-08-29T13:00:00+00:00")

    def test_station_state_contains_independent_products_sync_metadata_and_inference(self) -> None:
        response = self.client.get("/api/stations/station-01/state")

        self.assertEqual(200, response.status_code)
        payload = response.json()
        self.assertEqual({"station_id": "station-01", "name": "Mesoamerican_Fore_01", "latitude": 18.25, "longitude": -87.8}, payload["station"])
        self.assertEqual((29.1, "2026-08-27T00:00:00+00:00"), (payload["sst"]["value"], payload["sst"]["observed_at"]))
        self.assertEqual((3.2, "2026-08-28T00:00:00+00:00"), (payload["dhw"]["value"], payload["dhw"]["observed_at"]))
        self.assertEqual(
            {
                "product": "sst",
                "value": 29.1,
                "observed_at": "2026-08-27T00:00:00+00:00",
                "unit": "degree_C",
                "source": "fake",
                "dataset_id": "fake-dataset",
                "requested_latitude": 18.25,
                "requested_longitude": -87.8,
                "returned_latitude": 18.25,
                "returned_longitude": -87.8,
                "request_url": "https://fake.invalid",
                "accessed_at": "2026-08-27T00:00:00+00:00",
            },
            payload["sst"],
        )
        self.assertEqual("dhw", payload["dhw"]["product"])
        self.assertEqual("2026-08-28T00:00:00+00:00", payload["dhw"]["accessed_at"])
        self.assertEqual("success", payload["latest_sync_run"]["status"])
        self.assertEqual("ok", payload["inference"]["status"])
        self.assertEqual("Low", payload["inference"]["classification"])
        self.assertEqual(payload["baseline"]["status"], "available")
        self.assertEqual(payload["baseline"]["features"]["SST_degC"], 2.0)
        self.assertEqual(payload["retrieved_at"], "2026-08-29T13:00:00+00:00")
        self.assertEqual(self.baseline_loader.calls.count("station-01"), 1)
        self.assertEqual(self.decision_loader.calls.count("station-01"), 1)

    def test_baseline_loader_failure_is_reported_without_hiding_live_products(self) -> None:
        failing_loader = _CountingBaselineLoader(fail=True)
        client = TestClient(create_app(repository=self.repository, stations=CANONICAL_STATIONS, baseline_loader=failing_loader, clock=self.clock))

        payload = client.get("/api/stations/station-01/state").json()

        self.assertEqual(payload["baseline"], {"status": "unavailable", "reason": "baseline schema unavailable"})
        self.assertEqual(payload["sst"]["value"], 29.1)
        self.assertEqual(payload["dhw"]["value"], 3.2)

    def test_decision_loader_failure_is_isolated(self) -> None:
        failing_loader = _CountingDecisionLoader(fail=True)
        client = TestClient(create_app(repository=self.repository, stations=CANONICAL_STATIONS, decision_loader=failing_loader))

        payload = client.get("/api/stations/station-01/state").json()

        self.assertEqual(payload["decision"], {"status": "unavailable", "reason": "decision snapshot unavailable"})
        self.assertEqual(payload["sst"]["value"], 29.1)

    def test_unknown_station_returns_not_found_without_sync_side_effect(self) -> None:
        response = self.client.get("/api/stations/missing/state")

        self.assertEqual(404, response.status_code)
        self.assertEqual([], self.sync_service.station_calls)

    def test_sync_endpoint_delegates_single_or_all_without_network(self) -> None:
        client = TestClient(
            create_app(
                repository=self.repository,
                stations=CANONICAL_STATIONS,
                sync_service=self.sync_service,
                sync_token="test-token",
            )
        )
        headers = {"X-CoralTwin-Sync-Token": "test-token"}
        single = client.post("/api/sync", json={"station_id": "station-01"}, headers=headers)
        aggregate = client.post("/api/sync", json={}, headers=headers)
        omitted = client.post("/api/sync", headers=headers)

        self.assertEqual(200, single.status_code)
        self.assertEqual("station-01", single.json()["station_id"])
        self.assertEqual(["station-01"], self.sync_service.station_calls)
        self.assertEqual(200, aggregate.status_code)
        self.assertEqual(25, aggregate.json()["stations_total"])
        self.assertEqual(200, omitted.status_code)
        self.assertEqual(2, self.sync_service.all_calls)

    def test_sync_endpoint_rejects_invalid_station_ids_without_sync_all(self) -> None:
        client = TestClient(
            create_app(
                repository=self.repository,
                stations=CANONICAL_STATIONS,
                sync_service=self.sync_service,
                sync_token="test-token",
            )
        )
        for invalid in ("", "   ", None, 7, {}):
            response = client.post(
                "/api/sync",
                json={"station_id": invalid},
                headers={"X-CoralTwin-Sync-Token": "test-token"},
            )
            self.assertEqual(422, response.status_code, invalid)

        self.assertEqual([], self.sync_service.station_calls)
        self.assertEqual(0, self.sync_service.all_calls)

    def test_sync_endpoint_preserves_not_found_for_unknown_station(self) -> None:
        client = TestClient(
            create_app(
                repository=self.repository,
                stations=CANONICAL_STATIONS,
                sync_service=self.sync_service,
                sync_token="test-token",
            )
        )
        response = client.post(
            "/api/sync",
            json={"station_id": "station-99"},
            headers={"X-CoralTwin-Sync-Token": "test-token"},
        )

        self.assertEqual(404, response.status_code)
        self.assertEqual(["station-99"], self.sync_service.station_calls)
        self.assertEqual(0, self.sync_service.all_calls)

    def test_sync_requires_a_configured_token_before_calling_the_service(self) -> None:
        unconfigured = TestClient(
            create_app(repository=self.repository, stations=CANONICAL_STATIONS, sync_service=self.sync_service)
        )
        missing = TestClient(
            create_app(
                repository=self.repository,
                stations=CANONICAL_STATIONS,
                sync_service=self.sync_service,
                sync_token="test-token",
            )
        )

        self.assertEqual(503, unconfigured.post("/api/sync").status_code)
        self.assertEqual(401, missing.post("/api/sync").status_code)
        self.assertEqual(403, missing.post("/api/sync", headers={"X-CoralTwin-Sync-Token": "wrong"}).status_code)
        self.assertEqual([], self.sync_service.station_calls)
        self.assertEqual(0, self.sync_service.all_calls)

    def test_sync_service_missing_lease_protocol_fails_during_app_configuration(self) -> None:
        class MissingGuardService:
            def sync_station(self, station_id):
                raise AssertionError("must not run")

            def sync_all(self):
                raise AssertionError("must not run")

        with self.assertRaisesRegex(TypeError, "set_lease_guard"):
            create_app(
                repository=self.repository,
                stations=CANONICAL_STATIONS,
                sync_service=MissingGuardService(),
                sync_token="test-token",
            )

    def test_sync_lease_ttl_must_exceed_the_longest_bounded_effect(self) -> None:
        with self.assertRaisesRegex(ValueError, "longer than sync_max_effect_seconds"):
            create_app(
                repository=self.repository,
                stations=CANONICAL_STATIONS,
                sync_service=self.sync_service,
                sync_token="test-token",
                sync_lease_seconds=46.5,
                sync_max_effect_seconds=46.5,
            )

    def test_sync_rejects_overlapping_work_and_releases_the_lock_after_errors(self) -> None:
        entered = threading.Event()
        release = threading.Event()

        class BlockingService:
            def set_lease_guard(self, guard):
                self.guard = guard

            def sync_station(self, station_id):
                return self.sync_all()

            def sync_all(self):
                entered.set()
                release.wait(timeout=2)
                return _Result({"status": "success"})

        app = create_app(
            repository=self.repository,
            stations=CANONICAL_STATIONS,
            sync_service=BlockingService(),
            sync_token="test-token",
        )
        headers = {"X-CoralTwin-Sync-Token": "test-token"}
        first_response = []

        def first_request() -> None:
            with TestClient(app) as client:
                first_response.append(client.post("/api/sync", headers=headers))

        worker = threading.Thread(target=first_request)
        worker.start()
        self.assertTrue(entered.wait(timeout=1))
        with TestClient(app) as client:
            overlapping = client.post("/api/sync", headers=headers)
        release.set()
        worker.join(timeout=2)

        self.assertEqual(409, overlapping.status_code)
        self.assertEqual(200, first_response[0].status_code)

        class FailingService:
            def __init__(self) -> None:
                self.calls = 0

            def set_lease_guard(self, guard):
                self.guard = guard

            def sync_station(self, station_id):
                return self.sync_all()

            def sync_all(self):
                self.calls += 1
                if self.calls == 1:
                    raise RuntimeError("upstream failure")
                return _Result({"status": "success"})

        failing = FailingService()
        error_client = TestClient(
            create_app(
                repository=self.repository,
                stations=CANONICAL_STATIONS,
                sync_service=failing,
                sync_token="test-token",
            ),
            raise_server_exceptions=False,
        )
        self.assertEqual(500, error_client.post("/api/sync", headers=headers).status_code)
        self.assertEqual(200, error_client.post("/api/sync", headers=headers).status_code)

    def test_sync_rejects_a_cross_process_lease_and_releases_it_after_errors(self) -> None:
        other = SQLiteOperationalRepository(self.database_path)
        headers = {"X-CoralTwin-Sync-Token": "test-token"}
        try:
            self.assertTrue(other.try_acquire_sync_lease(SYNC_LEASE_NAME, "cli-owner"))
            client = TestClient(
                create_app(
                    repository=self.repository,
                    stations=CANONICAL_STATIONS,
                    sync_service=self.sync_service,
                    sync_token="test-token",
                )
            )
            self.assertEqual(409, client.post("/api/sync", headers=headers).status_code)
            self.assertEqual(0, self.sync_service.all_calls)
            self.assertTrue(other.release_sync_lease(SYNC_LEASE_NAME, "cli-owner"))
            self.assertEqual(200, client.post("/api/sync", headers=headers).status_code)

            class FailingService:
                def set_lease_guard(self, guard):
                    self.guard = guard

                def sync_station(self, station_id):
                    return self.sync_all()

                def sync_all(self):
                    raise RuntimeError("upstream failure")

            error_client = TestClient(
                create_app(
                    repository=self.repository,
                    stations=CANONICAL_STATIONS,
                    sync_service=FailingService(),
                    sync_token="test-token",
                ),
                raise_server_exceptions=False,
            )
            self.assertEqual(500, error_client.post("/api/sync", headers=headers).status_code)
            self.assertTrue(other.try_acquire_sync_lease(SYNC_LEASE_NAME, "next-owner"))
            self.assertTrue(other.release_sync_lease(SYNC_LEASE_NAME, "next-owner"))
        finally:
            other.close()

    def test_api_lease_loss_aborts_after_inflight_fetch_without_later_persistence(self) -> None:
        first_two = CANONICAL_STATIONS[:2]

        class SlowAdapter:
            def __init__(self):
                self.calls = []

            def fetch(self, station_id, product, latitude, longitude):
                self.calls.append((station_id, product))
                time.sleep(0.04)
                return observation(station_id, product, 29.0, datetime(2026, 8, 29, tzinfo=timezone.utc))

        adapter = SlowAdapter()
        service = SyncService(first_two, adapter, self.repository, request_delay=0)
        original_renew = self.repository.renew_sync_lease
        renew_calls = 0

        def renew(*args, **kwargs):
            nonlocal renew_calls
            renew_calls += 1
            return renew_calls < 4

        self.repository.renew_sync_lease = renew
        try:
            client = TestClient(
                create_app(
                    repository=self.repository,
                    stations=first_two,
                    sync_service=service,
                    sync_token="test-token",
                    sync_lease_seconds=0.1,
                    sync_heartbeat_interval=0.01,
                    sync_max_effect_seconds=0.05,
                ),
                raise_server_exceptions=False,
            )
            response = client.post("/api/sync", headers={"X-CoralTwin-Sync-Token": "test-token"})
        finally:
            self.repository.renew_sync_lease = original_renew

        self.assertEqual(409, response.status_code)
        self.assertEqual("Synchronization lease was lost", response.json()["detail"])
        self.assertEqual([("station-01", "sst")], adapter.calls)
        self.assertEqual(29.1, self.repository.get_latest_state("station-01").sst.value)
        self.assertIsNone(self.repository.get_latest_state("station-02").sst)
        latest_run = self.repository.get_latest_sync_run("station-01")
        self.assertEqual("running", latest_run["status"])
        self.assertEqual((), self.repository.list_sync_errors(latest_run["run_id"]))

    def test_api_release_cleanup_failure_returns_non_success_without_stranding_local_lock(self) -> None:
        service = _FakeSyncService()
        original_acquire = self.repository.try_acquire_sync_lease
        original_release = self.repository.release_sync_lease
        self.repository.try_acquire_sync_lease = lambda *args, **kwargs: True
        self.repository.release_sync_lease = lambda *args, **kwargs: (_ for _ in ()).throw(RuntimeError("release failed"))
        try:
            client = TestClient(
                create_app(
                    repository=self.repository,
                    stations=CANONICAL_STATIONS,
                    sync_service=service,
                    sync_token="test-token",
                ),
                raise_server_exceptions=False,
            )
            headers = {"X-CoralTwin-Sync-Token": "test-token"}
            first = client.post("/api/sync", headers=headers)
            second = client.post("/api/sync", headers=headers)
        finally:
            self.repository.try_acquire_sync_lease = original_acquire
            self.repository.release_sync_lease = original_release

        self.assertEqual(500, first.status_code)
        self.assertEqual(500, second.status_code)
        self.assertEqual(2, service.all_calls)

    def test_api_observes_lease_loss_that_occurs_while_stopping_heartbeat(self) -> None:
        service = _FakeSyncService()

        class LosingOnStopGuard:
            lost = False
            is_alive = False

            def start(self):
                return self

            def run_if_owned(self, effect):
                return effect()

            def stop(self):
                self.lost = True

        with patch("operational.api.SyncLeaseGuard", return_value=LosingOnStopGuard()):
            client = TestClient(
                create_app(
                    repository=self.repository,
                    stations=CANONICAL_STATIONS,
                    sync_service=service,
                    sync_token="test-token",
                ),
                raise_server_exceptions=False,
            )
            response = client.post(
                "/api/sync",
                headers={"X-CoralTwin-Sync-Token": "test-token"},
            )

        self.assertEqual(409, response.status_code)
        self.assertEqual("Synchronization lease was lost", response.json()["detail"])

    def test_uuid_failure_does_not_strand_api_local_lock(self) -> None:
        service = _FakeSyncService()
        client = TestClient(
            create_app(
                repository=self.repository,
                stations=CANONICAL_STATIONS,
                sync_service=service,
                sync_token="test-token",
            ),
            raise_server_exceptions=False,
        )
        headers = {"X-CoralTwin-Sync-Token": "test-token"}

        with patch("operational.api.uuid.uuid4", side_effect=RuntimeError("uuid failed")):
            first = client.post("/api/sync", headers=headers)
        second = client.post("/api/sync", headers=headers)

        self.assertEqual(500, first.status_code)
        self.assertEqual(200, second.status_code)
        self.assertEqual(1, service.all_calls)

    def test_latest_sync_run_returns_latest_mapping_or_null(self) -> None:
        response = self.client.get("/api/sync-runs/latest")

        self.assertEqual(200, response.status_code)
        self.assertEqual("success", response.json()["status"])
        self.assertEqual("station-01", response.json()["station_id"])

        empty_tempdir = tempfile.TemporaryDirectory()
        empty_repository = SQLiteOperationalRepository(Path(empty_tempdir.name) / "empty.sqlite")
        try:
            empty_client = TestClient(create_app(repository=empty_repository, stations=CANONICAL_STATIONS))
            empty_response = empty_client.get("/api/sync-runs/latest")
            self.assertEqual(200, empty_response.status_code)
            self.assertIsNone(empty_response.json())
        finally:
            empty_repository.close()
            empty_tempdir.cleanup()


if __name__ == "__main__":
    unittest.main()
