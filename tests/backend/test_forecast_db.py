from __future__ import annotations

from contextlib import contextmanager
from dataclasses import dataclass
from datetime import date, datetime, timezone

import db


class RecordingCursor:
    def __init__(self, statements, fetch_values=None):
        self.statements = statements
        self._fetch_values = fetch_values if fetch_values is not None else []

    def execute(self, sql: str, params=None) -> None:
        self.statements.append((sql, params))

    def fetchone(self):
        if self._fetch_values:
            return (self._fetch_values.pop(0),)
        return (7,)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        return None


class RecordingConnection:
    def __init__(self, fetch_values=None) -> None:
        self.statements = []
        self.committed = False
        self._fetch_values = list(fetch_values or [])

    def cursor(self) -> RecordingCursor:
        return RecordingCursor(self.statements, fetch_values=self._fetch_values)

    def commit(self) -> None:
        self.committed = True

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        return None


@dataclass(frozen=True)
class ForecastRecord:
    target_date: date
    temp_min_c: float | None = None
    temp_max_c: float | None = None
    temp_mean_c: float | None = None
    precipitation_mm: float | None = None
    rain_mm: float | None = None
    snowfall_cm: float | None = None
    pressure_hpa: float | None = None
    snow_depth_cm: float | None = None
    cloud_cover_pct: float | None = None
    sunshine_duration_min: float | None = None
    wind_speed_m_s: float | None = None
    wind_gust_m_s: float | None = None
    wind_direction_deg: int | None = None
    weather_code: int | None = None


def test_create_forecast_run_inserts_and_returns_id(monkeypatch):
    connection = RecordingConnection(fetch_values=[123])

    @contextmanager
    def fake_get_connection():
        yield connection

    monkeypatch.setattr(db, "get_connection", fake_get_connection)

    issued_at = datetime(2026, 4, 6, 12, 0, tzinfo=timezone.utc)
    forecast_run_id = db.create_forecast_run(99, issued_at)

    assert forecast_run_id == 123
    assert ("INSERT INTO forecast_runs" in connection.statements[0][0]) is True
    assert connection.statements[0][1] == (99, issued_at)
    assert connection.committed is True


def test_forecast_runs_are_versioned_by_issued_at(monkeypatch):
    connection = RecordingConnection(fetch_values=[101, 202])

    @contextmanager
    def fake_get_connection():
        yield connection

    monkeypatch.setattr(db, "get_connection", fake_get_connection)

    issued_at_1 = datetime(2026, 4, 6, 12, 0, tzinfo=timezone.utc)
    issued_at_2 = datetime(2026, 4, 6, 18, 0, tzinfo=timezone.utc)

    run_1 = db.create_forecast_run(99, issued_at_1)
    run_2 = db.create_forecast_run(99, issued_at_2)

    assert run_1 == 101
    assert run_2 == 202
    assert any("ON CONFLICT" in sql for sql, _ in connection.statements) is False
    assert (99, issued_at_1) in [params for _, params in connection.statements]
    assert (99, issued_at_2) in [params for _, params in connection.statements]


def test_save_forecast_daily_allows_same_target_date_across_runs(monkeypatch):
    connection = RecordingConnection()

    @contextmanager
    def fake_get_connection():
        yield connection

    monkeypatch.setattr(db, "get_connection", fake_get_connection)

    record = ForecastRecord(target_date=date(2026, 4, 6), temp_max_c=1.0)
    db.save_forecast_daily(111, record)
    db.save_forecast_daily(222, record)

    inserts = [(sql, params) for sql, params in connection.statements if "INSERT INTO forecast_daily" in sql]
    assert len(inserts) == 2
    assert inserts[0][1][0] == 111
    assert inserts[1][1][0] == 222
    assert any("ON CONFLICT (forecast_run_id, target_date)" in sql for sql, _ in inserts)
