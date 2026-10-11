# config.py - Cloud & Local Hybrid Config
import os

ODDS_API_KEY = os.getenv("ODDS_API_KEY", "YOUR_LOCAL_API_KEY_FALLBACK")

EMAIL_SENDER = os.getenv("EMAIL_SENDER", "your_email@gmail.com")
EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD", "abcdefghijklmnop")
EMAIL_RECEIVER = os.getenv("EMAIL_RECEIVER", "your_email@gmail.com")

GLOBAL_SETTINGS = {
    "min_over_prob": 58.0,
    "min_odds": 1.65
}

TARGET_LEAGUES = {
    "soccer_epl": "English Premier League",
    "soccer_spain_la_liga": "Spain La Liga",
    "soccer_germany_bundesliga": "Germany Bundesliga",
    "soccer_italy_serie_a": "Italy Serie A",
    "soccer_france_ligue_one": "France Ligue 1",
    "soccer_netherlands_eerste_divisie": "Netherlands Eerste Divisie",
    "soccer_germany_bundesliga2": "Germany 2. Bundesliga",
    "soccer_uefa_champs_league": "UEFA Champions League",
    "soccer_uefa_nations_league": "UEFA Nations League"
}