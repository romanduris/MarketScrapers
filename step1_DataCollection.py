"""
Step 1 – Data Collection (S&P 500)
- Zber všetkých údajov bez filtrovania
- Throttling, logovanie a detekcia ban (po 3 po sebe nasledujúcich prázdnych históriách)
"""

import json
import time
from pathlib import Path
import yfinance as yf
import requests
from bs4 import BeautifulSoup
import logging

OUTPUT_FILE = "data/step1_raw.json"
HEADERS = {"User-Agent": "Mozilla/5.0"}
WIKI_URL = "https://en.wikipedia.org/wiki/List_of_S%26P_500_companies"
THROTTLE_SECONDS = 0.25

# Logging
Path("logs").mkdir(exist_ok=True)
logging.basicConfig(
    filename="logs/step1_data_collection.log",
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

def throttled_sleep():
    time.sleep(THROTTLE_SECONDS)

def get_sp500_tickers():
    tickers = []
    resp = requests.get(WIKI_URL, headers=HEADERS, timeout=10)
    resp.raise_for_status()
    soup = BeautifulSoup(resp.text, "html.parser")
    table = soup.find("table", {"id": "constituents"})
    rows = table.find_all("tr")[1:]
    for row in rows:
        cols = row.find_all("td")
        ticker = cols[0].text.strip()
        name = cols[1].text.strip()
        tickers.append({"ticker": ticker, "name": name})
    print(f"✅ Načítaných {len(tickers)} S&P 500 tickerov")
    return tickers

def compute_momentum(hist, days):
    try:
        if len(hist) < days + 1:
            return None
        close_today = hist["Close"].iloc[-1]
        close_before = hist["Close"].iloc[-(days+1)]
        if close_before == 0:
            return None
        return (close_today / close_before) - 1
    except:
        return None

def safe_fetch_info(ticker_dict):
    ticker = ticker_dict["ticker"]
    name = ticker_dict["name"]
    throttled_sleep()
    try:
        yf_t = yf.Ticker(ticker)
        info = yf_t.info
        hist = yf_t.history(period="3mo")
        return info, hist
    except Exception as e:
        logging.error(f"Chyba pri {ticker}: {e}")
        return None, None

def run_collection():
    tickers = get_sp500_tickers()
    results = []
    empty_hist_count = 0  # Počet po sebe prázdnych histórií
    total = len(tickers)
    progress_step = max(total // 10, 1)

    for idx, ticker in enumerate(tickers, 1):
        info, hist = safe_fetch_info(ticker)

        # Kontrola banu: prázdne histórie
        if hist is None or hist.empty or not info:
            empty_hist_count += 1
            logging.warning(f"⚠️ Prázdne dáta pre {ticker} ({empty_hist_count}/3)")
            if empty_hist_count >= 3:
                print(f"⚠️ Ban detekovaný po 3 po sebe nasledujúcich prázdnych históriách. Ukončujem script!")
                break
            continue
        else:
            empty_hist_count = 0  # reset counter

        momentum_1w = compute_momentum(hist, 5)
        momentum_2m = compute_momentum(hist, 60)

        results.append({
            "ticker": ticker["ticker"],   # samotný string
            "name": ticker["name"],       # meno z dictionary
            "marketCap": info.get("marketCap"),
            "revenueGrowth": info.get("revenueGrowth"),
            "debtToEquity": info.get("debtToEquity"),
            "trailingPE": info.get("trailingPE"),
            "momentum_2m": momentum_2m,
            "momentum_1w": momentum_1w,
        })




        if idx % progress_step == 0 or idx == total:
            print(f"⏳ Spracovaných {int(idx/total*100)}% ({idx}/{total})")

    Path("data").mkdir(exist_ok=True)
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    print(f"\n💾 Raw data uložené do: {OUTPUT_FILE}")

if __name__ == "__main__":
    run_collection()
