"""Fail-closed, in-memory OGC SensorThings 1.1 Observation reader."""

from __future__ import annotations

import json
import math
import re
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Callable, Mapping
from urllib.error import HTTPError
from urllib.parse import quote, unquote, urlencode, urlsplit
from urllib.request import HTTPRedirectHandler, Request, build_opener

from .observations import CanonicalObservation
from .stations import StationNotFoundError, get_station


UTC = timezone.utc
_SAFE_ID = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:-]{2,80}$")
_INTERVAL_POLICIES = frozenset({"instant_only", "interval_start", "interval_end"})


class SensorThingsAdapterError(RuntimeError):
    """Raised when a SensorThings endpoint or response is unsafe to consume."""


@dataclass(frozen=True)
class SensorThingsHttpResponse:
    status: int
    body: bytes | str | Mapping[str, Any]
    url: str | None
    headers: Mapping[str, str] = ()


def _text(value: object, field: str) -> str:
    if not isinstance(value, str) or not value.strip() or any(ord(character) < 32 for character in value):
        raise ValueError(f"{field} must be a non-empty safe string")
    return value.strip()


def _positive_int(value: object, field: str) -> int:
    if type(value) is not int or value < 1:
        raise ValueError(f"{field} must be a positive integer")
    return value


def _finite(value: object, field: str, *, lower: float | None = None, upper: float | None = None) -> float:
    if isinstance(value, bool):
        raise ValueError(f"{field} must be numeric")
    try:
        number = float(value)
    except (TypeError, ValueError) as error:
        raise ValueError(f"{field} must be numeric") from error
    if not math.isfinite(number) or lower is not None and number < lower or upper is not None and number > upper:
        raise ValueError(f"{field} is outside its finite range")
    return number


def _utc(value: object, field: str) -> datetime:
    if not isinstance(value, datetime) or value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field} must be UTC-aware")
    return value.astimezone(UTC)


def _iso(value: datetime) -> str:
    return value.isoformat().replace("+00:00", "Z")


def _origin(url: str) -> str:
    parsed = urlsplit(url)
    if parsed.scheme != "https" or not parsed.hostname or parsed.username or parsed.password:
        raise ValueError("URL must use HTTPS without userinfo")
    port = f":{parsed.port}" if parsed.port else ""
    return f"https://{parsed.hostname}{port}"


def _base_url(value: object) -> tuple[str, str, str]:
    url = _text(value, "base_url")
    parsed = urlsplit(url)
    if parsed.query or parsed.fragment or parsed.path.endswith("/"):
        raise ValueError("base_url must not include query, fragment, or trailing slash")
    origin = _origin(url)
    if parsed.path in {"", "/"}:
        raise ValueError("base_url must include a versioned path")
    return url, origin, parsed.path


def _json(value: object, limit: int, field: str) -> str:
    try:
        encoded = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False).encode("utf-8")
    except (TypeError, ValueError) as error:
        raise SensorThingsAdapterError(f"invalid_{field}") from error
    if len(encoded) > limit:
        raise SensorThingsAdapterError(f"invalid_{field}")
    return encoded.decode("utf-8")


def _haversine_m(first_lat: float, first_lon: float, second_lat: float, second_lon: float) -> float:
    radians = math.pi / 180.0
    latitude_delta, longitude_delta = (second_lat - first_lat) * radians, (second_lon - first_lon) * radians
    a = math.sin(latitude_delta / 2) ** 2 + math.cos(first_lat * radians) * math.cos(second_lat * radians) * math.sin(longitude_delta / 2) ** 2
    return 12_742_000.0 * math.atan2(math.sqrt(a), math.sqrt(1.0 - a))


@dataclass(frozen=True)
class SensorThingsSourceConfig:
    enabled: bool
    base_url: str
    provider_namespace: str
    owner: str
    license: str
    allowed_origins: frozenset[str]
    base_path: str

    def __post_init__(self) -> None:
        if type(self.enabled) is not bool:
            raise ValueError("enabled must be a boolean")
        base_url, origin, path = _base_url(self.base_url)
        provider = _text(self.provider_namespace, "provider_namespace")
        if not _SAFE_ID.fullmatch(provider):
            raise ValueError("provider_namespace must be URL-safe")
        if isinstance(self.allowed_origins, str | bytes):
            raise ValueError("allowed_origins must be an iterable")
        try:
            origins = frozenset(_origin(_text(item, "allowed_origins item")) for item in self.allowed_origins)
        except TypeError as error:
            raise ValueError("allowed_origins must be an iterable") from error
        if not origins or origin not in origins:
            raise ValueError("allowed_origins must contain the base origin")
        base_path = _text(self.base_path, "base_path")
        if base_path != path or not base_path.startswith("/") or "?" in base_path or "#" in base_path:
            raise ValueError("base_path must exactly match the base_url path")
        object.__setattr__(self, "base_url", base_url)
        object.__setattr__(self, "provider_namespace", provider)
        object.__setattr__(self, "owner", _text(self.owner, "owner"))
        object.__setattr__(self, "license", _text(self.license, "license"))
        object.__setattr__(self, "allowed_origins", origins)


@dataclass(frozen=True)
class DatastreamMapping:
    datastream_id: int
    station_id: str
    metric: str
    unit: str
    observed_property_id: int
    max_location_distance_m: float
    interval_policy: str

    def __post_init__(self) -> None:
        object.__setattr__(self, "datastream_id", _positive_int(self.datastream_id, "datastream_id"))
        object.__setattr__(self, "observed_property_id", _positive_int(self.observed_property_id, "observed_property_id"))
        try:
            station = get_station(self.station_id)
        except StationNotFoundError as error:
            raise ValueError("station_id must be canonical") from error
        metric = _text(self.metric, "metric")
        if not _SAFE_ID.fullmatch(metric):
            raise ValueError("metric must be URL-safe")
        if self.interval_policy not in _INTERVAL_POLICIES:
            raise ValueError("interval_policy is invalid")
        object.__setattr__(self, "station_id", station.station_id)
        object.__setattr__(self, "metric", metric)
        object.__setattr__(self, "unit", _text(self.unit, "unit"))
        object.__setattr__(self, "max_location_distance_m", _finite(self.max_location_distance_m, "max_location_distance_m", lower=0.000001))


@dataclass(frozen=True)
class RejectedSensorThingsObservation:
    observation_id: int | None
    reason: str


@dataclass(frozen=True)
class SensorThingsIngestionResult:
    observations: tuple[CanonicalObservation, ...]
    rejected: tuple[RejectedSensorThingsObservation, ...]
    pages_fetched: int
    ready_for_persistence: bool

    def __post_init__(self) -> None:
        observations, rejected = tuple(self.observations), tuple(self.rejected)
        if any(not isinstance(item, CanonicalObservation) for item in observations) or any(not isinstance(item, RejectedSensorThingsObservation) for item in rejected):
            raise ValueError("invalid SensorThings result")
        if type(self.pages_fetched) is not int or self.pages_fetched < 0 or type(self.ready_for_persistence) is not bool:
            raise ValueError("invalid SensorThings result state")
        if self.ready_for_persistence != (not rejected) or rejected and observations:
            raise ValueError("SensorThings result cannot expose partial candidates")
        object.__setattr__(self, "observations", tuple(sorted(observations, key=lambda item: item.logical_observation_id)))
        object.__setattr__(self, "rejected", tuple(sorted(rejected, key=lambda item: ((item.observation_id or -1), item.reason))))


class _RejectRedirects(HTTPRedirectHandler):
    def redirect_request(self, request, fp, code, message, headers, new_url):  # type: ignore[no-untyped-def]
        raise SensorThingsAdapterError("SensorThings redirects are prohibited")


def _bounded_read(response: Any, max_response_bytes: int) -> bytes:
    body = response.read(max_response_bytes + 1)
    if not isinstance(body, bytes) or len(body) > max_response_bytes:
        raise SensorThingsAdapterError("SensorThings response exceeds configured byte limit")
    return body


def _default_transport(url: str, headers: dict[str, str], timeout: float, max_response_bytes: int) -> SensorThingsHttpResponse:
    """Issue one GET and bound socket reads before allocating an arbitrary body."""

    request = Request(url, headers=headers, method="GET")
    try:
        with build_opener(_RejectRedirects()).open(request, timeout=timeout) as response:
            return SensorThingsHttpResponse(int(response.status), _bounded_read(response, max_response_bytes), response.geturl(), dict(response.headers.items()))
    except HTTPError as error:
        return SensorThingsHttpResponse(error.code, _bounded_read(error, max_response_bytes), error.geturl(), dict(error.headers.items()) if error.headers else {})


Transport = Callable[[str, dict[str, str], float], SensorThingsHttpResponse]


class SensorThingsObservationAdapter:
    """Fetch raw observations only; this class never aggregates or persists them."""

    def __init__(self, *, transport: Transport | None = None, clock: Callable[[], datetime], auth_headers: Callable[[], Mapping[str, str]],
                 user_agent: str, timeout: float, page_size: int, max_pages: int, max_response_bytes: int,
                 max_retries: int, sleeper: Callable[[float], None] = time.sleep) -> None:
        if transport is not None and not callable(transport) or not callable(clock) or not callable(auth_headers) or not callable(sleeper):
            raise ValueError("transport, clock, auth_headers, and sleeper must be callable")
        self._clock, self._auth_headers, self._sleeper = clock, auth_headers, sleeper
        self._user_agent = _text(user_agent, "user_agent")
        self._timeout = _finite(timeout, "timeout", lower=0.000001)
        self._page_size, self._max_pages = _positive_int(page_size, "page_size"), _positive_int(max_pages, "max_pages")
        self._max_response_bytes = _positive_int(max_response_bytes, "max_response_bytes")
        self._transport = transport or (lambda url, headers, request_timeout: _default_transport(url, headers, request_timeout, self._max_response_bytes))
        if type(max_retries) is not int or max_retries < 0:
            raise ValueError("max_retries must be a non-negative integer")
        self._max_retries = max_retries

    def fetch(self, *, source: SensorThingsSourceConfig, mapping: DatastreamMapping, start: datetime, end: datetime) -> SensorThingsIngestionResult:
        if not isinstance(source, SensorThingsSourceConfig) or not isinstance(mapping, DatastreamMapping):
            raise ValueError("source and mapping must be SensorThings configuration values")
        if not source.enabled:
            raise SensorThingsAdapterError("SensorThings source is disabled")
        start, end, accessed_at = _utc(start, "start"), _utc(end, "end"), _utc(self._clock(), "clock result")
        if start >= end:
            raise ValueError("start must precede end")
        endpoint = f"{source.base_url}/Datastreams({mapping.datastream_id})/Observations"
        query = urlencode({
            "$filter": f"phenomenonTime ge {_iso(start)} and phenomenonTime lt {_iso(end)}",
            "$select": "@iot.id,phenomenonTime,result,resultTime,validTime,resultQuality,parameters",
            "$orderby": "phenomenonTime,@iot.id", "$top": str(self._page_size),
            "$expand": "FeatureOfInterest($select=@iot.id,feature),Datastream($select=@iot.id,unitOfMeasurement;$expand=ObservedProperty($select=@iot.id))",
        }, quote_via=quote)
        pending, pages, seen_urls, seen = f"{endpoint}?{query}", 0, set(), {}
        while pending is not None:
            if pages >= self._max_pages or pending in seen_urls:
                raise SensorThingsAdapterError("SensorThings pagination exceeded safe bounds")
            seen_urls.add(pending)
            payload = self._request(pending, source)
            pages += 1
            values, pending = self._page(payload, source)
            for raw in values:
                raw_id = raw.get("@iot.id") if isinstance(raw, Mapping) and type(raw.get("@iot.id")) is int else None
                try:
                    item = self._observation(raw, source, mapping, accessed_at)
                except SensorThingsAdapterError as error:
                    return SensorThingsIngestionResult((), (RejectedSensorThingsObservation(raw_id, str(error)),), pages, False)
                previous = seen.get(item.logical_observation_id)
                if previous is not None:
                    if previous.content_hash != item.content_hash:
                        return SensorThingsIngestionResult((), (RejectedSensorThingsObservation(raw_id, "conflicting_observation_id"),), pages, False)
                    continue
                seen[item.logical_observation_id] = item
        return SensorThingsIngestionResult(tuple(seen.values()), (), pages, True)

    def _request(self, url: str, source: SensorThingsSourceConfig) -> Mapping[str, Any]:
        _safe_url(url, source)
        headers = {"Accept": "application/json", "User-Agent": self._user_agent}
        try:
            supplied = self._auth_headers()
            if not isinstance(supplied, Mapping):
                raise ValueError
            for key, value in supplied.items():
                headers[_text(key, "auth header name")] = _text(value, "auth header value")
        except (TypeError, ValueError):
            raise SensorThingsAdapterError("invalid authentication header configuration") from None
        for attempt in range(self._max_retries + 1):
            try:
                response = self._transport(url, headers, self._timeout)
            except (TimeoutError, OSError):
                if attempt == self._max_retries:
                    raise SensorThingsAdapterError("SensorThings transport failed") from None
                self._sleeper(0.0)
                continue
            if not isinstance(response, SensorThingsHttpResponse) or not isinstance(response.url, str) or response.url != url:
                raise SensorThingsAdapterError("SensorThings response URL is unsafe")
            _safe_url(response.url, source)
            if type(response.status) is not int:
                raise SensorThingsAdapterError("SensorThings response status is invalid")
            if response.status in {429} or 500 <= response.status <= 599:
                if attempt < self._max_retries:
                    self._sleeper(_retry_delay(response.headers))
                    continue
            if response.status != 200:
                raise SensorThingsAdapterError(f"SensorThings HTTP {response.status}")
            raw = response.body
            if isinstance(raw, Mapping):
                raw = _json(raw, self._max_response_bytes, "response").encode("utf-8")
            elif isinstance(raw, str):
                raw = raw.encode("utf-8")
            if not isinstance(raw, bytes) or len(raw) > self._max_response_bytes:
                raise SensorThingsAdapterError("SensorThings response exceeds configured byte limit")
            try:
                payload = json.loads(raw.decode("utf-8"))
            except (UnicodeDecodeError, json.JSONDecodeError) as error:
                raise SensorThingsAdapterError("SensorThings response is not valid JSON") from error
            if not isinstance(payload, Mapping):
                raise SensorThingsAdapterError("SensorThings response must be an object")
            return payload
        raise AssertionError("retry loop must return or raise")

    def _page(self, payload: Mapping[str, Any], source: SensorThingsSourceConfig) -> tuple[list[Mapping[str, Any]], str | None]:
        values = payload.get("value")
        next_link = payload.get("@iot.nextLink")
        if not isinstance(values, list) or any(not isinstance(item, Mapping) for item in values):
            raise SensorThingsAdapterError("SensorThings payload value is invalid")
        if next_link is not None:
            if not isinstance(next_link, str):
                raise SensorThingsAdapterError("SensorThings next link is invalid")
            _safe_url(next_link, source)
        return values, next_link

    def _observation(self, raw: Mapping[str, Any], source: SensorThingsSourceConfig, mapping: DatastreamMapping, accessed_at: datetime) -> CanonicalObservation:
        identifier = raw.get("@iot.id")
        if type(identifier) is not int or identifier < 1:
            raise SensorThingsAdapterError("invalid_observation_id")
        observed_at = _phenomenon_time(raw.get("phenomenonTime"), mapping.interval_policy)
        try:
            value = _finite(raw.get("result"), "result")
            stream = raw.get("Datastream")
            if not isinstance(stream, Mapping) or stream.get("@iot.id") != mapping.datastream_id:
                raise ValueError
            unit = stream.get("unitOfMeasurement")
            property_value = stream.get("ObservedProperty")
            if not isinstance(unit, Mapping) or unit.get("symbol") != mapping.unit or not isinstance(property_value, Mapping) or property_value.get("@iot.id") != mapping.observed_property_id:
                raise ValueError
            feature = raw.get("FeatureOfInterest")
            if not isinstance(feature, Mapping):
                raise ValueError
            latitude, longitude = _feature_coordinates(feature)
        except ValueError as error:
            raise SensorThingsAdapterError("invalid_observation_mapping") from error
        station = get_station(mapping.station_id)
        if _haversine_m(latitude, longitude, station.latitude, station.longitude) > mapping.max_location_distance_m:
            raise SensorThingsAdapterError("invalid_feature_location")
        audits = _audit_flags(raw, self._max_response_bytes if hasattr(self, "_max_response_bytes") else 1)
        return CanonicalObservation(
            station_id=station.station_id, metric=mapping.metric, observed_at=observed_at, unit=mapping.unit, value=value,
            provenance_kind="observed", logical_observation_id=f"sensorthings:{source.provider_namespace}:{mapping.datastream_id}:{identifier}",
            provider=source.provider_namespace, dataset_id=f"datastream:{mapping.datastream_id}:{mapping.observed_property_id}",
            accessed_at=accessed_at, request_url=f"{source.base_url}/Observations({identifier})",
            requested_latitude=station.latitude, requested_longitude=station.longitude, returned_latitude=latitude, returned_longitude=longitude,
            quality_flags=tuple(sorted((f"owner:{source.owner}", f"license:{source.license}", f"datastream:{mapping.datastream_id}", f"observed_property:{mapping.observed_property_id}", *audits))),
        )


def _safe_url(value: object, source: SensorThingsSourceConfig) -> str:
    try:
        url = _text(value, "SensorThings URL")
        parsed = urlsplit(url)
        origin = _origin(url)
        if parsed.fragment or origin not in source.allowed_origins or not _safe_path(parsed.path, source.base_path):
            raise ValueError
    except ValueError as error:
        raise SensorThingsAdapterError("SensorThings URL escaped configured origin/path") from error
    return url


def _safe_path(path: str, base_path: str) -> bool:
    """Validate decoded path segments, including repeated percent encodings."""

    decoded = path
    for _ in range(4):
        if re.search(r"%(?![0-9A-Fa-f]{2})", decoded) or re.search(r"%(?:2[fF]|5[cC]|00)", decoded):
            return False
        next_path = unquote(decoded)
        if next_path == decoded:
            break
        decoded = next_path
    else:
        return False
    if "%" in decoded or "\\" in decoded or "\x00" in decoded or not decoded.startswith("/"):
        return False
    segments = decoded[1:].split("/")
    base_segments = base_path.strip("/").split("/")
    if any(not segment or segment in {".", ".."} for segment in segments):
        return False
    return len(segments) > len(base_segments) and segments[:len(base_segments)] == base_segments


def _retry_delay(headers: object) -> float:
    if not isinstance(headers, Mapping):
        return 0.0
    value = headers.get("Retry-After")
    try:
        delay = float(value)
    except (TypeError, ValueError):
        return 0.0
    return min(30.0, delay) if math.isfinite(delay) and delay > 0 else 0.0


def _parse_instant(value: object, reason: str) -> datetime:
    if not isinstance(value, str) or "T" not in value:
        raise SensorThingsAdapterError(reason)
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as error:
        raise SensorThingsAdapterError(reason) from error
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        raise SensorThingsAdapterError(reason)
    return parsed.astimezone(UTC)


def _phenomenon_time(value: object, policy: str) -> datetime:
    if not isinstance(value, str):
        raise SensorThingsAdapterError("invalid_phenomenon_time")
    if "/" not in value:
        return _parse_instant(value, "invalid_phenomenon_time")
    if policy == "instant_only":
        raise SensorThingsAdapterError("invalid_phenomenon_time")
    parts = value.split("/")
    if len(parts) != 2:
        raise SensorThingsAdapterError("invalid_phenomenon_time")
    start, end = (_parse_instant(part, "invalid_phenomenon_time") for part in parts)
    if start >= end:
        raise SensorThingsAdapterError("invalid_phenomenon_time")
    return start if policy == "interval_start" else end


def _feature_coordinates(feature: Mapping[str, Any]) -> tuple[float, float]:
    geometry = feature.get("feature")
    if not isinstance(geometry, Mapping) or geometry.get("type") != "Point":
        raise ValueError
    coordinates = geometry.get("coordinates")
    if not isinstance(coordinates, list | tuple) or len(coordinates) != 2:
        raise ValueError
    longitude, latitude = _finite(coordinates[0], "longitude", lower=-180, upper=180), _finite(coordinates[1], "latitude", lower=-90, upper=90)
    return latitude, longitude


def _audit_flags(raw: Mapping[str, Any], limit: int) -> tuple[str, ...]:
    flags: list[str] = []
    for key, prefix in (("resultTime", "result_time"), ("validTime", "valid_time")):
        value = raw.get(key)
        if value is not None:
            if key == "resultTime":
                _parse_instant(value, f"invalid_{prefix}")
            else:
                _phenomenon_time(value, "interval_start")
            flags.append(f"{prefix}:{value}")
    for key, prefix in (("resultQuality", "result_quality"), ("parameters", "parameters")):
        flags.append(f"{prefix}:{_json(raw.get(key), limit, prefix)}")
    return tuple(flags)
