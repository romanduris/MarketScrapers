"""
STEP 7 – Odoslanie reportu e-mailom
Odošle report ako HTML správu s odkazom na GitHub Pages a samotným obsahom HTML.
"""

import smtplib
import os
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from pathlib import Path
from datetime import datetime

# Nastavenia (nahrad len email adresu)
SENDER_EMAIL = "roman.duris@gmail.com"
RECEIVER_EMAIL = "roman.duris@gmail.com"  # alebo zoznam ["a@b.com", "c@d.com"]
EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD")  # uložené ako Codespaces Secret
REPORT_FILE = Path("docs/ai_report.html")  # teraz sa generuje do docs/ pre GitHub Pages
REPORT_LINK = "https://romanduris.github.io/MarketScrapers/ai_report.html"

def send_email():
    if not REPORT_FILE.exists():
        print(f"⚠️ Súbor {REPORT_FILE} neexistuje.")
        return

    with open(REPORT_FILE, "r", encoding="utf-8") as f:
        html_content = f.read()

    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # Vytvorenie HTML správy
    email_html = f"""
    <html>
    <body>
        <p>📅 Report vygenerovaný: <b>{now_str}</b></p>
        <p>🔗 Report je dostupný online tu: <a href="{REPORT_LINK}">{REPORT_LINK}</a></p>
        <hr>
        {html_content}
    </body>
    </html>
    """

    msg = MIMEMultipart("alternative")
    msg["Subject"] = "📊 AI Stock Report"
    msg["From"] = SENDER_EMAIL
    msg["To"] = RECEIVER_EMAIL

    msg.attach(MIMEText(email_html, "html", "utf-8"))

    try:
        print("📨 Pripájam sa na Gmail server...")
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(SENDER_EMAIL, EMAIL_PASSWORD)
            server.send_message(msg)
        print(f"✅ Report úspešne odoslaný na {RECEIVER_EMAIL}")
    except Exception as e:
        print(f"❌ Chyba pri odosielaní e-mailu: {e}")

if __name__ == "__main__":
    send_email()
