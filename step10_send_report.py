import smtplib 
import os
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from pathlib import Path
from datetime import datetime
import json

# ---------- SETTINGS ----------
SENDER_EMAIL = "roman.duris@gmail.com"
RECEIVER_EMAIL = "roman.duris@gmail.com"
EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD")

INPUT_FILE = Path("data/step8_SLTP.json")
REPORT_LINK = "https://romanduris.github.io/MarketScrapers/ai_report.html"
YAHOO_FINANCE_URL = "https://finance.yahoo.com/quote/{ticker}"

# ---------- Helper funkcie ----------
def colorize_rating(value):
    try:
        value = float(value)
    except:
        return f"<b>{value}</b>"
    if value >= 90:
        color = "#2ecc71"
    elif value >= 80:
        color = "#27ae60"
    elif value >= 70:
        color = "#f39c12"
    elif value >= 60:
        color = "#e67e22"
    elif value >= 50:
        color = "#e74c3c"
    else:
        color = "#c0392b"
    return f"<b style='color:{color}'>{value}</b>"

def colorize_trend(trend):
    if not trend:
        color = "#f39c12"
        text = "→ N/A"
    else:
        t = trend.strip().lower()
        if t == "up":
            color = "#2ecc71"
            text = "▲ UP"
        elif t == "down":
            color = "#e74c3c"
            text = "▼ DOWN"
        else:
            color = "#f39c12"
            text = f"→ {trend.strip().upper()}"
    return f"<b style='color:{color}'>{text}</b>"

def extract_top3_from_json():
    if not INPUT_FILE.exists():
        print(f"⚠️ Súbor {INPUT_FILE} neexistuje.")
        return []

    with open(INPUT_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)

    top3 = sorted(data, key=lambda x: x.get("AIScore", 0), reverse=True)[:3]
    return top3

# ---------- SEND EMAIL ----------
def send_email():
    print("📨 Generujem email...")
    top3 = extract_top3_from_json()
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    if not top3:
        summary_html = "<p>⚠️ Nepodarilo sa načítať TOP 3 akcie z reportu.</p>"
    else:
        summary_html = "<h3>🔥 TOP 3 akcie podľa AI</h3>"
        for stock in top3:
            yahoo_link = YAHOO_FINANCE_URL.format(ticker=stock['ticker'])
            summary_html += f"""
            <div style="margin-bottom:18px; padding:12px; border-left:4px solid #2c3e50;">
                <div style="font-size:15px; margin-bottom:6px;">
                    <b style="color:#2c3e50;">{stock['ticker']}</b> – 
                    <a href="{yahoo_link}" target="_blank" style="color:#1a3d7c; text-decoration:none;">
                        {stock['name']}
                    </a>
                </div>
                Cena: <b>{round(float(stock['price']),1)}$</b><br>
                SL: <b>{stock['SL']}$</b>, TP: <b>{stock['TP']}$</b><br>
                AI Score: {colorize_rating(stock['AIScore'])}, Overall: {colorize_rating(stock['OverallRating'])}
                , Market: {colorize_trend(stock.get('market_trend'))}, Sector: {colorize_trend(stock.get('sector_trend'))}<br><br>
                <i>{stock['AITicker']}</i><br><br>
                <i>{stock['AIComment']}</i>
            </div>
            """

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
