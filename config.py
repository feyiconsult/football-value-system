# config.py - Cloud & Local Hybrid Config
import os

# Secrets will be fetched from GitHub Actions secrets in the cloud,
# or fall back to your local environment variables.
ODDS_API_KEY = os.getenv("ODDS_API_KEY", "bfad19f9fc74e5f67cfc49ca4408d3a7")
EMAIL_SENDER = os.getenv("feyiconsult@gmail.com", "")
EMAIL_PASSWORD = os.getenv("edtgnzujycosfvpw", "")
EMAIL_RECEIVER = os.getenv("feyiconsult@gmail.com", "")

GLOBAL_SETTINGS = {
    "min_over_prob": 58.0,
    "min_odds": 1.65
}

# Configuration for Over 1.5 Accumulator System
OVER15_SYSTEM_SETTINGS = {
    "min_individual_prob": 78.0,
    "min_individual_odds": 1.15,
    "max_individual_odds": 1.35,
    "target_slip_games_min": 15,
    "target_slip_games_max": 20,
    "total_bankroll": 100000,
    "kelly_fraction": 0.05
}

# Verified League list for global 24/7 coverage
WEEK_ROUND_LEAGUES = {
    "soccer_epl": "English Premier League",
    "soccer_spain_la_liga": "Spain La Liga",
    "soccer_germany_bundesliga": "Germany Bundesliga",
    "soccer_italy_serie_a": "Italy Serie A",
    "soccer_france_ligue_one": "France Ligue 1",
    "soccer_netherlands_eredivisie": "Netherlands Eredivisie",
    "soccer_germany_bundesliga2": "Germany 2. Bundesliga",
    "soccer_austria_bundesliga": "Austria Bundesliga",
    "soccer_uefa_champs_league": "UEFA Champions League",
    "soccer_uefa_europa_league": "UEFA Europa League",
    "soccer_portugal_primeira_liga": "Portugal Primeira Liga",
    "soccer_belgium_first_division": "Belgium Pro League",
    "soccer_turkey_super_lig": "Turkey Super Lig",
    "soccer_efl_champ": "English Championship",
    "soccer_scotland_premiership": "Scotland Premiership",
    "soccer_sweden_allsvenskan": "Sweden Allsvenskan",
    "soccer_norway_eliteserien": "Norway Eliteserien",
    "soccer_argentina_primera_division": "Argentina Primera Division",
    "soccer_brazil_campeonato": "Brazil Serie A",
    "soccer_mexico_liga_mx": "Mexico Liga MX",
    "soccer_usa_mls": "USA MLS",
    "soccer_japan_j_league": "Japan J1 League",
    "soccer_denmark_superliga": "Denmark Superliga",
    "soccer_poland_ekstraklasa": "Poland Ekstraklasa",
    "soccer_switzerland_superleague": "Switzerland Super League"
}
TARGET_LEAGUES = WEEK_ROUND_LEAGUES