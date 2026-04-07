from __future__ import annotations

import argparse
from dataclasses import dataclass
from datetime import date
import sys
from typing import Callable, Sequence

from pipeline.forecast import fetch_and_ingest_forecast_daily
from pipeline.openmeteo import LocationSpec, ingest_historical_daily_weather


@dataclass(frozen=True)
class Locations:
    stowe_vt = LocationSpec(
        slug="stowe-vt",
        name="Stowe, Vermont",
        latitude=44.4654,
        longitude=-72.6874,
        elevation_m=486,
        timezone="America/New_York",
    )


def _parse_date(value: str) -> date:
    try:
        return date.fromisoformat(value)
    except ValueError as e:
        raise argparse.ArgumentTypeError(str(e)) from e


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="pipeline.cli")
    subparsers = parser.add_subparsers(dest="command", required=True)

    backfill = subparsers.add_parser("backfill", help="Backfill historical daily weather into Postgres")
    backfill.add_argument("--location", default="stowe-vt")
    backfill.add_argument("--start", type=_parse_date, required=True)
    backfill.add_argument("--end", type=_parse_date, required=True)

    forecast = subparsers.add_parser("forecast", help="Fetch and store a forecast snapshot into Postgres")
    forecast.add_argument("--location", default="stowe-vt")
    forecast.add_argument("--forecast-days", type=int, default=16)

    return parser


def _resolve_location(slug: str) -> LocationSpec:
    if slug == "stowe-vt":
        return Locations.stowe_vt
    raise SystemExit(f"Unknown --location {slug!r}")


def _default_backfill(location_slug: str, start: date, end: date) -> int:
    location = _resolve_location(location_slug)
    rows = ingest_historical_daily_weather(location, start, end)
    return len(rows)


def _default_forecast(location_slug: str, forecast_days: int) -> int:
    location = _resolve_location(location_slug)
    return fetch_and_ingest_forecast_daily(location, forecast_days=forecast_days)


def run(
    argv: Sequence[str] | None = None,
    *,
    backfill_fn: Callable[[str, date, date], int] | None = None,
    forecast_fn: Callable[[str, int], int] | None = None,
) -> int:
    parser = build_parser()
    args = parser.parse_args(list(argv) if argv is not None else None)

    backfill = backfill_fn or _default_backfill
    forecast = forecast_fn or _default_forecast

    if args.command == "backfill":
        backfill(args.location, args.start, args.end)
        return 0
    if args.command == "forecast":
        forecast(args.location, args.forecast_days)
        return 0

    raise SystemExit(f"Unhandled command: {args.command!r}")


def main() -> None:
    raise SystemExit(run(sys.argv[1:]))


if __name__ == "__main__":
    main()
