import os
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from datetime import datetime, timezone
import requests
import scipy.stats as stats
import numpy as np

# Import configuration variables from config.py
from config import ODDS_API_KEY, EMAIL_SENDER, EMAIL_PASSWORD, EMAIL_RECEIVER

def send_email(subject, content):
    """Sends a formatted email containing the generated slips using SSL."""
    if not EMAIL_SENDER or not EMAIL_PASSWORD or not EMAIL_RECEIVER:
        print("⚠️ Email credentials not fully set. Skipping email dispatch.")
        return

    msg = MIMEMultipart()
    msg['From'] = EMAIL_SENDER
    msg['To'] = EMAIL_RECEIVER
    msg['Subject'] = subject
    msg.attach(MIMEText(content, 'plain', 'utf-8'))

    try:
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as server:
            server.login(EMAIL_SENDER, EMAIL_PASSWORD)
            server.send_message(msg)
        print("📧 Value betting package successfully sent via email!")
    except Exception as e:
        print(f"❌ Failed to send email: {e}")

def fetch_live_matches():
    """Fetches real-time soccer fixtures and odds from The Odds API."""
    if not ODDS_API_KEY:
        print("⚠️ ODDS_API_KEY is missing.")
        return []

    sports = [
        'soccer_epl', 
        'soccer_spain_la_liga', 
        'soccer_italy_serie_a', 
        'soccer_germany_bundesliga', 
        'soccer_france_ligue_one'
    ]
    all_fixtures = []

    now_utc = datetime.now(timezone.utc)
    target_date_str = now_utc.strftime("%Y-%m-%d")

    for sport in sports:
        url = f"https://api.the-odds-api.com/v4/sports/{sport}/odds/"
        params = {
            'apiKey': ODDS_API_KEY,
            'regions': 'eu,uk',
            'markets': 'h2h,totals',
            'oddsFormat': 'decimal'
        }
        
        try:
            response = requests.get(url, params=params, timeout=15)
            if response.status_code == 200:
                matches = response.json()
                for match in matches:
                    commence_time = match.get('commence_time')
                    if commence_time:
                        kickoff_dt = datetime.fromisoformat(commence_time.replace('Z', '+00:00'))
                        if kickoff_dt.strftime("%Y-%m-%d") == target_date_str:
                            match['parsed_kickoff'] = kickoff_dt
                            all_fixtures.append(match)
        except Exception as e:
            print(f"❌ Connection error fetching {sport}: {e}")

    return all_fixtures

def calculate_poisson_probability(home_lambda, away_lambda, max_goals=5):
    """Calculates match outcome probabilities using the bivariate Poisson distribution."""
    home_win_prob = 0
    over_25_prob = 0
    
    for h in range(max_goals + 1):
        for a in range(max_goals + 1):
            p = stats.poisson.pmf(h, home_lambda) * stats.poisson.pmf(a, away_lambda)
            if h > a:
                home_win_prob += p
            if h + a > 2.5:
                over_25_prob += p
                
    return home_win_prob, over_25_prob

def run_pipeline():
    now_utc = datetime.now(timezone.utc)
    target_date = now_utc.strftime("%Y-%m-%d")
    
    print(f"🚀 Launching Statistical Poisson Value Engine...")
    fixtures = fetch_live_matches()
    print(f"⚽ Analyzing {len(fixtures)} total match(es) for today using statistical modeling...")

    if not fixtures:
        no_match_msg = f"No matches found for {target_date}."
        send_email(f"🎯 Value Slips [{target_date}] - No Matches", no_match_msg)
        return

    analyzed_bets = []

    for fixture in fixtures:
        home = fixture.get('home_team')
        away = fixture.get('away_team')
        sport_title = fixture.get('sport_title', 'Soccer').replace('Soccer_', '').title()
        
        bookmakers = fixture.get('bookmakers', [])
        if not bookmakers:
            continue
            
        # Extract market odds
        h2h_odds = {}
        for market in bookmakers[0].get('markets', []):
            if market.get('key') == 'h2h':
                for outcome in market.get('outcomes', []):
                    h2h_odds[outcome.get('name')] = outcome.get('price')

        if home not in h2h_odds or away not in h2h_odds:
            continue

        # Estimate expected goal rates (Lambda) based on market odds pricing heuristics
        # Lower odds indicate higher implied team strength
        home_price = h2h_odds[home]
        away_price = h2h_odds[away]
        
        home_lambda = max(1.0, 2.8 / (home_price ** 0.5))
        away_lambda = max(0.8, 2.2 / (away_price ** 0.5))

        # Run Poisson model analysis
        model_home_prob, model_over_prob = calculate_poisson_probability(home_lambda, away_lambda)

        # Evaluate Home Win Value Edge
        implied_home_prob = 1.0 / home_price
        home_edge = model_home_prob - implied_home_prob

        if home_edge > 0.03 and 1.30 <= home_price <= 3.50:
            analyzed_bets.append({
                'match': f"- {sport_title} | {home} vs {away} | {home} to Win",
                'odds': home_price,
                'edge': home_edge
            })

    # Sort bets by statistical edge/quality
    analyzed_bets = sorted(analyzed_bets, key=lambda x: x['edge'], reverse=True)

    slip_1_bets = []
    slip_2_bets = []
    slip_3_bets = []

    # Distribute selections into target odds categories
    for bet in analyzed_bets:
        price = bet['odds']
        desc = f"{bet['match']} | Odds: {price} (Edge: +{int(bet['edge']*100)}%)"
        
        if len(slip_1_bets) < 3 and price <= 1.80:
            slip_1_bets.append(desc)
        elif len(slip_2_bets) < 3 and 1.50 <= price <= 2.50:
            slip_2_bets.append(desc)
        elif len(slip_3_bets) < 4 and 2.00 <= price <= 5.50:
            slip_3_bets.append(desc)

    # Format Slips
    slip_1_text = "SLIP 1: DAILY 3 ODDS (Conservative Value)\n" + ("\n".join([f"- {b}" for b in slip_1_bets]) if slip_1_bets else "- No model-verified matches found") + "\n"
    slip_2_text = "SLIP 2: DAILY 5 ODDS (Moderate Accumulator)\n" + ("\n".join([f"- {b}" for b in slip_2_bets]) if slip_2_bets else "- No model-verified matches found") + "\n"
    slip_3_text = "SLIP 3: DAILY 20 ODDS (High Value Rollover)\n" + ("\n".join([f"- {b}" for b in slip_3_bets]) if slip_3_bets else "- No model-verified matches found") + "\n"
    
    slip_4_text = (
        "SLIP 4: COMBINED MEGA SLIP (Slip 1 + Slip 2 + Slip 3)\n"
        "---------------------------------------------------\n"
        "Master ticket combining statistically verified Poisson value edges.\n"
    )

    master_email_body = (
        f"🎯 STATISTICAL VALUE SLIPS - {target_date}\n"
        f"🕒 Generated at: {now_utc.strftime('%H:%M UTC')} (Poisson Model Analysis)\n"
        f"===================================================\n\n"
        f"{slip_1_text}\n"
        f"{slip_2_text}\n"
        f"{slip_3_text}\n"
        f"{slip_4_text}\n"
        f"===================================================\n"
    )

    print(master_email_body)

    with open("daily_slips.txt", "w", encoding="utf-8") as f:
        f.write(master_email_body)

    send_email(f"🎯 Statistical Value Package [{target_date}]", master_email_body)

if __name__ == "__main__":
    run_pipeline()