import json
from pathlib import Path

INPUT_FILE = "data/step7_AIAnalyze.json"
OUTPUT_FILE = "data/step8_SLTP.json"

def compute_sl_tp(stock):
    price = stock.get("price")
    ema20 = stock.get("EMA (20)")
    rsi = stock.get("RSI (14)")
    momentum2m = stock.get("momentum_2m")

    # --- STOP LOSS ---
    sl_ema_buffer = ema20 * 0.98                # 2% pod EMA
    sl_price_buffer = price * 0.97              # 3% pod cenou
    SL = max(sl_ema_buffer, sl_price_buffer)

    # --- TAKE PROFIT ---
    tp_rsi = price * (1.05 if rsi < 70 else 1.03)

    if momentum2m > 0.30:
        tp_mom = price * 1.07
    elif momentum2m > 0.10:
        tp_mom = price * 1.05
    else:
        tp_mom = price * 1.03

    TP = (tp_rsi + tp_mom) / 2

    return SL, TP

def compute_sl_tp_10e(price, SL, TP):
    fraction = 10 / price

    SL10 = SL * fraction
    TP10 = TP * fraction

    return SL10, TP10


# --- MAIN ---
if not Path(INPUT_FILE).exists():
    print(f"❌ Súbor {INPUT_FILE} neexistuje.")
    exit(1)

with open(INPUT_FILE, "r", encoding="utf-8") as f:
    stocks = json.load(f)

for stock in stocks:
    price = stock.get("price")

    # základné SL/TP
    SL, TP = compute_sl_tp(stock)
    stock["SL"] = round(SL, 2)
    stock["TP"] = round(TP, 2)

    # SL/TP pre investíciu 10 €
    SL10, TP10 = compute_sl_tp_10e(price, SL, TP)
    stock["SL10"] = round(SL10, 2)
    stock["TP10"] = round(TP10, 2)

Path("data").mkdir(exist_ok=True)
with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
    json.dump(stocks, f, indent=2, ensure_ascii=False)

print(f"✅ Hotovo! Výstup uložený do {OUTPUT_FILE}")
