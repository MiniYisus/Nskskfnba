"""Interfaz web móvil para NBA Analytics. Solo lectura; no inicia sincronizaciones públicas."""
from __future__ import annotations
import base64, hmac, os, sqlite3
from pathlib import Path
from typing import Optional
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse, Response
from fastapi.staticfiles import StaticFiles
from config import DB_PATH, NBA_SEASON

BASE = Path(__file__).resolve().parent
app = FastAPI(title="NBA Analytics 2026-27", docs_url=None, redoc_url=None)
app.mount("/static", StaticFiles(directory=BASE / "static"), name="static")

# En producción se recomienda configurar ambas variables. Basic Auth protege también los datos.
WEB_USER = os.getenv("NBA_WEB_USER", "")
WEB_PASSWORD = os.getenv("NBA_WEB_PASSWORD", "")

@app.middleware("http")
async def protect_dashboard(request: Request, call_next):
    if WEB_USER and WEB_PASSWORD and request.url.path != "/health":
        auth = request.headers.get("authorization", "")
        valid = False
        if auth.startswith("Basic "):
            try:
                decoded = base64.b64decode(auth.split(" ", 1)[1]).decode()
                user, password = decoded.split(":", 1)
                valid = hmac.compare_digest(user, WEB_USER) and hmac.compare_digest(password, WEB_PASSWORD)
            except Exception:
                valid = False
        if not valid:
            return Response(status_code=401, headers={"WWW-Authenticate": 'Basic realm="NBA Analytics"'})
    return await call_next(request)

def db():
    if not DB_PATH.exists():
        raise FileNotFoundError(f"No existe la base de datos: {DB_PATH}")
    con = sqlite3.connect(f"file:{DB_PATH}?mode=ro", uri=True, timeout=15)
    con.row_factory = sqlite3.Row
    return con

def rows(sql, params=()):
    with db() as con:
        return [dict(r) for r in con.execute(sql, params).fetchall()]

def scalar(sql, params=()):
    with db() as con:
        row = con.execute(sql, params).fetchone()
        return row[0] if row else 0

@app.get("/health")
def health():
    return {"ok": True, "database_exists": DB_PATH.exists(), "season": NBA_SEASON}

@app.get("/", response_class=HTMLResponse)
def home():
    return (BASE / "static" / "index.html").read_text(encoding="utf-8")

@app.get("/api/summary")
def summary():
    try:
        return {
            "season": NBA_SEASON,
            "teams": scalar("SELECT COUNT(*) FROM teams"),
            "players": scalar("SELECT COUNT(*) FROM players"),
            "games": scalar("SELECT COUNT(*) FROM games WHERE season=?", (NBA_SEASON,)),
            "completed": scalar("SELECT COUNT(*) FROM games WHERE season=? AND (game_status=3 OR lower(coalesce(game_status_text,'')) LIKE '%final%')", (NBA_SEASON,)),
            "player_rows": scalar("SELECT COUNT(*) FROM player_game_stats"),
            "team_rows": scalar("SELECT COUNT(*) FROM team_game_stats"),
            "odds_rows": scalar("SELECT COUNT(*) FROM odds"),
            "predictions": scalar("SELECT COUNT(*) FROM predictions"),
            "db_path": str(DB_PATH.name),
        }
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=503)

@app.get("/api/teams")
def teams():
    return rows("SELECT team_id, full_name, abbreviation FROM teams ORDER BY full_name")

@app.get("/api/games")
def games(limit: int = 40, status: str = "all"):
    limit=max(1,min(limit,150))
    where="g.season=?"; params=[NBA_SEASON]
    if status == "completed":
        where += " AND (g.game_status=3 OR lower(coalesce(g.game_status_text,'')) LIKE '%final%')"
    elif status == "upcoming":
        where += " AND NOT (g.game_status=3 OR lower(coalesce(g.game_status_text,'')) LIKE '%final%')"
    sql=f"""SELECT g.game_id,g.game_date,g.game_status_text,g.home_score,g.away_score,
        h.full_name home_team,h.abbreviation home_abbr,a.full_name away_team,a.abbreviation away_abbr
        FROM games g JOIN teams h ON h.team_id=g.home_team_id JOIN teams a ON a.team_id=g.away_team_id
        WHERE {where} ORDER BY g.game_date DESC LIMIT ?"""
    params.append(limit)
    return rows(sql,params)

@app.get("/api/leaders")
def leaders(stat: str="points", limit: int=20):
    allowed={"points":"points","rebounds":"rebounds","assists":"assists","threes":"fg3m","steals":"steals","blocks":"blocks","turnovers":"turnovers"}
    col=allowed.get(stat,"points"); limit=max(1,min(limit,100))
    return rows(f"""SELECT p.player_id,p.full_name,t.abbreviation team,
        COUNT(*) games,ROUND(AVG(s.{col}),2) average,MAX(s.{col}) high,
        ROUND(AVG(s.minutes_decimal),1) minutes
        FROM player_game_stats s JOIN players p ON p.player_id=s.player_id
        LEFT JOIN teams t ON t.team_id=s.team_id JOIN games g ON g.game_id=s.game_id
        WHERE g.season=? AND s.{col} IS NOT NULL
        GROUP BY p.player_id,p.full_name,t.abbreviation
        HAVING COUNT(*)>=1 ORDER BY average DESC LIMIT ?""",(NBA_SEASON,limit))

@app.get("/api/player-search")
def player_search(q: str=""):
    q=q.strip()[:60]
    if len(q)<2: return []
    return rows("SELECT player_id,full_name FROM players WHERE full_name LIKE ? ORDER BY full_name LIMIT 25",(f"%{q}%",))

@app.get("/api/player/{player_id}")
def player_detail(player_id: int):
    info=rows("SELECT p.player_id,p.full_name,p.position,t.full_name team FROM players p LEFT JOIN teams t ON t.team_id=p.current_team_id WHERE p.player_id=?",(player_id,))
    if not info: return JSONResponse({"error":"Jugador no encontrado"},status_code=404)
    stats=rows("""SELECT g.game_date,t.abbreviation team,s.minutes,s.points,s.rebounds,s.assists,s.steals,s.blocks,s.turnovers,s.fg3m,s.plus_minus
        FROM player_game_stats s JOIN games g ON g.game_id=s.game_id LEFT JOIN teams t ON t.team_id=s.team_id
        WHERE s.player_id=? AND g.season=? ORDER BY g.game_date DESC LIMIT 20""",(player_id,NBA_SEASON))
    return {"player":info[0],"games":stats}

@app.get("/api/odds")
def odds(limit: int=30):
    return rows("""SELECT o.*,m.display_name AS market_name FROM odds o LEFT JOIN market_catalog m ON m.market_key=o.market_key
        ORDER BY o.captured_at DESC LIMIT ?""",(max(1,min(limit,100)),))
