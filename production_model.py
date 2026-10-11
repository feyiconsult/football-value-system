# production_model.py - Unlimited Safety-First Rollover & Global Value Engine
import os
import requests
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime, timezone
from scipy.stats import poisson
from config import (
    ODDS_API_KEY, 
    TARGET_LEAGUES, 
    GLOBAL_SETTINGS, 
    EMAIL_SENDER, 
    EMAIL_PASSWORD, 
    EMAIL_RECEIVER
)

def calculate_match_probabilities(home_lambda=1.85, away_lambda=1.40, max_goals=6):
    """Calculates Poisson probabilities for Over 1.5, Over 2.5, and BTTS."""
    over_1_5_prob = 0.0
    over_2_5_prob = 0.0
    btts_prob = 0.0

    for h in range(max_goals + 1):
        for a in range(max_goals + 1):
            prob = poisson.pmf(h, home_lambda) * poisson.pmf(a, away_lambda)
            if (h + a) > 1.5:
                over_1_5_prob += prob
            if (h + a) > 2.5:
                over_2_5_prob += prob
            if h > 0 and a > 0:
                btts_prob += prob

    return {
        "over_1_5_pct": round(over_1_5_prob * 100, 1),
        "over_2_5_pct": round(over_2_5_prob * 100, 1),
        "btts_pct": round(btts_prob * 100, 1)
    }

def send_daily_email(slips_text):
    """Sends formatted daily slips via Gmail SSL on Port 465 to prevent timeouts."""
    if not slips_text or "No value bets" in slips_text or "No active matches" in slips_text:
        print("ℹ️ Skipping email dispatch: No active value slips generated today.")
        return

    today_str = datetime.now().strftime("%Y-%m-%d")
    
    msg = MIMEMultipart()
    msg['From'] = EMAIL_SENDER
    msg['To'] = EMAIL_RECEIVER
    msg['Subject'] = f"⚽ Daily Football Rollover & Value Slips - {today_str}"

    body = f"Hello,\n\nHere are your automated daily football slips for {today_str}:\n\n{slips_text}\n\nGood luck!"
    msg.attach(MIMEText(body, 'plain'))

    try:
        print("📧 Connecting to email server via SSL (Port 465)...")
        with smtplib.SMTP_SSL('smtp.gmail.com', 465, timeout=15) as server:
            server.login(EMAIL_SENDER, EMAIL_PASSWORD)
            server.send_message(msg)
        print("✅ Daily slips successfully sent to your email!")
    except Exception as e:
        print(f"⚠️ Failed to send email: {e}")

def fetch_live_odds():
    """Fetches live lines for TODAY across global leagues and international matches."""
    all_fixtures = []
    seen_matches = set()
    
    today_utc = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    print(f"📅 Target Date Filter: {today_utc}")

    for sport_key, league_name in TARGET_LEAGUES.items():
        url = f"https://api.the-odds-api.com/v4/sports/{sport_key}/odds"
        params = {
            "apiKey": ODDS_API_KEY,
            "regions": "eu",
            "markets": "totals",
            "oddsFormat": "decimal"
        }
        
        try:
            response = requests.get(url, params=params, timeout=10)
            if response.status_code != 200:
                continue

            data = response.json()
            for match in data:
                commence_time = match.get("commence_time", "")
                if not commence_time.startswith(today_utc):
                    continue

                home_team = match.get("home_team", "Home")
                away_team = match.get("away_team", "Away")
                match_id = f"{home_team}_vs_{away_team}"

                if match_id in seen_matches:
                    continue
                
                odds_found = False
                for bookmaker in match.get("bookmakers", []):
                    if odds_found:
                        break
                    for market in bookmaker.get("markets", []):
                        if market["key"] == "totals":
                            for outcome in market["outcomes"]:
                                if outcome["name"] == "Over" and outcome["point"] == 2.5:
                                    all_fixtures.append({
                                        "League_Name": league_name,
                                        "Home": home_team,
                                        "Away": away_team,
                                        "Bookie_Odds": outcome["price"],
                                        "Kickoff": commence_time
                                    })
                                    seen_matches.add(match_id)
                                    odds_found = True
                                    break
        except Exception:
            continue

    return all_fixtures

def generate_formatted_slips(value_bets):
    """Generates a Safety-First Rollover Combo and a Daily Value Slip."""
    if not value_bets:
        return "ℹ️ No active matches matching system safety criteria for today."

    slip_output = ""

    # 1. ROLLOVER SAFETY SLIP (High Probability Picks >= 65%)
    safety_picks = [b for b in value_bets if b["Over_2_5_Chance"] >= 65.0]
    safety_picks.sort(key=lambda x: x["Over_2_5_Chance"], reverse=True)

    if len(safety_picks) >= 2:
        rollover_matches = safety_picks[:2]
        rollover_odds = 1.0
        
        slip_output += "SLIP 1: ROLLOVER SAFETY COMBO (Target 1.50 - 1.80 odds)\n"
        for m in rollover_matches:
            slip_output += f"- {m['League_Name']} | {m['Home']} vs {m['Away']} | Over 2.5 Goals | {m['Bookie_Odds']}\n"
            rollover_odds *= m['Bookie_Odds']
        slip_output += f"- Total Odds: {round(rollover_odds, 2)}\n\n"

    # 2. DAILY VALUE SLIP (Top 5 Matches)
    value_bets.sort(key=lambda x: x["Over_2_5_Chance"], reverse=True)
    value_matches = value_bets[:5]
    value_odds = 1.0
    
    slip_output += "SLIP 2: DAILY VALUE (Target ~20 odds)\n"
    for m in value_matches:
        slip_output += f"- {m['League_Name']} | {m['Home']} vs {m['Away']} | Over 2.5 Goals | {m['Bookie_Odds']}\n"
        value_odds *= m['Bookie_Odds']
    slip_output += f"- Total Odds: {round(value_odds, 2)}\n"

    print(slip_output)
    return slip_output

def run_pipeline():
    print("🚀 Launching Safety-First Rollover Engine with SSL Auto-Email...")
    fixtures = fetch_live_odds()

    csv_rows = ["League,Home_Team,Away_Team,Over_2_5_Chance,BTTS_Chance,Bookie_Price,True_Odds,System_Signal"]
    value_bets = []

    if not fixtures:
        print("\nℹ️ No active matches scheduled for TODAY across monitored global leagues.")
    else:
        print(f"\n⚽ Found {len(fixtures)} match(es) playing TODAY! Evaluating safety signals...")
        for f in fixtures:
            probs = calculate_match_probabilities(1.85, 1.40)
            over_prob = probs["over_2_5_pct"]
            btts_prob = probs["btts_pct"]
            bookie_odds = f["Bookie_Odds"]
            true_odds = round(100 / over_prob, 2) if over_prob > 0 else 0.0

            if over_prob >= GLOBAL_SETTINGS["min_over_prob"] and bookie_odds > true_odds:
                value_bets.append({
                    "League_Name": f["League_Name"],
                    "Home": f["Home"],
                    "Away": f["Away"],
                    "Over_2_5_Chance": over_prob,
                    "Bookie_Odds": bookie_odds
                })

            row = f"{f['League_Name']},{f['Home']},{f['Away']},{over_prob}%,{btts_prob}%,{bookie_odds},{true_odds}"
            csv_rows.append(row)

    # 1. Save CSV report to Desktop
    desktop = os.path.expanduser("~/Desktop")
    file_path = "live_weekend_value.csv"
    with open(file_path, "w", encoding="utf-8") as file:
        file.write("\n".join(csv_rows))

    # 2. Save formatted slips to Desktop
    slips_text = generate_formatted_slips(value_bets)
    slips_file_path = os.path.join(desktop, "daily_slips.txt")
    with open(slips_file_path, "w", encoding="utf-8") as slips_file:
        slips_file.write(slips_text)

    print(f"📂 Updated reports saved to Desktop.")

    # 3. Dispatch Email Notification
    send_daily_email(slips_text)

if __name__ == "__main__":
    run_pipeline()