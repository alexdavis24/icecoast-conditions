from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime
from typing import Any, Mapping
from urllib.parse import urlencode
from urllib.request import urlopen
import json
from zoneinfo import ZoneInfo

from db import ensure_dates, ensure_schema, get_connection, save_daily_weather, upsert_location


ARCHIVE_API_URL = "https://archive-api.open-meteo.com/v1/archive"


@dataclass(frozen=True)
class LocationSpec:
    slug: str
    name: str
    latitude: float
    longitude: float
    elevation_m: float | None
    timezone: str


@dataclass(frozen=True)
class DailyWeatherRecord:
    observed_date: date
    temp_min_c: float | None
    temp_max_c: float | None
    temp_mean_c: float | None
    precipitation_mm: float | None
    rain_mm: float | None
    snowfall_cm: float | None
    pressure_hpa: float | None
    snow_depth_cm: float | None
    cloud_cover_pct: float | None
    sunshine_duration_min: float | None
    wind_speed_m_s: float | None
    wind_gust_m_s: float | None
    wind_direction_deg: int | None
    weather_code: int | None


class OpenMeteoArchiveClient:
    def fetch_daily_payload(
        self,
        location: LocationSpec,
        start_date: date,
        end_date: date,
    ) -> Mapping[str, Any]:
        params: dict[str, str] = {
            "latitude": str(location.latitude),
            "longitude": str(location.longitude),
            "start_date": start_date.isoformat(),
            "end_date": end_date.isoformat(),
            "daily": ",".join(
                [
                    "temperature_2m_min",
                    "temperature_2m_max",
                    "temperature_2m_mean",
                    "precipitation_sum",
                    "rain_sum",
                    "snowfall_sum",
                    "weather_code",
                    "sunshine_duration",
                    "cloud_cover_mean",
                    "pressure_msl_mean",
                    "wind_speed_10m_mean",
                    "wind_gusts_10m_mean",
                    "wind_direction_10m_dominant",
                ]
            ),
            "hourly": "snow_depth",
            "timezone": location.timezone,
            "temperature_unit": "celsius",
            "wind_speed_unit": "ms",
            "precipitation_unit": "mm",
            "timeformat": "iso8601",
        }
        if location.elevation_m is not None:
            params["elevation"] = str(location.elevation_m)

        url = f"{ARCHIVE_API_URL}?{urlencode(params)}"
        with urlopen(url) as response:
            return json.load(response)


def parse_daily_weather_payload(
    location: LocationSpec,
    payload: Mapping[str, Any],
) -> list[DailyWeatherRecord]:
    daily = payload.get("daily", {})
    daily_times = list(daily.get("time", []))
    snow_depth_by_date = _snow_depth_by_date(payload.get("hourly", {}), location.timezone)

    rows: list[DailyWeatherRecord] = []
    for index, date_string in enumerate(daily_times):
        observed_date = date.fromisoformat(date_string)
        rows.append(
            DailyWeatherRecord(
                observed_date=observed_date,
                temp_min_c=_float_value(daily, "temperature_2m_min", index),
                temp_max_c=_float_value(daily, "temperature_2m_max", index),
                temp_mean_c=_float_value(daily, "temperature_2m_mean", index),
                precipitation_mm=_float_value(daily, "precipitation_sum", index),
                rain_mm=_float_value(daily, "rain_sum", index),
                snowfall_cm=_float_value(daily, "snowfall_sum", index),
                pressure_hpa=_float_value(daily, "pressure_msl_mean", index),
                snow_depth_cm=snow_depth_by_date.get(observed_date),
                cloud_cover_pct=_float_value(daily, "cloud_cover_mean", index),
                sunshine_duration_min=_seconds_to_minutes(
                    _float_value(daily, "sunshine_duration", index)
                ),
                wind_speed_m_s=_float_value(daily, "wind_speed_10m_mean", index),
                wind_gust_m_s=_float_value(daily, "wind_gusts_10m_mean", index),
                wind_direction_deg=_int_value(daily, "wind_direction_10m_dominant", index),
                weather_code=_int_value(daily, "weather_code", index),
            )
        )
    return rows


def ingest_historical_daily_weather(
    location: LocationSpec,
    start_date: date,
    end_date: date,
    client: OpenMeteoArchiveClient | None = None,
) -> list[DailyWeatherRecord]:
    archive_client = client or OpenMeteoArchiveClient()
    payload = archive_client.fetch_daily_payload(location, start_date, end_date)
    rows = parse_daily_weather_payload(location, payload)

    with get_connection() as connection:
        ensure_schema(connection)
        location_id = upsert_location(location, connection)
        ensure_dates((row.observed_date for row in rows), connection)
        for row in rows:
            save_daily_weather(location_id, row, connection)
        connection.commit()

    return rows


def _float_value(values: Mapping[str, Any], key: str, index: int) -> float | None:
    series = values.get(key)
    if series is None:
        return None
    value = series[index]
    return None if value is None else float(value)


def _int_value(values: Mapping[str, Any], key: str, index: int) -> int | None:
    series = values.get(key)
    if series is None:
        return None
    value = series[index]
    return None if value is None else int(value)


def _seconds_to_minutes(value: float | None) -> float | None:
    if value is None:
        return None
    return value / 60.0


def _snow_depth_by_date(
    hourly: Mapping[str, Any],
    timezone: str,
) -> dict[date, float]:
    snow_depth_series = hourly.get("snow_depth", [])
    time_series = hourly.get("time", [])
    values: dict[date, float] = {}
    for time_value, snow_depth in zip(time_series, snow_depth_series):
        if snow_depth is None:
            continue
        timestamp = datetime.fromisoformat(str(time_value))
        if timestamp.tzinfo is not None:
            timestamp = timestamp.astimezone(ZoneInfo(timezone))
        values[timestamp.date()] = float(snow_depth) * 100.0
    return values
