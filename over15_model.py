import os
import requests
import smtplib
from datetime import datetime, timezone, timedelta
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

from config import (
    ODDS_API_KEY, 
    TARGET_LEAGUES, 
    GLOBAL_SETTINGS, 
    EMAIL_SENDER, 
    EMAIL_PASSWORD, 
    EMAIL_RECEIVER
)

def estimate_probabilities_from_odds(over_odds, under_odds):
    if not over_odds or not under_odds or over_odds <= 1.0 or under_odds <= 1.0:
        return 50.0, 50.0
    raw_over = 1 / over_odds
    raw_under = 1 / under_odds
    total_margin = raw_over + raw_under
    return round((raw_over / total_margin) * 100, 1), round((raw_under / total_margin) * 100, 1)

def calculate_kelly_stake(system_prob_pct, total_odds):
    p = system_prob_pct / 100.0
    q = 1.0 - p
    b = total_odds - 1.0  
    if b <= 0: return 0.0
    raw_kelly = (p * b - q) / b
    return round(max(0.0, raw_kelly * GLOBAL_SETTINGS.get("kelly_fraction", 0.05)), 4)

def fetch_live_odds():
    raw_fixtures = []
    
    today_dt = datetime.now(timezone.utc)
    allowed_dates = [(today_dt + timedelta(days=i)).strftime("%Y-%m-%d") for i in range(7)]
    print(f"🎯 Scanning Matches across target Leagues ({allowed_dates[0]} to {allowed_dates[-1]})...")

    for sport_key, league_name in TARGET_LEAGUES.items():
        url = f"https://api.the-odds-api.com/v4/sports/{sport_key}/odds/"
        params = {
            "apiKey": str(ODDS_API_KEY).strip(), 
            "regions": "eu,uk", 
            "markets": "totals", 
            "oddsFormat": "decimal"
        }
        try:
            response = requests.get(url, params=params, timeout=15)
            if response.status_code != 200: 
                continue
            
            for match in response.json():
                commence_time = match.get("commence_time", "")
                if not any(commence_time.startswith(d) for d in allowed_dates): 
                    continue
                
                home_team = match.get("home_team")
                away_team = match.get("away_team")
                
                for bookmaker in match.get("bookmakers", []):
                    for market in bookmaker.get("markets", []):
                        if market["key"] == "totals":
                            over_25_odds, under_25_odds = None, None
                            
                            for outcome in market["outcomes"]:
                                pt = outcome.get("point")
                                if pt == 2.5:
                                    if outcome["name"] == "Over": over_25_odds = outcome["price"]
                                    elif outcome["name"] == "Under": under_25_odds = outcome["price"]
                            
                            if over_25_odds and under_25_odds:
                                raw_fixtures.append({
                                    "League": league_name, 
                                    "Home": home_team, 
                                    "Away": away_team, 
                                    "Odds_25": over_25_odds, 
                                    "Under_Odds_25": under_25_odds,
                                    "Commence": commence_time[:10]
                                })
                                break
        except Exception as e:
            pass
            
    unique_fixtures = {}
    for f in raw_fixtures:
        match_key = (f["Home"], f["Away"])
        if match_key not in unique_fixtures:
            unique_fixtures[match_key] = f

    return list(unique_fixtures.values())

def build_slips(fixtures):
    processed = []
    for f in fixtures:
        prob_25, _ = estimate_probabilities_from_odds(f["Odds_25"], f["Under_Odds_25"])
        
        # Derived conservative estimate for Over 1.5 based on the match's goal potential
        prob_15 = min(96.0, round(prob_25 * 1.22, 1))
        odds_15 = round(max(1.05, 100 / (prob_15 * 0.92)), 2)
        
        processed.append({
            "Commence": f["Commence"],
            "League": f["League"],
            "Home": f["Home"],
            "Away": f["Away"],
            "Odds_25": f["Odds_25"],
            "Prob_25": prob_25,
            "Odds_15": odds_15,
            "Prob_15": prob_15
        })
        
    # Sort top 20 for Over 2.5
    slip_25 = sorted(processed, key=lambda x: x["Prob_25"], reverse=True)[:20]
    # Sort top 20 for Over 1.5 extracted from the pool
    slip_15 = sorted(processed, key=lambda x: x["Prob_15"], reverse=True)[:20]
    
    return slip_25, slip_15

def generate_html_slip(title, matches, market_type):
    total_odds = 1.0
    total_prob = 0.0
    
    html = f"<h3>{title} ({len(matches)} Games)</h3>"
    html += "<table border='1' cellpadding='5' style='border-collapse:collapse; width:100%;'><tr style='background:#f2f2f2;'><th>Date</th><th>League</th><th>Match</th><th>Market</th><th>Odds</th><th>Prob</th></tr>"
    
    for m in matches:
        odds = m["Odds_25"] if market_type == "Over 2.5" else m["Odds_15"]
        prob = m["Prob_25"] if market_type == "Over 2.5" else m["Prob_15"]
        total_odds *= odds
        total_prob += prob
        html += f"<tr><td>{m['Commence']}</td><td>{m['League']}</td><td>{m['Home']} vs {m['Away']}</td><td>{market_type}</td><td><b>{odds:.2f}</b></td><td>{prob}%</td></tr>"
        
    avg_prob = total_prob / len(matches) if matches else 0
    total_bankroll = GLOBAL_SETTINGS.get("total_bankroll", 100000)
    kelly_pct = calculate_kelly_stake(avg_prob, total_odds)
    stake = round(total_bankroll * kelly_pct, 2)
    
    html += f"</table><br><p><b>Total Multiplied Odds:</b> <b>{total_odds:.2f}</b><br><b>Average Probability:</b> {avg_prob:.1f}%<br><b>💰 Recommended Stake:</b> <span style='color:green;'><b>₦{stake}</b></span></p><hr>"
    return html, total_odds

def send_email(html_body):
    if not EMAIL_SENDER or not EMAIL_PASSWORD or not EMAIL_RECEIVER:
        print("⚠️ Email credentials incomplete in config.py. Skipping email dispatch.")
        return
    msg = MIMEMultipart()
    msg['From'] = EMAIL_SENDER
    msg['To'] = EMAIL_RECEIVER
    msg['Subject'] = f"🔥 Grinder Dual Accumulator Slips (Over 2.5 & Over 1.5) - {datetime.now().strftime('%Y-%m-%d')}"
    msg.attach(MIMEText(html_body, 'html'))
    try:
        with smtplib.SMTP_SSL('smtp.gmail.com', 465, timeout=15) as server:
            server.login(EMAIL_SENDER, EMAIL_PASSWORD)
            server.send_message(msg)
        print("📧 Dual Accumulator report successfully sent to your email!")
    except Exception as e:
        print(f"❌ Failed to send email: {e}")

def run_pipeline():
    print("🚀 Launching 'The Grinder' Dual Accumulator Engine...")
    fixtures = fetch_live_odds()
    print(f"📊 Evaluated {len(fixtures)} unique fixtures across target leagues.")
    
    slip_25, slip_15 = build_slips(fixtures)
    
    # Generate HTML reports
    html_25, odds_25 = generate_html_slip("SLIP 1: OVER 2.5 GOALS ACCUMULATOR", slip_25, "Over 2.5")
    html_15, odds_15 = generate_html_slip("SLIP 2: OVER 1.5 GOALS ACCUMULATOR", slip_15, "Over 1.5")
    full_html = html_25 + html_15
    
    print(f"✅ Slip 1 (Over 2.5) Total Multiplied Odds: {odds_25:.2f}")
    print(f"✅ Slip 2 (Over 1.5) Total Multiplied Odds: {odds_15:.2f}")
    
    # Save separate CSV reports on Desktop folder
    csv_rows = ["Slip_Type,Date,League,Home_Team,Away_Team,Market,Bookie_Price,System_Prob"]
    for m in slip_25:
        csv_rows.append(f"OVER_2.5_SLIP,{m['Commence']},{m['League']},{m['Home']},{m['Away']},Over 2.5,{m['Odds_25']},{m['Prob_25']}%")
    for m in slip_15:
        csv_rows.append(f"OVER_1.5_SLIP,{m['Commence']},{m['League']},{m['Home']},{m['Away']},Over 1.5,{m['Odds_15']},{m['Prob_15']}%")
        
    local_path = "curated_dual_accumulator_slips.csv"
    with open(local_path, "w", encoding="utf-8") as f:
        f.write("\n".join(csv_rows))
    print(f"📁 Local Dual Slips saved to: {os.path.abspath(local_path)}")
    
    # Dispatch Email
    send_email(full_html)

if __name__ == "__main__":
    run_pipeline()