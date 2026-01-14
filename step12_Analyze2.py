import json
from pathlib import Path
from datetime import datetime
import yfinance as yf
import time
import re

HISTORY_DIR = Path("history")
OUTPUT_FILE = Path("data/step12_Analyz2.json")

THROTTLE_SECONDS = 0.25
BAN_LIMIT = 3
MAX_DAYS = 5  # max počet obchodných dní

def throttled_sleep():
    time.sleep(THROTTLE_SECONDS)

def safe_fetch_history(ticker, start_dt):
    throttled_sleep()
    try:
        yf_t = yf.Ticker(ticker)
        hist = yf_t.history(start=start_dt.strftime("%Y-%m-%d"))
        return hist
    except Exception as e:
        print(f"❌ Chyba pri {ticker}: {e}")
        return None

def parse_purchase_datetime(filename):
    m = re.search(r"(\d{4}-\d{2}-\d{2})_(\d{2}-\d{2}-\d{2})", filename)
    if not m:
        return None
    date_part, time_part = m.groups()
    dt_str = f"{date_part} {time_part.replace('-', ':')}"
    return datetime.strptime(dt_str, "%Y-%m-%d %H:%M:%S")

def analyze_trade(trade, purchase_dt):
    ticker = trade["ticker"]
    sl = trade.get("SL")
    tp = trade.get("TP")
    entry_price = trade["price"]

    if purchase_dt > datetime.now():
        return {
            "purchase_dt": purchase_dt.strftime("%Y-%m-%d %H:%M:%S"),
            "ticker": ticker,
            "status": "OPEN",
            "hit_date": None,
            "profit": None
        }

    hist = safe_fetch_history(ticker, purchase_dt)

    if hist is None or hist.empty:
        return {
            "purchase_dt": purchase_dt.strftime("%Y-%m-%d %H:%M:%S"),
            "ticker": ticker,
            "status": "ERROR",
            "hit_date": None,
            "profit": None,
            "count_for_ban": True
        }

    # berieme len prvých MAX_DAYS obchodných dní
    hist_limited = hist.head(MAX_DAYS)

    for idx, row in hist_limited.iterrows():
        low = row["Low"]
        high = row["High"]

        if low <= sl:
            profit = sl - entry_price
            return {
                "purchase_dt": purchase_dt.strftime("%Y-%m-%d %H:%M:%S"),
                "ticker": ticker,
                "status": "SL",
                "hit_date": str(idx),
                "profit": round(profit, 2)
            }

        if high >= tp:
            profit = tp - entry_price
            return {
                "purchase_dt": purchase_dt.strftime("%Y-%m-%d %H:%M:%S"),
                "ticker": ticker,
                "status": "TP",
                "hit_date": str(idx),
                "profit": round(profit, 2)
            }

    # ⏱️ TIME EXIT na 5. deň – polovica obchodného dňa
    last_day = hist_limited.iloc[-1]
    mid_price = (last_day["High"] + last_day["Low"]) / 2
    profit = mid_price - entry_price

    return {
        "purchase_dt": purchase_dt.strftime("%Y-%m-%d %H:%M:%S"),
        "ticker": ticker,
        "status": "TIME_EXIT",
        "hit_date": str(hist_limited.index[-1]),
        "profit": round(profit, 2)
    }

def run():
    HISTORY_DIR.mkdir(exist_ok=True)
    OUTPUT_FILE.parent.mkdir(exist_ok=True)

    files = sorted(HISTORY_DIR.glob("????-??-??_??-??-??.json"))
    print(f"🔍 Načítaných súborov: {len(files)}")

    all_results = []
    ban_counter = 0
    stats = {"TP": 0, "SL": 0, "OPEN": 0, "ERROR": 0, "TIME_EXIT": 0}

    for file in files:
        with open(file, "r", encoding="utf-8") as f:
            trades = json.load(f)

        purchase_dt = parse_purchase_datetime(file.name)
        if not purchase_dt:
            print(f"❌ Neplatný názov súboru: {file.name}, preskakujem")
            continue

        for t in trades:
            print(f"⏳ Analyzujem {t['ticker']} z {purchase_dt.strftime('%Y-%m-%d %H:%M:%S')} ...")
            res = analyze_trade(t, purchase_dt)

            if res.get("count_for_ban", False):
                ban_counter += 1
                print(f"⚠️ History error ({ban_counter}/{BAN_LIMIT})")
                if ban_counter >= BAN_LIMIT:
                    print("🛑 Detekovaný BAN – ukončujem script!")
                    break
            else:
                ban_counter = 0

            all_results.append({
                "source_file": file.name,
                "purchase_dt": res["purchase_dt"],
                "ticker": res["ticker"],
                "status": res["status"],
                "hit_date": res["hit_date"],
                "profit": res["profit"],
                "market_trend": t.get("market_trend"),
                "sector_trend": t.get("sector_trend"),
                "price": t.get("price")
            })

            if res["status"] in stats:
                stats[res["status"]] += 1
            else:
                stats["ERROR"] += 1

        if ban_counter >= BAN_LIMIT:
            break

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(all_results, f, indent=2, ensure_ascii=False)

    print("\n📊 Štatistika analyzovaných obchodov:")
    print(f" - Počet analyzovaných súborov: {len(files)}")
    print(f" - Celkový počet obchodov: {len(all_results)}")
    print(f" - TP: {stats['TP']}")
    print(f" - SL: {stats['SL']}")
    print(f" - TIME_EXIT (5 dní): {stats['TIME_EXIT']}")
    print(f" - ERROR: {stats['ERROR']}")

    print(f"\n💾 Výsledky uložené do {OUTPUT_FILE}")

if __name__ == "__main__":
    run()
