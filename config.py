# config.py - System Settings & Email Credentials

ODDS_API_KEY = ""

# EMAIL CONFIGURATION
EMAIL_SENDER = "feyiconsult@gmail.com"       # Your Gmail address
EMAIL_PASSWORD = "vddxfgwevvhipttw"          # Your 16-character App Password
EMAIL_RECEIVER = "feyiconsult@gmail.com"     # Where you want to receive the slips

# Global target parameters
GLOBAL_SETTINGS = {
    "min_over_prob": 58.0,
    "min_odds": 1.65,
    "total_bankroll": 100000,    # 💰 Input your actual total bankroll here (e.g., ₦100,000)
    "kelly_fraction": 0.25       # 🛡️ Quarter-Kelly (Recommended safety buffer)
}

# Target Leagues...
TARGET_LEAGUES = {
    "soccer_epl": "English Premier League",
    "soccer_spain_la_liga": "Spain La Liga",
    "soccer_germany_bundesliga": "Germany Bundesliga",
    "soccer_italy_serie_a": "Italy Serie A",
    "soccer_france_ligue_one": "France Ligue 1",
    "soccer_netherlands_eerste_divisie": "Netherlands Eerste Divisie",
    "soccer_germany_bundesliga2": "Germany 2. Bundesliga",
    "soccer_austria_bundesliga": "Austria Bundesliga",
    "soccer_uefa_champs_league": "UEFA Champions League",
    "soccer_uefa_europa_league": "UEFA Europa League"
}
