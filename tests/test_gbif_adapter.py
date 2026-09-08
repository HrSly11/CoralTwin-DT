"""Offline contracts for public GBIF occurrence ingestion."""

from __future__ import annotations

import json
import unittest
from datetime import date, datetime, timezone
from urllib.error import HTTPError
from urllib.request import Request

from operational.gbif_adapter import (
    GbifAdapterError,
    GbifHttpResponse,
    GbifOccurrenceAdapter,
    GbifOccurrencePolicy,
    _RejectRedirectHandler,
)


UTC = timezone.utc


def policy(**changes: object) -> GbifOccurrencePolicy:
    values: dict[str, object] = {
        "allowed_licenses": frozenset({"CC0_1_0", "CC_BY_4_0"}),
        "allowed_basis_of_record": frozenset({"HUMAN_OBSERVATION"}),
        "blocking_issues": frozenset({"COORDINATE_INVALID"}),
        "max_coordinate_uncertainty_m": 1_000.0,
        "page_size": 2,
        "max_pages": 3,
        "max_records": 6,
    }
    values.update(changes)
    return GbifOccurrencePolicy(**values)


def record(key: int = 1001, **changes: object) -> dict[str, object]:
    values: dict[str, object] = {
        "key": key,
        "datasetKey": "8a863029-f435-446a-821e-275f4f641165",
        "scientificName": "Acropora cervicornis",
        "taxonKey": 1234,
        "basisOfRecord": "HUMAN_OBSERVATION",
        "eventDate": "2026-01-15",
        "decimalLatitude": 18.25,
        "decimalLongitude": -87.8,
        "coordinateUncertaintyInMeters": 30.0,
        "issues": [],
        "license": "CC_BY_4_0",
    }
    values.update(changes)
    return values


def page(url: str, results: list[dict[str, object]], *, end: bool, count: int = 1) -> GbifHttpResponse:
    return GbifHttpResponse(
        200,
        {"results": results, "endOfRecords": end, "count": count},
        url,
    )


class GbifOccurrenceAdapterTests(unittest.TestCase):
    def adapter(self, transport, **changes: object) -> GbifOccurrenceAdapter:
        return GbifOccurrenceAdapter(
            transport=transport,
            clock=lambda: datetime(2026, 2, 1, 12, tzinfo=UTC),
            contact="reef-team@example.org",
            user_agent="CoralTwin-GBIF-Test/1.0",
            **changes,
        )

    def fetch(self, adapter: GbifOccurrenceAdapter, **changes: object):
        values: dict[str, object] = {
            "station_id": "station-01",
            "bbox": (-88.0, 18.0, -87.0, 19.0),
            "start_date": date(2026, 1, 1),
            "end_date": date(2026, 1, 31),
            "taxon_key": 1234,
            "policy": policy(),
        }
        values.update(changes)
        return adapter.fetch(**values)

    def test_builds_deterministic_encoded_search_urls_and_paginates_with_contact_headers(self) -> None:
        calls: list[tuple[str, dict[str, str]]] = []
        responses = iter([
            lambda url: page(url, [record(2), record(1)], end=False, count=3),
            lambda url: page(url, [record(3)], end=True, count=3),
        ])

        def transport(url, headers, _timeout):
            calls.append((url, headers))
            return next(responses)(url)

        result = self.fetch(self.adapter(transport))

        self.assertEqual(3, len(result.observations))
        self.assertEqual(["gbif:1:station-01", "gbif:2:station-01", "gbif:3:station-01"], [item.logical_observation_id for item in result.observations])
        self.assertEqual(
            "https://api.gbif.org/v1/occurrence/search?taxon_key=1234&eventDate=2026-01-01%2C2026-01-31&decimalLongitude=-88.0%2C-87.0&decimalLatitude=18.0%2C19.0&limit=2&offset=0",
            calls[0][0],
        )
        self.assertIn("offset=2", calls[1][0])
        self.assertEqual("reef-team@example.org", calls[0][1]["From"])
        self.assertIn("reef-team@example.org", calls[0][1]["User-Agent"])
        self.assertEqual((2, 3, True), (result.pages_fetched, result.reported_count, result.end_of_records))

    def test_policy_enforces_gbif_page_and_window_bounds_before_transport(self) -> None:
        calls = 0

        def transport(*_args):
            nonlocal calls
            calls += 1
            return page(_args[0], [], end=True, count=0)

        adapter = self.adapter(transport)
        for invalid in ({"page_size": 301}, {"max_records": 100_001}, {"page_size": 2, "max_pages": 50_001}):
            with self.subTest(invalid=invalid):
                with self.assertRaises(ValueError):
                    policy(**invalid)
        self.assertEqual(0, calls)

    def test_policy_rejects_string_collections_and_ambiguous_scalar_types(self) -> None:
        invalid = (
            {"allowed_licenses": "CC_BY_4_0"},
            {"allowed_basis_of_record": b"HUMAN_OBSERVATION"},
            {"blocking_issues": ["COORDINATE_INVALID", 3]},
            {"allowed_licenses": ["  "]},
            {"max_coordinate_uncertainty_m": True},
            {"max_coordinate_uncertainty_m": "1000"},
            {"page_size": True},
            {"page_size": 2.0},
            {"max_pages": "3"},
            {"max_records": 6.0},
        )

        for changes in invalid:
            with self.subTest(changes=changes):
                with self.assertRaises(ValueError):
                    policy(**changes)

    def test_request_validation_rejects_noncanonical_station_invalid_bbox_dates_and_taxon_before_transport(self) -> None:
        calls = 0

        def transport(*_args):
            nonlocal calls
            calls += 1
            return page(_args[0], [], end=True, count=0)

        adapter = self.adapter(transport)
        invalid = (
            {"station_id": "unknown"},
            {"bbox": (-88.0, 18.0, -87.0, 95.0)},
            {"start_date": date(2026, 2, 1), "end_date": date(2026, 1, 1)},
            {"taxon_key": 0},
        )
        for changes in invalid:
            with self.subTest(changes=changes):
                with self.assertRaises(ValueError):
                    self.fetch(adapter, **changes)
        self.assertEqual(0, calls)

    def test_valid_exact_date_and_aware_datetime_map_to_observed_canonical_evidence(self) -> None:
        result = self.fetch(self.adapter(lambda url, *_: page(url, [
            record(1, eventDate="2026-01-15"), record(2, eventDate="2026-01-16T03:04:05Z"),
        ], end=True, count=2)))

        first, second = result.observations
        self.assertEqual(datetime(2026, 1, 15, tzinfo=UTC), first.observed_at)
        self.assertEqual(datetime(2026, 1, 16, 3, 4, 5, tzinfo=UTC), second.observed_at)
        self.assertEqual(("observed", "gbif", "biodiversity_occurrence_presence", "count", 1.0), (
            first.provenance_kind, first.provider, first.metric, first.unit, first.value,
        ))
        self.assertEqual("https://api.gbif.org/v1/occurrence/1", first.request_url)
        self.assertEqual((18.25, -87.8, 30.0), (first.returned_latitude, first.returned_longitude, first.uncertainty))
        self.assertIn("license:CC_BY_4_0", first.quality_flags)
        self.assertIn("taxon_key:1234", first.quality_flags)

    def test_scientific_name_is_normalized_in_immutable_deterministic_quality_audit(self) -> None:
        result = self.fetch(self.adapter(lambda url, *_: page(url, [
            record(scientificName="  Acropora   cervicornis  "),
        ], end=True)))

        observation = result.observations[0]
        self.assertIn("scientific_name:Acropora   cervicornis", observation.quality_flags)
        self.assertIn("dataset:8a863029-f435-446a-821e-275f4f641165", observation.quality_flags)
        self.assertIn("taxon_key:1234", observation.quality_flags)
        self.assertIn("license:CC_BY_4_0", observation.quality_flags)
        self.assertIn("basis_of_record:HUMAN_OBSERVATION", observation.quality_flags)
        self.assertEqual("biodiversity_occurrence_presence", observation.metric)
        self.assertEqual(1.0, observation.value)
        self.assertEqual(observation.to_dict(), json.loads(json.dumps(observation.to_dict(), allow_nan=False)))
        with self.assertRaises(TypeError):
            observation.quality_flags[0] = "mutated"  # type: ignore[index]

    def test_invalid_records_are_rejected_with_structured_reasons_without_inventing_presence(self) -> None:
        rows = [
            record(1, eventDate="2026-01"),
            record(2, eventDate="2026-01-01/2026-01-31"),
            record(3, eventDate="2026-01-20T03:00:00"),
            record(4, decimalLatitude=30.0),
            record(5, license="CC_BY_NC_4_0"),
            record(6, issues=["COORDINATE_INVALID"]),
            record(7, scientificName=""),
        ]
        result = self.fetch(self.adapter(lambda url, *_: page(url, rows, end=True, count=len(rows))), policy=policy(page_size=7, max_records=7))

        self.assertEqual((), result.observations)
        self.assertEqual(7, result.rejected_total)
        self.assertEqual(3, dict(result.rejected_by_reason)["invalid_event_date"])
        self.assertEqual(1, dict(result.rejected_by_reason)["coordinate_outside_bbox"])
        self.assertEqual(1, dict(result.rejected_by_reason)["license_not_allowed"])
        self.assertEqual(1, dict(result.rejected_by_reason)["blocking_issue"])
        self.assertEqual(result.to_dict(), json.loads(json.dumps(result.to_dict(), allow_nan=False)))

    def test_top_level_status_schema_and_pagination_fail_closed(self) -> None:
        adapter = self.adapter(lambda url, *_: GbifHttpResponse(503, {}, url))
        with self.assertRaisesRegex(GbifAdapterError, "HTTP 503"):
            self.fetch(adapter)
        for response in (
            {"results": [], "count": 0},
            {"results": [], "endOfRecords": False, "count": 1},
            {"results": {}, "endOfRecords": True, "count": 0},
        ):
            with self.subTest(response=response):
                with self.assertRaises(GbifAdapterError):
                    self.fetch(self.adapter(lambda url, *_args, item=response: GbifHttpResponse(200, item, url)))

    def test_duplicate_key_is_deduplicated_only_when_identical_and_conflicts_fail(self) -> None:
        identical = self.fetch(self.adapter(lambda url, *_: page(url, [record(1), record(1)], end=True, count=2)))
        self.assertEqual(1, len(identical.observations))
        with self.assertRaisesRegex(GbifAdapterError, "conflicting GBIF key"):
            self.fetch(self.adapter(lambda url, *_: page(url, [record(1), record(1, decimalLatitude=18.5)], end=True, count=2)))

    def test_adapter_never_persists_and_rejects_host_escape_in_transport_response_url(self) -> None:
        with self.assertRaisesRegex(GbifAdapterError, "host"):
            self.adapter(lambda *_: GbifHttpResponse(200, {"results": [record()], "endOfRecords": True, "count": 1}, "https://evil.test/result")).fetch(
                station_id="station-01", bbox=(-88.0, 18.0, -87.0, 19.0), start_date=date(2026, 1, 1),
                end_date=date(2026, 1, 31), taxon_key=1234, policy=policy(),
            )

    def test_redirects_to_an_untrusted_host_fail_before_any_second_request(self) -> None:
        for status in (301, 302, 307):
            calls: list[str] = []

            def transport(url, _headers, _timeout):
                calls.append(url)
                return GbifHttpResponse(status, {}, "https://evil.example/redirected")

            with self.subTest(status=status):
                with self.assertRaisesRegex(GbifAdapterError, "HTTPS host"):
                    self.fetch(self.adapter(transport))
                self.assertEqual(1, len(calls))
                self.assertTrue(all(url.startswith("https://api.gbif.org/") for url in calls))

    def test_injected_transport_requires_a_verifiable_final_request_url(self) -> None:
        with self.assertRaisesRegex(GbifAdapterError, "final URL"):
            self.fetch(self.adapter(lambda *_: GbifHttpResponse(200, {"results": [], "endOfRecords": True, "count": 0}, None)))

    def test_injected_transport_final_url_must_exactly_match_the_requested_url(self) -> None:
        final_urls = (
            "https://api.gbif.org/v1/occurrence/other",
            "https://api.gbif.org/v1/occurrence/search?offset=unexpected",
            "https://api.gbif.org/v1/occurrence/search#fragment",
            "https://user@api.gbif.org/v1/occurrence/search",
            "https://evil.example/v1/occurrence/search",
        )
        for final_url in final_urls:
            calls: list[str] = []
            def transport(url, _headers, _timeout):
                calls.append(url)
                return GbifHttpResponse(200, {"results": [], "endOfRecords": True, "count": 0}, final_url)
            with self.subTest(final_url=final_url), self.assertRaisesRegex(GbifAdapterError, "final URL|HTTPS host"):
                self.fetch(self.adapter(transport))
            self.assertEqual(1, len(calls))

    def test_default_redirect_handler_rejects_before_following_301_302_or_307(self) -> None:
        handler = _RejectRedirectHandler()
        for status in (301, 302, 307):
            with self.subTest(status=status), self.assertRaises(HTTPError):
                handler.redirect_request(
                    Request("https://api.gbif.org/v1/occurrence/search"), None, status, "redirect", {},
                    "https://evil.example/redirected",
                )


if __name__ == "__main__":
    unittest.main()
