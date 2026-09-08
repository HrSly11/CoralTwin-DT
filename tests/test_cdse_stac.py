"""Offline contracts for bounded CDSE Sentinel-2 STAC metadata discovery."""

from __future__ import annotations

import json
import unittest
from datetime import datetime, timezone
from unittest.mock import patch

from operational import cdse_stac
from operational.cdse_stac import (
    CDSE_SEARCH_URL,
    CdseStacAdapter,
    StacAdapterError,
    StacHttpResponse,
    StacSearchRequest,
)


UTC = timezone.utc


def request(**changes: object) -> StacSearchRequest:
    values: dict[str, object] = {
        "station_id": "station-01", "bbox": (-88.0, 18.0, -87.0, 19.0),
        "start": datetime(2026, 1, 1, tzinfo=UTC), "end": datetime(2026, 2, 1, tzinfo=UTC),
        "max_cloud_cover": 20.0, "page_limit": 2,
    }
    values.update(changes)
    return StacSearchRequest(**values)


def feature(item: str = "tile-a", **changes: object) -> dict[str, object]:
    values: dict[str, object] = {
        "type": "Feature", "id": item, "collection": "sentinel-2-l2a",
        "properties": {"datetime": "2026-01-15T10:00:00Z", "eo:cloud_cover": 10.0},
        "assets": {"visual": {"href": "https://signed.example.invalid/asset?token=secret"}},
    }
    values.update(changes)
    return values


def page(features: list[dict[str, object]], *, next_link: object = None, response_url: str | None = CDSE_SEARCH_URL) -> StacHttpResponse:
    body: dict[str, object] = {"type": "FeatureCollection", "features": features}
    if next_link is not None:
        body["links"] = [next_link]
    return StacHttpResponse(200, json.dumps(body).encode("utf-8"), response_url)


class CdseStacAdapterTests(unittest.TestCase):
    def adapter(self, transport, **changes: object) -> CdseStacAdapter:
        values: dict[str, object] = {
            "transport": transport, "clock": lambda: datetime(2026, 2, 2, 12, tzinfo=UTC),
            "contact": "reef-team@example.org", "user_agent": "CoralTwin-CDSE-Test/1.0",
            "timeout": 15.0, "max_pages": 3, "max_response_bytes": 10_000,
        }
        values.update(changes)
        return CdseStacAdapter(**values)

    def test_posts_exact_stac_search_and_maps_observed_metadata(self) -> None:
        calls: list[tuple[str, str, dict[str, str], bytes | None]] = []

        def transport(method, url, headers, body, _timeout):
            calls.append((method, url, headers, body))
            return page([feature()])

        result = self.adapter(transport).search(request())
        method, url, headers, body = calls[0]
        self.assertEqual(("POST", CDSE_SEARCH_URL), (method, url))
        self.assertEqual("reef-team@example.org", headers["From"])
        self.assertIn("reef-team@example.org", headers["User-Agent"])
        self.assertEqual({
            "collections": ["sentinel-2-l2a"], "bbox": [-88.0, 18.0, -87.0, 19.0],
            "datetime": "2026-01-01T00:00:00Z/2026-02-01T00:00:00Z",
            "query": {"eo:cloud_cover": {"lte": 20.0}}, "limit": 2,
        }, json.loads(body or b"{}"))
        tile, observation = result.tiles[0], result.observations[0]
        self.assertEqual(("sentinel-2-l2a", "tile-a", 10.0), (tile.collection, tile.item_id, tile.cloud_cover))
        self.assertEqual(("observed", "copernicus_cdse_stac", "sentinel2_tile_cloud_cover_pct", "percent", 10.0),
                         (observation.provenance_kind, observation.provider, observation.metric, observation.unit, observation.value))
        self.assertIsNone(observation.asset_href)
        self.assertNotIn("signed.example", observation.to_dict())
        self.assertEqual(datetime(2026, 2, 2, 12, tzinfo=UTC), observation.accessed_at)

    def test_follows_only_safe_opaque_get_or_post_next_links(self) -> None:
        calls: list[tuple[str, str, bytes | None]] = []
        responses = iter([
            page([feature("b")], next_link={"rel": "next", "href": "https://stac.dataspace.copernicus.eu/v1/search?cursor=opaque"}),
            page([feature("a", properties={"datetime": "2026-01-14T10:00:00Z", "eo:cloud_cover": 5.0})], response_url="https://stac.dataspace.copernicus.eu/v1/search?cursor=opaque"),
        ])
        def transport(method, url, _headers, body, _timeout):
            calls.append((method, url, body)); return next(responses)
        result = self.adapter(transport).search(request())
        self.assertEqual([("POST", CDSE_SEARCH_URL), ("GET", "https://stac.dataspace.copernicus.eu/v1/search?cursor=opaque")],
                         [(method, url) for method, url, _ in calls])
        self.assertIsNone(calls[1][2])
        self.assertEqual(["a", "b"], [tile.item_id for tile in result.tiles])

        post_calls: list[tuple[str, bytes | None]] = []
        def post_transport(method, _url, _headers, body, _timeout):
            post_calls.append((method, body))
            if len(post_calls) == 1:
                return page([], next_link={"rel": "next", "href": "https://stac.dataspace.copernicus.eu/v1/search", "method": "POST", "body": {"cursor": "opaque"}})
            return page([feature()])
        self.adapter(post_transport).search(request())
        self.assertEqual(("POST", b'{"cursor":"opaque"}'), post_calls[1])

    def test_rejects_unsafe_links_and_bounded_response_or_page_failures_without_partial_result(self) -> None:
        unsafe = (
            {"rel": "next", "href": "http://stac.dataspace.copernicus.eu/v1/search"},
            {"rel": "next", "href": "https://user@stac.dataspace.copernicus.eu/v1/search"},
            {"rel": "next", "href": "https://evil.test/v1/search"},
            {"rel": "next", "href": "https://stac.dataspace.copernicus.eu/v1/search", "method": "DELETE"},
            {"rel": "next", "href": "https://stac.dataspace.copernicus.eu/v1/search", "method": "GET", "body": {}},
            {"rel": "next", "href": "https://stac.dataspace.copernicus.eu/v1/search", "method": "GET", "body": None},
            {"rel": "next", "href": "https://stac.dataspace.copernicus.eu/v1/search", "method": "POST", "body": []},
        )
        for link in unsafe:
            with self.subTest(link=link), self.assertRaises(StacAdapterError):
                self.adapter(lambda *_: page([], next_link=link)).search(request())
        with self.assertRaises(StacAdapterError):
            self.adapter(lambda *_: StacHttpResponse(200, b"x" * 20), max_response_bytes=10).search(request())
        loop = lambda *_: page([], next_link={"rel": "next", "href": "https://stac.dataspace.copernicus.eu/v1/search?cursor=x"})
        with self.assertRaises(StacAdapterError):
            self.adapter(loop, max_pages=2).search(request())

    def test_rejects_invalid_request_and_feature_shapes_before_claiming_data(self) -> None:
        for changes in (
            {"station_id": "missing"}, {"bbox": (-88.0, 18.0, -87.0, 95.0)}, {"bbox": (-87.7, 18.0, -87.0, 19.0)},
            {"start": datetime(2026, 2, 1, tzinfo=UTC)}, {"start": datetime(2026, 1, 1)}, {"max_cloud_cover": 101}, {"page_limit": 0},
        ):
            with self.subTest(changes=changes), self.assertRaises(ValueError): request(**changes)
        malformed = (
            {"type": "FeatureCollection", "features": {}},
            {"type": "FeatureCollection", "features": [feature(collection="other")]},
            {"type": "FeatureCollection", "features": [feature(properties={"datetime": "2026-01-15", "eo:cloud_cover": 1})]},
            {"type": "FeatureCollection", "features": [feature(properties={"datetime": "2026-01-15T00:00:00Z", "eo:cloud_cover": 21})]},
            {"type": "FeatureCollection", "features": [feature(assets={})]},
        )
        for body in malformed:
            with self.subTest(body=body), self.assertRaises(StacAdapterError):
                self.adapter(lambda *_args, value=body: StacHttpResponse(200, value, CDSE_SEARCH_URL)).search(request())

    def test_deduplicates_identical_items_but_conflicts_abort_and_ids_are_revision_stable(self) -> None:
        first = self.adapter(lambda *_: page([feature(), feature()])).search(request())
        self.assertEqual(1, len(first.tiles))
        with self.assertRaises(StacAdapterError):
            self.adapter(lambda *_: page([feature(), feature(properties={"datetime": "2026-01-15T10:00:00Z", "eo:cloud_cover": 11.0})])).search(request())
        changed_cloud = self.adapter(lambda *_: page([feature(properties={"datetime": "2026-01-15T10:00:00Z", "eo:cloud_cover": 11.0})])).search(request())
        changed_time = self.adapter(lambda *_: page([feature(properties={"datetime": "2026-01-16T10:00:00Z", "eo:cloud_cover": 10.0})])).search(request())
        self.assertEqual(first.observations[0].logical_observation_id, changed_cloud.observations[0].logical_observation_id)
        self.assertNotEqual(first.observations[0].logical_observation_id, changed_time.observations[0].logical_observation_id)
        with self.assertRaises(AttributeError): first.tiles[0].asset_keys += ("x",)

    def test_requires_each_final_transport_url_to_be_safe_and_exactly_requested(self) -> None:
        invalid = (None, "", "https://stac.dataspace.copernicus.eu/v1/items", "https://stac.dataspace.copernicus.eu/v1/search?changed=1", "https://evil.test/v1/search")
        for response_url in invalid:
            with self.subTest(response_url=response_url), self.assertRaises(StacAdapterError):
                self.adapter(lambda *_args, value=response_url: page([feature()], response_url=value)).search(request())

        calls: list[str] = []
        next_url = "https://stac.dataspace.copernicus.eu/v1/search?cursor=opaque"
        responses = iter([page([], next_link={"rel": "next", "href": next_url}), page([feature()], response_url=next_url)])
        def transport(_method, url, _headers, _body, _timeout):
            calls.append(url); return next(responses)
        self.adapter(transport).search(request())
        self.assertEqual([CDSE_SEARCH_URL, next_url], calls)

    def test_default_transport_rejects_redirect_before_any_destination_request(self) -> None:
        for code in (301, 302, 307):
            calls: list[str] = []
            class RedirectingOpener:
                def __init__(self, handler): self.handler = handler
                def open(self, request, *, timeout):
                    calls.append(request.full_url)
                    return self.handler.redirect_request(request, None, code, "redirect", {}, "https://evil.test/next")
            with self.subTest(code=code), patch("operational.cdse_stac.build_opener", side_effect=lambda handler: RedirectingOpener(handler)):
                with self.assertRaises(StacAdapterError):
                    cdse_stac._default_transport("GET", CDSE_SEARCH_URL, {}, None, 1.0)
            self.assertEqual([CDSE_SEARCH_URL], calls)


if __name__ == "__main__":
    unittest.main()
