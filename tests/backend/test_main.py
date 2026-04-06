from contextlib import contextmanager

import db
import main


def test_read_env_file_parses_values(tmp_path):
    env_file = tmp_path / ".env"
    env_file.write_text(
        "\n".join(
            [
                "# sample config",
                "POSTGRES_DB=icecoast",
                "POSTGRES_USER=icecoast",
                "POSTGRES_PASSWORD=icecoast",
                "DATABASE_URL=postgresql://icecoast:icecoast@postgres:5432/icecoast",
            ]
        )
    )

    values = db.read_env_file(env_file)

    assert values["POSTGRES_DB"] == "icecoast"
    assert values["POSTGRES_USER"] == "icecoast"
    assert values["POSTGRES_PASSWORD"] == "icecoast"
    assert values["DATABASE_URL"] == "postgresql://icecoast:icecoast@postgres:5432/icecoast"


def test_startup_initializes_database(monkeypatch):
    calls: list[str] = []

    def fake_initialize_database() -> None:
        calls.append("initialized")

    monkeypatch.setattr(main, "initialize_database", fake_initialize_database, raising=False)

    main.startup()

    assert calls == ["initialized"]


def test_health_reports_ok_when_database_is_available(monkeypatch):
    calls: list[str] = []

    def fake_check_database() -> None:
        calls.append("checked")

    monkeypatch.setattr(main, "check_database", fake_check_database, raising=False)

    response = main.health()

    assert response == {"status": "ok"}
    assert calls == ["checked"]


def test_save_dummy_message_inserts_into_messages_table(monkeypatch):
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

    connection = RecordingConnection()

    @contextmanager
    def fake_get_connection():
        yield connection

    monkeypatch.setattr(db, "get_connection", fake_get_connection)

    message_id = db.save_dummy_message()

    assert message_id == 7
    assert any("CREATE TABLE IF NOT EXISTS frontend_messages" in sql for sql, _ in connection.statements)
    assert (
        "INSERT INTO frontend_messages (body) VALUES (%s) RETURNING id",
        ("Hello from the frontend",),
    ) in connection.statements
    assert connection.committed is True


def test_create_message_endpoint_returns_saved_payload(monkeypatch):
    calls: list[str] = []

    def fake_save_dummy_message() -> int:
        calls.append("saved")
        return 7

    monkeypatch.setattr(main, "save_dummy_message", fake_save_dummy_message, raising=False)

    response = main.create_message()

    assert response == {"status": "saved", "message_id": 7}
    assert calls == ["saved"]
