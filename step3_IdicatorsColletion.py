"""
step2_techCollect.py: Stiahne historické dáta SP500 kandidátov a vypočíta indikátory
- RSI, EMA, MACD + Signal
- Percent change
- Žiadne filtrovanie ani volume
- Výstup: JSON s indikátormi
"""

import json
from pathlib import Path
from datetime import date
import yfinance as yf
import pandas as pd
import logging

# ---------- SETTINGS ----------
INPUT_FILE = "data/step2_FundamentalFilter.json"
OUTPUT_FILE = "data/step3_IndicatorsData.json"

RSI_PERIOD = 14
EMA_PERIOD = 20
MACD_FAST = 12
MACD_SLOW = 26
MACD_SIGNAL = 9

# Logovanie
Path("logs").mkdir(exist_ok=True)
logging.basicConfig(
    filename="logs/step2_techCollect.log",
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

# ---------- HELPER ----------
def calculate_rsi(prices, period=RSI_PERIOD):
    delta = prices.diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)
    avg_gain = gain.rolling(period, min_periods=period).mean()
    avg_loss = loss.rolling(period, min_periods=period).mean()
    rs = avg_gain / (avg_loss + 1e-6)
    rsi = 100 - (100 / (1 + rs))
    return rsi.iloc[-1] if not rsi.empty else None

def calculate_ema(prices, period=EMA_PERIOD):
    ema = prices.ewm(span=period, adjust=False).mean()
    return ema.iloc[-1] if not ema.empty else None

def calculate_macd(prices):
    ema_fast = prices.ewm(span=MACD_FAST, adjust=False).mean()
    ema_slow = prices.ewm(span=MACD_SLOW, adjust=False).mean()
    macd = ema_fast - ema_slow
    signal = macd.ewm(span=MACD_SIGNAL, adjust=False).mean()
    return (macd.iloc[-1] if not macd.empty else None,
            signal.iloc[-1] if not signal.empty else None)

# ---------- LOAD CANDIDATES ----------
if not Path(INPUT_FILE).exists():
    print(f"⚠️ Súbor {INPUT_FILE} neexistuje!")
    exit(1)

with open(INPUT_FILE, "r", encoding="utf-8") as f:
    candidates = json.load(f)

tickers = [c["ticker"] for c in candidates]
print(f"✅ Step 2 Collect: Start ({len(tickers)} kandidátov)")

# ---------- BATCH DOWNLOAD ----------
hist_data = yf.download(tickers, period="1mo", interval="1d", group_by='ticker', threads=True)

# ---------- PROCESS ----------
results = []
processed_count = 0

for idx, c in enumerate(candidates, 1):
    ticker = c["ticker"]
    try:
        hist = hist_data[ticker]["Close"] if ticker in hist_data else pd.Series(dtype=float)
        if hist.empty:
            logging.warning(f"{ticker}: historické dáta chýbajú")
            continue

        current_price = hist.iloc[-1]
        prev_close = hist.iloc[-2] if len(hist) > 1 else current_price
        percent_change = ((current_price - prev_close)/prev_close)*100 if prev_close else 0

        rsi = calculate_rsi(hist)
        ema = calculate_ema(hist)
        macd, macd_signal = calculate_macd(hist)

        c.update({
            "price": current_price,
            f"RSI ({RSI_PERIOD})": round(rsi,2) if rsi else None,
            f"EMA ({EMA_PERIOD})": round(ema,2) if ema else None,
            f"MACD ({MACD_FAST},{MACD_SLOW},{MACD_SIGNAL})": round(macd,4) if macd else None,
            f"MACD_Signal ({MACD_FAST},{MACD_SLOW},{MACD_SIGNAL})": round(macd_signal,4) if macd_signal else None,
            "percent_change": round(percent_change,2)
        })
        results.append(c)
        processed_count += 1
        logging.info(f"{idx}/{len(candidates)} {ticker} processed")

    except Exception as e:
        logging.error(f"{ticker}: {e}")

# ---------- SAVE ----------
Path("data").mkdir(exist_ok=True)
with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
    json.dump(results, f, indent=2, ensure_ascii=False)

# ---------- SUMMARY ----------
print(f"\n💾 Výstup uložený do: {OUTPUT_FILE}")
print("✅ Step 2 Collect: Hotovo")
print(f"🟢 Celkom tickrov vo vstupnom súbore: {len(candidates)}")
print(f"🔵 Tickery úspešne spracované a uložené: {processed_count}")
print(f"❌ Tickery bez historických dát: {len(candidates) - processed_count}")
