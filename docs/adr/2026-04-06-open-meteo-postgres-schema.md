# ADR: Open-Meteo Weather Schema For Ski Conditions

## Status

Accepted

## Context

We need to ingest Open-Meteo data for Stowe, Vermont into Postgres, starting with daily historical weather and later adding forecast snapshots. The database should stay small, support multiple locations, and avoid storing raw API payloads.

## Decision

Use a normalized daily schema with:

- `locations` for stable place metadata
- `dates` as a calendar dimension
- `daily_weather` for curated historical daily observations
- `forecast_runs` for forecast snapshot history
- `forecast_daily` for per-date forecast values tied to a run

For the initial historical load:

- store daily temperature, precipitation, pressure, cloud cover, sunshine, wind, weather code, rain, and snowfall
- derive `snow_depth_cm` from hourly `snow_depth` by taking the last available local-hour value for each day
- store sunshine duration in minutes
- store barometric pressure as mean sea level pressure in hPa
- do not store raw JSON payloads
- do not store a separate precipitation type field yet

## Consequences

- The schema stays compact and queryable.
- Historical data and forecast snapshots can be compared by date without overwriting previous forecast runs.
- Location and calendar metadata are reusable across all weather records.
- We may need to extend the schema later if we decide to store hourly data or raw source payloads.
