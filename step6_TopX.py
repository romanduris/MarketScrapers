import json
from pathlib import Path

# ---------- SETTINGS ----------
INPUT_FILE = "data/step6_MarketInfo.json"
OUTPUT_FILE = "data/step6_TopX.json"

# Počet TOP akcií, ktoré ostanú vo výsledku
TOP_X = 20

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
    Trend sa NEPOUŽÍVA ani ako filter, ani ako multiplier
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

    return round(min(100, base_score), 1)

# Vypočítame OverallRating
for stock in stocks:
    stock["OverallRating"] = calculate_overall(stock)

# ---------- SORT (bez filtrovania trendu) ----------
stocks_sorted = sorted(stocks, key=lambda x: x["OverallRating"], reverse=True)

# ---------- APPLY TOP_X ----------
stocks_sorted = stocks_sorted[:TOP_X]

# ---------- SAVE ----------
Path("data").mkdir(exist_ok=True)
with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
    json.dump(stocks_sorted, f, indent=2, ensure_ascii=False)

# ---------- SUMMARY ----------
print("\n========== STEP 7 SUMMARY ==========")
print(f"📊 Vstupný počet akcií: {total_stocks}")
print(f"📊 Zoradené podľa OverallRating (bez trend filtrov)")
print(f"🔥 Zobrazených TOP {TOP_X}")
print(f"💾 Výstup uložený do {OUTPUT_FILE}")
print("====================================\n")
