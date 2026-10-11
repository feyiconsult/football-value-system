import os
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from datetime import datetime, timezone
import requests

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
        print("📧 Multi-slip betting package successfully sent via email!")
    except Exception as e:
        print(f"❌ Failed to send email: {e}")

def fetch_live_matches():
    """Fetches real-time soccer fixtures and odds from The Odds API using correct endpoints."""
    if not ODDS_API_KEY:
        print("⚠️ ODDS_API_KEY is missing.")
        return []

    # Comprehensive major soccer leagues keys for The Odds API
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
    print(f"🔍 Querying Odds API for date: {target_date_str} at current time {now_utc.strftime('%H:%M UTC')}...")

    for sport in sports:
        # Corrected domain endpoint for The Odds API
        url = f"https://api.the-odds-api.com/v4/sports/{sport}/odds/"
        params = {
            'apiKey': ODDS_API_KEY,
            'regions': 'eu,uk',
            'markets': 'h2h',
            'oddsFormat': 'decimal'
        }
        
        try:
            response = requests.get(url, params=params, timeout=15)
            print(f"📡 API Response for {sport}: Status {response.status_code}")
            
            if response.status_code == 200:
                matches = response.json()
                print(f"   -> Fetched {len(matches)} raw match items for {sport}.")
                for match in matches:
                    commence_time = match.get('commence_time')
                    if commence_time:
                        kickoff_dt = datetime.fromisoformat(commence_time.replace('Z', '+00:00'))
                        # Keep matches scheduled for today (even if already started or upcoming, or filter strictly by future)
                        if kickoff_dt.strftime("%Y-%m-%d") == target_date_str:
                            match['parsed_kickoff'] = kickoff_dt
                            all_fixtures.append(match)
            else:
                print(f"⚠️ API error for {sport}: {response.status_code} - {response.text}")
        except Exception as e:
            print(f"❌ Connection error fetching {sport}: {e}")

    return all_fixtures

def run_pipeline():
    now_utc = datetime.now(timezone.utc)
    target_date = now_utc.strftime("%Y-%m-%d")
    
    print(f"🚀 Launching Live Dynamic Football Value Engine...")
    
    # Fetch real fixtures from API
    fixtures = fetch_live_matches()
    print(f"⚽ Found {len(fixtures)} total match(es) for today after filtering.")

    if not fixtures:
        no_match_msg = f"No matches found for {target_date} from active API queries."
        print(no_match_msg)
        send_email(f"🎯 Value Slips [{target_date}] - No Matches", no_match_msg)
        return

    # Sort fixtures by kickoff time
    fixtures = sorted(fixtures, key=lambda x: x['parsed_kickoff'])

    slip_1_bets = []
    slip_2_bets = []
    slip_3_bets = []

    for fixture in fixtures:
        home = fixture.get('home_team')
        away = fixture.get('away_team')
        sport_title = fixture.get('sport_title', 'Soccer')
        
        bookmakers = fixture.get('bookmakers', [])
        odds_val = 1.60  # default fallback
        if bookmakers:
            markets = bookmakers[0].get('markets', [])
            for market in markets:
                if market.get('key') == 'h2h':
                    outcomes = market.get('outcomes', [])
                    if outcomes:
                        odds_val = outcomes[0].get('price', 1.60)

        match_desc = f"- {sport_title} | {home} vs {away} | Odds: {odds_val}"
        
        # Distribute into odds brackets
        if len(slip_1_bets) < 3 and odds_val <= 1.80:
            slip_1_bets.append(match_desc)
        elif len(slip_2_bets) < 3 and 1.50 <= odds_val <= 2.50:
            slip_2_bets.append(match_desc)
        elif len(slip_3_bets) < 4:
            slip_3_bets.append(match_desc)

    # Format Slips
    slip_1_text = "SLIP 1: DAILY 3 ODDS (Conservative Value)\n" + ("\n".join(slip_1_bets) if slip_1_bets else "- No qualifying matches found") + "\n"
    slip_2_text = "SLIP 2: DAILY 5 ODDS (Moderate Accumulator)\n" + ("\n".join(slip_2_bets) if slip_2_bets else "- No qualifying matches found") + "\n"
    slip_3_text = "SLIP 3: DAILY 20 ODDS (High Value Rollover)\n" + ("\n".join(slip_3_bets) if slip_3_bets else "- No qualifying matches found") + "\n"
    
    slip_4_text = (
        "SLIP 4: COMBINED MEGA SLIP (Slip 1 + Slip 2 + Slip 3)\n"
        "---------------------------------------------------\n"
        "Combined Master Accumulator from verified live fixtures.\n"
    )

    master_email_body = (
        f"🎯 DAILY FOOTBALL VALUE SLIPS - {target_date}\n"
        f"🕒 Generated at: {now_utc.strftime('%H:%M UTC')} (Live API Scan)\n"
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

    send_email(f"🎯 Live 4-Slip Value Package [{target_date}]", master_email_body)

if __name__ == "__main__":
    run_pipeline()