"""Bounded, metadata-only Sentinel-2 L2A discovery through CDSE STAC."""

from __future__ import annotations

import hashlib
import json
import math
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Callable, Mapping
from urllib.error import HTTPError
from urllib.parse import urlsplit
from urllib.request import HTTPRedirectHandler, Request, build_opener

from .observations import CanonicalObservation
from .stations import StationNotFoundError, get_station


CDSE_SEARCH_URL = "https://stac.dataspace.copernicus.eu/v1/search"
CDSE_HOST = "stac.dataspace.copernicus.eu"
SENTINEL2_L2A = "sentinel-2-l2a"


class StacAdapterError(RuntimeError):
    """Raised when a CDSE STAC response cannot be safely used in full."""


@dataclass(frozen=True)
class StacHttpResponse:
    status: int
    body: bytes | str | Mapping[str, Any]
    url: str | None = None


def _text(value: object, field: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{field} must be a non-empty string")
    return value.strip()


def _finite(value: object, field: str, *, lower: float | None = None, upper: float | None = None) -> float:
    if isinstance(value, bool):
        raise ValueError(f"{field} must be numeric")
    try:
        result = float(value)
    except (TypeError, ValueError) as error:
        raise ValueError(f"{field} must be numeric") from error
    if not math.isfinite(result) or (lower is not None and result < lower) or (upper is not None and result > upper):
        raise ValueError(f"{field} is outside its valid finite range")
    return result


def _positive_int(value: object, field: str) -> int:
    if not isinstance(value, int) or isinstance(value, bool) or value < 1:
        raise ValueError(f"{field} must be a positive integer")
    return value


def _utc(value: object, field: str) -> datetime:
    if not isinstance(value, datetime) or value.tzinfo is None:
        raise ValueError(f"{field} must be a timezone-aware datetime")
    return value.astimezone(timezone.utc)


def _iso(value: datetime) -> str:
    return value.isoformat().replace("+00:00", "Z")


def _json_bytes(value: object, field: str) -> bytes:
    try:
        return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False).encode("utf-8")
    except (TypeError, ValueError) as error:
        raise StacAdapterError(f"{field} is not JSON-safe") from error


def _safe_catalog_url(url: object) -> str:
    try:
        candidate = _text(url, "STAC link href")
        parsed = urlsplit(candidate)
        valid = (
            parsed.scheme == "https" and parsed.netloc == CDSE_HOST and parsed.hostname == CDSE_HOST
            and parsed.username is None and parsed.password is None
        )
    except ValueError as error:
        raise StacAdapterError("STAC link escaped the required HTTPS host") from error
    if not valid:
        raise StacAdapterError("STAC link escaped the required HTTPS host")
    return candidate


@dataclass(frozen=True)
class StacSearchRequest:
    station_id: str
    bbox: tuple[float, float, float, float]
    start: datetime
    end: datetime
    max_cloud_cover: float
    page_limit: int

    def __post_init__(self) -> None:
        try:
            station = get_station(self.station_id)
        except StationNotFoundError as error:
            raise ValueError("station_id must identify a canonical station") from error
        try:
            west, south, east, north = tuple(self.bbox)
        except (TypeError, ValueError) as error:
            raise ValueError("bbox must contain west, south, east, north") from error
        normalized = tuple(_finite(value, "bbox value") for value in (west, south, east, north))
        if not (-180 <= normalized[0] < normalized[2] <= 180 and -90 <= normalized[1] < normalized[3] <= 90):
            raise ValueError("bbox must be ordered, within geographic bounds, and not cross the antimeridian")
        if not normalized[1] <= station.latitude <= normalized[3] or not normalized[0] <= station.longitude <= normalized[2]:
            raise ValueError("bbox must contain the canonical station coordinates")
        start, end = _utc(self.start, "start"), _utc(self.end, "end")
        if start >= end:
            raise ValueError("start must be before end")
        object.__setattr__(self, "station_id", station.station_id)
        object.__setattr__(self, "bbox", normalized)
        object.__setattr__(self, "start", start)
        object.__setattr__(self, "end", end)
        object.__setattr__(self, "max_cloud_cover", _finite(self.max_cloud_cover, "max_cloud_cover", lower=0, upper=100))
        object.__setattr__(self, "page_limit", _positive_int(self.page_limit, "page_limit"))


@dataclass(frozen=True)
class SentinelTileMetadata:
    collection: str
    item_id: str
    datetime: datetime
    cloud_cover: float
    asset_keys: tuple[str, ...]
    request_url: str
    logical_observation_id: str

    def __post_init__(self) -> None:
        object.__setattr__(self, "collection", _text(self.collection, "collection"))
        object.__setattr__(self, "item_id", _text(self.item_id, "item_id"))
        object.__setattr__(self, "datetime", _utc(self.datetime, "datetime"))
        object.__setattr__(self, "cloud_cover", _finite(self.cloud_cover, "cloud_cover", lower=0, upper=100))
        object.__setattr__(self, "asset_keys", tuple(sorted(_text(key, "asset key") for key in self.asset_keys)))
        object.__setattr__(self, "request_url", _safe_catalog_url(self.request_url))
        object.__setattr__(self, "logical_observation_id", _text(self.logical_observation_id, "logical_observation_id"))


@dataclass(frozen=True)
class StacSearchResult:
    tiles: tuple[SentinelTileMetadata, ...]
    observations: tuple[CanonicalObservation, ...]
    pages_fetched: int

    def __post_init__(self) -> None:
        tiles, observations = tuple(self.tiles), tuple(self.observations)
        if len(tiles) != len(observations) or any(not isinstance(tile, SentinelTileMetadata) for tile in tiles):
            raise ValueError("tiles and observations must have matching valid entries")
        if any(not isinstance(item, CanonicalObservation) for item in observations):
            raise ValueError("observations must contain CanonicalObservation values")
        object.__setattr__(self, "tiles", tiles)
        object.__setattr__(self, "observations", observations)
        object.__setattr__(self, "pages_fetched", _positive_int(self.pages_fetched, "pages_fetched"))


Transport = Callable[[str, str, dict[str, str], bytes | None, float], StacHttpResponse]


class _RejectRedirects(HTTPRedirectHandler):
    """Fail before urllib can issue a redirected request to another endpoint."""

    def redirect_request(self, request, fp, code, message, headers, new_url):  # type: ignore[no-untyped-def]
        if code in {301, 302, 307}:
            raise StacAdapterError("STAC redirects are prohibited")
        return None


def _default_transport(method: str, url: str, headers: dict[str, str], body: bytes | None, timeout: float) -> StacHttpResponse:
    """Issue exactly one request; redirects are rejected before a second request."""

    request = Request(url, data=body, headers=headers, method=method)
    try:
        with build_opener(_RejectRedirects()).open(request, timeout=timeout) as response:
            return StacHttpResponse(int(response.status), response.read(), response.geturl())
    except HTTPError as error:
        return StacHttpResponse(error.code, error.read(), error.geturl())


class CdseStacAdapter:
    """Search only catalogue metadata; it never fetches Sentinel assets or persists data."""

    def __init__(self, *, transport: Transport | None = None, clock: Callable[[], datetime], contact: str, user_agent: str,
                 timeout: float, max_pages: int, max_response_bytes: int) -> None:
        if transport is not None and not callable(transport) or not callable(clock):
            raise ValueError("transport and clock must be callable")
        self._transport, self._clock = transport or _default_transport, clock
        self._contact, self._user_agent = _text(contact, "contact"), _text(user_agent, "user_agent")
        self._timeout = _finite(timeout, "timeout", lower=0)
        if self._timeout == 0:
            raise ValueError("timeout must be positive")
        self._max_pages = _positive_int(max_pages, "max_pages")
        self._max_response_bytes = _positive_int(max_response_bytes, "max_response_bytes")

    def search(self, request: StacSearchRequest) -> StacSearchResult:
        if not isinstance(request, StacSearchRequest):
            raise ValueError("request must be a StacSearchRequest")
        accessed_at = _utc(self._clock(), "clock result")
        body = _json_bytes({"collections": [SENTINEL2_L2A], "bbox": list(request.bbox),
                            "datetime": f"{_iso(request.start)}/{_iso(request.end)}",
                            "query": {"eo:cloud_cover": {"lte": request.max_cloud_cover}}, "limit": request.page_limit}, "request")
        pending: tuple[str, str, bytes | None] | None = ("POST", CDSE_SEARCH_URL, body)
        seen: dict[tuple[str, str], tuple[bytes, SentinelTileMetadata, CanonicalObservation]] = {}
        pages = 0
        while pending is not None:
            if pages >= self._max_pages:
                raise StacAdapterError("STAC pagination exceeded configured max_pages")
            method, url, request_body = pending
            payload = self._request(method, url, request_body)
            pages += 1
            features, pending = self._page(payload)
            for raw in features:
                fingerprint, tile, observation = self._feature(raw, request, accessed_at, url)
                key = (tile.collection, tile.item_id)
                previous = seen.get(key)
                if previous is not None:
                    if previous[0] != fingerprint:
                        raise StacAdapterError(f"conflicting STAC item {tile.collection}/{tile.item_id}")
                    continue
                seen[key] = (fingerprint, tile, observation)
        ordered = sorted(((value[1], value[2]) for value in seen.values()), key=lambda pair: (pair[0].datetime, pair[0].item_id))
        return StacSearchResult(tuple(pair[0] for pair in ordered), tuple(pair[1] for pair in ordered), pages)

    def _request(self, method: str, url: str, body: bytes | None) -> Mapping[str, Any]:
        if method not in {"GET", "POST"} or (method == "GET" and body is not None) or (method == "POST" and body is None):
            raise StacAdapterError("STAC request method or body is invalid")
        _safe_catalog_url(url)
        headers = {"Accept": "application/geo+json, application/json", "User-Agent": f"{self._user_agent} ({self._contact})", "From": self._contact}
        if method == "POST":
            headers["Content-Type"] = "application/json"
        response = self._transport(method, url, headers, body, self._timeout)
        if not isinstance(response, StacHttpResponse):
            raise StacAdapterError("STAC transport must return StacHttpResponse")
        if not isinstance(response.url, str) or not response.url:
            raise StacAdapterError("STAC response must include a final URL")
        _safe_catalog_url(response.url)
        if response.url != url:
            raise StacAdapterError("STAC response final URL differs from the requested URL")
        if response.status != 200:
            raise StacAdapterError(f"STAC HTTP {response.status}")
        raw = response.body
        if isinstance(raw, Mapping):
            raw = _json_bytes(raw, "STAC response")
        elif isinstance(raw, str):
            raw = raw.encode("utf-8")
        if not isinstance(raw, bytes) or len(raw) > self._max_response_bytes:
            raise StacAdapterError("STAC response exceeds configured byte limit")
        try:
            payload = json.loads(raw.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError) as error:
            raise StacAdapterError("STAC response is not valid JSON") from error
        if not isinstance(payload, Mapping):
            raise StacAdapterError("STAC response must be an object")
        return payload

    def _page(self, payload: Mapping[str, Any]) -> tuple[list[Mapping[str, Any]], tuple[str, str, bytes | None] | None]:
        if payload.get("type") != "FeatureCollection" or not isinstance(payload.get("features"), list):
            raise StacAdapterError("STAC FeatureCollection payload is invalid")
        features = payload["features"]
        if any(not isinstance(feature, Mapping) for feature in features):
            raise StacAdapterError("STAC features are invalid")
        links = payload.get("links", [])
        if not isinstance(links, list) or any(not isinstance(link, Mapping) for link in links):
            raise StacAdapterError("STAC links are invalid")
        next_links = [link for link in links if link.get("rel") == "next"]
        if len(next_links) > 1:
            raise StacAdapterError("STAC page has multiple next links")
        return list(features), self._next(next_links[0]) if next_links else None

    @staticmethod
    def _next(link: Mapping[str, Any]) -> tuple[str, str, bytes | None]:
        url = _safe_catalog_url(link.get("href"))
        method = link.get("method", "GET")
        if not isinstance(method, str) or method not in {"GET", "POST"}:
            raise StacAdapterError("STAC next-link method is invalid")
        has_body, body = "body" in link, link.get("body")
        if method == "GET":
            if has_body:
                raise StacAdapterError("STAC GET next link must not have a body")
            return method, url, None
        if not isinstance(body, Mapping):
            raise StacAdapterError("STAC POST next link requires an object body")
        return method, url, _json_bytes(body, "STAC next-link body")

    @staticmethod
    def _feature(raw: Mapping[str, Any], request: StacSearchRequest, accessed_at: datetime,
                 request_url: str) -> tuple[bytes, SentinelTileMetadata, CanonicalObservation]:
        try:
            item_id = _text(raw.get("id"), "feature id")
            if raw.get("type") != "Feature" or raw.get("collection") != SENTINEL2_L2A:
                raise ValueError("feature collection is invalid")
            properties, assets = raw.get("properties"), raw.get("assets")
            if not isinstance(properties, Mapping) or not isinstance(assets, Mapping) or not assets:
                raise ValueError("feature properties or assets are invalid")
            observed_at = _utc(datetime.fromisoformat(_text(properties.get("datetime"), "properties.datetime").replace("Z", "+00:00")), "properties.datetime")
            cloud_cover = _finite(properties.get("eo:cloud_cover"), "eo:cloud_cover", lower=0, upper=100)
            asset_keys = tuple(sorted(_text(key, "asset key") for key, asset in assets.items()
                                      if isinstance(asset, Mapping) and isinstance(asset.get("href"), str) and asset["href"].strip()))
            if len(asset_keys) != len(assets):
                raise ValueError("feature assets are invalid")
        except (TypeError, ValueError) as error:
            raise StacAdapterError("STAC feature is invalid") from error
        if cloud_cover > request.max_cloud_cover:
            raise StacAdapterError("STAC feature exceeds requested cloud cover")
        logical_id = "cdse-s2:" + hashlib.sha256(f"{request.station_id}|{SENTINEL2_L2A}|{item_id}|{_iso(observed_at)}".encode("utf-8")).hexdigest()
        asset_id = "cdse-stac-assets:" + hashlib.sha256(f"{SENTINEL2_L2A}|{item_id}|{'|'.join(asset_keys)}".encode("utf-8")).hexdigest()
        tile = SentinelTileMetadata(SENTINEL2_L2A, item_id, observed_at, cloud_cover, asset_keys, request_url, logical_id)
        observation = CanonicalObservation(
            station_id=request.station_id, metric="sentinel2_tile_cloud_cover_pct", observed_at=observed_at,
            unit="percent", value=cloud_cover, provenance_kind="observed", logical_observation_id=logical_id,
            provider="copernicus_cdse_stac", dataset_id=SENTINEL2_L2A, accessed_at=accessed_at,
            request_url=request_url, asset_id=asset_id, quality_flags=("scope:sentinel2_tile", "estimate:catalog_metadata"),
        )
        return _json_bytes(raw, "STAC feature"), tile, observation


__all__ = ["CDSE_SEARCH_URL", "CdseStacAdapter", "SentinelTileMetadata", "StacAdapterError", "StacHttpResponse",
           "StacSearchRequest", "StacSearchResult"]
