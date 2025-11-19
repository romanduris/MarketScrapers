"""
STEP 7 – Top X podľa kombinovaného skóre (vrátane trhu a sektora)
- Vstup: step6_MarketInfo.json
- Vypočíta OverallRating = priemer(Fundamental, Tech, news_sentiment) * trend_multiplier
- Vyberie top X akcií
- Zachová všetky pôvodné polia (vrátane market/sector info)
- Výstup: step6_TopX.json
"""

import json
from pathlib import Path

# ---------- SETTINGS ----------
INPUT_FILE = "data/step6_MarketInfo.json"
OUTPUT_FILE = "data/step6_TopX.json"
TOP_X = 20  # počet najlepších akcií

# ---------- LOAD ----------
if not Path(INPUT_FILE).exists():
    print(f"⚠️ Vstupný súbor {INPUT_FILE} neexistuje.")
    exit(1)

with open(INPUT_FILE, "r", encoding="utf-8") as f:
    stocks = json.load(f)

total_stocks = len(stocks)

# ---------- CALCULATE OVERALL RATING ----------
def calculate_overall(stock):
    """
    OverallRating = priemer(Fundamental, Tech, news_sentiment) * trend_multiplier
    Trend multiplier podľa market a sector trend
    Výsledok je obmedzený na 100.
    """
    ratings = []

    if stock.get("FundamentalFilterRating") is not None:
        ratings.append(stock["FundamentalFilterRating"])
    if stock.get("TechFilterRating") is not None:
        ratings.append(stock["TechFilterRating"])
    if stock.get("news_sentiment_percent") is not None:
        ratings.append(stock["news_sentiment_percent"])

    if not ratings:
        base_score = 0
    else:
        base_score = sum(ratings) / len(ratings)

    # trend multiplier
    market_trend = stock.get("market_trend")
    sector_trend = stock.get("sector_trend")

    multiplier = 1.0

    if market_trend == "up" and sector_trend == "up":
        multiplier = 1.20
    elif market_trend == "up" or sector_trend == "up":
        multiplier = 1.10
    elif market_trend == "down" and sector_trend == "down":
        multiplier = 0.80
    elif market_trend == "down" or sector_trend == "down":
        multiplier = 0.90
    else:
        multiplier = 1.00  # oba neutral alebo unknown

    overall = round(min(100, base_score * multiplier), 1)
    return overall

for stock in stocks:
    stock["OverallRating"] = calculate_overall(stock)

# ---------- SORT ----------
stocks_sorted = sorted(stocks, key=lambda x: x["OverallRating"], reverse=True)

# ---------- SELECT TOP X ----------
top_stocks = stocks_sorted[:TOP_X]

# ---------- SAVE ----------
Path("data").mkdir(exist_ok=True)
with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
    json.dump(top_stocks, f, indent=2, ensure_ascii=False)

# ---------- SUMMARY ----------
print("\n========== STEP 7 SUMMARY ==========")
print(f"📊 Vstupný počet akcií: {total_stocks}")
print(f"📊 Počet vybraných TOP {TOP_X} akcií: {len(top_stocks)}")
print(f"💾 Výstup uložený do {OUTPUT_FILE}")
print("====================================\n")
