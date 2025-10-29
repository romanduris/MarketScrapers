"""
step2_techAnalyze.py: doplnenie technických dát (RSI, MACD, EMA), filtry a vyhodnotenie vhodnosti nákupu
"""

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
EMA_PERIOD = 20            # EMA
MACD_FAST = 12
MACD_SLOW = 26
MACD_SIGNAL = 9

# váhy pre Buy Score
RSI_WEIGHT = 0.3
MACD_WEIGHT = 0.4
EMA_WEIGHT = 0.3

# ---------- HELPER ----------
def calculate_rsi(prices, period=14):
    delta = prices.diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)
    avg_gain = gain.rolling(period, min_periods=period).mean()
    avg_loss = loss.rolling(period, min_periods=period).mean()
    rs = avg_gain / (avg_loss + 1e-6)
    rsi = 100 - (100 / (1 + rs))
    return rsi.iloc[-1] if not rsi.empty else None

def calculate_macd(prices):
    ema_fast = prices.ewm(span=MACD_FAST, adjust=False).mean()
    ema_slow = prices.ewm(span=MACD_SLOW, adjust=False).mean()
    macd = ema_fast - ema_slow
    signal = macd.ewm(span=MACD_SIGNAL, adjust=False).mean()
    return macd.iloc[-1] if not macd.empty else None, signal.iloc[-1] if not signal.empty else None

def calculate_ema(prices, period=EMA_PERIOD):
    ema = prices.ewm(span=period, adjust=False).mean()
    return ema.iloc[-1] if not ema.empty else None

def evaluate_rsi(rsi: float) -> float:
    if rsi < 30 or rsi > 70:
        return 0.0
    elif 40 <= rsi <= 60:
        return 1.0
    else:
        return 0.7

def evaluate_macd(macd: float, macd_signal: float) -> float:
    if macd > macd_signal:
        return 1.0
    elif macd < macd_signal:
        return 0.0
    else:
        return 0.5

def evaluate_ema(price: float, ema: float) -> float:
    return 1.0 if price > ema else 0.0

def calculate_buy_score(rsi_score: float, macd_score: float, ema_score: float) -> float:
    return round(RSI_WEIGHT*rsi_score + MACD_WEIGHT*macd_score + EMA_WEIGHT*ema_score,3)

def classify_buy(score: float) -> str:
    if score >= 0.7:
        return "Strong Buy"
    elif score >= 0.4:
        return "Buy"
    else:
        return "Hold / Avoid"

# ---------- LOAD CANDIDATES ----------
if not Path(INPUT_FILE).exists():
    print(f"⚠️ Chyba: súbor {INPUT_FILE} neexistuje. Spusti najprv krok 1 scraper.py")
    exit(1)

with open(INPUT_FILE, "r", encoding="utf-8") as f:
    candidates = json.load(f)

filtered = []
processed = 0

# Štatistika filtrov
filtered_volume = 0
filtered_percent = 0
filtered_rsi = 0
filtered_no_data = 0

# ---------- PROCESS ----------
for c in candidates:
    processed += 1
    ticker = c["ticker"]
    try:
        t = yf.Ticker(ticker)
        hist = t.history(period="1mo")["Close"]
        if hist.empty:
            filtered_no_data += 1
            print(f"⚠️ Chyba pri ticker {ticker}: historické dáta nie sú dostupné, odfiltrované")
            continue

        rsi = calculate_rsi(hist, RSI_PERIOD)
        macd, macd_signal = calculate_macd(hist)
        ema = calculate_ema(hist)

        info = t.info
        volume = info.get("volume", 0) or 0
        current_price = info.get("regularMarketPrice") or hist.iloc[-1]
        prev_close = info.get("previousClose") or current_price
        percent_change = ((current_price - prev_close)/prev_close*100) if prev_close else 0

        # aplikujeme filtre
        if volume < MIN_VOLUME:
            filtered_volume += 1
            continue
        if abs(percent_change) < MIN_PERCENT_CHANGE:
            filtered_percent += 1
            continue
        if rsi is not None and (rsi < RSI_LOW or rsi > RSI_HIGH):
            filtered_rsi += 1
            continue

        # vyhodnotenie Buy Score
        rsi_score = evaluate_rsi(rsi)
        macd_score = evaluate_macd(macd, macd_signal)
        ema_score = evaluate_ema(current_price, ema)
        buy_score = calculate_buy_score(rsi_score, macd_score, ema_score)
        recommendation = classify_buy(buy_score)

        filtered.append({
            "ticker": ticker,
            "name": info.get("shortName") or c.get("name",""),
            "volume": volume,
            "percent_change": round(percent_change,2),
            "rsi": round(rsi,2) if rsi else None,
            "macd": round(macd,4) if macd else None,
            "macd_signal": round(macd_signal,4) if macd_signal else None,
            "ema": round(ema,2) if ema else None,
            "buy_score": buy_score,
            "recommendation": recommendation,
            "market_cap": info.get("marketCap"),
            "url": f"https://finance.yahoo.com/quote/{ticker}",
            "date": str(date.today())
        })
        print(f"✅ [{processed}] {ticker} | Vol:{volume} Δ%:{round(percent_change,2)} RSI:{round(rsi,2) if rsi else 'NA'} EMA:{round(ema,2) if ema else 'NA'} MACD:{round(macd,4) if macd else 'NA'} | Buy Score:{buy_score} -> {recommendation}")

    except Exception as e:
        filtered_no_data += 1
        print(f"⚠️ Chyba pri ticker {ticker}: {e}")

# ---------- SAVE ----------
Path("data").mkdir(exist_ok=True)
with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
    json.dump(filtered, f, indent=2, ensure_ascii=False)

# ---------- STATISTIKA ----------
print("\n📊 ŠTATISTIKA STEP 2 - TECHNICKÁ ANALÝZA & BUY SCORE")
print(f"🟣 Celkom kandidátov: {len(candidates)}")
print(f"🔵 Po filtroch: {len(filtered)}")
print(f"❌ Odfiltrované podľa objemu: {filtered_volume}")
print(f"❌ Odfiltrované podľa percent change: {filtered_percent}")
print(f"❌ Odfiltrované podľa RSI: {filtered_rsi}")
print(f"❌ Odfiltrované kvôli nedostupným historickým dátam: {filtered_no_data}")
print(f"💾 Filtrované tickery + Buy Score uložené do {OUTPUT_FILE}")
print("✅ Step 2: Hotovo")
