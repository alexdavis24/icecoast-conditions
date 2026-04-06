from __future__ import annotations

from contextlib import contextmanager
from datetime import date

import db


class RecordingCursor:
    def __init__(self, statements):
        self.statements = statements

    def execute(self, sql: str, params=None) -> None:
        self.statements.append((sql, params))

    def fetchone(self):
        return (7,)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        return None


class RecordingConnection:
    def __init__(self) -> None:
        self.statements = []
        self.committed = False

    def cursor(self) -> RecordingCursor:
        return RecordingCursor(self.statements)

    def commit(self) -> None:
        self.committed = True

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        return None


def test_initialize_database_creates_weather_schema_tables(monkeypatch):
    connection = RecordingConnection()

    @contextmanager
    def fake_get_connection():
        yield connection

    monkeypatch.setattr(db, "get_connection", fake_get_connection)

    db.initialize_database()

    create_sql = [sql for sql, _ in connection.statements if sql.lstrip().startswith("CREATE TABLE IF NOT EXISTS")]

    assert any("CREATE TABLE IF NOT EXISTS locations" in sql for sql in create_sql)
    assert any("CREATE TABLE IF NOT EXISTS dates" in sql for sql in create_sql)
    assert any("CREATE TABLE IF NOT EXISTS daily_weather" in sql for sql in create_sql)
    assert any("CREATE TABLE IF NOT EXISTS forecast_runs" in sql for sql in create_sql)
    assert any("CREATE TABLE IF NOT EXISTS forecast_daily" in sql for sql in create_sql)
    assert connection.committed is True


def test_ensure_schema_creates_weather_tables_without_heartbeat(monkeypatch):
    connection = RecordingConnection()

    @contextmanager
    def fake_get_connection():
        yield connection

    monkeypatch.setattr(db, "get_connection", fake_get_connection)

    db.ensure_schema()

    normalized_statements = [
        (" ".join(sql.split()), params) for sql, params in connection.statements
    ]

    assert any("CREATE TABLE IF NOT EXISTS locations" in sql for sql, _ in normalized_statements)
    assert any("CREATE TABLE IF NOT EXISTS forecast_daily" in sql for sql, _ in normalized_statements)
    assert not any("startup_heartbeat" in sql for sql, _ in normalized_statements)
    assert connection.committed is True


def test_ensure_dates_inserts_iso_calendar_rows(monkeypatch):
    connection = RecordingConnection()

    @contextmanager
    def fake_get_connection():
        yield connection

    monkeypatch.setattr(db, "get_connection", fake_get_connection)

    db.ensure_dates([date(2024, 1, 6), date(2024, 1, 7)])

    normalized_statements = [
        (" ".join(sql.split()), params) for sql, params in connection.statements
    ]

    assert (
        "INSERT INTO dates (date, year, month, day, day_of_week, day_of_year, week_of_year, is_weekend) "
        "VALUES (%s, %s, %s, %s, %s, %s, %s, %s) ON CONFLICT (date) DO NOTHING",
        (date(2024, 1, 6), 2024, 1, 6, 6, 6, 1, True),
    ) in normalized_statements
    assert (
        "INSERT INTO dates (date, year, month, day, day_of_week, day_of_year, week_of_year, is_weekend) "
        "VALUES (%s, %s, %s, %s, %s, %s, %s, %s) ON CONFLICT (date) DO NOTHING",
        (date(2024, 1, 7), 2024, 1, 7, 7, 7, 1, True),
    ) in normalized_statements
    assert connection.committed is True
