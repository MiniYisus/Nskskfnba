"""Acceso SQLite y operaciones idempotentes (se pueden ejecutar varias veces)."""
from __future__ import annotations

import json
import sqlite3
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable

import pandas as pd

from config import DB_PATH, ROOT_DIR

SCHEMA_PATH = ROOT_DIR / "database" / "schema.sql"


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def connect() -> sqlite3.Connection:
    connection = sqlite3.connect(DB_PATH, timeout=30)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    connection.execute("PRAGMA journal_mode = WAL")
    return connection


@contextmanager
def db_connection():
    """Contexto que confirma/ revierte transacciones y siempre cierra la conexión."""
    con = connect()
    try:
        with con:
            yield con
    finally:
        con.close()


def initialize_database() -> None:
    """Crea las tablas e índices si todavía no existen."""
    with db_connection() as con:
        con.executescript(SCHEMA_PATH.read_text(encoding="utf-8"))
    print(f"Base de datos lista: {DB_PATH}")


def _clean(value: Any) -> Any:
    if value is None:
        return None
    try:
        if pd.isna(value):
            return None
    except (TypeError, ValueError):
        pass
    if hasattr(value, "item"):
        try:
            value = value.item()
        except (ValueError, TypeError):
            pass
    if isinstance(value, (dict, list, tuple)):
        return json.dumps(value, ensure_ascii=False, default=str)
    return value


def save_raw_payload(source: str, endpoint: str, external_id: str | None,
                     payload: Any, relative_path: str) -> None:
    import hashlib

    destination = ROOT_DIR / relative_path
    destination.parent.mkdir(parents=True, exist_ok=True)
    content = json.dumps(payload, ensure_ascii=False, default=str, indent=2)
    destination.write_text(content, encoding="utf-8")
    checksum = hashlib.sha256(content.encode("utf-8")).hexdigest()
    with db_connection() as con:
        con.execute(
            """INSERT INTO raw_payloads
               (source, endpoint, external_id, captured_at, file_path, checksum_sha256)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (source, endpoint, external_id, utc_now(), str(destination.relative_to(ROOT_DIR)), checksum),
        )


def upsert_teams(teams: Iterable[dict[str, Any]]) -> int:
    rows = []
    for team in teams:
        rows.append((
            int(team["id"]), team.get("full_name"), team.get("abbreviation"),
            team.get("nickname"), team.get("city"), team.get("state"),
            _clean(team.get("year_founded")),
        ))
    with db_connection() as con:
        con.executemany(
            """INSERT INTO teams
               (team_id, full_name, abbreviation, nickname, city, state, year_founded)
               VALUES (?, ?, ?, ?, ?, ?, ?)
               ON CONFLICT(team_id) DO UPDATE SET
                 full_name=excluded.full_name, abbreviation=excluded.abbreviation,
                 nickname=excluded.nickname, city=excluded.city, state=excluded.state,
                 year_founded=excluded.year_founded, updated_at=CURRENT_TIMESTAMP""",
            rows,
        )
    return len(rows)


def upsert_game(game: dict[str, Any]) -> None:
    fields = (
        "game_id", "season", "season_type", "game_date", "game_datetime_utc",
        "game_status", "game_status_text", "home_team_id", "away_team_id",
        "home_score", "away_score", "arena_name", "arena_city", "arena_state", "is_neutral",
    )
    values = [_clean(game.get(field)) for field in fields]
    with db_connection() as con:
        # Dar un mensaje accionable antes de que SQLite lance un error de FK
        # poco descriptivo. Los team_id=0 (partidos con equipos TBD) se filtran
        # en sync_schedule; cualquier otro ID ausente merece investigarse.
        missing_team_ids = []
        for field in ("home_team_id", "away_team_id"):
            team_id = game.get(field)
            if team_id is None or int(team_id) <= 0:
                raise ValueError(
                    f"Partido {game.get('game_id')} sin {field} válido: {team_id!r}. "
                    "El calendario contiene un emparejamiento todavía no asignado."
                )
            exists = con.execute(
                "SELECT 1 FROM teams WHERE team_id = ?", (int(team_id),)
            ).fetchone()
            if not exists:
                missing_team_ids.append(int(team_id))
        if missing_team_ids:
            raise ValueError(
                f"Partido {game.get('game_id')} referencia team_id no sincronizado: "
                f"{sorted(set(missing_team_ids))}. Ejecuta la sincronización del directorio "
                "de equipos y revisa si NBA Stats introdujo un ID nuevo."
            )
        con.execute(
            f"""INSERT INTO games ({', '.join(fields)})
                VALUES ({', '.join('?' for _ in fields)})
                ON CONFLICT(game_id) DO UPDATE SET
                {', '.join(f'{field}=excluded.{field}' for field in fields if field != 'game_id')},
                last_synced_at=CURRENT_TIMESTAMP""",
            values,
        )


def upsert_player(player: dict[str, Any]) -> None:
    fields = ("player_id", "first_name", "last_name", "full_name", "current_team_id",
              "position", "jersey_number")
    values = [_clean(player.get(field)) for field in fields]
    with db_connection() as con:
        con.execute(
            f"""INSERT INTO players ({', '.join(fields)})
                VALUES ({', '.join('?' for _ in fields)})
                ON CONFLICT(player_id) DO UPDATE SET
                {', '.join(f'{field}=excluded.{field}' for field in fields if field != 'player_id')},
                updated_at=CURRENT_TIMESTAMP""",
            values,
        )


def upsert_player_stats(row: dict[str, Any]) -> None:
    fields = (
        "game_id", "player_id", "team_id", "minutes", "minutes_decimal", "started",
        "points", "rebounds", "offensive_rebounds", "defensive_rebounds", "assists",
        "steals", "blocks", "turnovers", "personal_fouls", "fgm", "fga", "fg_pct",
        "fg3m", "fg3a", "fg3_pct", "ftm", "fta", "ft_pct", "plus_minus", "comment",
    )
    values = [_clean(row.get(field)) for field in fields]
    with db_connection() as con:
        con.execute(
            f"""INSERT INTO player_game_stats ({', '.join(fields)})
                VALUES ({', '.join('?' for _ in fields)})
                ON CONFLICT(game_id, player_id) DO UPDATE SET
                {', '.join(f'{field}=excluded.{field}' for field in fields if field not in ('game_id','player_id'))},
                source_updated_at=CURRENT_TIMESTAMP""",
            values,
        )


def upsert_team_stats(row: dict[str, Any]) -> None:
    fields = (
        "game_id", "team_id", "minutes", "points", "rebounds", "offensive_rebounds",
        "defensive_rebounds", "assists", "steals", "blocks", "turnovers", "personal_fouls",
        "fgm", "fga", "fg_pct", "fg3m", "fg3a", "fg3_pct", "ftm", "fta", "ft_pct", "plus_minus",
    )
    values = [_clean(row.get(field)) for field in fields]
    with db_connection() as con:
        con.execute(
            f"""INSERT INTO team_game_stats ({', '.join(fields)})
                VALUES ({', '.join('?' for _ in fields)})
                ON CONFLICT(game_id, team_id) DO UPDATE SET
                {', '.join(f'{field}=excluded.{field}' for field in fields if field not in ('game_id','team_id'))},
                source_updated_at=CURRENT_TIMESTAMP""",
            values,
        )


def completed_games(season: str) -> list[dict[str, Any]]:
    with db_connection() as con:
        rows = con.execute(
            """SELECT g.* FROM games g
               WHERE g.season=? AND (
                 LOWER(COALESCE(g.game_status_text,'')) LIKE '%final%'
                 OR g.game_status=3
               )
               ORDER BY g.game_date, g.game_id""",
            (season,),
        ).fetchall()
    return [dict(row) for row in rows]


def has_complete_boxscore(game_id: str) -> bool:
    with db_connection() as con:
        player_count = con.execute(
            "SELECT COUNT(*) FROM player_game_stats WHERE game_id=?", (game_id,)
        ).fetchone()[0]
        team_count = con.execute(
            "SELECT COUNT(*) FROM team_game_stats WHERE game_id=?", (game_id,)
        ).fetchone()[0]
    return player_count > 0 and team_count == 2


def print_database_report(season: str) -> None:
    with db_connection() as con:
        counts = {}
        for table in ("teams", "players", "games", "player_game_stats", "team_game_stats", "odds"):
            counts[table] = con.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
        missing = con.execute(
            """SELECT COUNT(*) FROM games g
               WHERE g.season=?
                 AND (g.game_status=3 OR LOWER(COALESCE(g.game_status_text,'')) LIKE '%final%')
                 AND (
                   NOT EXISTS (
                     SELECT 1 FROM team_game_stats t WHERE t.game_id=g.game_id
                     GROUP BY t.game_id HAVING COUNT(*)=2
                   )
                   OR NOT EXISTS (SELECT 1 FROM player_game_stats p WHERE p.game_id=g.game_id)
                 )""", (season,)
        ).fetchone()[0]
    print("\n========== ESTADO DE LA BASE DE DATOS ==========")
    for table, count in counts.items():
        print(f"{table:24s} {count:>8}")
    print(f"Partidos finalizados sin box score completo: {missing}")
    print("================================================\n")
