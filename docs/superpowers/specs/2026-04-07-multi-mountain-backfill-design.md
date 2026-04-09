# Design Spec: Multi-Mountain Historical Backfill

**Author:** Gemini CLI
**Date:** 2026-04-07
**Status:** Draft

## Problem Statement
The current pipeline only supports backfilling historical weather data for a single location (Stowe, VT) and does not have a mechanism to skip dates that already exist in the database. Adding more mountains requires a scalable way to manage location metadata and an efficient way to backfill data without redundant API calls.

## Proposed Solution
1. **CSV-Based Location Management**: Move all mountain metadata (coordinates, elevation, etc.) to a CSV file.
2. **Gap-Aware Backfill Logic**: Implement logic to identify missing dates in the database for each location and only fetch those from the Open-Meteo API.
3. **CLI Integration**: Update the `icecoast-pipeline backfill` command to support processing all locations by default.

## Architecture

### 1. Data Layer
- **`src/pipeline/locations.csv`**: A single source of truth for mountain metadata.
- **`src/pipeline/locations.py`**: A module to load and provide `LocationSpec` objects from the CSV.

### 2. Business Logic
- **`src/pipeline/backfill.py`**:
    - `get_missing_dates(location_id: int, start_date: date, end_date: date) -> list[date]`: Identifies gaps in the `daily_weather` table.
    - `backfill_location(location: LocationSpec, start_date: date, end_date: date)`: Fetches missing data for a specific location.
    - `backfill_all_locations(start_date: date, end_date: date)`: Iterates through all locations in the CSV.

### 3. CLI
- **`src/pipeline/cli.py`**:
    - Update `backfill` command:
        - `--location`: Defaults to "all" (loads all from CSV).
        - `--start`: Defaults to `2024-01-01`.
        - `--end`: Defaults to today.

## Technical Details

### CSV Structure
```csv
slug,name,latitude,longitude,elevation_m,timezone
stowe-vt,"Stowe, Vermont",44.4654,-72.6874,486,America/New_York
wildcat-nh,"Wildcat Mountain",44.2631,-71.2383,914,America/New_York
black-mountain-nh,"Black Mountain",44.2253,-71.1722,548,America/New_York
attitash-nh,"Attitash Mountain",44.0822,-71.2297,450,America/New_York
jay-peak-vt,"Jay Peak",44.9242,-72.5256,865,America/New_York
```

### Gap Detection Strategy
We will query the `daily_weather` table for the requested `location_id` and `date_range`. Dates that do not have a record will be collected and grouped into ranges (if possible) to minimize API calls, or simply fetched as a single range covering the first missing date to the last missing date (since the API handles redundant data gracefully due to our `ON CONFLICT` logic, but we want to avoid unnecessary requests).

**Optimized Approach**:
1. Find the latest `observed_date` for the location.
2. If `latest_date < requested_end_date`, fetch from `latest_date + 1` to `requested_end_date`.
3. If no data exists at all, fetch from `requested_start_date` to `requested_end_date`.

## Testing Plan
1. **Unit Tests**:
    - Test CSV loader in `locations.py`.
    - Test gap detection logic with mocked database states.
2. **Integration Tests**:
    - Verify `icecoast-pipeline backfill --location all` correctly populates multiple locations.
    - Verify subsequent runs of the same command do not trigger API calls (by mocking the API client).

## Open Questions / Risks
- **Open-Meteo Rate Limits**: For 5+ mountains, we are well within the free tier (10,000 daily requests), but we should monitor this.
- **Incomplete Historical Data**: Some mountains might not have data for all dates in 2024. The API handles this by returning `null` values, which our DB schema supports.
