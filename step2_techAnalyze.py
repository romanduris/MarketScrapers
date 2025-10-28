"""step2_techAnalyze.py: doplnenie technických dát a základné filtre pre tickery"""
import json
from pathlib import Path
from datetime import date
import yfinance as yf
import pandas as pd

print("✅ Step 2: Technická analýza - Start")

# ---------- SETTINGS ----------
INPUT_FILE = "data/step1_candidates.json"
OUTPUT_FILE = "data/step2_filtered.json"

# filtre
MIN_VOLUME = 100_000       # minimálny denný objem
MIN_PERCENT_CHANGE = 0.5   # minimalna percentuálna zmena
RSI_PERIOD = 14            # počet dní pre RSI
RSI_LOW = 30               # prepredané
RSI_HIGH = 70              # prekúpené

# ---------- HELPER ----------
def calculate_rsi(prices, period=14):
    """Jednoduchý RSI výpočet"""
    delta = prices.diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)
    avg_gain = gain.rolling(period, min_periods=period).mean()
    avg_loss = loss.rolling(period, min_periods=period).mean()
    rs = avg_gain / (avg_loss + 1e-6)
    rsi = 100 - (100 / (1 + rs))
    return rsi.iloc[-1] if not rsi.empty else None

# ---------- LOAD CANDIDATES ----------
if not Path(INPUT_FILE).exists():
    print(f"⚠️ Chyba: súbor {INPUT_FILE} neexistuje. Spusti najprv krok 1 scraper.py")
    exit(1)

with open(INPUT_FILE, "r", encoding="utf-8") as f:
    candidates = json.load(f)

filtered = []
processed = 0

# ---------- PROCESS ----------
for c in candidates:
    processed += 1
    ticker = c["ticker"]
    try:
        t = yf.Ticker(ticker)
        hist = t.history(period="1mo")["Close"]  # posledný mesiac pre RSI
        rsi = calculate_rsi(hist, RSI_PERIOD)

        info = t.info
        volume = info.get("volume", 0) or 0
        current_price = info.get("regularMarketPrice") or 0
        prev_close = info.get("previousClose") or current_price
        percent_change = ((current_price - prev_close)/prev_close*100) if prev_close else 0

        # aplikujeme filtre
        if volume < MIN_VOLUME:
            continue
        if abs(percent_change) < MIN_PERCENT_CHANGE:
            continue
        if rsi is not None and (rsi < RSI_LOW or rsi > RSI_HIGH):
            continue

        filtered.append({
            "ticker": ticker,
            "name": info.get("shortName") or c.get("name",""),
            "volume": volume,
            "percent_change": round(percent_change,2),
            "rsi": round(rsi,2) if rsi else None,
            "market_cap": info.get("marketCap"),
            "url": f"https://finance.yahoo.com/quote/{ticker}",
            "date": str(date.today())
        })
        print(f"✅ [{processed}] {ticker} | Vol:{volume} Δ%:{round(percent_change,2)} RSI:{round(rsi,2) if rsi else 'NA'}")

    except Exception as e:
        print(f"⚠️ Chyba pri ticker {ticker}: {e}")

# ---------- SAVE ----------
Path("data").mkdir(exist_ok=True)
with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
    json.dump(filtered, f, indent=2, ensure_ascii=False)

print(f"\n💾 Step 2: filtrované tickery uložené do {OUTPUT_FILE} ({len(filtered)} položiek)")
print("✅ Step 2: Hotovo")
