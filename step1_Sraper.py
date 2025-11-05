"""
Step 1 – Scraper V14.3 (S&P 500, filter switches)
Načítanie S&P 500 tickerov, doplnenie finančných údajov a filtrácia
Výstup: data/step1_candidates.json
"""

import json
import time
from pathlib import Path
import concurrent.futures
import yfinance as yf
import requests
from bs4 import BeautifulSoup

OUTPUT_FILE = "data/step1_candidates.json"
THREADS = 5
HEADERS = {"User-Agent": "Mozilla/5.0"}
WIKI_URL = "https://en.wikipedia.org/wiki/List_of_S%26P_500_companies"

# ---------- FILTER SWITCHES ----------
ENABLE_PRICE_FILTER = True
ENABLE_VOLUME_FILTER = False
ENABLE_MARKETCAP_FILTER = False
ENABLE_MOMENTUM_FILTER = False
ENABLE_DEBT_EQUITY_FILTER = False
ENABLE_REVENUE_GROWTH_FILTER = False
ENABLE_PE_FILTER = False

# ---------- FILTERS ----------
FILTERS = {
    "Price > 10 USD": (
        "Cena > 10 USD, vyraďuje veľmi lacné akcie",
        lambda info: info.get("price") is not None and info.get("price") > 10,
        ENABLE_PRICE_FILTER
    ),
    "Volume > 500k": (
        "Objem > 500k, zaručuje likviditu",
        lambda info: info.get("volume") is not None and info.get("volume") > 500000,
        ENABLE_VOLUME_FILTER
    ),
    "MarketCap > 2B": (
        "MarketCap > 2B USD, vyraďuje malé firmy",
        lambda info: info.get("marketCap") is not None and info.get("marketCap") > 2_000_000_000,
        ENABLE_MARKETCAP_FILTER
    ),
    "Momentum > 0%": (
        "Momentum > 0%, vyraďuje akcie v downtrende",
        lambda info: info.get("regularMarketChangePercent") is not None and info.get("regularMarketChangePercent") > 0,
        ENABLE_MOMENTUM_FILTER
    ),
    "Debt/Equity < 2": (
        "Debt/Equity < 2, vyraďuje nadmerne zadlžené firmy",
        lambda info: info.get("debtToEquity") is not None and info.get("debtToEquity") < 2,
        ENABLE_DEBT_EQUITY_FILTER
    ),
    "RevenueGrowth > 0%": (
        "RevenueGrowth > 0%, firma má rastúce tržby",
        lambda info: info.get("revenueGrowth") is not None and info.get("revenueGrowth") > 0,
        ENABLE_REVENUE_GROWTH_FILTER
    ),
    "P/E 0-50": (
        "P/E 0–50, extrémne vysoké alebo záporné P/E nie sú vhodné",
        lambda info: info.get("trailingPE") is not None and 0 < info.get("trailingPE") < 50,
        ENABLE_PE_FILTER
    ),
}

# ---------- FUNCTIONS ----------
def get_sp500_tickers():
    tickers = []
    resp = requests.get(WIKI_URL, headers=HEADERS, timeout=10)
    resp.raise_for_status()
    soup = BeautifulSoup(resp.text, "html.parser")
    table = soup.find("table", {"id": "constituents"})
    rows = table.find_all("tr")[1:]
    for row in rows:
        cols = row.find_all("td")
        if len(cols) >= 2:
            ticker = cols[0].text.strip()
            name = cols[1].text.strip()
            tickers.append({"ticker": ticker, "name": name})
    print(f"✅ Načítaných {len(tickers)} S&P 500 tickerov")
    return tickers

def safe_fetch_info(ticker_dict):
    ticker = ticker_dict["ticker"]
    name = ticker_dict["name"]
    try:
        info = yf.Ticker(ticker).info
        info_data = {
            "ticker": ticker,
            "name": name,
            "price": info.get("regularMarketPrice"),
            "volume": info.get("volume"),
            "marketCap": info.get("marketCap"),
            "debtToEquity": info.get("debtToEquity"),
            "trailingPE": info.get("trailingPE"),
            "revenueGrowth": info.get("revenueGrowth")
        }
        return info_data
    except Exception:
        return {
            "ticker": ticker,
            "name": name,
            "price": None,
            "volume": None,
            "marketCap": None,
            "debtToEquity": None,
            "trailingPE": None,
            "revenueGrowth": None
        }

def run_scraper():
    tickers = get_sp500_tickers()
    results = []
    total = len(tickers)
    filtered_out = {key: 0 for key, (_, _, enabled) in FILTERS.items() if enabled}
    progress_interval = max(total // 8, 1)
    count = 0

    with concurrent.futures.ThreadPoolExecutor(max_workers=THREADS) as executor:
        futures = {executor.submit(safe_fetch_info, t): t for t in tickers}
        for future in concurrent.futures.as_completed(futures):
            info = future.result()
            count += 1

            passes_all = True
            for key, (desc, rule, enabled) in FILTERS.items():
                if not enabled:
                    continue
                try:
                    if not rule(info):
                        filtered_out[key] += 1
                        passes_all = False
                        break
                except Exception:
                    filtered_out[key] += 1
                    passes_all = False
                    break

            if passes_all:
                results.append(info)

            # Progress po 12.5 %
            if count % progress_interval == 0 or count == total:
                percent = int(count / total * 100)
                print(f"⏳ Spracovaných {percent}% ({count}/{total})")

    Path("data").mkdir(exist_ok=True)
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)

    print("\n📊 ŠTATISTIKA SCRAPERU")
    print(f"- 📈 Celkovo spracovaných: {total}")
    print(f"- ✅ Vyhovujúcich akcií: {len(results)}")
    if filtered_out:
        print("- 🔎 Počet vyradených podľa kritérií:")
        for key, count_out in filtered_out.items():
            count_pass = total - count_out
            print(f"   • {key} ({FILTERS[key][0]}): {count_pass} splnilo, {count_out} vyradených")

    print(f"\n💾 Výstup uložený do: {OUTPUT_FILE}")
    return results

# ---------- MAIN ----------
if __name__ == "__main__":
    start = time.time()
    run_scraper()
    print(f"⏱️ Trvanie: {time.time() - start:.2f} sekúnd")
