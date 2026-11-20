"""Recolector NBA Stats: calendario y box scores tradicionales V3.

El proceso es reanudable: vuelve a sincronizar el calendario, pero omite box scores
que ya tengan estadísticas de jugadores y dos filas de equipo, salvo --force.
"""
from __future__ import annotations

import logging
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pandas as pd
from config import (
    NBA_MAX_RETRIES, NBA_REQUEST_DELAY, NBA_REQUEST_TIMEOUT,
    NBA_SEASON, NBA_SEASON_TYPE, RAW_DIR,
)
from database.db import (
    completed_games, has_complete_boxscore, save_raw_payload,
    upsert_game, upsert_player, upsert_player_stats, upsert_team_stats, upsert_teams,
)

LOGGER = logging.getLogger("nba_collector")


def _call_with_retries(function, *args, **kwargs):
    last_error = None
    for attempt in range(1, NBA_MAX_RETRIES + 1):
        try:
            return function(*args, **kwargs)
        except Exception as exc:  # NBA Stats puede responder 403/429/5xx de manera intermitente.
            last_error = exc
            wait = min(45, NBA_REQUEST_DELAY * (2 ** (attempt - 1)))
            LOGGER.warning("Intento %s/%s falló: %s. Reintento en %.1fs", attempt,
                           NBA_MAX_RETRIES, exc, wait)
            if attempt < NBA_MAX_RETRIES:
                time.sleep(wait)
    raise RuntimeError(f"La solicitud falló después de {NBA_MAX_RETRIES} intentos") from last_error


def _frames(endpoint) -> list[pd.DataFrame]:
    frames = endpoint.get_data_frames()
    return [frame.copy() for frame in frames]


def _records(df: pd.DataFrame) -> list[dict[str, Any]]:
    if df is None or df.empty:
        return []
    return df.astype(object).where(pd.notna(df), None).to_dict(orient="records")


def _to_int(value):
    if value is None or pd.isna(value) or value == "":
        return None
    try:
        return int(float(value))
    except (TypeError, ValueError):
        return None


def _to_float(value):
    if value is None or pd.isna(value) or value == "":
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _minutes_to_decimal(value):
    """Convierte PT34M12.00S o 34:12 a minutos decimales."""
    if value is None or pd.isna(value):
        return None
    text = str(value).strip()
    try:
        if text.startswith("PT"):
            text = text[2:]
            minutes = 0.0
            if "M" in text:
                mins, text = text.split("M", 1)
                minutes += float(mins)
            if "S" in text:
                seconds = text.split("S", 1)[0]
                if seconds:
                    minutes += float(seconds) / 60
            return round(minutes, 4)
        if ":" in text:
            mins, seconds = text.split(":", 1)
            return round(float(mins) + float(seconds) / 60, 4)
        return float(text)
    except (TypeError, ValueError):
        return None


def sync_team_directory() -> int:
    """Los IDs oficiales se obtienen del catálogo estático incluido en nba_api."""
    from nba_api.stats.static import teams as nba_teams

    rows = nba_teams.get_teams()
    count = upsert_teams(rows)
    LOGGER.info("Equipos sincronizados: %s", count)
    return count


def _has_unassigned_team(row: dict[str, Any]) -> bool:
    """True cuando ScheduleLeagueV2 marca un participante pendiente con teamId=0."""
    return (
        _to_int(row.get("homeTeam_teamId")) == 0
        or _to_int(row.get("awayTeam_teamId")) == 0
    )


def _schedule_record(row: dict[str, Any]) -> dict[str, Any] | None:
    required = ("gameId", "homeTeam_teamId", "awayTeam_teamId", "gameDate")
    if any(row.get(key) is None for key in required):
        return None
    date_value = str(row.get("gameDate") or row.get("gameDateEst") or "")[:10]
    if len(date_value) != 10:
        return None
    game_status = _to_int(row.get("gameStatus"))
    return {
        "game_id": str(row["gameId"]),
        "season": NBA_SEASON,
        "season_type": NBA_SEASON_TYPE,
        "game_date": date_value,
        "game_datetime_utc": row.get("gameDateTimeUTC") or row.get("gameDateUTC"),
        "game_status": game_status,
        "game_status_text": row.get("gameStatusText"),
        "home_team_id": _to_int(row.get("homeTeam_teamId")),
        "away_team_id": _to_int(row.get("awayTeam_teamId")),
        "home_score": _to_int(row.get("homeTeam_score")) if game_status == 3 else None,
        "away_score": _to_int(row.get("awayTeam_score")) if game_status == 3 else None,
        "arena_name": row.get("arenaName"),
        "arena_city": row.get("arenaCity"),
        "arena_state": row.get("arenaState"),
        "is_neutral": _to_int(row.get("isNeutral")) or 0,
    }


def sync_schedule() -> int:
    from nba_api.stats.endpoints import scheduleleaguev2

    LOGGER.info("Descargando calendario %s desde ScheduleLeagueV2...", NBA_SEASON)
    endpoint = _call_with_retries(
        scheduleleaguev2.ScheduleLeagueV2,
        season=NBA_SEASON,
        league_id="00",
        timeout=NBA_REQUEST_TIMEOUT,
    )
    frames = _frames(endpoint)
    if not frames or frames[0].empty:
        raise RuntimeError("ScheduleLeagueV2 devolvió un calendario vacío. No se modificó la colección de partidos.")

    schedule_df = frames[0]
    saved = 0
    skipped_unassigned = 0
    invalid_rows = 0
    for record in _records(schedule_df):
        # ScheduleLeagueV2 puede incluir partidos eliminatorios de la NBA Cup
        # cuyo emparejamiento todavía no está definido. NBA representa esos
        # equipos pendientes con teamId=0. No es un team_id real ni existe en
        # nuestro catálogo de 30 equipos, así que no debe insertarse en games.
        if _has_unassigned_team(record):
            skipped_unassigned += 1
            continue

        game = _schedule_record(record)
        if game:
            upsert_game(game)
            saved += 1
        else:
            invalid_rows += 1

    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    payload = {f"dataset_{i}": _records(frame) for i, frame in enumerate(frames)}
    save_raw_payload(
        "NBA Stats", "ScheduleLeagueV2", NBA_SEASON, payload,
        f"data/raw/nba/schedule_{NBA_SEASON}_{stamp}.json",
    )
    LOGGER.info("Partidos del calendario guardados/actualizados: %s", saved)
    if skipped_unassigned:
        LOGGER.info(
            "Partidos con emparejamiento pendiente omitidos (teamId=0, normalmente NBA Cup): %s. "
            "Se conservaron en el JSON original y se incorporarán cuando la NBA asigne los equipos.",
            skipped_unassigned,
        )
    if invalid_rows:
        LOGGER.warning("Filas de calendario inválidas omitidas: %s", invalid_rows)
    return saved


def _upsert_boxscore(game_id: str, player_df: pd.DataFrame, team_df: pd.DataFrame) -> tuple[int, int]:
    player_count = 0
    team_count = 0

    if not player_df.empty:
        for raw in _records(player_df):
            player_id = _to_int(raw.get("personId"))
            team_id = _to_int(raw.get("teamId"))
            if player_id is None or team_id is None:
                continue
            first_name = raw.get("firstName")
            last_name = raw.get("familyName")
            full_name = " ".join(part for part in (first_name, last_name) if part).strip()
            upsert_player({
                "player_id": player_id,
                "first_name": first_name,
                "last_name": last_name,
                "full_name": full_name or raw.get("nameI") or str(player_id),
                "current_team_id": team_id,
                "position": raw.get("position"),
                "jersey_number": raw.get("jerseyNum"),
            })
            minutes = raw.get("minutes")
            position = str(raw.get("position") or "").strip()
            stat = {
                "game_id": game_id, "player_id": player_id, "team_id": team_id,
                "minutes": minutes, "minutes_decimal": _minutes_to_decimal(minutes),
                # No inferimos titularidad a partir de la posición: se incorporará desde lineup data.
                "started": None,
                "points": _to_int(raw.get("points")),
                "rebounds": _to_int(raw.get("reboundsTotal")),
                "offensive_rebounds": _to_int(raw.get("reboundsOffensive")),
                "defensive_rebounds": _to_int(raw.get("reboundsDefensive")),
                "assists": _to_int(raw.get("assists")),
                "steals": _to_int(raw.get("steals")),
                "blocks": _to_int(raw.get("blocks")),
                "turnovers": _to_int(raw.get("turnovers")),
                "personal_fouls": _to_int(raw.get("foulsPersonal")),
                "fgm": _to_int(raw.get("fieldGoalsMade")),
                "fga": _to_int(raw.get("fieldGoalsAttempted")),
                "fg_pct": _to_float(raw.get("fieldGoalsPercentage")),
                "fg3m": _to_int(raw.get("threePointersMade")),
                "fg3a": _to_int(raw.get("threePointersAttempted")),
                "fg3_pct": _to_float(raw.get("threePointersPercentage")),
                "ftm": _to_int(raw.get("freeThrowsMade")),
                "fta": _to_int(raw.get("freeThrowsAttempted")),
                "ft_pct": _to_float(raw.get("freeThrowsPercentage")),
                "plus_minus": _to_int(raw.get("plusMinusPoints")),
                "comment": raw.get("comment"),
            }
            upsert_player_stats(stat)
            player_count += 1

    if not team_df.empty:
        for raw in _records(team_df):
            team_id = _to_int(raw.get("teamId"))
            if team_id is None:
                continue
            stat = {
                "game_id": game_id, "team_id": team_id,
                "minutes": raw.get("minutes"),
                "points": _to_int(raw.get("points")),
                "rebounds": _to_int(raw.get("reboundsTotal")),
                "offensive_rebounds": _to_int(raw.get("reboundsOffensive")),
                "defensive_rebounds": _to_int(raw.get("reboundsDefensive")),
                "assists": _to_int(raw.get("assists")),
                "steals": _to_int(raw.get("steals")),
                "blocks": _to_int(raw.get("blocks")),
                "turnovers": _to_int(raw.get("turnovers")),
                "personal_fouls": _to_int(raw.get("foulsPersonal")),
                "fgm": _to_int(raw.get("fieldGoalsMade")),
                "fga": _to_int(raw.get("fieldGoalsAttempted")),
                "fg_pct": _to_float(raw.get("fieldGoalsPercentage")),
                "fg3m": _to_int(raw.get("threePointersMade")),
                "fg3a": _to_int(raw.get("threePointersAttempted")),
                "fg3_pct": _to_float(raw.get("threePointersPercentage")),
                "ftm": _to_int(raw.get("freeThrowsMade")),
                "fta": _to_int(raw.get("freeThrowsAttempted")),
                "ft_pct": _to_float(raw.get("freeThrowsPercentage")),
                "plus_minus": _to_int(raw.get("plusMinusPoints")),
            }
            upsert_team_stats(stat)
            team_count += 1

    return player_count, team_count


def sync_boxscores(max_games: int | None = None, force: bool = False) -> tuple[int, int, int]:
    from nba_api.stats.endpoints import boxscoretraditionalv3

    games = completed_games(NBA_SEASON)
    if not games:
        LOGGER.warning("No hay partidos finalizados para descargar en %s.", NBA_SEASON)
        return 0, 0, 0

    if not force:
        games = [game for game in games if not has_complete_boxscore(game["game_id"])]
    if max_games is not None:
        games = games[:max_games]

    LOGGER.info("Box scores pendientes: %s", len(games))
    games_done = players_saved = teams_saved = 0

    for index, game in enumerate(games, start=1):
        game_id = str(game["game_id"])
        LOGGER.info("[%s/%s] Descargando box score %s (%s)", index, len(games), game_id, game["game_date"])
        endpoint = _call_with_retries(
            boxscoretraditionalv3.BoxScoreTraditionalV3,
            game_id=game_id,
            timeout=NBA_REQUEST_TIMEOUT,
        )
        frames = _frames(endpoint)
        if len(frames) < 3:
            LOGGER.error("%s: se esperaban 3 conjuntos de datos V3; recibidos %s", game_id, len(frames))
            continue

        player_df = frames[0]
        team_df = frames[2]
        if player_df.empty or len(team_df) != 2:
            LOGGER.warning("%s: box score incompleto (jugadores=%s, equipos=%s); se conserva para reintento.",
                           game_id, len(player_df), len(team_df))
            continue

        player_count, team_count = _upsert_boxscore(game_id, player_df, team_df)
        payload = {f"dataset_{i}": _records(frame) for i, frame in enumerate(frames)}
        stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        save_raw_payload(
            "NBA Stats", "BoxScoreTraditionalV3", game_id, payload,
            f"data/raw/nba/boxscore_{game_id}_{stamp}.json",
        )
        games_done += 1
        players_saved += player_count
        teams_saved += team_count
        time.sleep(NBA_REQUEST_DELAY)

    return games_done, players_saved, teams_saved


def run_sync(max_games: int | None = None, force: bool = False) -> None:
    run_started = datetime.now(timezone.utc).isoformat(timespec="seconds")
    try:
        teams_count = sync_team_directory()
        schedule_count = sync_schedule()
        game_count, player_count, team_stat_count = sync_boxscores(max_games=max_games, force=force)
        LOGGER.info(
            "Sincronización completada | equipos=%s calendario=%s box_scores=%s filas_jugador=%s filas_equipo=%s",
            teams_count, schedule_count, game_count, player_count, team_stat_count,
        )
    except Exception:
        LOGGER.exception("La sincronización terminó con error. Puedes volver a ejecutarla; es reanudable.")
        raise
