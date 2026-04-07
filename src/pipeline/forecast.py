from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, timezone
from typing import Any, Mapping
from urllib.parse import urlencode
from urllib.request import urlopen
import json
from zoneinfo import ZoneInfo

from db import (
    create_forecast_run,
    ensure_dates,
    get_connection,
    save_forecast_daily,
    upsert_location,
)
from pipeline.openmeteo import LocationSpec


FORECAST_API_URL = "https://api.open-meteo.com/v1/forecast"


@dataclass(frozen=True)
class ForecastDailyRecord:
    target_date: date
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


class OpenMeteoForecastClient:
    def fetch_forecast_payload(
        self,
        location: LocationSpec,
        forecast_days: int = 16,
    ) -> Mapping[str, Any]:
        params: dict[str, str] = {
            "latitude": str(location.latitude),
            "longitude": str(location.longitude),
            "forecast_days": str(forecast_days),
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

        url = f"{FORECAST_API_URL}?{urlencode(params)}"
        with urlopen(url) as response:
            return json.load(response)


def parse_forecast_daily_payload(
    location: LocationSpec,
    payload: Mapping[str, Any],
    *,
    issued_at: datetime,
) -> list[ForecastDailyRecord]:
    if issued_at.tzinfo is None:
        raise ValueError("issued_at must be timezone-aware")

    daily = payload.get("daily", {})
    daily_times = list(daily.get("time", []))
    snow_depth_by_date = _snow_depth_by_date(payload.get("hourly", {}), location.timezone)

    rows: list[ForecastDailyRecord] = []
    for index, date_string in enumerate(daily_times):
        target_date = date.fromisoformat(date_string)
        rows.append(
            ForecastDailyRecord(
                target_date=target_date,
                temp_min_c=_float_value(daily, "temperature_2m_min", index),
                temp_max_c=_float_value(daily, "temperature_2m_max", index),
                temp_mean_c=_float_value(daily, "temperature_2m_mean", index),
                precipitation_mm=_float_value(daily, "precipitation_sum", index),
                rain_mm=_float_value(daily, "rain_sum", index),
                snowfall_cm=_float_value(daily, "snowfall_sum", index),
                pressure_hpa=_float_value(daily, "pressure_msl_mean", index),
                snow_depth_cm=snow_depth_by_date.get(target_date),
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


def fetch_and_ingest_forecast_daily(
    location: LocationSpec,
    *,
    forecast_days: int = 16,
    client: OpenMeteoForecastClient | None = None,
    issued_at: datetime | None = None,
) -> int:
    forecast_client = client or OpenMeteoForecastClient()
    payload = forecast_client.fetch_forecast_payload(location, forecast_days=forecast_days)
    issued = issued_at or datetime.now(tz=timezone.utc)
    records = parse_forecast_daily_payload(location, payload, issued_at=issued)
    return ingest_forecast_daily(location, issued, records)


def ingest_forecast_daily(
    location: LocationSpec,
    issued_at: datetime,
    records: list[ForecastDailyRecord],
) -> int:
    if not records:
        return 0

    with get_connection() as connection:
        location_id = upsert_location(location, connection)
        ensure_dates((record.target_date for record in records), connection)
        forecast_run_id = create_forecast_run(location_id, issued_at, connection)
        for record in records:
            save_forecast_daily(forecast_run_id, record, connection)
        connection.commit()

    return forecast_run_id


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


def _snow_depth_by_date(hourly: Mapping[str, Any], timezone: str) -> dict[date, float]:
    snow_depth_series = hourly.get("snow_depth", [])
    time_series = hourly.get("time", [])
    values: dict[date, float] = {}
    tz = ZoneInfo(timezone)
    for time_value, snow_depth in zip(time_series, snow_depth_series):
        if snow_depth is None:
            continue
        timestamp = datetime.fromisoformat(str(time_value))
        if timestamp.tzinfo is None:
            timestamp = timestamp.replace(tzinfo=tz)
        else:
            timestamp = timestamp.astimezone(tz)
        values[timestamp.date()] = round(float(snow_depth) * 100.0, 1)
    return values
