import json
from pathlib import Path
from datetime import datetime
import yfinance as yf
import time
import re

# =========================
# KONFIGURÁCIA
# =========================

HISTORY_DIR = Path("history")
OUTPUT_FILE = Path("data/step12_Analyze.json")

THROTTLE_SECONDS = 0.25
BAN_LIMIT = 3

MAX_HOLD_DAYS = 10  # max počet obchodných dní pre SL/TP

# =========================
# UTILITIES
# =========================

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
    """
    Očakáva názov súboru: YYYY-MM-DD_HH-MM-SS.json
    """
    m = re.search(r"(\d{4}-\d{2}-\d{2})_(\d{2}-\d{2}-\d{2})", filename)
    if not m:
        return None
    date_part, time_part = m.groups()
    dt_str = f"{date_part} {time_part.replace('-', ':')}"
    return datetime.strptime(dt_str, "%Y-%m-%d %H:%M:%S")

# =========================
# HLAVNÁ FUNKCIA ANALÝZY
# =========================

def analyze_trade(trade, purchase_dt):
    ticker = trade["ticker"]
    entry_price = trade["price"]
    sl = trade["SL"]
    tp = trade["TP"]

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

    hist = hist.sort_index()

    # =========================
    # 1–MAX_HOLD_DAYS obchodný deň: SL / TP
    # =========================

    for day_idx, (idx, row) in enumerate(hist.iterrows()):
        if day_idx >= MAX_HOLD_DAYS:
            break

        low = row["Low"]
        high = row["High"]

        # SL má prioritu
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

    # =========================
    # OPEN alebo TIME_EXIT podľa dostupných dát
    # =========================

    if len(hist) <= MAX_HOLD_DAYS:
        last_row = hist.iloc[-1]
        current_price = last_row["Close"]
        profit = current_price - entry_price

        status = "OPEN" if len(hist) < MAX_HOLD_DAYS else "TIME_EXIT"

        return {
            "purchase_dt": purchase_dt.strftime("%Y-%m-%d %H:%M:%S"),
            "ticker": ticker,
            "status": status,
            "hit_date": str(last_row.name) if status == "TIME_EXIT" else None,
            "profit": round(profit, 2)
        }

    # =========================
    # TIME_EXIT – 11. deň (MAX_HOLD_DAYS+1) alebo posledný dostupný deň
    # =========================
    if len(hist) > MAX_HOLD_DAYS:
        exit_row = hist.iloc[MAX_HOLD_DAYS]  # 11. deň (0-based)
    else:
        exit_row = hist.iloc[-1]  # posledný dostupný deň

    exit_price = exit_row["Close"]
    exit_idx = exit_row.name
    profit = exit_price - entry_price

    return {
        "purchase_dt": purchase_dt.strftime("%Y-%m-%d %H:%M:%S"),
        "ticker": ticker,
        "status": "TIME_EXIT",
        "hit_date": str(exit_idx),
        "profit": round(profit, 2)
    }

# =========================
# RUNNER
# =========================

def run():
    HISTORY_DIR.mkdir(exist_ok=True)
    OUTPUT_FILE.parent.mkdir(exist_ok=True)

    files = sorted(HISTORY_DIR.glob("????-??-??_??-??-??.json"))
    print(f"🔍 Načítaných súborov: {len(files)}")

    all_results = []
    ban_counter = 0

    stats = {
        "TP": 0,
        "SL": 0,
        "OPEN": 0,
        "TIME_EXIT": 0,
        "ERROR": 0
    }

    for file in files:
        with open(file, "r", encoding="utf-8") as f:
            trades = json.load(f)

        purchase_dt = parse_purchase_datetime(file.name)
        if not purchase_dt:
            print(f"❌ Neplatný názov súboru: {file.name}, preskakujem")
            continue

        for trade in trades:
            print(f"⏳ Analyzujem {trade['ticker']} z {purchase_dt}")

            res = analyze_trade(trade, purchase_dt)

            if res.get("count_for_ban"):
                ban_counter += 1
                print(f"⚠️ History error ({ban_counter}/{BAN_LIMIT})")
                if ban_counter >= BAN_LIMIT:
                    print("🛑 Detekovaný BAN – ukončujem script")
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
                "market_trend": trade.get("market_trend"),
                "sector_trend": trade.get("sector_trend"),
                "price": trade.get("price")
            })

            stats[res["status"]] = stats.get(res["status"], 0) + 1

        if ban_counter >= BAN_LIMIT:
            break

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(all_results, f, indent=2, ensure_ascii=False)

    print("\n📊 Štatistika:")
    for k, v in stats.items():
        print(f" - {k}: {v}")

    print(f"\n💾 Výsledky uložené do {OUTPUT_FILE}")

# =========================
# ENTRYPOINT
# =========================

if __name__ == "__main__":
    run()
