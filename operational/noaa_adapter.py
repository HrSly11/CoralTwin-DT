"""Small, testable NOAA Coral Reef Watch ERDDAP point-query adapter."""

from __future__ import annotations

import json
import math
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Callable, Mapping
from urllib.error import HTTPError, URLError
from urllib.parse import quote
from urllib.request import Request, urlopen


BASE_URL = "https://coastwatch.noaa.gov/erddap"
SOURCE = "noaa_crw_erddap"
USER_AGENT = "CoralTwin-DT/1.0 (operational NOAA CRW synchronizer)"
FILL_VALUE = -327.68


class AdapterError(RuntimeError):
    """The remote response or transport could not satisfy the adapter contract."""


class NoDataError(AdapterError):
    """The requested point has no usable observation."""


@dataclass(frozen=True)
class ProductDefinition:
    dataset_id: str
    variable: str
    unit: str


PRODUCTS: Mapping[str, ProductDefinition] = {
    "sst": ProductDefinition("noaacrwsstDaily", "analysed_sst", "degree_C"),
    "dhw": ProductDefinition("noaacrwdhwDaily", "degree_heating_week", "degree_Celsius_weeks"),
}


@dataclass(frozen=True)
class ProductObservation:
    station_id: str
    product: str
    observed_at: datetime
    requested_latitude: float
    requested_longitude: float
    returned_latitude: float
    returned_longitude: float
    value: float
    unit: str
    source: str
    dataset_id: str
    request_url: str
    accessed_at: datetime


Transport = Callable[[str, dict[str, str], float], bytes | str | Mapping[str, Any]]


def _default_transport(url: str, headers: dict[str, str], timeout: float) -> bytes:
    request = Request(url, headers=headers)
    with urlopen(request, timeout=timeout) as response:  # nosec B310 - fixed NOAA base URL
        return response.read()


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


class NOAAErddapAdapter:
    """Fetch CRW SST/DHW cells through ERDDAP with bounded transient retries."""

    def __init__(
        self,
        transport: Transport | None = None,
        sleeper: Callable[[float], None] | None = None,
        *,
        retries: int = 2,
        backoff_seconds: float = 0.5,
        timeout: float = 15.0,
        clock: Callable[[], datetime] = _utc_now,
    ) -> None:
        if retries < 0:
            raise ValueError("retries must be non-negative")
        if backoff_seconds < 0:
            raise ValueError("backoff_seconds must be non-negative")
        self._transport = transport or _default_transport
        self._sleeper = sleeper or time.sleep
        self._retries = retries
        self._backoff_seconds = backoff_seconds
        self._timeout = timeout
        self._clock = clock

    def build_request_url(self, product: str, latitude: float, longitude: float) -> str:
        definition = self._definition_for(product)
        query = f"{definition.variable}[(last)][({latitude})][({longitude})]"
        encoded_query = quote(query, safe="")
        return f"{BASE_URL}/griddap/{definition.dataset_id}.json?{encoded_query}"

    def fetch(self, station_id: str, product: str, latitude: float, longitude: float) -> ProductObservation:
        definition = self._definition_for(product)
        request_url = self.build_request_url(product, latitude, longitude)
        body = self._request_with_retries(request_url)
        payload = self._decode_payload(body)
        return self._parse_observation(
            payload=payload,
            station_id=station_id,
            product=product,
            definition=definition,
            requested_latitude=float(latitude),
            requested_longitude=float(longitude),
            request_url=request_url,
        )

    def _definition_for(self, product: str) -> ProductDefinition:
        try:
            return PRODUCTS[product]
        except KeyError as error:
            raise AdapterError(f"Unsupported NOAA product: {product}") from error

    def _request_with_retries(self, request_url: str) -> bytes | str | Mapping[str, Any]:
        headers = {"Accept": "application/json", "User-Agent": USER_AGENT}
        for attempt in range(self._retries + 1):
            try:
                return self._transport(request_url, headers, self._timeout)
            except HTTPError as error:
                retryable = error.code == 429 or 500 <= error.code <= 599
                if not retryable:
                    raise AdapterError(f"NOAA HTTP {error.code}") from error
                last_error: Exception = error
            except (URLError, TimeoutError) as error:
                last_error = error

            if attempt == self._retries:
                raise AdapterError("NOAA request failed after bounded retries") from last_error
            self._sleeper(self._backoff_seconds * (2**attempt))
        raise AssertionError("unreachable")

    @staticmethod
    def _decode_payload(body: bytes | str | Mapping[str, Any]) -> Mapping[str, Any]:
        if isinstance(body, Mapping):
            return body
        try:
            decoded = body.decode("utf-8") if isinstance(body, bytes) else body
            payload = json.loads(decoded)
        except (UnicodeDecodeError, json.JSONDecodeError, TypeError) as error:
            raise AdapterError("NOAA response is not valid JSON") from error
        if not isinstance(payload, Mapping):
            raise AdapterError("NOAA JSON response must be an object")
        return payload

    def _parse_observation(
        self,
        *,
        payload: Mapping[str, Any],
        station_id: str,
        product: str,
        definition: ProductDefinition,
        requested_latitude: float,
        requested_longitude: float,
        request_url: str,
    ) -> ProductObservation:
        table = payload.get("table")
        if not isinstance(table, Mapping):
            raise AdapterError("NOAA JSON response has no table object")
        column_names = table.get("columnNames")
        column_units = table.get("columnUnits")
        rows = table.get("rows")
        if not isinstance(column_names, list) or not isinstance(column_units, list) or not isinstance(rows, list):
            raise AdapterError("NOAA table schema is malformed")
        required = ("time", "latitude", "longitude", definition.variable)
        if any(name not in column_names for name in required) or len(column_units) != len(column_names):
            raise AdapterError("NOAA table columns do not contain the requested point fields")
        if not rows:
            raise NoDataError("NOAA returned no rows for requested point")
        row = rows[0]
        if not isinstance(row, list) or len(row) != len(column_names):
            raise AdapterError("NOAA table row does not match its schema")
        values = dict(zip(column_names, row, strict=True))
        units = dict(zip(column_names, column_units, strict=True))
        value = self._usable_value(values[definition.variable])
        observed_at = self._parse_timestamp(values["time"])
        try:
            returned_latitude = float(values["latitude"])
            returned_longitude = float(values["longitude"])
        except (TypeError, ValueError) as error:
            raise AdapterError("NOAA returned invalid grid coordinates") from error
        if not math.isfinite(returned_latitude) or not math.isfinite(returned_longitude):
            raise AdapterError("NOAA returned non-finite grid coordinates")
        unit = units[definition.variable]
        if not isinstance(unit, str) or not unit:
            raise AdapterError("NOAA response has no unit for requested product")
        return ProductObservation(
            station_id=station_id,
            product=product,
            observed_at=observed_at,
            requested_latitude=requested_latitude,
            requested_longitude=requested_longitude,
            returned_latitude=returned_latitude,
            returned_longitude=returned_longitude,
            value=value,
            unit=unit,
            source=SOURCE,
            dataset_id=definition.dataset_id,
            request_url=request_url,
            accessed_at=self._clock(),
        )

    @staticmethod
    def _usable_value(raw_value: Any) -> float:
        if raw_value is None:
            raise NoDataError("NOAA returned a null observation")
        try:
            value = float(raw_value)
        except (TypeError, ValueError) as error:
            raise AdapterError("NOAA observation is not numeric") from error
        if not math.isfinite(value) or value == FILL_VALUE:
            raise NoDataError("NOAA returned a missing observation")
        return value

    @staticmethod
    def _parse_timestamp(raw_value: Any) -> datetime:
        if not isinstance(raw_value, str):
            raise AdapterError("NOAA observation timestamp is invalid")
        try:
            timestamp = datetime.fromisoformat(raw_value.replace("Z", "+00:00"))
        except ValueError as error:
            raise AdapterError("NOAA observation timestamp is invalid") from error
        if timestamp.tzinfo is None:
            timestamp = timestamp.replace(tzinfo=timezone.utc)
        return timestamp.astimezone(timezone.utc)
