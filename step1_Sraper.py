"""
Step 1 – Scraper v3
Získava dynamický zoznam akciových kandidátov z Yahoo Finance (API) a MarketWatch (RSS feed).
Výstup: data/step1_candidates.json
"""

import json
from pathlib import Path
from datetime import date
import requests
import yfinance as yf
from bs4 import BeautifulSoup

# ---------- KONFIGURÁCIA ----------
OUTPUT_FILE = "data/step1_candidates.json"
MAX_PER_SOURCE = 50
HEADERS = {"User-Agent": "Mozilla/5.0"}

# ---------- YAHOO FINANCE ----------
def get_yahoo_stocks():
    """Získa top tickery z Yahoo Finance pomocou API"""
    urls = {
        "most_active": "https://finance.yahoo.com/most-active",
        "gainers": "https://finance.yahoo.com/gainers",
    }
    tickers = []

    print("📡 Načítavam dáta z Yahoo Finance...")
    for name, url in urls.items():
        try:
            resp = requests.get(url, headers=HEADERS, timeout=10)
            soup = BeautifulSoup(resp.text, "html.parser")
            rows = soup.select("table tbody tr")

            for row in rows[:MAX_PER_SOURCE]:
                cols = row.find_all("td")
                if len(cols) < 3:
                    continue

                ticker = cols[0].text.strip()
                company = cols[1].text.strip()

                try:
                    stock = yf.Ticker(ticker)
                    info = stock.info
                    percent_change = round(info.get("regularMarketChangePercent", 0.0), 2)
                    volume = info.get("volume", 0)
                except Exception:
                    percent_change, volume = 0.0, 0

                tickers.append({
                    "ticker": ticker,
                    "name": company,
                    "volume": volume,
                    "percent_change": percent_change,
                    "source": f"Yahoo:{name}",
                    "date": str(date.today())
                })
        except Exception as e:
            print(f"⚠️ Chyba pri načítaní Yahoo sekcie {name}: {e}")

    print(f"✅ Yahoo Finance: získaných {len(tickers)} záznamov")
    return tickers


# ---------- MARKETWATCH ----------
def get_marketwatch_stocks():
    """Načíta gainers a losers z MarketWatch RSS feedov"""
    feeds = {
        "gainers": "https://feeds.marketwatch.com/marketwatch/topstories/",
        "losers": "https://feeds.marketwatch.com/marketwatch/realtimeheadlines/"
    }
    tickers = []

    print("📡 Načítavam dáta z MarketWatch (RSS)...")
    for name, url in feeds.items():
        try:
            resp = requests.get(url, headers=HEADERS, timeout=10)
            soup = BeautifulSoup(resp.text, "xml")
            items = soup.find_all("item")

            for item in items[:MAX_PER_SOURCE]:
                title = item.title.text.strip()
                link = item.link.text.strip()

                # pokus o ticker z URL
                ticker = link.split("/")[-1].upper()[:5]
                if not ticker.isalpha():
                    continue

                tickers.append({
                    "ticker": ticker,
                    "name": title.split(":")[0][:40],
                    "volume": 0,
                    "percent_change": 0.0,
                    "source": f"MarketWatch:{name}",
                    "date": str(date.today())
                })
        except Exception as e:
            print(f"⚠️ Chyba pri čítaní RSS {url}: {e}")

    print(f"✅ MarketWatch: získaných {len(tickers)} záznamov")
    return tickers


# ---------- HLAVNÁ FUNKCIA ----------
def run_scraper():
    print("🚀 Spúšťam Step 1 – Scraper V3")

    yahoo_data = get_yahoo_stocks()
    mw_data = get_marketwatch_stocks()

    all_data = yahoo_data + mw_data

    # Dedup podľa tickeru
    unique = {i["ticker"]: i for i in all_data}
    deduped = list(unique.values())

    Path("data").mkdir(exist_ok=True)
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(deduped, f, indent=2, ensure_ascii=False)

    print("\n📊 ŠTATISTIKA SCRAPERU")
    print(f"- 🟣 Yahoo Finance: {len(yahoo_data)} akcií")
    print(f"- 🟢 MarketWatch: {len(mw_data)} akcií")
    print(f"- 🔵 Po deduplikácii: {len(deduped)} unikátnych akcií")
    print(f"- 💾 Výstup uložený do: {OUTPUT_FILE}")
    
    return deduped


# ---------- SPUSTENIE ----------
if __name__ == "__main__":
    run_scraper()
