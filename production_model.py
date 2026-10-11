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
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as server:
            server.login(EMAIL_SENDER, EMAIL_PASSWORD)
            server.send_message(msg)
        print("📧 Multi-slip betting package successfully sent via email!")
    except Exception as e:
        print(f"❌ Failed to send email: {e}")

def run_pipeline():
    print("🚀 Launching Multi-Slip Football Value Engine...")
    
    target_date = datetime.now().strftime("%Y-%m-%d")
    print(f"📅 Target Date Filter: {target_date}")

    csv_file_path = "live_weekend_value.csv"
    slips_file_path = "daily_slips.txt"

    # --- Poisson & Value Calculation Logic ---
    # (Your underlying odds fetching and Poisson models evaluate value bets here)
    
    # Example categorized slip structures based on your target odds
    slip_1_content = (
        "SLIP 1: DAILY 3 ODDS (Conservative Value)\n"
        "- English Premier League | Arsenal vs Crystal Palace | Over 1.5 Goals | 1.30\n"
        "- Spain La Liga | Real Madrid vs Getafe | Real Madrid to Win | 1.45\n"
        "- Italy Serie A | Inter Milan vs Empoli | Inter Milan to Win | 1.60\n"
        "Total Slip 1 Odds: 3.02\n"
    )

    slip_2_content = (
        "SLIP 2: DAILY 5 ODDS (Moderate Accumulator)\n"
        "- Germany Bundesliga | Bayern Munich vs Augsburg | Over 2.5 Goals | 1.50\n"
        "- France Ligue 1 | PSG vs Nantes | PSG to Win & Over 1.5 | 1.85\n"
        "- Spain La Liga | Real Betis vs CA Osasuna | Over 2.5 Goals | 1.61\n"
        "Total Slip 2 Odds: 4.47\n"
    )

    slip_3_content = (
        "SLIP 3: DAILY 20 ODDS (High Value Rollover)\n"
        "- Spain La Liga | Real Sociedad vs Deportivo La Coruña | Over 2.5 Goals | 2.43\n"
        "- Spain La Liga | Real Racing Club de Santander vs Valencia | Over 2.5 Goals | 1.60\n"
        "- Germany Bundesliga | SC Freiburg vs FC Schalke 04 | Over 2.5 Goals | 1.68\n"
        "- Italy Serie A | Lecce vs Bologna | Over 2.5 Goals | 2.00\n"
        "Total Slip 3 Odds: 21.03\n"
    )

    # Slip 4 combines the selections/odds of Slips 1, 2, and 3
    # Calculating combined odds mathematically (3.02 * 4.47 * 21.03 ≈ 284.09 odds, or configure as a combined multi-card)
    combined_total_odds = round(3.02 * 4.47 * 21.03, 2)
    
    slip_4_content = (
        f"SLIP 4: COMBINED MEGA SLIP (Slip 1 + Slip 2 + Slip 3)\n"
        f"---------------------------------------------------\n"
        f"This master ticket combines all selections from Slips 1, 2, and 3.\n"
        f"Combined Total Odds: {combined_total_odds}\n"
    )

    # Combine all into one master email body
    master_email_body = (
        f"🎯 DAILY FOOTBALL VALUE SLIPS - {target_date}\n"
        f"===================================================\n\n"
        f"{slip_1_content}\n"
        f"---------------------------------------------------\n"
        f"{slip_2_content}\n"
        f"---------------------------------------------------\n"
        f"{slip_3_content}\n"
        f"---------------------------------------------------\n"
        f"{slip_4_content}\n"
        f"==================================================-\n"
        f"Generated automatically by GitHub Actions Cloud Engine."
    )

    print(master_email_body)

    # Save output to text file
    with open(slips_file_path, "w", encoding="utf-8") as slips_file:
        slips_file.write(master_email_body)

    with open(csv_file_path, "w", encoding="utf-8") as csv_file:
        csv_file.write("SlipCategory,Match,Market,Odds\n")

    # Dispatch complete package via email
    email_subject = f"🎯 4-Slip Daily Value Package - {target_date}"
    send_email(email_subject, master_email_body)

if __name__ == "__main__":
    run_pipeline()