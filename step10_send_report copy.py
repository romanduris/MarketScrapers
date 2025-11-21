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
ANALYZE_LINK = "https://romanduris.github.io/MarketScrapers/ai_analyze.html"

YAHOO_FINANCE_URL = "https://finance.yahoo.com/quote/{ticker}"

# ---------- Helper: count tickers in a file ----------
def count_tickers(path):
    if not path.exists():
        return 0
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
        return len(data)

# ---------- Helper: colorizers ----------
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
        return "<b style='color:#f39c12'>→ N/A</b>"
    t = trend.strip().lower()
    if t == "up":
        return "<b style='color:#2ecc71'>▲ UP</b>"
    elif t == "down":
        return "<b style='color:#e74c3c'>▼ DOWN</b>"
    return f"<b style='color:#f39c12'>→ {trend.strip().upper()}</b>"

# ---------- Helper: Top 5 ----------
def extract_top5_from_json():
    if not INPUT_FILE.exists():
        return []
    with open(INPUT_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)
    return sorted(data, key=lambda x: x.get("AIScore", 0), reverse=True)[:5]

# ---------- SEND EMAIL ----------
def send_email():
    print("📨 Generujem email...")

    # ---- Load statistics ----
    raw = count_tickers(Path("data/step1_raw.json"))
    fundamental = count_tickers(Path("data/step2_FundamentalFilter.json"))
    technical = count_tickers(Path("data/step4_IndicatorsFilter.json"))
    sentiment = count_tickers(Path("data/step5_SentimentFilter.json"))

    removed_fundamental = raw - fundamental
    removed_technical = fundamental - technical
    removed_sentiment = technical - sentiment

    # ---- Top 5 ----
    top5 = extract_top5_from_json()
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # ---- Statistics HTML ----
    stats_html = f"""
        <h3>📊 MarketScraper Daily Pipeline Summary</h3>
        <ul>
            <li><b>Raw tickers collected:</b> {raw}</li>
            <li><b>After Fundamental Analysis:</b> {fundamental} 
                <span style="color:#c0392b;">(filtered out: {removed_fundamental})</span></li>
            <li><b>After Technical Analysis:</b> {technical}
                <span style="color:#c0392b;">(filtered out: {removed_technical})</span></li>
            <li><b>After Sentiment Filter:</b> {sentiment}
                <span style="color:#c0392b;">(filtered out: {removed_sentiment})</span></li>
        </ul>
        <p>The remaining {sentiment} tickers were analyzed using advanced AI ranking, 
        from which the <b>Top 20</b> were selected — and below you will find today's <b>Top 5</b>.</p>
        <hr>
    """

    # ---- Top 5 HTML ----
    if not top5:
        summary_html = "<p>⚠️ Failed to load Top 5 stocks.</p>"
    else:
        summary_html = "<h3>🔥 Top 5 Stocks selected by AI</h3>"
        for stock in top5:
            yahoo_link = YAHOO_FINANCE_URL.format(ticker=stock['ticker'])
            summary_html += f"""
            <div style="margin-bottom:18px; padding:12px; border-left:4px solid #2c3e50;">
                <div style="font-size:15px; margin-bottom:6px;">
                    <b style="color:#2c3e50;">{stock['ticker']}</b> – 
                    <a href="{yahoo_link}" target="_blank" style="color:#1a3d7c; text-decoration:none;">
                        {stock['name']}
                    </a>
                </div>
                Price: <b>{round(float(stock['price']),1)}$</b><br>
                SL: <b>{stock['SL']}$</b>, TP: <b>{stock['TP']}$</b><br>
                AI Score: {colorize_rating(stock['AIScore'])},
                Overall: {colorize_rating(stock['OverallRating'])},
                Market: {colorize_trend(stock.get('market_trend'))},
                Sector: {colorize_trend(stock.get('sector_trend'))}<br><br>
                <i>{stock['AITicker']}</i><br><br>
                <i>{stock['AIComment']}</i>
            </div>
            """

    # ---- Email content ----
    email_html = f"""
    <html>
    <body style="font-family:Arial; font-size:14px; color:#333;">

        <p>Dear Trader,</p>

        <p>✅ Your daily AI Stock Report has been generated : 📅 <b>{now_str}</b></p>

        <hr>

        {stats_html}

        <p>🔗 Full report: <a href="{REPORT_LINK}" target="_blank">{REPORT_LINK}</a></p>
        <p>🔗 Analysis of all tickers: <a href="{ANALYZE_LINK}" target="_blank">{ANALYZE_LINK}</a></p>

        {summary_html}

        <hr>
        <p style="font-size:12px; color:#777;">Automatically generated by the MarketScraper system 🤖</p>

    </body>
    </html>
    """

    # ---- Send ----
    msg = MIMEMultipart("alternative")
    msg["Subject"] = "📊 Daily AI Stock Report – Top Picks Inside"
    msg["From"] = SENDER_EMAIL
    msg["To"] = RECEIVER_EMAIL
    msg.attach(MIMEText(email_html, "html", "utf-8"))

    try:
        print("📡 Pripájam sa na Gmail...")
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(SENDER_EMAIL, EMAIL_PASSWORD)
            server.send_message(msg)
        print(f"✅ Email sent to {RECEIVER_EMAIL}")
    except Exception as e:
        print(f"❌ Email sending error: {e}")

if __name__ == "__main__":
    send_email()
