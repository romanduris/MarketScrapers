import smtplib
import os
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from pathlib import Path
from datetime import datetime
import json
import yfinance as yf
import time

# ---------- SETTINGS ----------
SENDER_EMAIL = "Rodu.Market.Scraper@gmail.com"
alias_name = "RODU Market Scraper"
EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD")

INPUT_FILE = Path("data/step8_SLTP.json")
SUBSCRIBER_FILE = Path("data/subscribers.json")
REPORT_LINK = "https://romanduris.github.io/MarketScrapers/ai_report.html"
ANALYZE_LINK = "https://romanduris.github.io/MarketScrapers/ai_analyze.html"

YAHOO_FINANCE_URL = "https://finance.yahoo.com/quote/{ticker}"

# ---------- Market/sector config ----------
MARKET_INDEX = "^GSPC"  # S&P 500

SECTOR_ETF = {
    "Technology": "XLK",
    "Healthcare": "XLV",
    "Financial Services": "XLF",
    "Financial": "XLF",
    "Energy": "XLE",
    "Industrials": "XLI",
    "Utilities": "XLU",
    "Real Estate": "XLRE",
    "Consumer Defensive": "XLP",
    "Consumer Staples": "XLP",
    "Consumer Cyclical": "XLY",
    "Basic Materials": "XLB",
    "Materials": "XLB",
    "Communication Services": "XLC"
}

THROTTLE_SECONDS = 0.25

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

# ---------- Market Overview helpers ----------
def throttled_sleep():
    time.sleep(THROTTLE_SECONDS)

def get_multi_trend(ticker):
    throttled_sleep()
    try:
        t = yf.Ticker(ticker)
        hist = t.history(period="30d")
        if len(hist) < 21:
            return None, None, None
        close = hist["Close"]
        change_1d = ((close.iloc[-1] / close.iloc[-2]) - 1) * 100
        change_5d = ((close.iloc[-1] / close.iloc[-6]) - 1) * 100
        change_20d = ((close.iloc[-1] / close.iloc[-21]) - 1) * 100
        return change_1d, change_5d, change_20d
    except Exception as e:
        print(f"❌ Error fetching {ticker}: {e}")
        return None, None, None

def calculate_trend(change):
    if change is None:
        return "neutral"
    if change > 1.0:
        return "up"
    elif change < -1.0:
        return "down"
    return "neutral"

def generate_market_overview():
    _, market_5d, _ = get_multi_trend(MARKET_INDEX)
    market_trend = calculate_trend(market_5d)

    up_count = down_count = neutral_count = 0
    for etf in SECTOR_ETF.values():
        _, sec_5d, _ = get_multi_trend(etf)
        trend = calculate_trend(sec_5d)
        if trend == "up":
            up_count += 1
        elif trend == "down":
            down_count += 1
        else:
            neutral_count += 1

    arrows = {"up": "▲", "down": "▼", "neutral": "→"}
    colors = {"up": "#2ecc71", "down": "#e74c3c", "neutral": "#f39c12"}

    return f"""
    <h3>📈 Market Overview</h3>
    <p>
    S&P 500: <b style='color:{colors[market_trend]}'>{arrows[market_trend]} {market_trend.upper()}</b><br>
    Sectors: 🟩 UP: {up_count} , 🟨 NEUTRAL: {neutral_count} , 🟥 DOWN: {down_count}
    </p>
    <hr>
    """

# ---------- Helper: load subscribers ----------
def load_subscribers():
    if not SUBSCRIBER_FILE.exists():
        print("⚠️ subscribers.json not found.")
        return []
    with open(SUBSCRIBER_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)
    return [s for s in data if s.get("active", False)]

# ---------- SEND EMAIL ----------
def send_email():
    print("📨 Generujem email...")

    raw = count_tickers(Path("data/step1_raw.json"))
    fundamental = count_tickers(Path("data/step2_FundamentalFilter.json"))
    technical = count_tickers(Path("data/step4_IndicatorsFilter.json"))
    sentiment = count_tickers(Path("data/step5_SentimentFilter.json"))

    removed_fundamental = raw - fundamental
    removed_technical = fundamental - technical
    removed_sentiment = technical - sentiment

    top5 = extract_top5_from_json()
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    stats_html = f"""
        <h3>📊 MarketScraper Today's Pipeline Summary</h3>
        <ul>
            <li><b>Raw tickers:</b> {raw}</li>
            <li><b>Fundamental Analysis:</b> {fundamental} 
                <span style="color:#c0392b;">(filtered out: {removed_fundamental})</span></li>
            <li><b>Technical Analysis:</b> {technical}
                <span style="color:#c0392b;">(filtered out: {removed_technical})</span></li>
            <li><b>Sentiment Filter:</b> {sentiment}
                <span style="color:#c0392b;">(filtered out: {removed_sentiment})</span></li>
        </ul>
        <p>The remaining {sentiment} tickers were analyzed using <b>advanced AI ranking</b>, from which the <b>Top 20</b> were selected — and below you will find today's <b>Top 5</b>.</p>
        <hr>
    """

    market_html = generate_market_overview()

    subscribers = load_subscribers()
    if not subscribers:
        print("⚠️ No active subscribers found. Aborting email send.")
        return

    try:
        print("📡 Connecting to Gmail...")
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(SENDER_EMAIL, EMAIL_PASSWORD)

            for sub in subscribers:
                recipient_email = sub["email"]
                recipient_name = sub.get("name", "").strip() or "Trader"
                plan = sub.get("plan", "").upper()

                # Personalizované oslovenie
                email_html = f"<html><body style='font-family:Arial; font-size:14px; color:#333;'>"
                email_html += f"<p>Dear {recipient_name},</p><p>✅ Stock Report has been generated: 📅 <b>{now_str}</b></p><hr>"

                # Základný obsah pre všetkých
                email_html += market_html + stats_html

                # --- Extra links a hlášky podľa plánu ---
                if plan == "VIP":
                    email_html += f'<p>🔗 Full report: <a href="{REPORT_LINK}" target="_blank">{REPORT_LINK}</a></p>'
                    email_html += f'<p>🔗 Analysis of all tickers: <a href="{ANALYZE_LINK}" target="_blank">{ANALYZE_LINK}</a></p>'
                elif plan == "PREMIUM":
                    email_html += f'<p>🔗 Full report: <a href="{REPORT_LINK}" target="_blank">{REPORT_LINK}</a></p>'
                    email_html += '<p>⚠️ Your subscription level does not allow backets access</p>'
                elif plan == "EA":
                    email_html += f'<p>🔗 Full report: <a href="{REPORT_LINK}" target="_blank">{REPORT_LINK}</a></p>'
                    email_html += '<p>⚠️ Your subscription level does not allow backets access</p>'
                elif plan == "DEMO":
                    email_html += '<p>⚠️ Your subscription level does not allow full report access</p>'
                    email_html += '<p>⚠️ Your subscription level does not allow backets access</p>'

                # --- Top 5 stocks ---
                summary_html = ""
                if not top5:
                    summary_html = "<p>⚠️ Failed to load Top 5 stocks.</p>"
                else:
                    summary_html = "<h3>🔥 Top 5 Stocks selected</h3>"
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
                        """
                        # SL/TP iba pre VIP a EA
                        if plan in ["VIP", "EA"]:
                            summary_html += f"SL: <b>{stock['SL']}$</b>, TP: <b>{stock['TP']}$</b><br>"

                        summary_html += f"""
                            AI Score: {colorize_rating(stock['AIScore'])}, Overall: {colorize_rating(stock['OverallRating'])}, Market: {colorize_trend(stock.get('market_trend'))}, Sector: {colorize_trend(stock.get('sector_trend'))}<br><br>
                            <i>{stock['AITicker']}</i><br><br>
                            <i>{stock['AIComment']}</i>
                        </div>
                        """

                email_html += summary_html

                # --- Disclaimer ---
                email_html += """
                <hr>
                <p><b>LEGAL & SAFE DISCLAIMER</b><br>
                This product is provided for informational and educational purposes only. It does not constitute financial advice, investment recommendations, or an offer to buy or sell any securities.<br><br>
                You are solely responsible for your own trading and investment decisions. Past performance is not indicative of future results. The author/provider assumes no liability for losses, risks, or consequences arising from the use of this information. Trading and investing involve the risk of capital loss.
                </p>
                """

                # --- Footer ---
                email_html += "<p style='font-size:12px; color:#777;'>Automatically generated by the MarketScraper system 🤖</p></body></html>"

                msg = MIMEMultipart("alternative")
                msg["Subject"] = "📊 Your Daily Stock Report – Top Picks"
                msg["From"] = f"{alias_name} <{SENDER_EMAIL}>"
                msg["To"] = recipient_email
                msg.attach(MIMEText(email_html, "html", "utf-8"))

                try:
                    server.send_message(msg)
                    print(f"✅ Email sent to {recipient_email} ({recipient_name})")
                except Exception as e:
                    print(f"❌ Error sending to {recipient_email}: {e}")

                time.sleep(1)  # pauza medzi emailami

    except Exception as e:
        print(f"❌ Email sending error: {e}")


if __name__ == "__main__":
    send_email()
