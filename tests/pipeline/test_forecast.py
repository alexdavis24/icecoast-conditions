from __future__ import annotations

from datetime import date, datetime, timezone

from pipeline.forecast import LocationSpec, parse_forecast_daily_payload


def test_parse_forecast_daily_payload_maps_values_and_derived_snow_depth():
    location = LocationSpec(
        slug="stowe-vt",
        name="Stowe, Vermont",
        latitude=44.4654,
        longitude=-72.6874,
        elevation_m=486,
        timezone="America/New_York",
    )
    payload = {
        "daily": {
            "time": ["2026-04-06", "2026-04-07"],
            "weather_code": [3, 61],
            "temperature_2m_min": [-2.0, 0.0],
            "temperature_2m_max": [6.0, 7.5],
            "temperature_2m_mean": [2.0, 3.5],
            "precipitation_sum": [0.0, 4.0],
            "rain_sum": [0.0, 4.0],
            "snowfall_sum": [0.0, 0.0],
            "pressure_msl_mean": [1018.0, 1012.0],
            "cloud_cover_mean": [25.0, 90.0],
            "sunshine_duration": [18000, 3600],
            "wind_speed_10m_mean": [4.0, 8.0],
            "wind_gusts_10m_mean": [7.0, 14.0],
            "wind_direction_10m_dominant": [200, 150],
        },
        "hourly": {
            "time": [
                "2026-04-06T00:00",
                "2026-04-06T23:00",
                "2026-04-07T00:00",
                "2026-04-07T23:00",
            ],
            "snow_depth": [0.33, 0.30, 0.30, 0.28],
        },
    }

    issued_at = datetime(2026, 4, 6, 12, 0, tzinfo=timezone.utc)
    rows = parse_forecast_daily_payload(location, payload, issued_at=issued_at)

    assert len(rows) == 2
    assert rows[0].target_date == date(2026, 4, 6)
    assert rows[0].snow_depth_cm == 30.0
    assert rows[0].sunshine_duration_min == 300.0
    assert rows[1].target_date == date(2026, 4, 7)
    assert rows[1].snow_depth_cm == 28.0
