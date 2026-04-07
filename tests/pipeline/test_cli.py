from __future__ import annotations

from datetime import date

from pipeline import cli


def test_cli_backfill_parses_args_and_calls_ingest():
    calls: list[tuple[date, date, str]] = []

    def fake_backfill(location_slug: str, start: date, end: date) -> int:
        calls.append((start, end, location_slug))
        return 3

    exit_code = cli.run(
        ["backfill", "--start", "2024-01-01", "--end", "2024-01-07"],
        backfill_fn=fake_backfill,
    )

    assert exit_code == 0
    assert calls == [(date(2024, 1, 1), date(2024, 1, 7), "stowe-vt")]


def test_cli_forecast_parses_args_and_calls_ingest():
    calls: list[tuple[str, int]] = []

    def fake_forecast(location_slug: str, forecast_days: int) -> int:
        calls.append((location_slug, forecast_days))
        return 11

    exit_code = cli.run(
        ["forecast", "--location", "stowe-vt", "--forecast-days", "10"],
        forecast_fn=fake_forecast,
    )

    assert exit_code == 0
    assert calls == [("stowe-vt", 10)]
