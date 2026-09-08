"""Contract tests for durable operational NOAA observations."""

from __future__ import annotations

import tempfile
import threading
import time
import unittest
from dataclasses import replace
from datetime import datetime, timezone

from operational.noaa_adapter import ProductObservation
from operational.repository import SQLiteOperationalRepository, SyncLeaseGuard
from operational.sync import LeaseLostError


class FakeLeaseRepository:
    def __init__(self, outcomes):
        self.outcomes = iter(outcomes)
        self.renewed = threading.Event()
        self.calls = 0

    def renew_sync_lease(self, lease_name, owner_token, **kwargs):
        self.calls += 1
        self.renewed.set()
        outcome = next(self.outcomes)
        if isinstance(outcome, BaseException):
            raise outcome
        return outcome


class BlockingLeaseRepository:
    def __init__(self, outcome):
        self.outcome = outcome
        self.entered = threading.Event()
        self.release = threading.Event()

    def renew_sync_lease(self, lease_name, owner_token, **kwargs):
        self.entered.set()
        self.release.wait(timeout=1)
        return self.outcome


def observation(product: str, observed_at: datetime, value: float) -> ProductObservation:
    return ProductObservation(
        station_id="piura-01",
        product=product,
        observed_at=observed_at,
        requested_latitude=-4.5,
        requested_longitude=-81.25,
        returned_latitude=-4.5001,
        returned_longitude=-81.2502,
        value=value,
        unit="degree_C" if product == "sst" else "degree_Celsius_weeks",
        source="noaa_crw_erddap",
        dataset_id="noaacrwsstDaily" if product == "sst" else "noaacrwdhwDaily",
        request_url="https://example.test/query",
        accessed_at=datetime(2026, 8, 29, tzinfo=timezone.utc),
    )


class SQLiteOperationalRepositoryTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.NamedTemporaryFile(suffix=".sqlite3", delete=False)
        self.temp.close()
        self.repository = SQLiteOperationalRepository(self.temp.name)
        self.repository.upsert_station("piura-01", "Piura Reef", -4.5, -81.25)

    def tearDown(self) -> None:
        self.repository.close()
        import os

        os.unlink(self.temp.name)

    def test_saves_observations_idempotently_with_full_provenance(self) -> None:
        item = observation("sst", datetime(2026, 8, 28, tzinfo=timezone.utc), 28.25)

        self.assertTrue(self.repository.save_observation(item))
        self.assertFalse(self.repository.save_observation(item))
        stored = self.repository.get_latest_state("piura-01")

        self.assertEqual(28.25, stored.sst.value)
        self.assertEqual("noaacrwsstDaily", stored.sst.dataset_id)
        self.assertEqual("https://example.test/query", stored.sst.request_url)
        self.assertEqual("Piura Reef", stored.station.name)

    def test_same_timestamp_correction_updates_latest_observation_provenance(self) -> None:
        observed_at = datetime(2026, 8, 28, tzinfo=timezone.utc)
        original = observation("sst", observed_at, 28.25)
        corrected = replace(
            original,
            value=28.75,
            returned_latitude=-4.51,
            returned_longitude=-81.26,
            dataset_id="noaacrwsstDaily-v2",
            request_url="https://example.test/corrected-query",
            accessed_at=datetime(2026, 8, 30, tzinfo=timezone.utc),
        )

        self.assertTrue(self.repository.save_observation(original))
        self.assertTrue(self.repository.save_observation(corrected))
        self.assertFalse(self.repository.save_observation(corrected))
        stored = self.repository.get_latest_state("piura-01").sst

        self.assertEqual(28.75, stored.value)
        self.assertEqual((-4.51, -81.26), (stored.returned_latitude, stored.returned_longitude))
        self.assertEqual("noaacrwsstDaily-v2", stored.dataset_id)
        self.assertEqual("https://example.test/corrected-query", stored.request_url)
        self.assertEqual(datetime(2026, 8, 30, tzinfo=timezone.utc), stored.accessed_at)

    def test_latest_state_selects_sst_and_dhw_independently(self) -> None:
        self.repository.save_observation(observation("sst", datetime(2026, 8, 27, tzinfo=timezone.utc), 27.5))
        self.repository.save_observation(observation("sst", datetime(2026, 8, 28, tzinfo=timezone.utc), 28.5))
        self.repository.save_observation(observation("dhw", datetime(2026, 8, 26, tzinfo=timezone.utc), 1.5))

        state = self.repository.get_latest_state("piura-01")

        self.assertEqual(28.5, state.sst.value)
        self.assertEqual(datetime(2026, 8, 28, tzinfo=timezone.utc), state.sst.observed_at)
        self.assertEqual(1.5, state.dhw.value)
        self.assertEqual(datetime(2026, 8, 26, tzinfo=timezone.utc), state.dhw.observed_at)

    def test_failure_recording_preserves_previous_observations(self) -> None:
        self.repository.save_observation(observation("sst", datetime(2026, 8, 28, tzinfo=timezone.utc), 28.5))
        run_id = self.repository.start_sync_run("piura-01")
        self.repository.record_sync_error(run_id, "sst", "NoDataError", "No current SST")
        self.repository.finish_sync_run(run_id, "failed")

        state = self.repository.get_latest_state("piura-01")
        run = self.repository.get_sync_run(run_id)
        errors = self.repository.list_sync_errors(run_id)

        self.assertEqual(28.5, state.sst.value)
        self.assertEqual("failed", run.status)
        self.assertEqual(("sst", "NoDataError", "No current SST"), (errors[0].product, errors[0].error_type, errors[0].message))

    def test_unknown_station_returns_no_state(self) -> None:
        self.assertIsNone(self.repository.get_latest_state("unknown-station"))

    def test_lists_stations_as_sorted_json_safe_mappings(self) -> None:
        self.repository.upsert_station("alpha-01", "Alpha Reef", 1.25, 2.5)

        stations = self.repository.list_stations()

        self.assertEqual(
            [
                {"station_id": "alpha-01", "name": "Alpha Reef", "latitude": 1.25, "longitude": 2.5},
                {"station_id": "piura-01", "name": "Piura Reef", "latitude": -4.5, "longitude": -81.25},
            ],
            stations,
        )

    def test_get_latest_sync_run_is_json_safe_and_filters_by_station(self) -> None:
        self.repository.upsert_station("alpha-01", "Alpha Reef", 1.25, 2.5)
        first_started = datetime(2026, 8, 28, 12, tzinfo=timezone.utc)
        second_started = datetime(2026, 8, 29, 12, tzinfo=timezone.utc)
        first_run = self.repository.start_sync_run("piura-01", first_started)
        self.repository.finish_sync_run(first_run, "success", datetime(2026, 8, 28, 12, 1, tzinfo=timezone.utc))
        second_run = self.repository.start_sync_run("alpha-01", second_started)
        self.repository.finish_sync_run(second_run, "failed", datetime(2026, 8, 29, 12, 1, tzinfo=timezone.utc))

        self.assertIsNone(self.repository.get_latest_sync_run("missing"))
        self.assertEqual(
            {
                "run_id": second_run,
                "station_id": "alpha-01",
                "started_at": "2026-08-29T12:00:00+00:00",
                "finished_at": "2026-08-29T12:01:00+00:00",
                "status": "failed",
            },
            self.repository.get_latest_sync_run("alpha-01"),
        )
        self.assertEqual(
            {"run_id": second_run, "station_id": "alpha-01", "status": "failed"},
            {
                key: value
                for key, value in self.repository.get_latest_sync_run().items()
                if key in {"run_id", "station_id", "status"}
            },
        )

    def test_connection_can_be_used_for_reads_and_writes_from_another_thread(self) -> None:
        errors: list[BaseException] = []
        observed_values: list[float] = []

        def worker() -> None:
            try:
                self.repository.upsert_station("worker-01", "Worker Reef", 1.0, 2.0)
                self.repository.save_observation(
                    ProductObservation(
                        station_id="worker-01",
                        product="sst",
                        observed_at=datetime(2026, 8, 29, tzinfo=timezone.utc),
                        requested_latitude=1.0,
                        requested_longitude=2.0,
                        returned_latitude=1.0,
                        returned_longitude=2.0,
                        value=28.5,
                        unit="degree_C",
                        source="worker",
                        dataset_id="worker-dataset",
                        request_url="https://example.test/worker",
                        accessed_at=datetime(2026, 8, 29, tzinfo=timezone.utc),
                    )
                )
                observed_values.append(self.repository.get_latest_state("worker-01").sst.value)
            except BaseException as error:  # surfaced in the test thread below
                errors.append(error)

        thread = threading.Thread(target=worker)
        thread.start()
        thread.join()

        self.assertEqual([], errors)
        self.assertEqual([28.5], observed_values)

    def test_sync_lease_is_shared_by_connections_owner_scoped_and_expires(self) -> None:
        other = SQLiteOperationalRepository(self.temp.name)
        now = datetime(2026, 8, 29, 12, tzinfo=timezone.utc)
        try:
            self.assertTrue(
                self.repository.try_acquire_sync_lease(
                    "operational-noaa-sync", "owner-one", now=now, lease_seconds=60
                )
            )
            self.assertFalse(
                other.try_acquire_sync_lease(
                    "operational-noaa-sync", "owner-two", now=now, lease_seconds=60
                )
            )
            self.assertFalse(other.release_sync_lease("operational-noaa-sync", "owner-two"))
            self.assertTrue(
                other.try_acquire_sync_lease(
                    "operational-noaa-sync", "owner-two", now=datetime(2026, 8, 29, 12, 1, tzinfo=timezone.utc), lease_seconds=60
                )
            )
            self.assertFalse(self.repository.release_sync_lease("operational-noaa-sync", "owner-one"))
            self.assertTrue(other.release_sync_lease("operational-noaa-sync", "owner-two"))
        finally:
            other.close()

    def test_sync_lease_renewal_extends_expiry_and_normalizes_naive_clock(self) -> None:
        other = SQLiteOperationalRepository(self.temp.name)
        acquired = datetime(2026, 8, 29, 12)
        try:
            self.assertTrue(self.repository.try_acquire_sync_lease("heartbeat", "owner-one", now=acquired, lease_seconds=1))
            self.assertTrue(self.repository.renew_sync_lease("heartbeat", "owner-one", now=datetime(2026, 8, 29, 12, 0, 0, 500000), lease_seconds=1))
            self.assertFalse(other.renew_sync_lease("heartbeat", "owner-two", now=datetime(2026, 8, 29, 12, 0, 0, 600000), lease_seconds=1))
            self.assertFalse(other.try_acquire_sync_lease("heartbeat", "owner-two", now=datetime(2026, 8, 29, 12, 0, 1, 200000), lease_seconds=1))
            self.assertTrue(other.try_acquire_sync_lease("heartbeat", "owner-two", now=datetime(2026, 8, 29, 12, 0, 2), lease_seconds=1))
        finally:
            other.close()

    def test_sync_lease_guard_renews_repeatedly_past_the_original_ttl(self) -> None:
        fake = FakeLeaseRepository([True] * 20)
        guard = SyncLeaseGuard(fake, "heartbeat", "owner", lease_seconds=0.06, heartbeat_interval=0.01).start()
        try:
            deadline = time.monotonic() + 0.2
            while fake.calls < 7 and time.monotonic() < deadline:
                time.sleep(0.002)
            self.assertGreaterEqual(fake.calls, 7)
            self.assertFalse(guard.lost)
        finally:
            guard.stop()

    def test_sync_lease_guard_stop_interrupts_a_long_heartbeat_wait(self) -> None:
        fake = FakeLeaseRepository([True])
        guard = SyncLeaseGuard(fake, "heartbeat", "owner", lease_seconds=30, heartbeat_interval=10).start()

        started = time.monotonic()
        guard.stop()

        self.assertLess(time.monotonic() - started, 0.2)
        self.assertEqual(0, fake.calls)

    def test_sync_lease_guard_marks_false_and_exception_renewals_as_lost(self) -> None:
        for outcome in (False, RuntimeError("renew failed")):
            with self.subTest(outcome=type(outcome).__name__):
                fake = FakeLeaseRepository([outcome])
                guard = SyncLeaseGuard(fake, "heartbeat", "owner", lease_seconds=0.1, heartbeat_interval=0.01).start()
                self.assertTrue(fake.renewed.wait(timeout=0.2))
                deadline = time.monotonic() + 0.2
                while not guard.lost and time.monotonic() < deadline:
                    time.sleep(0.002)
                guard.stop()
                self.assertTrue(guard.lost)

    def test_sync_lease_guard_run_if_owned_rejects_before_effect_when_renewal_fails(self) -> None:
        fake = FakeLeaseRepository([False])
        guard = SyncLeaseGuard(fake, "heartbeat", "owner", lease_seconds=1, heartbeat_interval=0.5)
        effects = []

        with self.assertRaises(LeaseLostError):
            guard.run_if_owned(lambda: effects.append("ran"))

        self.assertEqual([], effects)
        self.assertTrue(guard.lost)

    def test_sync_lease_guard_stop_waits_for_inflight_renewal_and_observes_loss(self) -> None:
        fake = BlockingLeaseRepository(False)
        guard = SyncLeaseGuard(fake, "heartbeat", "owner", lease_seconds=0.2, heartbeat_interval=0.01).start()
        self.assertTrue(fake.entered.wait(timeout=0.2))
        stopped = threading.Event()

        worker = threading.Thread(target=lambda: (guard.stop(), stopped.set()))
        worker.start()
        self.assertFalse(stopped.wait(timeout=0.03))
        fake.release.set()
        worker.join(timeout=0.5)

        self.assertTrue(stopped.is_set())
        self.assertTrue(guard.lost)
        self.assertFalse(guard.is_alive)

    def test_sync_lease_guard_stop_explicitly_fails_if_heartbeat_stays_blocked(self) -> None:
        fake = BlockingLeaseRepository(True)
        guard = SyncLeaseGuard(
            fake,
            "heartbeat",
            "owner",
            lease_seconds=0.2,
            heartbeat_interval=0.01,
            shutdown_timeout=0.02,
        ).start()
        self.assertTrue(fake.entered.wait(timeout=0.2))
        try:
            with self.assertRaisesRegex(RuntimeError, "did not stop"):
                guard.stop()
            self.assertTrue(guard.is_alive)
        finally:
            fake.release.set()
            guard.stop()


if __name__ == "__main__":
    unittest.main()
