"""Contract tests for the NOAA Coral Reef Watch ERDDAP adapter."""

from __future__ import annotations

import json
import math
import unittest
from datetime import datetime, timezone
from urllib.error import HTTPError, URLError

from operational.noaa_adapter import AdapterError, NOAAErddapAdapter, NoDataError


def payload(product: str, value: object, observed_at: str = "2026-08-28T12:00:00Z") -> bytes:
    variable = "analysed_sst" if product == "sst" else "degree_heating_week"
    unit = "degree_C" if product == "sst" else "degree_Celsius_weeks"
    return json.dumps(
        {
            "table": {
                "columnNames": ["time", "latitude", "longitude", variable],
                "columnUnits": ["UTC", "degrees_north", "degrees_east", unit],
                "rows": [[observed_at, -4.5001, -81.2502, value]],
            }
        }
    ).encode("utf-8")


class NOAAErddapAdapterTests(unittest.TestCase):
    def test_fetches_sst_and_preserves_requested_returned_grid_and_provenance(self) -> None:
        received: list[tuple[str, dict[str, str], float]] = []

        def transport(url: str, headers: dict[str, str], timeout: float) -> bytes:
            received.append((url, headers, timeout))
            return payload("sst", 28.75)

        observation = NOAAErddapAdapter(transport=transport).fetch(
            station_id="piura-01", product="sst", latitude=-4.5, longitude=-81.25
        )

        self.assertEqual("piura-01", observation.station_id)
        self.assertEqual("sst", observation.product)
        self.assertEqual(datetime(2026, 8, 28, 12, tzinfo=timezone.utc), observation.observed_at)
        self.assertEqual((-4.5, -81.25), (observation.requested_latitude, observation.requested_longitude))
        self.assertEqual((-4.5001, -81.2502), (observation.returned_latitude, observation.returned_longitude))
        self.assertEqual(28.75, observation.value)
        self.assertEqual("degree_C", observation.unit)
        self.assertEqual("noaa_crw_erddap", observation.source)
        self.assertEqual("noaacrwsstDaily", observation.dataset_id)
        self.assertIn("User-Agent", received[0][1])
        self.assertEqual(received[0][0], observation.request_url)
        self.assertIsNotNone(observation.accessed_at)

    def test_builds_url_with_a_url_encoded_point_query_for_each_product(self) -> None:
        adapter = NOAAErddapAdapter(transport=lambda *_: payload("dhw", 3.5))

        sst_url = adapter.build_request_url("sst", -4.5, -81.25)
        dhw_url = adapter.build_request_url("dhw", -4.5, -81.25)

        self.assertEqual(
            "https://coastwatch.noaa.gov/erddap/griddap/noaacrwsstDaily.json?"
            "analysed_sst%5B%28last%29%5D%5B%28-4.5%29%5D%5B%28-81.25%29%5D",
            sst_url,
        )
        self.assertEqual(
            "https://coastwatch.noaa.gov/erddap/griddap/noaacrwdhwDaily.json?"
            "degree_heating_week%5B%28last%29%5D%5B%28-4.5%29%5D%5B%28-81.25%29%5D",
            dhw_url,
        )

    def test_each_product_keeps_its_own_observation_timestamp(self) -> None:
        responses = iter([payload("sst", 29.0, "2026-08-27T00:00:00Z"), payload("dhw", 2.25, "2026-08-28T00:00:00Z")])
        adapter = NOAAErddapAdapter(transport=lambda *_: next(responses))

        sst = adapter.fetch("piura-01", "sst", -4.5, -81.25)
        dhw = adapter.fetch("piura-01", "dhw", -4.5, -81.25)

        self.assertEqual(datetime(2026, 8, 27, tzinfo=timezone.utc), sst.observed_at)
        self.assertEqual(datetime(2026, 8, 28, tzinfo=timezone.utc), dhw.observed_at)

    def test_normalizes_null_nan_and_fill_value_to_typed_no_data(self) -> None:
        for missing in (None, float("nan"), -327.68):
            with self.subTest(missing=missing):
                with self.assertRaises(NoDataError):
                    NOAAErddapAdapter(transport=lambda *_args, value=missing: payload("sst", value)).fetch(
                        "piura-01", "sst", -4.5, -81.25
                    )

    def test_rejects_malformed_table_schema_without_retrying(self) -> None:
        calls = 0

        def transport(*_args: object) -> bytes:
            nonlocal calls
            calls += 1
            return b'{"table": {"columnNames": ["time"], "rows": []}}'

        with self.assertRaises(AdapterError):
            NOAAErddapAdapter(transport=transport, retries=3).fetch("piura-01", "sst", -4.5, -81.25)

        self.assertEqual(1, calls)

    def test_retries_only_transient_transport_errors_then_returns_observation(self) -> None:
        calls = 0
        delays: list[float] = []

        def transport(*_args: object) -> bytes:
            nonlocal calls
            calls += 1
            if calls < 3:
                raise URLError("temporary outage")
            return payload("sst", 28.0)

        observation = NOAAErddapAdapter(transport=transport, sleeper=delays.append, retries=3, backoff_seconds=0.25).fetch(
            "piura-01", "sst", -4.5, -81.25
        )

        self.assertEqual(28.0, observation.value)
        self.assertEqual(3, calls)
        self.assertEqual([0.25, 0.5], delays)

    def test_retries_http_429_but_not_non_transient_http_error(self) -> None:
        throttled_calls = 0
        throttled_delays: list[float] = []

        def throttled_transport(*_args: object) -> bytes:
            nonlocal throttled_calls
            throttled_calls += 1
            if throttled_calls == 1:
                raise HTTPError("https://example.test", 429, "too many requests", {}, None)
            return payload("sst", 28.0)

        result = NOAAErddapAdapter(
            transport=throttled_transport, sleeper=throttled_delays.append, retries=2, backoff_seconds=0.1
        ).fetch("piura-01", "sst", -4.5, -81.25)

        self.assertEqual(28.0, result.value)
        self.assertEqual(2, throttled_calls)
        self.assertEqual([0.1], throttled_delays)

        permanent_calls = 0

        def permanent_transport(*_args: object) -> bytes:
            nonlocal permanent_calls
            permanent_calls += 1
            raise HTTPError("https://example.test", 404, "not found", {}, None)

        with self.assertRaises(AdapterError):
            NOAAErddapAdapter(transport=permanent_transport, retries=2).fetch("piura-01", "sst", -4.5, -81.25)
        self.assertEqual(1, permanent_calls)

    def test_no_data_is_not_retried(self) -> None:
        calls = 0

        def transport(*_args: object) -> bytes:
            nonlocal calls
            calls += 1
            return payload("sst", None)

        with self.assertRaises(NoDataError):
            NOAAErddapAdapter(transport=transport, retries=3).fetch("piura-01", "sst", -4.5, -81.25)
        self.assertEqual(1, calls)


if __name__ == "__main__":
    unittest.main()
