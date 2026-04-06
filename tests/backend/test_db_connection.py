from __future__ import annotations

import db
import psycopg


class DummyConnection:
    def __init__(self, label: str) -> None:
        self.label = label

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        return None


def test_get_connection_retries_localhost_when_postgres_host_cannot_resolve(monkeypatch):
    calls: list[str] = []
    fallback_connection = DummyConnection("fallback")

    def fake_connect(database_url: str):
        calls.append(database_url)
        if database_url.endswith("@postgres:5432/icecoast"):
            raise psycopg.OperationalError("failed to resolve host 'postgres'")
        return fallback_connection

    monkeypatch.setattr(db.psycopg, "connect", fake_connect)
    monkeypatch.setattr(db, "DATABASE_URL", "postgresql://icecoast:icecoastpwd@postgres:5432/icecoast")

    with db.get_connection() as connection:
        assert connection is fallback_connection

    assert calls == [
        "postgresql://icecoast:icecoastpwd@postgres:5432/icecoast",
        "postgresql://icecoast:icecoastpwd@localhost:5432/icecoast",
    ]
