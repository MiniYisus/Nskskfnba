# NBA Analytics 2026-27 — Entregable 01

Base inicial de datos y recopilador de calendario/box scores para la temporada 2026-27. Pensado para Windows y Python 3.12.

## Qué incluye esta primera entrega

- Base SQLite con claves, relaciones, índices y restricciones de duplicados.
- Catálogo inicial de 30 equipos NBA mediante los datos estáticos de `nba_api`.
- Importación del calendario de temporada con `ScheduleLeagueV2`.
- Box scores tradicionales por partido mediante `BoxScoreTraditionalV3`.
- Estadísticas individuales y colectivas de cada partido.
- Guardado de cada respuesta procesada como JSON en `data/raw/nba/`.
- Descarga reanudable: omite box scores que ya tienen datos de jugadores y dos registros de equipo.
- Reintentos con espera creciente para errores temporales de la API.
- Informe básico de calidad y volumen de datos.

**Alcance deliberado:** en esta primera entrega se guarda el calendario y el box score tradicional. Tracking, play-by-play, lesiones, quintetos, cuotas y predicciones se incorporarán en entregas separadas para validar cada fuente sin mezclar errores.

## 1. Requisitos

- Windows 10/11.
- Python 3.12 recomendado.
- Conexión a Internet.
- Acceso a `stats.nba.com`. NBA Stats puede limitar o bloquear solicitudes automatizadas temporalmente; el código reintenta, pero no puede garantizar disponibilidad permanente.

## 2. Instalación

1. Descomprime la carpeta en una ubicación sencilla, por ejemplo `C:\NBA_ANALYTICS_2026_27`.
2. Abre la carpeta.
3. Haz doble clic en `setup_windows.bat`.
4. El instalador crea `.venv`, instala dependencias, crea `.env`, SQLite e importa los equipos.

También puedes ejecutarlo desde VS Code en la terminal:

```powershell
py -3.12 -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
copy .env.example .env
python main.py init
```

Si PowerShell bloquea la activación, puedes llamar directamente a `.venv\Scripts\python.exe` sin activar el entorno.

## 3. Primera prueba controlada

Ejecuta `test_sync.bat`, o desde terminal:

```powershell
.venv\Scripts\python.exe main.py sync --max-games 3
```

Esto descarga el calendario y hasta tres box scores finalizados que todavía no existan en la base. El límite es para probar la conexión y revisar la calidad antes de hacer la descarga completa.

## 4. Descargar todos los box scores finalizados

Cuando la prueba termine correctamente:

```powershell
.venv\Scripts\python.exe main.py sync
```

También puedes usar `sync_season.bat`.

La sincronización se puede repetir. Vuelve a actualizar el calendario y solo descarga los box scores pendientes. Para forzar la relectura de los ya existentes:

```powershell
.venv\Scripts\python.exe main.py sync --force
```

Para actualizar solamente calendario y equipos:

```powershell
.venv\Scripts\python.exe main.py sync --schedule-only
```

## 5. Consultar estado y calidad

```powershell
.venv\Scripts\python.exe main.py report
```

El reporte muestra los equipos, jugadores, partidos, filas estadísticas y cuántos partidos finalizados no cuentan todavía con las estadísticas de ambos equipos.

## 6. Ubicación de los datos

- `database/nba_analytics.db`: base SQLite.
- `database/schema.sql`: definición SQL.
- `data/raw/nba/`: respuestas guardadas en JSON para trazabilidad.
- `logs/nba_analytics.log`: historial técnico de ejecución.

No borres la carpeta `data/raw` si quieres conservar las capturas originales. La base de datos y los datos se mantienen en tu computadora; no se suben a ningún servicio por este programa.

## 7. Tablas que ya existen

`teams`, `players`, `games`, `player_game_stats`, `team_game_stats`, `player_advanced_game_stats`, `team_advanced_game_stats`, `player_tracking_game_stats`, `play_by_play`, `shot_chart`, `team_context`, `player_context`, `injuries`, `lineups`, `odds`, `market_catalog`, `model_versions`, `predictions`, `prediction_results`, `collection_runs` y `raw_payloads`.

Algunas tablas ya están creadas para las siguientes fases, pero todavía no reciben datos automáticamente.

## Notas metodológicas importantes

- El calendario incluye partidos programados; el recolector de box scores procesa únicamente partidos identificados como finalizados.
- La titularidad no se deduce de la posición del jugador. Se deja como dato pendiente para una fuente fiable de quintetos.
- Los promedios, ventanas recientes y variables predictivas se calcularán después a partir de los registros por partido.
- El histórico de cuotas no puede reconstruirse retroactivamente si nunca fue archivado. Desde que conectemos las fuentes de cuotas comenzaremos a almacenar snapshots con hora de captura.
- Las estadísticas NBA pueden corregirse después del partido. Los JSON originales ayudan a auditar cuándo fueron capturadas; la política de versiones se ampliará en la siguiente etapa.

## Fuentes técnicas

- `nba_api` y su guía de endpoints: https://github.com/swar/nba_api
- Calendario `ScheduleLeagueV2`: https://github.com/swar/nba_api/blob/master/docs/nba_api/stats/endpoints/scheduleleaguev2.md
- Box score `BoxScoreTraditionalV3`: https://github.com/swar/nba_api/blob/master/docs/nba_api/stats/endpoints/boxscoretraditionalv3.md


## Solución de problemas: `FOREIGN KEY constraint failed` al sincronizar calendario

`ScheduleLeagueV2` puede devolver partidos eliminatorios de la NBA Cup con `homeTeam_teamId=0` o `awayTeam_teamId=0` cuando todavía no se conocen los equipos participantes. El ID `0` es un marcador de posición, no uno de los 30 equipos NBA.

El recolector actualizado omite esos emparejamientos pendientes de la tabla `games`, conserva el calendario completo en `data/raw/nba/` y los incorporará automáticamente en una sincronización posterior cuando la NBA asigne los equipos. No es necesario borrar ni recrear `nba_analytics.db`.

Si después de actualizar el proyecto aparece un mensaje que identifica otro `team_id` distinto de cero como no sincronizado, revisa el directorio de equipos y comparte ese mensaje: no conviene desactivar las claves foráneas ni inventar un equipo para ocultar el problema.
