from __future__ import annotations

from collections.abc import Iterator
from contextlib import contextmanager
import os
from pathlib import Path

import psycopg


ENV_FILE = Path(__file__).resolve().parents[2] / ".env"


def read_env_file(path: Path) -> dict[str, str]:
    values: dict[str, str] = {}
    if not path.exists():
        return values

    for raw_line in path.read_text().splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        values[key.strip()] = value.strip().strip('"').strip("'")

    return values


for key, value in read_env_file(ENV_FILE).items():
    os.environ.setdefault(key, value)


DATABASE_URL = os.environ["DATABASE_URL"]


@contextmanager
def get_connection() -> Iterator[psycopg.Connection]:
    with psycopg.connect(DATABASE_URL) as connection:
        yield connection


def initialize_database() -> None:
    with get_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS startup_heartbeat (
                    id BIGSERIAL PRIMARY KEY,
                    inserted_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
                )
                """
            )
            cursor.execute("INSERT INTO startup_heartbeat DEFAULT VALUES")
        connection.commit()


def check_database() -> None:
    with get_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")


def save_dummy_message() -> int:
    with get_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS frontend_messages (
                    id BIGSERIAL PRIMARY KEY,
                    body TEXT NOT NULL,
                    inserted_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
                )
                """
            )
            cursor.execute(
                "INSERT INTO frontend_messages (body) VALUES (%s) RETURNING id",
                ("Hello from the frontend",),
            )
            row = cursor.fetchone()
            message_id = int(row[0]) if row is not None else 0
        connection.commit()
    return message_id
