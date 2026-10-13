import os
import requests
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime, timezone

from config import (
    ODDS_API_KEY, 
    TARGET_LEAGUES, 
    GLOBAL_SETTINGS, 
    EMAIL_SENDER, 
    EMAIL_PASSWORD, 
    EMAIL_RECEIVER
)

def estimate_probabilities_from_odds(over_odds, under_odds):
    if not over_odds or not under_odds: return 50.0, 50.0
    raw_over = 1 / over_odds
    raw_under = 1 / under_odds
    total_margin = raw_over + raw_under
    return round((raw_over / total_margin) * 100, 1), round((raw_under / total_margin) * 100, 1)

def calculate_kelly_stake(system_prob_pct, bookie_odds):
    p = system_prob_pct / 100.0
    q = 1.0 - p
    b = bookie_odds - 1.0  
    if b <= 0: return 0.0
    raw_kelly = (p * b - q) / b
    return round(max(0.0, raw_kelly * GLOBAL_SETTINGS.get("kelly_fraction", 0.25)), 4)

def fetch_live_odds():
    all_fixtures = []
    today_utc = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    print(f"?? Target Date Filter: {today_utc}")

    for sport_key, league_name in TARGET_LEAGUES.items():
        url = f"https://the-odds-api.com{sport_key}/odds"
        params = {"apiKey": str(ODDS_API_KEY).strip(), "regions": "eu", "markets": "totals", "oddsFormat": "decimal"}
        try:
            response = requests.get(url, params=params, timeout=15)
            if response.status_code != 200: continue
            for match in response.json():
                commence_time = match.get("commence_time", "")
                if not commence_time.startswith(today_utc): continue
                for bookmaker in match.get("bookmakers", []):
                    for market in bookmaker.get("markets", []):
                        if market["key"] == "totals":
                            over_odds, under_odds = None, None
                            for outcome in market["outcomes"]:
                                if outcome["point"] == 2.5:
                                    if outcome["name"] == "Over": over_odds = outcome["price"]
                                    elif outcome["name"] == "Under": under_odds = outcome["price"]
                            if over_odds and under_odds:
                                all_fixtures.append({"League": league_name, "Home": match.get("home_team"), "Away": match.get("away_team"), "Odds": over_odds, "Under_Odds": under_odds, "Market": "Over 2.5 Goals"})
                                break
        except Exception as e:
            pass
    return all_fixtures

def generate_accumulator_slip(value_matches, target_odds=20.0):
    if not value_matches: return "", []
    selected_matches = []
    current_total_odds = 1.0
    for match in sorted(value_matches, key=lambda x: x["System_Prob"], reverse=True):
        if current_total_odds < target_odds:
            selected_matches.append(match)
            current_total_odds *= match["Odds"]
        else: break
    if not selected_matches: return "", []
    avg_prob = sum(m["System_Prob"] for m in selected_matches) / len(selected_matches)
    suggested_stake = round(GLOBAL_SETTINGS.get("total_bankroll", 100000) * calculate_kelly_stake(avg_prob, current_total_odds), 2)
    html_text = "<h3>SLIP 1: DAILY VALUE SLIP</h3><table border='1' cellpadding='5' style='border-collapse:collapse; width:100%;'><tr style='background:#f2f2f2;'><th>League</th><th>Match</th><th>Odds</th><th>Prob</th><th>Stake %</th></tr>"
    for m in selected_matches:
        html_text += f"<tr><td>{m['League']}</td><td>{m['Home']} vs {m['Away']}</td><td><b>{m['Odds']:.2f}</b></td><td>{m['System_Prob']}%</td><td>{round(m['Kelly_Stake']*100,2)}%</td></tr>"
    html_text += f"</table><p><b>Total Odds:</b> {current_total_odds:.2f}<br><b>?? Rec. Stake:</b> <span style='color:green;'><b>?{suggested_stake}</b></span></p>"
    return html_text, selected_matches

def send_daily_email(html_body):
    if not html_body or "No matches" in html_body: return
    msg = MIMEMultipart()
    msg['From'] = EMAIL_SENDER; msg['To'] = EMAIL_RECEIVER; msg['Subject'] = f"? Daily Slips - {datetime.now().strftime('%Y-%m-%d')}"
    msg.attach(MIMEText(html_body, 'html'))
    try:
        with smtplib.SMTP_SSL('://gmail.com', 465, timeout=15) as server:
            server.login(EMAIL_SENDER, EMAIL_PASSWORD)
            server.send_message(msg)
        print("? Daily bankroll slips successfully sent to your email!")
    except Exception as e: print(f"?? Failed to send email: {e}")

def run_pipeline():
    print("?? Launching Bankroll-Managed Value Engine...")
    fixtures = fetch_live_odds()
    print(f"? Analyzing {len(fixtures)} matches across monitored European leagues...")
    csv_rows = ["League,Home_Team,Away_Team,Market,Bookie_Price,System_Prob,True_Odds,Kelly_Stake_Pct,Signal"]
    value_bets = []
    
    if not fixtures:
        csv_rows.append("No active matches scheduled for today across monitored leagues,,,,,,,,")
    else:
        for f in fixtures:
            over_prob, _ = estimate_probabilities_from_odds(f["Odds"], f["Under_Odds"])
            true_odds = round(100 / over_prob, 2) if over_prob > 0 else 0.0
            kelly_stake = calculate_kelly_stake(over_prob, f["Odds"])
            signal = "PASS"
            if over_prob >= GLOBAL_SETTINGS["min_over_prob"] and f["Odds"] >= GLOBAL_SETTINGS["min_odds"] and kelly_stake > 0:
                signal = "VALUE_BET"
                value_bets.append({"League": f["League"], "Home": f["Home"], "Away": f["Away"], "Market": f["Market"], "Odds": f["Odds"], "System_Prob": over_prob, "Kelly_Stake": kelly_stake})
            csv_rows.append(f"{f['League']},{f['Home']},{f['Away']},{f['Market']},{f['Odds']},{over_prob}%,{true_odds},{round(kelly_stake*100,2)}%,{signal}")
    
    html_slips, _ = generate_accumulator_slip(value_bets, target_odds=20.0)
    
    # CHANGED: Saves directly in the same folder where your script is running
    local_path = "live_weekend_value.csv"
    with open(local_path, "w", encoding="utf-8") as file:
        file.write("\n".join(csv_rows))
    print(f"?? Report successfully saved directly inside this folder as: {os.path.abspath(local_path)}")
    
    if html_slips:
        send_daily_email(html_slips)
    else:
        print("?? No high-value picks qualified for selection today. Staking report saved to local CSV.")

if __name__ == "__main__":
    run_pipeline()
