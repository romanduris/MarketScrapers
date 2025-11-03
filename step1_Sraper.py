"""
Step 1 – Scraper v3
Získava dynamický zoznam akciových kandidátov z Yahoo Finance (API).
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
                    avg_volume = info.get("averageVolume", 1)  # aby nedošlo k deleniu nulou
                    volume_gain = round((volume - avg_volume) / avg_volume * 100, 2)
                except Exception:
                    percent_change, volume, volume_gain = 0.0, 0, 0.0

                tickers.append({
                    "ticker": ticker,
                    "name": company,
                    "volume": volume,
                    "average_volume": avg_volume,
                    "volume_gain": volume_gain,
                    "percent_change": percent_change,
                    "source": f"Yahoo:{name}",
                    "date": str(date.today())
                })
        except Exception as e:
            print(f"⚠️ Chyba pri načítaní Yahoo sekcie {name}: {e}")

    print(f"✅ Yahoo Finance: získaných {len(tickers)} záznamov")
    return tickers

# ---------- HLAVNÁ FUNKCIA ----------
def run_scraper():
    print("🚀 Spúšťam Step 1 – Scraper V3")

    yahoo_data = get_yahoo_stocks()
    deduped = {i["ticker"]: i for i in yahoo_data}  # dedup podľa tickeru
    deduped_list = list(deduped.values())

    Path("data").mkdir(exist_ok=True)
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(deduped_list, f, indent=2, ensure_ascii=False)

    print("\n📊 ŠTATISTIKA SCRAPERU")
    print(f"- 🟣 Yahoo Finance: {len(yahoo_data)} akcií")
    print(f"- 🔵 Po deduplikácii: {len(deduped_list)} unikátnych akcií")
    print(f"- 💾 Výstup uložený do: {OUTPUT_FILE}")
    
    return deduped_list

# ---------- SPUSTENIE ----------
if __name__ == "__main__":
    run_scraper()
