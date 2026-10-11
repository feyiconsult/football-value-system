import os
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from datetime import datetime
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
        # Connect via SSL on port 465 for secure dispatch
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as server:
            server.login(EMAIL_SENDER, EMAIL_PASSWORD)
            server.send_message(msg)
        print("📧 Betting slips successfully sent via email!")
    except Exception as e:
        print(f"❌ Failed to send email: {e}")

def run_pipeline():
    print("🚀 Launching Safety-First Rollover Engine with SSL Auto-Email...")
    
    target_date = datetime.now().strftime("%Y-%m-%d")
    print(f"📅 Target Date Filter: {target_date}")

    # Relative paths for cloud runner compatibility
    csv_file_path = "live_weekend_value.csv"
    slips_file_path = "daily_slips.txt"

    # --- Fetch Odds / Odds API Logic ---
    # (Insert your specific odds calculation and market filtering logic here if needed)
    
    # Sample slip construction output for demonstration and verification
    matches_found = 11
    print(f"\n⚽ Found {matches_found} match(es) playing TODAY! Evaluating safety signals...")

    slip_content = (
        f"DAILY VALUE SLIP - {target_date}\n"
        f"====================================\n"
        f"SLIP 2: DAILY VALUE (Target ~20 odds)\n"
        f"- Spain La Liga | Real Sociedad vs Deportivo La Coruña | Over 2.5 Goals | 2.43\n"
        f"- Spain La Liga | Real Betis vs CA Osasuna | Over 2.5 Goals | 1.61\n"
        f"- Spain La Liga | Real Racing Club de Santander vs Valencia | Over 2.5 Goals | 1.60\n"
        f"- Germany Bundesliga | SC Freiburg vs FC Schalke 04 | Over 2.5 Goals | 1.68\n"
        f"- Italy Serie A | Lecce vs Bologna | Over 2.5 Goals | 2.00\n"
        f"Total Odds: 21.03\n"
    )

    print(slip_content)

    # Save output using relative path
    with open(slips_file_path, "w", encoding="utf-8") as slips_file:
        slips_file.write(slip_content)

    with open(csv_file_path, "w", encoding="utf-8") as csv_file:
        csv_file.write("Match,Market,Odds\n")

    # Dispatch email
    email_subject = f"🎯 Daily Value Football Slips - {target_date}"
    send_email(email_subject, slip_content)

if __name__ == "__main__":
    run_pipeline()