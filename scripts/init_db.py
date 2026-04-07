#!/usr/bin/env python3
from __future__ import annotations

import sys
from pathlib import Path

from dotenv import load_dotenv


ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = ROOT / "src"
BACKEND_DIR = SRC_DIR / "backend"

load_dotenv(ROOT / ".env")

for path in (BACKEND_DIR, SRC_DIR):
    path_str = str(path)
    if path_str not in sys.path:
        sys.path.insert(0, path_str)

from db import ensure_schema


def main() -> int:
    ensure_schema()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
