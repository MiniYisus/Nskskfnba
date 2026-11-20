PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS teams (
    team_id INTEGER PRIMARY KEY,
    full_name TEXT NOT NULL,
    abbreviation TEXT NOT NULL UNIQUE,
    nickname TEXT,
    city TEXT,
    state TEXT,
    year_founded INTEGER,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS players (
    player_id INTEGER PRIMARY KEY,
    first_name TEXT,
    last_name TEXT,
    full_name TEXT NOT NULL,
    current_team_id INTEGER,
    position TEXT,
    jersey_number TEXT,
    height TEXT,
    weight TEXT,
    birthdate TEXT,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (current_team_id) REFERENCES teams(team_id)
);

CREATE TABLE IF NOT EXISTS games (
    game_id TEXT PRIMARY KEY,
    season TEXT NOT NULL,
    season_type TEXT NOT NULL,
    game_date TEXT NOT NULL,
    game_datetime_utc TEXT,
    game_status INTEGER,
    game_status_text TEXT,
    home_team_id INTEGER NOT NULL,
    away_team_id INTEGER NOT NULL,
    home_score INTEGER,
    away_score INTEGER,
    arena_name TEXT,
    arena_city TEXT,
    arena_state TEXT,
    is_neutral INTEGER DEFAULT 0,
    last_synced_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (home_team_id) REFERENCES teams(team_id),
    FOREIGN KEY (away_team_id) REFERENCES teams(team_id)
);
CREATE INDEX IF NOT EXISTS idx_games_date ON games(game_date);
CREATE INDEX IF NOT EXISTS idx_games_season_status ON games(season, game_status);

CREATE TABLE IF NOT EXISTS player_game_stats (
    game_id TEXT NOT NULL,
    player_id INTEGER NOT NULL,
    team_id INTEGER NOT NULL,
    minutes TEXT,
    minutes_decimal REAL,
    started INTEGER,
    points INTEGER,
    rebounds INTEGER,
    offensive_rebounds INTEGER,
    defensive_rebounds INTEGER,
    assists INTEGER,
    steals INTEGER,
    blocks INTEGER,
    turnovers INTEGER,
    personal_fouls INTEGER,
    fgm INTEGER,
    fga INTEGER,
    fg_pct REAL,
    fg3m INTEGER,
    fg3a INTEGER,
    fg3_pct REAL,
    ftm INTEGER,
    fta INTEGER,
    ft_pct REAL,
    plus_minus INTEGER,
    comment TEXT,
    source_updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (game_id, player_id),
    FOREIGN KEY (game_id) REFERENCES games(game_id),
    FOREIGN KEY (player_id) REFERENCES players(player_id),
    FOREIGN KEY (team_id) REFERENCES teams(team_id)
);
CREATE INDEX IF NOT EXISTS idx_player_stats_player_game ON player_game_stats(player_id, game_id);
CREATE INDEX IF NOT EXISTS idx_player_stats_team_game ON player_game_stats(team_id, game_id);

CREATE TABLE IF NOT EXISTS team_game_stats (
    game_id TEXT NOT NULL,
    team_id INTEGER NOT NULL,
    minutes TEXT,
    points INTEGER,
    rebounds INTEGER,
    offensive_rebounds INTEGER,
    defensive_rebounds INTEGER,
    assists INTEGER,
    steals INTEGER,
    blocks INTEGER,
    turnovers INTEGER,
    personal_fouls INTEGER,
    fgm INTEGER,
    fga INTEGER,
    fg_pct REAL,
    fg3m INTEGER,
    fg3a INTEGER,
    fg3_pct REAL,
    ftm INTEGER,
    fta INTEGER,
    ft_pct REAL,
    plus_minus INTEGER,
    source_updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (game_id, team_id),
    FOREIGN KEY (game_id) REFERENCES games(game_id),
    FOREIGN KEY (team_id) REFERENCES teams(team_id)
);


CREATE TABLE IF NOT EXISTS player_advanced_game_stats (
    game_id TEXT NOT NULL,
    player_id INTEGER NOT NULL,
    team_id INTEGER NOT NULL,
    minutes REAL,
    offensive_rating REAL,
    defensive_rating REAL,
    net_rating REAL,
    assist_pct REAL,
    assist_to_turnover REAL,
    assist_ratio REAL,
    offensive_rebound_pct REAL,
    defensive_rebound_pct REAL,
    rebound_pct REAL,
    turnover_pct REAL,
    effective_fg_pct REAL,
    true_shooting_pct REAL,
    usage_pct REAL,
    pace REAL,
    pie REAL,
    source_updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (game_id, player_id),
    FOREIGN KEY (game_id) REFERENCES games(game_id),
    FOREIGN KEY (player_id) REFERENCES players(player_id),
    FOREIGN KEY (team_id) REFERENCES teams(team_id)
);

CREATE TABLE IF NOT EXISTS team_advanced_game_stats (
    game_id TEXT NOT NULL,
    team_id INTEGER NOT NULL,
    possessions REAL,
    pace REAL,
    offensive_rating REAL,
    defensive_rating REAL,
    net_rating REAL,
    assist_pct REAL,
    assist_to_turnover REAL,
    offensive_rebound_pct REAL,
    defensive_rebound_pct REAL,
    rebound_pct REAL,
    turnover_pct REAL,
    effective_fg_pct REAL,
    true_shooting_pct REAL,
    pie REAL,
    source_updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (game_id, team_id),
    FOREIGN KEY (game_id) REFERENCES games(game_id),
    FOREIGN KEY (team_id) REFERENCES teams(team_id)
);

CREATE TABLE IF NOT EXISTS player_tracking_game_stats (
    game_id TEXT NOT NULL,
    player_id INTEGER NOT NULL,
    team_id INTEGER NOT NULL,
    touches REAL,
    time_of_possession REAL,
    passes_made REAL,
    passes_received REAL,
    potential_assists REAL,
    secondary_assists REAL,
    assist_points_created REAL,
    rebound_chances REAL,
    contested_rebounds REAL,
    uncontested_rebounds REAL,
    drives REAL,
    drive_points REAL,
    drive_assists REAL,
    paint_touches REAL,
    elbow_touches REAL,
    post_touches REAL,
    contested_shots REAL,
    deflections REAL,
    screen_assists REAL,
    box_outs REAL,
    source_updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (game_id, player_id),
    FOREIGN KEY (game_id) REFERENCES games(game_id),
    FOREIGN KEY (player_id) REFERENCES players(player_id),
    FOREIGN KEY (team_id) REFERENCES teams(team_id)
);

CREATE TABLE IF NOT EXISTS play_by_play (
    game_id TEXT NOT NULL,
    event_id INTEGER NOT NULL,
    period INTEGER,
    clock TEXT,
    event_type TEXT,
    action_type TEXT,
    description TEXT,
    team_id INTEGER,
    person1_id INTEGER,
    person2_id INTEGER,
    person3_id INTEGER,
    home_score INTEGER,
    away_score INTEGER,
    video_available INTEGER,
    captured_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (game_id, event_id),
    FOREIGN KEY (game_id) REFERENCES games(game_id)
);
CREATE INDEX IF NOT EXISTS idx_pbp_game_period ON play_by_play(game_id, period, event_id);

CREATE TABLE IF NOT EXISTS shot_chart (
    game_id TEXT NOT NULL,
    game_event_id INTEGER NOT NULL,
    player_id INTEGER,
    team_id INTEGER,
    period INTEGER,
    minutes_remaining TEXT,
    seconds_remaining TEXT,
    shot_made INTEGER,
    shot_type TEXT,
    action_type TEXT,
    shot_zone_basic TEXT,
    shot_zone_area TEXT,
    shot_zone_range TEXT,
    shot_distance REAL,
    loc_x REAL,
    loc_y REAL,
    opponent_team_id INTEGER,
    defender_id INTEGER,
    defender_distance REAL,
    PRIMARY KEY (game_id, game_event_id),
    FOREIGN KEY (game_id) REFERENCES games(game_id),
    FOREIGN KEY (player_id) REFERENCES players(player_id),
    FOREIGN KEY (team_id) REFERENCES teams(team_id)
);

CREATE TABLE IF NOT EXISTS team_context (
    game_id TEXT NOT NULL,
    team_id INTEGER NOT NULL,
    is_home INTEGER NOT NULL,
    rest_days REAL,
    is_back_to_back INTEGER,
    games_last_3_days INTEGER,
    games_last_5_days INTEGER,
    travel_distance_km REAL,
    timezone_change REAL,
    previous_game_date TEXT,
    context_as_of TEXT NOT NULL,
    PRIMARY KEY (game_id, team_id),
    FOREIGN KEY (game_id) REFERENCES games(game_id),
    FOREIGN KEY (team_id) REFERENCES teams(team_id)
);

CREATE TABLE IF NOT EXISTS player_context (
    game_id TEXT NOT NULL,
    player_id INTEGER NOT NULL,
    team_id INTEGER NOT NULL,
    availability_status TEXT,
    expected_minutes REAL,
    is_expected_starter INTEGER,
    role_estimate TEXT,
    teammates_unavailable INTEGER,
    minutes_load_last_3 REAL,
    minutes_load_last_5 REAL,
    context_as_of TEXT NOT NULL,
    source TEXT,
    PRIMARY KEY (game_id, player_id, context_as_of),
    FOREIGN KEY (game_id) REFERENCES games(game_id),
    FOREIGN KEY (player_id) REFERENCES players(player_id),
    FOREIGN KEY (team_id) REFERENCES teams(team_id)
);

CREATE TABLE IF NOT EXISTS injuries (
    injury_id INTEGER PRIMARY KEY AUTOINCREMENT,
    player_id INTEGER,
    team_id INTEGER,
    status TEXT,
    injury_type TEXT,
    description TEXT,
    source TEXT NOT NULL,
    reported_at TEXT NOT NULL,
    captured_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (player_id) REFERENCES players(player_id),
    FOREIGN KEY (team_id) REFERENCES teams(team_id)
);
CREATE INDEX IF NOT EXISTS idx_injuries_player_time ON injuries(player_id, reported_at);

CREATE TABLE IF NOT EXISTS lineups (
    lineup_id INTEGER PRIMARY KEY AUTOINCREMENT,
    game_id TEXT NOT NULL,
    team_id INTEGER NOT NULL,
    player_id INTEGER NOT NULL,
    role TEXT,
    announced_at TEXT,
    captured_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    source TEXT,
    FOREIGN KEY (game_id) REFERENCES games(game_id),
    FOREIGN KEY (team_id) REFERENCES teams(team_id),
    FOREIGN KEY (player_id) REFERENCES players(player_id)
);

CREATE TABLE IF NOT EXISTS odds (
    odds_id INTEGER PRIMARY KEY AUTOINCREMENT,
    game_id TEXT NOT NULL,
    sportsbook TEXT NOT NULL,
    market_key TEXT NOT NULL,
    selection TEXT NOT NULL,
    player_id INTEGER,
    team_id INTEGER,
    line REAL,
    odds_decimal REAL NOT NULL,
    implied_probability REAL,
    captured_at TEXT NOT NULL,
    provider_event_id TEXT,
    provider_market_id TEXT,
    is_live INTEGER DEFAULT 0,
    raw_reference TEXT,
    FOREIGN KEY (game_id) REFERENCES games(game_id),
    FOREIGN KEY (player_id) REFERENCES players(player_id),
    FOREIGN KEY (team_id) REFERENCES teams(team_id)
);
CREATE INDEX IF NOT EXISTS idx_odds_game_market_time ON odds(game_id, market_key, captured_at);
CREATE INDEX IF NOT EXISTS idx_odds_book_time ON odds(sportsbook, captured_at);

CREATE TABLE IF NOT EXISTS market_catalog (
    market_key TEXT PRIMARY KEY,
    category TEXT NOT NULL,
    entity_type TEXT NOT NULL,
    display_name TEXT NOT NULL,
    stat_definition TEXT,
    settlement_rule TEXT,
    active INTEGER NOT NULL DEFAULT 1
);

CREATE TABLE IF NOT EXISTS model_versions (
    model_version_id INTEGER PRIMARY KEY AUTOINCREMENT,
    model_name TEXT NOT NULL,
    version TEXT NOT NULL,
    trained_through TEXT,
    feature_set_version TEXT,
    parameters_json TEXT,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(model_name, version)
);

CREATE TABLE IF NOT EXISTS predictions (
    prediction_id INTEGER PRIMARY KEY AUTOINCREMENT,
    game_id TEXT NOT NULL,
    market_key TEXT NOT NULL,
    entity_type TEXT NOT NULL,
    player_id INTEGER,
    team_id INTEGER,
    selection TEXT,
    line REAL,
    predicted_value REAL,
    probability_over REAL,
    probability_under REAL,
    probability_yes REAL,
    fair_odds REAL,
    confidence_label TEXT,
    model_version_id INTEGER,
    generated_at TEXT NOT NULL,
    feature_snapshot_id TEXT,
    FOREIGN KEY (game_id) REFERENCES games(game_id),
    FOREIGN KEY (player_id) REFERENCES players(player_id),
    FOREIGN KEY (team_id) REFERENCES teams(team_id),
    FOREIGN KEY (market_key) REFERENCES market_catalog(market_key),
    FOREIGN KEY (model_version_id) REFERENCES model_versions(model_version_id)
);
CREATE INDEX IF NOT EXISTS idx_predictions_game_market ON predictions(game_id, market_key);

CREATE TABLE IF NOT EXISTS prediction_results (
    prediction_result_id INTEGER PRIMARY KEY AUTOINCREMENT,
    prediction_id INTEGER NOT NULL,
    actual_value REAL,
    settlement TEXT,
    closing_odds_decimal REAL,
    closing_line REAL,
    settled_at TEXT,
    FOREIGN KEY (prediction_id) REFERENCES predictions(prediction_id)
);

CREATE TABLE IF NOT EXISTS collection_runs (
    run_id INTEGER PRIMARY KEY AUTOINCREMENT,
    collector TEXT NOT NULL,
    season TEXT,
    started_at TEXT NOT NULL,
    finished_at TEXT,
    status TEXT NOT NULL,
    records_read INTEGER DEFAULT 0,
    records_written INTEGER DEFAULT 0,
    error_message TEXT
);

CREATE TABLE IF NOT EXISTS raw_payloads (
    payload_id INTEGER PRIMARY KEY AUTOINCREMENT,
    source TEXT NOT NULL,
    endpoint TEXT NOT NULL,
    external_id TEXT,
    captured_at TEXT NOT NULL,
    file_path TEXT NOT NULL,
    checksum_sha256 TEXT
);


CREATE VIEW IF NOT EXISTS v_player_game_betting_stats AS
SELECT pgs.*,
       COALESCE(points, 0) + COALESCE(rebounds, 0) + COALESCE(assists, 0) AS pra,
       COALESCE(points, 0) + COALESCE(rebounds, 0) AS pr,
       COALESCE(points, 0) + COALESCE(assists, 0) AS pa,
       COALESCE(rebounds, 0) + COALESCE(assists, 0) AS ra,
       CASE WHEN (COALESCE(points,0) >= 10) + (COALESCE(rebounds,0) >= 10) +
                      (COALESCE(assists,0) >= 10) + (COALESCE(blocks,0) >= 10) +
                      (COALESCE(steals,0) >= 10) >= 2 THEN 1 ELSE 0 END AS double_double_flag,
       CASE WHEN (COALESCE(points,0) >= 10) + (COALESCE(rebounds,0) >= 10) +
                      (COALESCE(assists,0) >= 10) + (COALESCE(blocks,0) >= 10) +
                      (COALESCE(steals,0) >= 10) >= 3 THEN 1 ELSE 0 END AS triple_double_flag
FROM player_game_stats pgs;

CREATE VIEW IF NOT EXISTS v_game_boxscore_completeness AS
SELECT g.game_id, g.game_date, g.game_status_text,
       COUNT(DISTINCT t.team_id) AS team_rows,
       COUNT(DISTINCT p.player_id) AS player_rows,
       CASE WHEN COUNT(DISTINCT t.team_id) = 2 AND COUNT(DISTINCT p.player_id) > 0
            THEN 1 ELSE 0 END AS is_complete
FROM games g
LEFT JOIN team_game_stats t ON t.game_id = g.game_id
LEFT JOIN player_game_stats p ON p.game_id = g.game_id
GROUP BY g.game_id, g.game_date, g.game_status_text;

-- Semilla de mercados comunes; iremos ampliando el catálogo según las casas.
INSERT OR IGNORE INTO market_catalog
(market_key, category, entity_type, display_name, stat_definition, settlement_rule)
VALUES
('moneyline','result','team','Ganador del partido','Victoria del equipo','Incluye prórroga salvo regla distinta de la casa'),
('spread','result','team','Hándicap','Margen de puntos','Incluye prórroga salvo regla distinta de la casa'),
('total_points','totals','game','Total de puntos del partido','Puntos local + visitante','Incluye prórroga salvo regla distinta de la casa'),
('team_total_points','totals','team','Total de puntos del equipo','Puntos del equipo','Incluye prórroga salvo regla distinta de la casa'),
('player_points','player','player','Puntos del jugador','PTS','Reglas de participación según la casa'),
('player_rebounds','player','player','Rebotes del jugador','REB','Reglas de participación según la casa'),
('player_assists','player','player','Asistencias del jugador','AST','Reglas de participación según la casa'),
('player_threes','player','player','Triples anotados','FG3M','Reglas de participación según la casa'),
('player_steals','player','player','Robos del jugador','STL','Reglas de participación según la casa'),
('player_blocks','player','player','Tapones del jugador','BLK','Reglas de participación según la casa'),
('player_turnovers','player','player','Pérdidas del jugador','TOV','Reglas de participación según la casa'),
('player_pra','combo','player','Puntos + rebotes + asistencias','PTS + REB + AST','Reglas de participación según la casa'),
('player_pr','combo','player','Puntos + rebotes','PTS + REB','Reglas de participación según la casa'),
('player_pa','combo','player','Puntos + asistencias','PTS + AST','Reglas de participación según la casa'),
('player_ra','combo','player','Rebotes + asistencias','REB + AST','Reglas de participación según la casa'),
('player_double_double','milestones','player','Doble-doble','Al menos 10 en dos categorías estadísticas','Reglas de participación según la casa'),
('player_triple_double','milestones','player','Triple-doble','Al menos 10 en tres categorías estadísticas','Reglas de participación según la casa'),
('player_steals_blocks','combo','player','Robos + tapones','STL + BLK','Reglas de participación según la casa'),
('player_three_point_attempts','player','player','Intentos de triple','FG3A','Reglas de participación según la casa'),
('player_field_goals_made','player','player','Tiros de campo anotados','FGM','Reglas de participación según la casa'),
('player_free_throws_made','player','player','Tiros libres anotados','FTM','Reglas de participación según la casa'),
('team_rebounds','team','team','Rebotes del equipo','REB','Reglas de participación según la casa'),
('team_assists','team','team','Asistencias del equipo','AST','Reglas de participación según la casa'),
('team_threes','team','team','Triples del equipo','FG3M','Reglas de participación según la casa'),
('team_turnovers','team','team','Pérdidas del equipo','TOV','Reglas de participación según la casa'),
('first_half_total','period','game','Total primera mitad','Puntos Q1 + Q2','Según reglas de la casa'),
('quarter_total','period','game','Total de cuarto','Puntos de un cuarto','Según reglas de la casa'),
('first_quarter_winner','period','team','Ganador primer cuarto','Puntos Q1','Según reglas de la casa');
