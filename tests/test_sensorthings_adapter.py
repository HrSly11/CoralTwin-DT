"""Offline contracts for the fail-closed OGC SensorThings adapter."""

from __future__ import annotations

import json
import math
import unittest
from datetime import datetime, timezone
from urllib.parse import parse_qs, urlsplit
from unittest.mock import patch

from operational.sensorthings_adapter import (
    DatastreamMapping,
    SensorThingsAdapterError,
    SensorThingsHttpResponse,
    SensorThingsSourceConfig,
    SensorThingsObservationAdapter,
    _default_transport,
)


UTC = timezone.utc
BASE = "https://sensors.example.test/v1.1"


def source(**changes: object) -> SensorThingsSourceConfig:
    values: dict[str, object] = {
        "enabled": True,
        "base_url": BASE,
        "provider_namespace": "reef_lab",
        "owner": "Reef Field Lab",
        "license": "CC-BY-4.0",
        "allowed_origins": frozenset({"https://sensors.example.test"}),
        "base_path": "/v1.1",
    }
    values.update(changes)
    return SensorThingsSourceConfig(**values)


def mapping(**changes: object) -> DatastreamMapping:
    values: dict[str, object] = {
        "datastream_id": 7,
        "station_id": "station-01",
        "metric": "sea_surface_temperature",
        "unit": "degree_C",
        "observed_property_id": 17,
        "max_location_distance_m": 500.0,
        "interval_policy": "instant_only",
    }
    values.update(changes)
    return DatastreamMapping(**values)


def observation(identifier: int = 12, **changes: object) -> dict[str, object]:
    values: dict[str, object] = {
        "@iot.id": identifier,
        "phenomenonTime": "2026-05-01T10:00:00Z",
        "result": 29.5,
        "resultTime": "2026-05-01T10:01:00Z",
        "validTime": "2026-05-01T10:00:00Z/2026-05-01T11:00:00Z",
        "resultQuality": {"flag": "suspect"},
        "parameters": {"sensor": "thermistor"},
        "Datastream": {"@iot.id": 7, "unitOfMeasurement": {"symbol": "degree_C"}, "ObservedProperty": {"@iot.id": 17}},
        "FeatureOfInterest": {"@iot.id": 4, "feature": {"type": "Point", "coordinates": [-87.8, 18.25]}},
    }
    values.update(changes)
    return values


def response(url: str, items: list[dict[str, object]], **changes: object) -> SensorThingsHttpResponse:
    payload: dict[str, object] = {"value": items}
    payload.update(changes.pop("payload", {}))
    return SensorThingsHttpResponse(200, payload, url, **changes)


class SensorThingsAdapterTests(unittest.TestCase):
    def adapter(self, transport, **changes: object) -> SensorThingsObservationAdapter:
        values: dict[str, object] = {
            "transport": transport,
            "clock": lambda: datetime(2026, 5, 2, 12, tzinfo=UTC),
            "auth_headers": lambda: {"Authorization": "Bearer hidden-token"},
            "user_agent": "CoralTwin-SensorThings-Test/1.0",
            "timeout": 3.0,
            "page_size": 2,
            "max_pages": 3,
            "max_response_bytes": 10_000,
            "max_retries": 1,
            "sleeper": lambda _delay: None,
        }
        values.update(changes)
        return SensorThingsObservationAdapter(**values)

    def fetch(self, adapter: SensorThingsObservationAdapter, **changes: object):
        values: dict[str, object] = {
            "source": source(), "mapping": mapping(),
            "start": datetime(2026, 5, 1, tzinfo=UTC), "end": datetime(2026, 5, 2, tzinfo=UTC),
        }
        values.update(changes)
        return adapter.fetch(**values)

    def test_disabled_source_never_calls_transport_and_auth_secret_never_escapes(self) -> None:
        calls = 0
        def transport(*_args):
            nonlocal calls
            calls += 1
            raise AssertionError("must not fetch")
        adapter = self.adapter(transport)
        with self.assertRaises(SensorThingsAdapterError) as raised:
            self.fetch(adapter, source=source(enabled=False))
        self.assertEqual(0, calls)
        self.assertNotIn("hidden-token", str(raised.exception))
        self.assertNotIn("hidden-token", repr(adapter))

    def test_configuration_auth_and_time_boundaries_fail_before_transport(self) -> None:
        for changes in (
            {"base_url": "https://user@sensors.example.test/v1.1"},
            {"base_url": "https://sensors.example.test/v1.1?token=x"},
            {"allowed_origins": frozenset({"https://else.test"})},
            {"base_path": "/other"},
        ):
            with self.subTest(changes=changes):
                with self.assertRaises(ValueError):
                    source(**changes)
        for changes in ({"station_id": "unknown"}, {"metric": "not safe space"}, {"interval_policy": "average"}):
            with self.subTest(changes=changes):
                with self.assertRaises(ValueError):
                    mapping(**changes)
        calls = 0
        def transport(*_args):
            nonlocal calls
            calls += 1
            raise AssertionError("must not fetch")
        with self.assertRaises(ValueError):
            self.fetch(self.adapter(transport), start=datetime(2026, 5, 1), end=datetime(2026, 5, 2, tzinfo=UTC))
        self.assertEqual(0, calls)

    def test_builds_deterministic_get_query_and_maps_complete_observed_evidence(self) -> None:
        calls: list[tuple[str, dict[str, str]]] = []
        def transport(url, headers, _timeout):
            calls.append((url, headers))
            return response(url, [observation()])
        result = self.fetch(self.adapter(transport))
        query = parse_qs(urlsplit(calls[0][0]).query)
        self.assertEqual("2", query["$top"][0])
        self.assertIn("phenomenonTime ge 2026-05-01T00:00:00Z", query["$filter"][0])
        self.assertEqual("phenomenonTime,@iot.id", query["$orderby"][0])
        self.assertIn("FeatureOfInterest", query["$expand"][0])
        self.assertEqual("Bearer hidden-token", calls[0][1]["Authorization"])
        item = result.observations[0]
        self.assertEqual(("observed", "reef_lab", "datastream:7:17", "degree_C", 29.5),
                         (item.provenance_kind, item.provider, item.dataset_id, item.unit, item.value))
        self.assertEqual("sensorthings:reef_lab:7:12", item.logical_observation_id)
        self.assertEqual(f"{BASE}/Observations(12)", item.request_url)
        self.assertIn('result_quality:{"flag":"suspect"}', item.quality_flags)
        self.assertTrue(result.ready_for_persistence)

    def test_interval_policies_and_response_schema_are_fail_closed(self) -> None:
        def transport(url, *_args):
            return response(url, [observation(phenomenonTime="2026-05-01T10:00:00Z/2026-05-01T11:00:00Z")])
        for interval_policy, expected in (("interval_start", 10), ("interval_end", 11)):
            with self.subTest(interval_policy=interval_policy):
                result = self.fetch(self.adapter(transport), mapping=mapping(interval_policy=interval_policy))
                self.assertEqual(expected, result.observations[0].observed_at.hour)
        rejected = self.fetch(self.adapter(transport))
        self.assertFalse(rejected.ready_for_persistence)
        self.assertEqual("invalid_phenomenon_time", rejected.rejected[0].reason)

    def test_invalid_measurement_mapping_or_foi_returns_no_partial_candidates(self) -> None:
        invalids = (
            {"result": True}, {"Datastream": {"@iot.id": 8, "unitOfMeasurement": {"symbol": "degree_C"}, "ObservedProperty": {"@iot.id": 17}}},
            {"Datastream": {"@iot.id": 7, "unitOfMeasurement": {"symbol": "K"}, "ObservedProperty": {"@iot.id": 17}}},
            {"Datastream": {"@iot.id": 7, "unitOfMeasurement": {"symbol": "degree_C"}, "ObservedProperty": {"@iot.id": 18}}},
            {"FeatureOfInterest": {"feature": {"type": "Point", "coordinates": [0, 0]}}},
            {"resultTime": "2026-05-01T10:00:00"}, {"validTime": "not-a-time"},
        )
        for changes in invalids:
            with self.subTest(changes=changes):
                result = self.fetch(self.adapter(lambda url, *_: response(url, [observation(**changes)])))
                self.assertFalse(result.ready_for_persistence)
                self.assertEqual((), result.observations)
        with self.assertRaises(SensorThingsAdapterError):
            self.fetch(self.adapter(lambda url, *_: response(url, [observation(result=math.nan)])))

    def test_opaque_pagination_rejects_ssrf_loops_redirects_and_final_url_changes(self) -> None:
        next_url = f"{BASE}/Datastreams(7)/Observations?$skip=2"
        calls: list[str] = []
        responses = iter([
            lambda url: response(url, [observation(1)], payload={"@iot.nextLink": next_url}),
            lambda url: response(url, [observation(2)]),
        ])
        result = self.fetch(self.adapter(lambda url, *_: (calls.append(url), next(responses)(url))[1]))
        self.assertEqual((2, 2), (result.pages_fetched, len(result.observations)))
        self.assertEqual(next_url, calls[1])
        for next_link in ("http://sensors.example.test/v1.1/x", "https://evil.test/v1.1/x", "https://user@\u0073ensors.example.test/v1.1/x", f"{BASE}/../admin"):
            with self.subTest(next_link=next_link):
                with self.assertRaises(SensorThingsAdapterError):
                    self.fetch(self.adapter(lambda url, *_: response(url, [], payload={"@iot.nextLink": next_link})))
        with self.assertRaises(SensorThingsAdapterError):
            self.fetch(self.adapter(lambda url, *_: SensorThingsHttpResponse(302, b"", url)))
        with self.assertRaises(SensorThingsAdapterError):
            self.fetch(self.adapter(lambda url, *_: response(f"{BASE}/else", [])))

    def test_next_link_encoded_traversal_cannot_trigger_a_second_transport_call(self) -> None:
        for suffix in ("%2e%2e/admin", "%252e%252e/admin", "%2fadmin", "%5cadmin", "%00admin"):
            calls = 0
            def transport(url, *_args):
                nonlocal calls
                calls += 1
                return response(url, [], payload={"@iot.nextLink": f"{BASE}/Datastreams(7)/Observations/{suffix}"})
            with self.subTest(suffix=suffix):
                with self.assertRaises(SensorThingsAdapterError):
                    self.fetch(self.adapter(transport))
                self.assertEqual(1, calls)

    def test_default_transport_reads_at_most_limit_plus_one_and_rejects_large_socket_body(self) -> None:
        limits: list[int] = []
        class FakeResponse:
            status = 200
            headers: dict[str, str] = {}
            def read(self, limit: int) -> bytes:
                limits.append(limit)
                return b"x" * limit
            def geturl(self) -> str:
                return BASE
            def __enter__(self):
                return self
            def __exit__(self, *_args):
                return False
        class FakeOpener:
            def open(self, *_args, **_kwargs):
                return FakeResponse()
        with patch("operational.sensorthings_adapter.build_opener", return_value=FakeOpener()):
            with self.assertRaises(SensorThingsAdapterError):
                _default_transport(BASE, {}, 1.0, 10)
        self.assertEqual([11], limits)

    def test_bytes_pages_retries_and_duplicate_conflicts_are_bounded(self) -> None:
        with self.assertRaises(SensorThingsAdapterError):
            self.fetch(self.adapter(lambda url, *_: SensorThingsHttpResponse(200, b"x" * 10_001, url)))
        with self.assertRaises(SensorThingsAdapterError):
            self.fetch(self.adapter(lambda url, *_: response(url, [], payload={"@iot.nextLink": url}), max_pages=1))
        calls = 0
        sleeps: list[float] = []
        def retrying(url, *_args):
            nonlocal calls
            calls += 1
            return SensorThingsHttpResponse(429 if calls == 1 else 200, {"value": []}, url, {"Retry-After": "2"})
        result = self.fetch(self.adapter(retrying, sleeper=sleeps.append))
        self.assertEqual((2, [2.0], 0), (calls, sleeps, len(result.observations)))
        with self.assertRaises(SensorThingsAdapterError):
            self.fetch(self.adapter(lambda url, *_: SensorThingsHttpResponse(401, b"", url), max_retries=3))
        duplicate = self.fetch(self.adapter(lambda url, *_: response(url, [observation(1), observation(1)])))
        self.assertEqual(1, len(duplicate.observations))
        conflict = self.fetch(self.adapter(lambda url, *_: response(url, [observation(1), observation(1, result=30.0)])))
        self.assertFalse(conflict.ready_for_persistence)
