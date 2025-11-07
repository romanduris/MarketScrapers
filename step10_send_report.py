"""
STEP 7 – Odoslanie krátkeho emailového súhrnu
- Pošle pekný e-mail s linkom na online report
- Do tela vloží prehľad TOP 3 akcií (Ticker, názov, AIComment, AIScore, Overall, cena, SL, TP)
"""

import smtplib
import os
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from pathlib import Path
from bs4 import BeautifulSoup
from datetime import datetime

# ---------- SETTINGS ----------
SENDER_EMAIL = "roman.duris@gmail.com"
RECEIVER_EMAIL = "roman.duris@gmail.com"
#EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD")
#EMAIL_USER = os.getenv("EMAIL_USER")
EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD")

REPORT_FILE = Path("docs/ai_report.html")
REPORT_LINK = "https://romanduris.github.io/MarketScrapers/ai_report.html"


def extract_top3_from_html():
    """Načíta ai_report.html a extrahuje TOP 3 akcie + ich údaje."""
    if not REPORT_FILE.exists():
        print(f"⚠️ Súbor {REPORT_FILE} neexistuje.")
        return []

    with open(REPORT_FILE, "r", encoding="utf-8") as f:
        soup = BeautifulSoup(f.read(), "html.parser")

    rows = soup.find_all("tr")[1:]  # preskočí hlavičku tabuľky

    extracted = []
    i = 0

    # HTML má 2 riadky na 1 akciu → vezmi prvých 6 <tr> (3 akcie)
    while i < 6 and i < len(rows):
        row1 = rows[i]
        row2 = rows[i + 1]

        cols = row1.find_all("td")
        comment = row2.find("td").get_text(strip=True)

        stock_data = {
            "ticker": cols[0].get_text(strip=True).split("\n")[0],
            "name": cols[0].find("small").get_text(strip=True),
            "price": cols[1].get_text(strip=True),
            "SL": cols[2].get_text(strip=True),
            "TP": cols[3].get_text(strip=True),
            "AIScore": cols[4].get_text(strip=True),
            "OverallRating": cols[5].get_text(strip=True),
            "FundamentalFilterRating": cols[6].get_text(strip=True),
            "TechFilterRating": cols[7].get_text(strip=True),
            "NewsSentiment": cols[8].get_text(strip=True),
            "AIComment": comment
        }

        extracted.append(stock_data)
        i += 2

    return extracted[:3]


def send_email():
    print("📨 Generujem email...")

    top3 = extract_top3_from_html()

    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # ---------- BUILD SHORT SUMMARY ----------
    if not top3:
        summary_html = "<p>⚠️ Nepodarilo sa načítať TOP 3 akcie z reportu.</p>"
    else:
        summary_html = "<h3>🔥 TOP 3 akcie podľa AI</h3>"
        for stock in top3:
            summary_html += f"""
            <div style="margin-bottom:18px; padding:10px; border-left:4px solid #2c3e50;">
                <b>{stock['ticker']} – {stock['name']}</b><br>
                Cena: <b>{stock['price']}$</b><br>
                AI Score: <b>{stock['AIScore']}</b>, Overall: <b>{stock['OverallRating']}</b><br>
                SL: <b>{stock['SL']}$</b>, TP: <b>{stock['TP']}$</b><br><br>
                <i>{stock['AIComment']}</i>
            </div>
            """

    # ---------- FINAL EMAIL HTML ----------
    email_html = f"""
    <html>
    <body style="font-family:Arial; font-size:14px; color:#333;">
        <p>✅ Tvoj denný AI Stock report bol úspešne vygenerovaný.</p>
        <p>📅 <b>{now_str}</b></p>

        <p>🔗 Kompletný prehľad nájdeš tu:<br>
        <a href="{REPORT_LINK}" target="_blank">{REPORT_LINK}</a></p>

        <hr>
        {summary_html}
        <hr>

        <p style="font-size:12px; color:#777;">Automaticky odoslané MarketScraper systémom 🤖</p>
    </body>
    </html>
    """

    msg = MIMEMultipart("alternative")
    msg["Subject"] = "📊 Denný AI Stock Report – TOP 3 inside"
    msg["From"] = SENDER_EMAIL
    msg["To"] = RECEIVER_EMAIL

    msg.attach(MIMEText(email_html, "html", "utf-8"))

    try:
        print("📡 Pripájam sa na Gmail...")
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(SENDER_EMAIL, EMAIL_PASSWORD)
            server.send_message(msg)
        print(f"✅ Email odoslaný na {RECEIVER_EMAIL}")
    except Exception as e:
        print(f"❌ Chyba pri odosielaní e-mailu: {e}")


if __name__ == "__main__":
    send_email()
