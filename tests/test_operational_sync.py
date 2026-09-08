import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path

from operational.noaa_adapter import ProductObservation
from operational.repository import SQLiteOperationalRepository, Station
from operational.stations import StationNotFoundError
from operational.sync import LeaseLostError, SyncService


class FakeLeaseGuard:
    def __init__(self):
        self.lost = False

    def run_if_owned(self, effect):
        if self.lost:
            raise LeaseLostError("Synchronization lease was lost")
        result = effect()
        if self.lost:
            raise LeaseLostError("Synchronization lease was lost")
        return result


class FakeClock:
    def __init__(self):
        self.values = iter(
            [
                datetime(2026, 1, 1, 0, 0, tzinfo=timezone.utc),
                datetime(2026, 1, 1, 0, 1, tzinfo=timezone.utc),
                datetime(2026, 1, 1, 0, 2, tzinfo=timezone.utc),
            ]
        )

    def __call__(self):
        return next(self.values)


class FakeAdapter:
    def __init__(self, observations, failures=None):
        self.observations = observations
        self.failures = failures or {}
        self.calls = []

    def fetch(self, station_id, product, latitude, longitude):
        self.calls.append((station_id, product, latitude, longitude))
        failure = self.failures.get((station_id, product))
        if failure:
            raise failure
        return self.observations[(station_id, product)]


class LeaseLosingAdapter(FakeAdapter):
    def __init__(self, observations, guard):
        super().__init__(observations)
        self.guard = guard

    def fetch(self, station_id, product, latitude, longitude):
        result = super().fetch(station_id, product, latitude, longitude)
        self.guard.lost = True
        return result


def observation(station_id, product, value, observed_at):
    return ProductObservation(
        station_id=station_id,
        product=product,
        observed_at=observed_at,
        requested_latitude=18.25,
        requested_longitude=-87.8,
        returned_latitude=18.25,
        returned_longitude=-87.8,
        value=value,
        unit="degree_C" if product == "sst" else "degree_Celsius_weeks",
        source="fake",
        dataset_id="fake-dataset",
        request_url="https://fake.invalid",
        accessed_at=observed_at,
    )


class SyncServiceTests(unittest.TestCase):
    def setUp(self):
        self.station = Station("station-01", "Mesoamerican_Fore_01", 18.25, -87.8)
        self.other = Station("station-02", "Mesoamerican_Crest_02", 18.28, -87.82)
        self.started = datetime(2026, 1, 1, 0, 0, tzinfo=timezone.utc)
        self.observations = {
            ("station-01", "sst"): observation("station-01", "sst", 29.1, self.started),
            ("station-01", "dhw"): observation("station-01", "dhw", 3.2, self.started),
            ("station-02", "sst"): observation("station-02", "sst", 28.4, self.started),
            ("station-02", "dhw"): observation("station-02", "dhw", 1.7, self.started),
        }
        self.tempdir = tempfile.TemporaryDirectory()
        self.repository = SQLiteOperationalRepository(Path(self.tempdir.name) / "sync.sqlite")

    def tearDown(self):
        self.repository.close()
        self.tempdir.cleanup()

    def service(self, adapter, sleeper=lambda delay: None):
        return SyncService(
            stations=[self.station, self.other],
            adapter=adapter,
            repository=self.repository,
            sleeper=sleeper,
            request_delay=2.5,
            clock=FakeClock(),
        )

    def test_unknown_explicit_station_is_rejected_without_run(self):
        service = self.service(FakeAdapter(self.observations))
        with self.assertRaises(StationNotFoundError):
            service.sync_station("missing")
        self.assertIsNone(self.repository.get_latest_state("missing"))

    def test_sync_station_saves_both_products_and_finishes_with_timestamps(self):
        adapter = FakeAdapter(self.observations)
        sleeps = []
        result = self.service(adapter, sleeps.append).sync_station("station-01")
        self.assertEqual(result.status, "success")
        self.assertEqual(result.station_id, "station-01")
        self.assertEqual(result.products_succeeded, 2)
        self.assertEqual(result.products_failed, 0)
        self.assertLess(result.started_at, result.finished_at)
        self.assertEqual(sleeps, [2.5])
        state = self.repository.get_latest_state("station-01")
        self.assertEqual((state.sst.value, state.dhw.value), (29.1, 3.2))
        run = self.repository.get_sync_run(result.run_id)
        self.assertEqual((run.status, run.started_at, run.finished_at), ("success", result.started_at, result.finished_at))

    def test_sync_mirrors_each_successful_product_to_the_canonical_ledger(self):
        self.service(FakeAdapter(self.observations)).sync_station("station-01")

        sst = self.repository.get_latest_canonical_observation("station-01", "sst")
        dhw = self.repository.get_latest_canonical_observation("station-01", "dhw")

        self.assertEqual(("observed", "fake-dataset", 29.1), (sst["provenance_kind"], sst["dataset_id"], sst["value"]))
        self.assertEqual(("observed", "fake-dataset", 3.2), (dhw["provenance_kind"], dhw["dataset_id"], dhw["value"]))

    def test_product_failure_is_recorded_and_other_product_still_succeeds(self):
        adapter = FakeAdapter(self.observations, {("station-01", "sst"): RuntimeError("sst unavailable")})
        result = self.service(adapter).sync_station("station-01")
        self.assertEqual(result.status, "partial")
        self.assertEqual(result.products_succeeded, 1)
        self.assertEqual(result.products_failed, 1)
        self.assertEqual(result.product_results["dhw"].status, "success")
        self.assertEqual(result.product_results["sst"].error_message, "sst unavailable")
        errors = self.repository.list_sync_errors(result.run_id)
        self.assertEqual([(error.product, error.error_type) for error in errors], [("sst", "RuntimeError")])
        self.assertEqual(self.repository.get_latest_state("station-01").dhw.value, 3.2)

    def test_both_product_failures_finish_failed_and_preserve_prior_state(self):
        prior = observation("station-01", "sst", 27.0, datetime(2025, 12, 31, tzinfo=timezone.utc))
        self.repository.upsert_station(self.station.station_id, self.station.name, self.station.latitude, self.station.longitude)
        self.repository.save_observation(prior)
        adapter = FakeAdapter(self.observations, {("station-01", "sst"): ValueError("bad sst"), ("station-01", "dhw"): ValueError("bad dhw")})
        result = self.service(adapter).sync_station("station-01")
        self.assertEqual(result.status, "failed")
        self.assertEqual(result.products_succeeded, 0)
        state = self.repository.get_latest_state("station-01")
        self.assertEqual(state.sst.value, 27.0)
        self.assertIsNone(state.dhw)

    def test_sync_all_continues_and_returns_json_safe_aggregate(self):
        adapter = FakeAdapter(self.observations, {("station-01", "sst"): RuntimeError("offline")})
        result = self.service(adapter).sync_all()
        self.assertEqual(result.stations_total, 2)
        self.assertEqual(result.stations_succeeded, 1)
        self.assertEqual(result.stations_partial, 1)
        self.assertEqual(result.products_succeeded, 3)
        self.assertEqual(result.products_failed, 1)
        self.assertEqual([item.station_id for item in result.stations], ["station-01", "station-02"])
        payload = result.to_dict()
        self.assertEqual(payload["stations_total"], 2)
        self.assertEqual(payload["stations"][1]["status"], "success")

    def test_lease_loss_after_fetch_aborts_all_stations_without_persisting_or_finishing(self):
        guard = FakeLeaseGuard()
        adapter = LeaseLosingAdapter(self.observations, guard)
        service = self.service(adapter)
        service.set_lease_guard(guard)

        with self.assertRaises(LeaseLostError):
            service.sync_all()

        self.assertEqual([("station-01", "sst", 18.25, -87.8)], adapter.calls)
        first_state = self.repository.get_latest_state("station-01")
        self.assertIsNone(first_state.sst)
        self.assertIsNone(first_state.dhw)
        self.assertIsNone(self.repository.get_latest_state("station-02"))
        latest_run = self.repository.get_latest_sync_run("station-01")
        self.assertEqual("running", latest_run["status"])
        self.assertEqual((), self.repository.list_sync_errors(latest_run["run_id"]))

    def test_lease_loss_before_station_start_performs_no_database_write(self):
        guard = FakeLeaseGuard()
        guard.lost = True
        service = self.service(FakeAdapter(self.observations))
        service.set_lease_guard(guard)

        with self.assertRaises(LeaseLostError):
            service.sync_station("station-01")

        self.assertIsNone(self.repository.get_latest_state("station-01"))
        self.assertIsNone(self.repository.get_latest_sync_run("station-01"))

    def test_atomic_lease_gate_fails_before_the_selected_database_effect(self):
        class FailingGate:
            lost = False

            def __init__(self):
                self.calls = 0

            def run_if_owned(self, effect):
                self.calls += 1
                if self.calls == 4:
                    self.lost = True
                    raise LeaseLostError("Synchronization lease was lost")
                return effect()

        gate = FailingGate()
        adapter = FakeAdapter(self.observations)
        service = self.service(adapter)
        service.set_lease_guard(gate)

        with self.assertRaises(LeaseLostError):
            service.sync_all()

        self.assertEqual([("station-01", "sst", 18.25, -87.8)], adapter.calls)
        self.assertIsNone(self.repository.get_latest_state("station-01").sst)
        self.assertEqual("running", self.repository.get_latest_sync_run("station-01")["status"])
        self.assertIsNone(self.repository.get_latest_state("station-02"))


if __name__ == "__main__":
    unittest.main()
