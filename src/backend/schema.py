from __future__ import annotations

from datetime import date
from typing import Iterable


SCHEMA_STATEMENTS: tuple[str, ...] = (
    """
    CREATE TABLE IF NOT EXISTS locations (
        id BIGSERIAL PRIMARY KEY,
        slug TEXT NOT NULL UNIQUE,
        name TEXT NOT NULL,
        latitude DOUBLE PRECISION NOT NULL,
        longitude DOUBLE PRECISION NOT NULL,
        elevation_m DOUBLE PRECISION,
        timezone TEXT NOT NULL,
        created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
        updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS dates (
        date DATE PRIMARY KEY,
        year SMALLINT NOT NULL,
        month SMALLINT NOT NULL,
        day SMALLINT NOT NULL,
        day_of_week SMALLINT NOT NULL,
        day_of_year SMALLINT NOT NULL,
        week_of_year SMALLINT NOT NULL,
        is_weekend BOOLEAN NOT NULL
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS daily_weather (
        id BIGSERIAL PRIMARY KEY,
        location_id BIGINT NOT NULL REFERENCES locations(id),
        observed_date DATE NOT NULL REFERENCES dates(date),
        temp_min_c NUMERIC,
        temp_max_c NUMERIC,
        temp_mean_c NUMERIC,
        precipitation_mm NUMERIC,
        rain_mm NUMERIC,
        snowfall_cm NUMERIC,
        pressure_hpa NUMERIC,
        snow_depth_cm NUMERIC,
        cloud_cover_pct NUMERIC,
        sunshine_duration_min NUMERIC,
        wind_speed_m_s NUMERIC,
        wind_gust_m_s NUMERIC,
        wind_direction_deg SMALLINT,
        weather_code INTEGER,
        created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
        updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
        UNIQUE (location_id, observed_date)
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS forecast_runs (
        id BIGSERIAL PRIMARY KEY,
        location_id BIGINT NOT NULL REFERENCES locations(id),
        issued_at TIMESTAMPTZ NOT NULL,
        created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS forecast_daily (
        id BIGSERIAL PRIMARY KEY,
        forecast_run_id BIGINT NOT NULL REFERENCES forecast_runs(id),
        target_date DATE NOT NULL REFERENCES dates(date),
        temp_min_c NUMERIC,
        temp_max_c NUMERIC,
        temp_mean_c NUMERIC,
        precipitation_mm NUMERIC,
        rain_mm NUMERIC,
        snowfall_cm NUMERIC,
        pressure_hpa NUMERIC,
        snow_depth_cm NUMERIC,
        cloud_cover_pct NUMERIC,
        sunshine_duration_min NUMERIC,
        wind_speed_m_s NUMERIC,
        wind_gust_m_s NUMERIC,
        wind_direction_deg SMALLINT,
        weather_code INTEGER,
        created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
        UNIQUE (forecast_run_id, target_date)
    )
    """,
)


def calendar_row_for(day: date) -> tuple[date, int, int, int, int, int, int, bool]:
    iso_calendar = day.isocalendar()
    return (
        day,
        day.year,
        day.month,
        day.day,
        day.isoweekday(),
        day.timetuple().tm_yday,
        iso_calendar.week,
        day.isoweekday() >= 6,
    )


def unique_sorted_dates(values: Iterable[date]) -> list[date]:
    return sorted(set(values))
