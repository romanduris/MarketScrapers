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
EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD")

REPORT_FILE = Path("docs/ai_report.html")
REPORT_LINK = "https://romanduris.github.io/MarketScrapers/ai_report.html"
YAHOO_FINANCE_URL = "https://finance.yahoo.com/quote/{ticker}"


def extract_top3_from_html():
    if not REPORT_FILE.exists():
        print(f"⚠️ Súbor {REPORT_FILE} neexistuje.")
        return []

    with open(REPORT_FILE, "r", encoding="utf-8") as f:
        soup = BeautifulSoup(f.read(), "html.parser")

    rows = soup.find_all("tr")[1:]
    extracted = []
    i = 0

    while i < 6 and i < len(rows):
        row1 = rows[i]
        row2 = rows[i + 1]
        cols = row1.find_all("td")
        comment = row2.find("td").get_text(strip=True)

        ticker_cell = cols[0] if len(cols) > 0 else None

        # ---------------- FIXED TICKER EXTRACTION ----------------
        ticker_text = ""
        name_text = ""
        if ticker_cell:
            small_tag = ticker_cell.find("small")
            name_text = small_tag.get_text(strip=True) if small_tag else ""
            # iba ticker pred <small>
            all_text = ticker_cell.get_text(separator="\n", strip=True)
            ticker_text = all_text.split("\n")[0]

        stock_data = {
            "ticker": ticker_text,
            "name": name_text,
            "price": cols[1].get_text(strip=True) if len(cols) > 1 else "",
            "SL": cols[2].get_text(strip=True) if len(cols) > 2 else "",
            "TP": cols[3].get_text(strip=True) if len(cols) > 3 else "",
            "AIScore": cols[4].get_text(strip=True) if len(cols) > 4 else "",
            "OverallRating": cols[5].get_text(strip=True) if len(cols) > 5 else "",
            "FundamentalFilterRating": cols[6].get_text(strip=True) if len(cols) > 6 else "",
            "TechFilterRating": cols[7].get_text(strip=True) if len(cols) > 7 else "",
            "NewsSentiment": cols[8].get_text(strip=True) if len(cols) > 8 else "",
            "AIComment": comment
        }

        extracted.append(stock_data)
        i += 2

    return extracted[:3]


def send_email():
    print("📨 Generujem email...")
    top3 = extract_top3_from_html()
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
                Cena: <b>{stock['price']}$</b><br>
                AI Score: <b>{stock['AIScore']}</b>, Overall: <b>{stock['OverallRating']}</b><br>
                SL: <b>{stock['SL']}$</b>, TP: <b>{stock['TP']}$</b><br><br>
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
