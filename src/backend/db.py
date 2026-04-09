from __future__ import annotations

from collections.abc import Iterator
from contextlib import contextmanager
import os
from pathlib import Path
from datetime import date, datetime
from typing import Any, Iterable
from urllib.parse import urlsplit, urlunsplit

import psycopg
from dotenv import load_dotenv

from schema import SCHEMA_STATEMENTS, calendar_row_for, unique_sorted_dates


ENV_FILE = Path(__file__).resolve().parents[2] / ".env"


def read_env_file(path: Path) -> dict[str, str]:
    values: dict[str, str] = {}
    if not path.exists():
        return values

    for raw_line in path.read_text().splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        values[key.strip()] = value.strip().strip('"').strip("'")

    return values


load_dotenv(ENV_FILE)
for key, value in read_env_file(ENV_FILE).items():
    os.environ.setdefault(key, value)


DATABASE_URL = os.environ["DATABASE_URL"]


@contextmanager
def get_connection() -> Iterator[psycopg.Connection]:
    with _connect_with_localhost_fallback(DATABASE_URL) as connection:
        yield connection


def _connect_with_localhost_fallback(database_url: str) -> psycopg.Connection:
    try:
        return psycopg.connect(database_url)
    except psycopg.OperationalError as exc:
        fallback_url = _localhost_fallback_url(database_url)
        if fallback_url is None or not _looks_like_host_resolution_failure(exc):
            raise
        return psycopg.connect(fallback_url)


def _localhost_fallback_url(database_url: str) -> str | None:
    parts = urlsplit(database_url)
    if parts.hostname != "postgres":
        return None

    netloc = ""
    if parts.username is not None:
        netloc += parts.username
        if parts.password is not None:
            netloc += f":{parts.password}"
        netloc += "@"
    netloc += "localhost"
    if parts.port is not None:
        netloc += f":{parts.port}"

    return urlunsplit((parts.scheme, netloc, parts.path, parts.query, parts.fragment))


def _looks_like_host_resolution_failure(exc: BaseException) -> bool:
    message = str(exc).lower()
    return "resolve host" in message or "name or service not known" in message or "temporary failure in name resolution" in message


def initialize_database() -> None:
    ensure_schema()
    with get_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS startup_heartbeat (
                    id BIGSERIAL PRIMARY KEY,
                    inserted_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
                )
                """
            )
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS frontend_messages (
                    id BIGSERIAL PRIMARY KEY,
                    body TEXT NOT NULL,
                    inserted_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
                )
                """
            )
            cursor.execute("INSERT INTO startup_heartbeat DEFAULT VALUES")
        connection.commit()


def check_database() -> None:
    with get_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")


def ensure_schema(connection: psycopg.Connection | None = None) -> None:
    should_commit = connection is None
    if connection is None:
        with get_connection() as connection:
            _ensure_schema(connection)
            connection.commit()
        return

    _ensure_schema(connection)
    if should_commit:
        connection.commit()


def _ensure_schema(connection: psycopg.Connection) -> None:
    with connection.cursor() as cursor:
        for statement in SCHEMA_STATEMENTS:
            cursor.execute(statement)


def ensure_dates(dates: Iterable[date], connection: psycopg.Connection | None = None) -> None:
    values = unique_sorted_dates(dates)
    if not values:
        return

    should_commit = connection is None
    if connection is None:
        with get_connection() as connection:
            _ensure_dates(connection, values)
            connection.commit()
        return

    _ensure_dates(connection, values)
    if should_commit:
        connection.commit()


def _ensure_dates(connection: psycopg.Connection, values: list[date]) -> None:
    with connection.cursor() as cursor:
        for value in values:
            cursor.execute(
                "INSERT INTO dates (date, year, month, day, day_of_week, day_of_year, week_of_year, is_weekend) "
                "VALUES (%s, %s, %s, %s, %s, %s, %s, %s) ON CONFLICT (date) DO NOTHING",
                calendar_row_for(value),
            )


def upsert_location(location: Any, connection: psycopg.Connection | None = None) -> int:
    should_commit = connection is None
    if connection is None:
        with get_connection() as connection:
            location_id = _upsert_location(connection, location)
            connection.commit()
            return location_id

    location_id = _upsert_location(connection, location)
    if should_commit:
        connection.commit()
    return location_id


def _upsert_location(connection: psycopg.Connection, location: Any) -> int:
    with connection.cursor() as cursor:
        cursor.execute(
            """
            INSERT INTO locations (
                slug,
                name,
                latitude,
                longitude,
                elevation_m,
                timezone
            )
            VALUES (%s, %s, %s, %s, %s, %s)
            ON CONFLICT (slug) DO UPDATE SET
                name = EXCLUDED.name,
                latitude = EXCLUDED.latitude,
                longitude = EXCLUDED.longitude,
                elevation_m = EXCLUDED.elevation_m,
                timezone = EXCLUDED.timezone,
                updated_at = NOW()
            RETURNING id
            """,
            (
                location.slug,
                location.name,
                location.latitude,
                location.longitude,
                location.elevation_m,
                location.timezone,
            ),
        )
        row = cursor.fetchone()
        return int(row[0]) if row is not None else 0


def save_daily_weather(location_id: int, record: Any, connection: psycopg.Connection | None = None) -> None:
    should_commit = connection is None
    if connection is None:
        with get_connection() as connection:
            _save_daily_weather(connection, location_id, record)
            connection.commit()
        return

    _save_daily_weather(connection, location_id, record)
    if should_commit:
        connection.commit()


def _save_daily_weather(connection: psycopg.Connection, location_id: int, record: Any) -> None:
    with connection.cursor() as cursor:
        cursor.execute(
            """
            INSERT INTO daily_weather (
                location_id,
                observed_date,
                temp_min_c,
                temp_max_c,
                temp_mean_c,
                precipitation_mm,
                rain_mm,
                snowfall_cm,
                pressure_hpa,
                snow_depth_cm,
                cloud_cover_pct,
                sunshine_duration_min,
                wind_speed_m_s,
                wind_gust_m_s,
                wind_direction_deg,
                weather_code
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (location_id, observed_date) DO UPDATE SET
                temp_min_c = EXCLUDED.temp_min_c,
                temp_max_c = EXCLUDED.temp_max_c,
                temp_mean_c = EXCLUDED.temp_mean_c,
                precipitation_mm = EXCLUDED.precipitation_mm,
                rain_mm = EXCLUDED.rain_mm,
                snowfall_cm = EXCLUDED.snowfall_cm,
                pressure_hpa = EXCLUDED.pressure_hpa,
                snow_depth_cm = EXCLUDED.snow_depth_cm,
                cloud_cover_pct = EXCLUDED.cloud_cover_pct,
                sunshine_duration_min = EXCLUDED.sunshine_duration_min,
                wind_speed_m_s = EXCLUDED.wind_speed_m_s,
                wind_gust_m_s = EXCLUDED.wind_gust_m_s,
                wind_direction_deg = EXCLUDED.wind_direction_deg,
                weather_code = EXCLUDED.weather_code,
                updated_at = NOW()
            """,
            (
                location_id,
                record.observed_date,
                record.temp_min_c,
                record.temp_max_c,
                record.temp_mean_c,
                record.precipitation_mm,
                record.rain_mm,
                record.snowfall_cm,
                record.pressure_hpa,
                record.snow_depth_cm,
                record.cloud_cover_pct,
                record.sunshine_duration_min,
                record.wind_speed_m_s,
                record.wind_gust_m_s,
                record.wind_direction_deg,
                record.weather_code,
            ),
        )


def create_forecast_run(
    location_id: int,
    issued_at: datetime,
    connection: psycopg.Connection | None = None,
) -> int:
    should_commit = connection is None
    if connection is None:
        with get_connection() as connection:
            forecast_run_id = _create_forecast_run(connection, location_id, issued_at)
            connection.commit()
            return forecast_run_id

    forecast_run_id = _create_forecast_run(connection, location_id, issued_at)
    if should_commit:
        connection.commit()
    return forecast_run_id


def _create_forecast_run(connection: psycopg.Connection, location_id: int, issued_at: datetime) -> int:
    with connection.cursor() as cursor:
        cursor.execute(
            "INSERT INTO forecast_runs (location_id, issued_at) VALUES (%s, %s) RETURNING id",
            (location_id, issued_at),
        )
        row = cursor.fetchone()
        return int(row[0]) if row is not None else 0


def save_forecast_daily(
    forecast_run_id: int,
    record: Any,
    connection: psycopg.Connection | None = None,
) -> None:
    should_commit = connection is None
    if connection is None:
        with get_connection() as connection:
            _save_forecast_daily(connection, forecast_run_id, record)
            connection.commit()
        return

    _save_forecast_daily(connection, forecast_run_id, record)
    if should_commit:
        connection.commit()


def _save_forecast_daily(connection: psycopg.Connection, forecast_run_id: int, record: Any) -> None:
    with connection.cursor() as cursor:
        cursor.execute(
            """
            INSERT INTO forecast_daily (
                forecast_run_id,
                target_date,
                temp_min_c,
                temp_max_c,
                temp_mean_c,
                precipitation_mm,
                rain_mm,
                snowfall_cm,
                pressure_hpa,
                snow_depth_cm,
                cloud_cover_pct,
                sunshine_duration_min,
                wind_speed_m_s,
                wind_gust_m_s,
                wind_direction_deg,
                weather_code
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (forecast_run_id, target_date) DO UPDATE SET
                temp_min_c = EXCLUDED.temp_min_c,
                temp_max_c = EXCLUDED.temp_max_c,
                temp_mean_c = EXCLUDED.temp_mean_c,
                precipitation_mm = EXCLUDED.precipitation_mm,
                rain_mm = EXCLUDED.rain_mm,
                snowfall_cm = EXCLUDED.snowfall_cm,
                pressure_hpa = EXCLUDED.pressure_hpa,
                snow_depth_cm = EXCLUDED.snow_depth_cm,
                cloud_cover_pct = EXCLUDED.cloud_cover_pct,
                sunshine_duration_min = EXCLUDED.sunshine_duration_min,
                wind_speed_m_s = EXCLUDED.wind_speed_m_s,
                wind_gust_m_s = EXCLUDED.wind_gust_m_s,
                wind_direction_deg = EXCLUDED.wind_direction_deg,
                weather_code = EXCLUDED.weather_code
            """,
            (
                forecast_run_id,
                record.target_date,
                record.temp_min_c,
                record.temp_max_c,
                record.temp_mean_c,
                record.precipitation_mm,
                record.rain_mm,
                record.snowfall_cm,
                record.pressure_hpa,
                record.snow_depth_cm,
                record.cloud_cover_pct,
                record.sunshine_duration_min,
                record.wind_speed_m_s,
                record.wind_gust_m_s,
                record.wind_direction_deg,
                record.weather_code,
            ),
        )


def save_dummy_message() -> int:
    with get_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS frontend_messages (
                    id BIGSERIAL PRIMARY KEY,
                    body TEXT NOT NULL,
                    inserted_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
                )
                """
            )
            cursor.execute(
                "INSERT INTO frontend_messages (body) VALUES (%s) RETURNING id",
                ("Hello from the frontend",),
            )
            row = cursor.fetchone()
            message_id = int(row[0]) if row is not None else 0
        connection.commit()
    return message_id


def get_latest_observed_date(location_id: int, connection: psycopg.Connection | None = None) -> date | None:
    if connection is None:
        with get_connection() as connection:
            return _get_latest_observed_date(connection, location_id)
    return _get_latest_observed_date(connection, location_id)


def _get_latest_observed_date(connection: psycopg.Connection, location_id: int) -> date | None:
    with connection.cursor() as cursor:
        cursor.execute(
            "SELECT MAX(observed_date) FROM daily_weather WHERE location_id = %s",
            (location_id,),
        )
        row = cursor.fetchone()
        return row[0] if row and row[0] else None
