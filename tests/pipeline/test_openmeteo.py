from __future__ import annotations

from contextlib import contextmanager
from datetime import date

import pipeline.openmeteo as openmeteo
from pipeline.openmeteo import LocationSpec, parse_daily_weather_payload


def test_parse_daily_weather_payload_maps_values_and_derived_snow_depth():
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
            "time": ["2024-01-06"],
            "weather_code": [71],
            "temperature_2m_min": [-4.0],
            "temperature_2m_max": [1.5],
            "temperature_2m_mean": [-1.0],
            "precipitation_sum": [12.3],
            "rain_sum": [4.5],
            "snowfall_sum": [7.8],
            "pressure_msl_mean": [1012.4],
            "cloud_cover_mean": [62.0],
            "sunshine_duration": [7200],
            "wind_speed_10m_mean": [5.2],
            "wind_gusts_10m_mean": [8.9],
            "wind_direction_10m_dominant": [270],
        },
        "hourly": {
            "time": [
                "2024-01-06T00:00",
                "2024-01-06T01:00",
                "2024-01-06T02:00",
                "2024-01-06T23:00",
            ],
            "snow_depth": [0.42, 0.43, None, 0.50],
        },
    }

    rows = parse_daily_weather_payload(location, payload)

    assert len(rows) == 1
    row = rows[0]
    assert row.observed_date == date(2024, 1, 6)
    assert row.temp_min_c == -4.0
    assert row.temp_max_c == 1.5
    assert row.temp_mean_c == -1.0
    assert row.precipitation_mm == 12.3
    assert row.rain_mm == 4.5
    assert row.snowfall_cm == 7.8
    assert row.pressure_hpa == 1012.4
    assert row.cloud_cover_pct == 62.0
    assert row.sunshine_duration_min == 120.0
    assert row.wind_speed_m_s == 5.2
    assert row.wind_gust_m_s == 8.9
    assert row.wind_direction_deg == 270
    assert row.weather_code == 71
    assert row.snow_depth_cm == 50.0


def test_ingest_historical_daily_weather_is_idempotent_for_same_range(monkeypatch):
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
            "time": ["2024-01-06"],
            "weather_code": [71],
            "temperature_2m_min": [-4.0],
            "temperature_2m_max": [1.5],
            "temperature_2m_mean": [-1.0],
            "precipitation_sum": [12.3],
            "rain_sum": [4.5],
            "snowfall_sum": [7.8],
            "pressure_msl_mean": [1012.4],
            "cloud_cover_mean": [62.0],
            "sunshine_duration": [7200],
            "wind_speed_10m_mean": [5.2],
            "wind_gusts_10m_mean": [8.9],
            "wind_direction_10m_dominant": [270],
        },
        "hourly": {
            "time": [
                "2024-01-06T00:00",
                "2024-01-06T23:00",
            ],
            "snow_depth": [0.42, 0.50],
        },
    }

    class FakeClient:
        def fetch_daily_payload(self, *args, **kwargs):
            return payload

    class SemanticCursor:
        def __init__(self, state):
            self.state = state
            self._fetchone_value = None

        def execute(self, sql: str, params=None) -> None:
            normalized_sql = " ".join(sql.split())
            if "INSERT INTO locations" in normalized_sql:
                slug = params[0]
                self.state.locations.setdefault(slug, 1)
                self._fetchone_value = (self.state.locations[slug],)
                return
            if "INSERT INTO dates" in normalized_sql:
                self.state.dates[params[0]] = params[1:]
                return
            if "INSERT INTO daily_weather" in normalized_sql:
                key = (params[0], params[1])
                self.state.daily_weather[key] = params[2:]
                return
            raise AssertionError(f"Unexpected SQL: {sql}")

        def fetchone(self):
            return self._fetchone_value

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb) -> None:
            return None

    class SemanticConnection:
        def __init__(self) -> None:
            self.locations = {}
            self.dates = {}
            self.daily_weather = {}
            self.committed = False

        def cursor(self) -> SemanticCursor:
            return SemanticCursor(self)

        def commit(self) -> None:
            self.committed = True

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb) -> None:
            return None

    connection = SemanticConnection()

    @contextmanager
    def fake_get_connection():
        yield connection

    monkeypatch.setattr(openmeteo, "get_connection", fake_get_connection)
    monkeypatch.setattr(openmeteo, "ensure_schema", lambda connection: None)

    rows_first = openmeteo.ingest_historical_daily_weather(
        location,
        date(2024, 1, 6),
        date(2024, 1, 6),
        client=FakeClient(),
    )
    rows_second = openmeteo.ingest_historical_daily_weather(
        location,
        date(2024, 1, 6),
        date(2024, 1, 6),
        client=FakeClient(),
    )

    assert len(rows_first) == 1
    assert len(rows_second) == 1
    assert len(connection.locations) == 1
    assert len(connection.dates) == 1
    assert len(connection.daily_weather) == 1
    assert (1, date(2024, 1, 6)) in connection.daily_weather
    assert connection.committed is True


def test_ingest_historical_daily_weather_bootstraps_schema_first(monkeypatch):
    calls: list[str] = []
    location = LocationSpec(
        slug="stowe-vt",
        name="Stowe, Vermont",
        latitude=44.4654,
        longitude=-72.6874,
        elevation_m=486,
        timezone="America/New_York",
    )

    class FakeClient:
        def fetch_daily_payload(self, *args, **kwargs):
            return {
                "daily": {
                    "time": ["2024-01-06"],
                    "temperature_2m_min": [0.0],
                }
            }

    class DummyConnection:
        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb) -> None:
            return None

        def cursor(self):
            class Cursor:
                def __enter__(self_inner):
                    return self_inner

                def __exit__(self_inner, exc_type, exc, tb) -> None:
                    return None

                def execute(self_inner, sql, params=None):
                    calls.append("sql")

                def fetchone(self_inner):
                    return (1,)

            return Cursor()

        def commit(self):
            calls.append("commit")

    def fake_get_connection():
        from contextlib import contextmanager

        @contextmanager
        def _manager():
            yield DummyConnection()

        return _manager()

    def fake_ensure_schema(connection):
        calls.append("schema")

    monkeypatch.setattr(openmeteo, "get_connection", fake_get_connection)
    monkeypatch.setattr(openmeteo, "ensure_schema", fake_ensure_schema)
    monkeypatch.setattr(openmeteo, "upsert_location", lambda location, connection: 1)
    monkeypatch.setattr(openmeteo, "ensure_dates", lambda dates, connection: calls.append("dates"))
    monkeypatch.setattr(openmeteo, "save_daily_weather", lambda location_id, record, connection: calls.append("daily"))

    openmeteo.ingest_historical_daily_weather(location, date(2024, 1, 6), date(2024, 1, 6), client=FakeClient())

    assert calls[0] == "schema"
