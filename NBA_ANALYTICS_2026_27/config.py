"""Configuración central del proyecto NBA Analytics 2026-27."""
from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv

ROOT_DIR = Path(__file__).resolve().parent
load_dotenv(ROOT_DIR / ".env")

NBA_SEASON = os.getenv("NBA_SEASON", "2026-27")
NBA_SEASON_TYPE = os.getenv("NBA_SEASON_TYPE", "Regular Season")
DB_PATH = Path(os.getenv("NBA_DB_PATH", str(ROOT_DIR / "database" / "nba_analytics.db"))).expanduser()
DB_PATH.parent.mkdir(parents=True, exist_ok=True)
RAW_DIR = ROOT_DIR / "data" / "raw"
PROCESSED_DIR = ROOT_DIR / "data" / "processed"
PARQUET_DIR = ROOT_DIR / "data" / "parquet"
LOG_DIR = ROOT_DIR / "logs"

NBA_REQUEST_TIMEOUT = int(os.getenv("NBA_REQUEST_TIMEOUT", "60"))
NBA_REQUEST_DELAY = float(os.getenv("NBA_REQUEST_DELAY", "1.2"))
NBA_MAX_RETRIES = int(os.getenv("NBA_MAX_RETRIES", "4"))

for directory in (DB_PATH.parent, RAW_DIR, PROCESSED_DIR, PARQUET_DIR, LOG_DIR):
    directory.mkdir(parents=True, exist_ok=True)
