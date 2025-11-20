import json
from pathlib import Path

# ---------- SETTINGS ----------
INPUT_FILE = "data/step6_MarketInfo.json"
OUTPUT_FILE = "data/step6_TopX.json"

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
    OverallRating = priemer(Fundamental, Tech, news_sentiment)
    Trend multiplier sa NEPOUŽÍVA
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

    overall = round(min(100, base_score), 1)
    return overall

# Vypočítame OverallRating
for stock in stocks:
    stock["OverallRating"] = calculate_overall(stock)

# ---------- FILTER NEGATIVE SECTOR TREND ----------
filtered_stocks = [s for s in stocks if s.get("sector_trend") != "down"]

# ---------- SORT ----------
stocks_sorted = sorted(filtered_stocks, key=lambda x: x["OverallRating"], reverse=True)

# ---------- SAVE ----------
Path("data").mkdir(exist_ok=True)
with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
    json.dump(stocks_sorted, f, indent=2, ensure_ascii=False)

# ---------- SUMMARY ----------
print("\n========== STEP 7 SUMMARY (MOD) ==========")
print(f"📊 Vstupný počet akcií: {total_stocks}")
print(f"📊 Počet akcií po odfiltrovaní negatívneho sektoru: {len(filtered_stocks)}")
print(f"💾 Výstup uložený do {OUTPUT_FILE}")
print("===========================================\n")
