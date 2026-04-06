from __future__ import annotations

from contextlib import contextmanager
from datetime import date, datetime, timezone

import db


class RecordingCursor:
    def __init__(self, statements, fetchone_value=None):
        self.statements = statements
        self._fetchone_value = fetchone_value

    def execute(self, sql: str, params=None) -> None:
        self.statements.append((sql, params))

    def fetchone(self):
        return self._fetchone_value

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        return None


class RecordingConnection:
    def __init__(self, fetchone_value=None) -> None:
        self.statements = []
        self.committed = False
        self._fetchone_value = fetchone_value

    def cursor(self) -> RecordingCursor:
        return RecordingCursor(self.statements, fetchone_value=self._fetchone_value)

    def commit(self) -> None:
        self.committed = True

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        return None


def test_create_forecast_run_inserts_row(monkeypatch):
    issued_at = datetime(2026, 4, 6, 12, 0, tzinfo=timezone.utc)
    connection = RecordingConnection(fetchone_value=(11,))

    @contextmanager
    def fake_get_connection():
        yield connection

    monkeypatch.setattr(db, "get_connection", fake_get_connection)

    forecast_run_id = db.create_forecast_run(location_id=3, issued_at=issued_at)

    assert forecast_run_id == 11
    assert any("INSERT INTO forecast_runs" in sql for sql, _ in connection.statements)
    assert connection.committed is True


def test_save_forecast_daily_upserts_by_run_and_target_date(monkeypatch):
    class Record:
        target_date = date(2026, 4, 7)
        temp_min_c = -1.0
        temp_max_c = 7.0
        temp_mean_c = 2.0
        precipitation_mm = 4.0
        rain_mm = 4.0
        snowfall_cm = 0.0
        pressure_hpa = 1012.0
        snow_depth_cm = 28.0
        cloud_cover_pct = 90.0
        sunshine_duration_min = 60.0
        wind_speed_m_s = 8.0
        wind_gust_m_s = 14.0
        wind_direction_deg = 150
        weather_code = 61

    connection = RecordingConnection()

    @contextmanager
    def fake_get_connection():
        yield connection

    monkeypatch.setattr(db, "get_connection", fake_get_connection)

    db.save_forecast_daily(forecast_run_id=11, record=Record())

    assert any("INSERT INTO forecast_daily" in sql for sql, _ in connection.statements)
    assert any("ON CONFLICT (forecast_run_id, target_date) DO UPDATE" in sql for sql, _ in connection.statements)
    assert connection.committed is True
