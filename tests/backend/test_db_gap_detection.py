from datetime import date
from contextlib import contextmanager
import db

class RecordingCursor:
    def __init__(self, statements, fetch_values=None):
        self.statements = statements
        self._fetch_values = fetch_values if fetch_values is not None else []

    def execute(self, sql: str, params=None) -> None:
        self.statements.append((sql, params))

    def fetchone(self):
        if self._fetch_values:
            val = self._fetch_values.pop(0)
            return (val,) if val is not None else None
        return None

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

def test_get_latest_observed_date_returns_none_when_no_data(monkeypatch):
    connection = RecordingConnection(fetch_values=[None])
    @contextmanager
    def fake_get_connection():
        yield connection
    monkeypatch.setattr(db, "get_connection", fake_get_connection)
    
    assert db.get_latest_observed_date(123) is None
    assert "SELECT MAX(observed_date)" in connection.statements[0][0]

def test_get_latest_observed_date_returns_date(monkeypatch):
    today = date.today()
    connection = RecordingConnection(fetch_values=[today])
    @contextmanager
    def fake_get_connection():
        yield connection
    monkeypatch.setattr(db, "get_connection", fake_get_connection)
    
    assert db.get_latest_observed_date(123) == today
