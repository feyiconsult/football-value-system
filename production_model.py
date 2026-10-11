import os
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from datetime import datetime, timezone
import requests
import scipy.stats as stats

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
        print("📧 Multi-market betting package successfully sent via email!")
    except Exception as e:
        print(f"❌ Failed to send email: {e}")

def fetch_diverse_european_matches():
    """Fetches real-time soccer fixtures and odds across a wide range of European leagues."""
    if not ODDS_API_KEY:
        print("⚠️ ODDS_API_KEY is missing.")
        return []

    # Expanded diverse European leagues
    sports = [
        'soccer_epl', 
        'soccer_spain_la_liga', 
        'soccer_italy_serie_a', 
        'soccer_germany_bundesliga', 
        'soccer_france_ligue_one',
        'soccer_netherlands_eredivisie',
        'soccer_portugal_primeira_liga',
        'soccer_turkey_super_lig',
        'soccer_belgium_first_division'
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

def evaluate_poisson_markets(home_lambda, away_lambda, home_price, away_price, max_goals=6):
    """Calculates probabilities for Straight Win, Over 2.5, and BTTS."""
    home_win_prob = 0
    over_25_prob = 0
    btts_prob = 0
    
    for h in range(max_goals + 1):
        for a in range(max_goals + 1):
            p = stats.poisson.pmf(h, home_lambda) * stats.poisson.pmf(a, away_lambda)
            if h > a:
                home_win_prob += p
            if h + a > 2.5:
                over_25_prob += p
            if h > 0 and a > 0:
                btts_prob += p
                
    return home_win_prob, over_25_prob, btts_prob

def run_pipeline():
    now_utc = datetime.now(timezone.utc)
    target_date = now_utc.strftime("%Y-%m-%d")
    
    print(f"🚀 Launching Diverse European Multi-Market Value Engine...")
    fixtures = fetch_diverse_european_matches()
    print(f"⚽ Analyzing {len(fixtures)} matches across diverse European leagues...")

    if not fixtures:
        no_match_msg = f"No matches found for {target_date} across target leagues."
        send_email(f"🎯 Value Slips [{target_date}] - No Matches", no_match_msg)
        return

    qualified_bets = []

    for fixture in fixtures:
        home = fixture.get('home_team')
        away = fixture.get('away_team')
        sport_title = fixture.get('sport_title', 'Soccer').replace('Soccer_', '').title()
        
        bookmakers = fixture.get('bookmakers', [])
        if not bookmakers:
            continue
            
        h2h_odds = {}
        totals_odds = {}
        
        for market in bookmakers[0].get('markets', []):
            if market.get('key') == 'h2h':
                for outcome in market.get('outcomes', []):
                    h2h_odds[outcome.get('name')] = outcome.get('price')
            elif market.get('key') == 'totals':
                for outcome in market.get('outcomes', []):
                    if outcome.get('point') == 2.5:
                        totals_odds[outcome.get('name')] = outcome.get('price')

        if home not in h2h_odds or away not in h2h_odds:
            continue

        home_price = h2h_odds[home]
        away_price = h2h_odds[away]

        # Expected goals heuristic based on odds pricing
        home_lambda = max(1.1, 2.7 / (home_price ** 0.45))
        away_lambda = max(0.9, 2.1 / (away_price ** 0.45))

        hw_prob, o25_prob, btts_prob = evaluate_poisson_markets(home_lambda, away_lambda, home_price, away_price)

        # 1. Evaluate Straight Win (High probability home win)
        if hw_prob > 0.60 and 1.35 <= home_price <= 2.20:
            qualified_bets.append({
                'market_type': 'Straight Win',
                'desc': f"- {sport_title} | {home} vs {away} | {home} to Win",
                'odds': home_price,
                'score': hw_prob
            })

        # 2. Evaluate Over 2.5 Goals
        over_price = totals_odds.get('Over', 1.85)
        if o25_prob > 0.58 and 1.50 <= over_price <= 2.20:
            qualified_bets.append({
                'market_type': 'Over 2.5 Goals',
                'desc': f"- {sport_title} | {home} vs {away} | Over 2.5 Goals",
                'odds': over_price,
                'score': o25_prob
            })

        # 3. Evaluate BTTS (Both Teams to Score)
        if btts_prob > 0.58 and 1.55 <= (1 / btts_prob) <= 2.20:
            btts_odds = round(1 / btts_prob, 2)
            qualified_bets.append({
                'market_type': 'BTTS',
                'desc': f"- {sport_title} | {home} vs {away} | BTTS (Yes)",
                'odds': btts_odds,
                'score': btts_prob
            })

    # Sort selections by statistical confidence score
    qualified_bets = sorted(qualified_bets, key=lambda x: x['score'], reverse=True)

    slip_1_bets = []
    slip_2_bets = []
    slip_3_bets = []

    for bet in qualified_bets:
        price = bet['odds']
        formatted_entry = f"{bet['desc']} ({bet['market_type']}) | Odds: {price}"
        
        if len(slip_1_bets) < 3 and price <= 1.80:
            slip_1_bets.append(formatted_entry)
        elif len(slip_2_bets) < 3 and 1.50 <= price <= 2.40:
            slip_2_bets.append(formatted_entry)
        elif len(slip_3_bets) < 4 and 1.80 <= price <= 3.50:
            slip_3_bets.append(formatted_entry)

    # Format Slips
    slip_1_text = "SLIP 1: DAILY 3 ODDS (Conservative Value)\n" + ("\n".join([f"- {b}" for b in slip_1_bets]) if slip_1_bets else "- No qualifying matches found") + "\n"
    slip_2_text = "SLIP 2: DAILY 5 ODDS (Moderate Accumulator)\n" + ("\n".join([f"- {b}" for b in slip_2_bets]) if slip_2_bets else "- No qualifying matches found") + "\n"
    slip_3_text = "SLIP 3: DAILY 20 ODDS (High Value Rollover)\n" + ("\n".join([f"- {b}" for b in slip_3_bets]) if slip_3_bets else "- No qualifying matches found") + "\n"
    
    slip_4_text = (
        "SLIP 4: COMBINED MEGA SLIP (Slip 1 + Slip 2 + Slip 3)\n"
        "---------------------------------------------------\n"
        "Master accumulator combining diverse European league selections.\n"
    )

    master_email_body = (
        f"🎯 DIVERSE EUROPEAN VALUE SLIPS - {target_date}\n"
        f"🕒 Generated at: {now_utc.strftime('%H:%M UTC')} (Multi-Market Analysis)\n"
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

    send_email(f"🎯 Diverse European Value Package [{target_date}]", master_email_body)

if __name__ == "__main__":
    run_pipeline()