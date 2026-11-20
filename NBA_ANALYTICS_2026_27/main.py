"""Punto de entrada de NBA Analytics 2026-27."""
from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path

from config import LOG_DIR, NBA_SEASON
from database.db import initialize_database, print_database_report


def configure_logging() -> None:
    log_file = LOG_DIR / "nba_analytics.log"
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
        handlers=[logging.FileHandler(log_file, encoding="utf-8"), logging.StreamHandler(sys.stdout)],
        force=True,
    )


def main() -> int:
    parser = argparse.ArgumentParser(
        description="NBA Analytics 2026-27: base de datos y recolector de estadísticas."
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    subparsers.add_parser("init", help="Crear la base de datos e importar los 30 equipos.")

    sync_parser = subparsers.add_parser("sync", help="Actualizar calendario y descargar box scores.")
    sync_parser.add_argument("--max-games", type=int, default=None,
                             help="Limitar el número de box scores nuevos (útil para una prueba).")
    sync_parser.add_argument("--force", action="store_true",
                             help="Volver a descargar box scores aunque ya estén guardados.")
    sync_parser.add_argument("--schedule-only", action="store_true",
                             help="Actualizar únicamente calendario y equipos.")

    report_parser = subparsers.add_parser("report", help="Mostrar el estado de la base de datos.")
    report_parser.add_argument("--season", default=NBA_SEASON)

    args = parser.parse_args()
    configure_logging()

    try:
        if args.command == "init":
            initialize_database()
            from collectors.nba_stats import sync_team_directory
            count = sync_team_directory()
            print(f"\nInicialización terminada. Equipos importados/actualizados: {count}")
            print_database_report(NBA_SEASON)
            return 0

        if args.command == "sync":
            initialize_database()
            from collectors.nba_stats import sync_schedule, sync_team_directory, sync_boxscores
            sync_team_directory()
            scheduled = sync_schedule()
            print(f"Calendario sincronizado: {scheduled} partidos.")
            if not args.schedule_only:
                games, player_rows, team_rows = sync_boxscores(
                    max_games=args.max_games, force=args.force
                )
                print(f"Box scores guardados: {games}; filas jugador: {player_rows}; filas equipo: {team_rows}.")
            print_database_report(NBA_SEASON)
            return 0

        if args.command == "report":
            initialize_database()
            print_database_report(args.season)
            return 0
    except KeyboardInterrupt:
        print("\nProceso interrumpido por el usuario. La próxima sincronización podrá continuar.")
        return 130
    except Exception as exc:
        logging.getLogger("nba_analytics").exception("Error: %s", exc)
        print("\nLa ejecución falló. Revisa logs/nba_analytics.log para ver el detalle.")
        return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
