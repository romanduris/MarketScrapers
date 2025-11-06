"""
STEP 6 – Top X podľa kombinovaného skóre
- Vstup: step5_SentimentFilter.json
- Vypočíta OverallRating = priemer(FundamentalFilterRating, TechFilterRating, news_sentiment_percent)
- Vyberie top X akcií podľa OverallRating
- Výstup uložený do data/step6_TopX.json
- Zobrazí súhrn: počet vstupných akcií a počet vybraných top X
"""

import json
from pathlib import Path

# ---------- SETTINGS ----------
INPUT_FILE = "data/step5_SentimentFilter.json"
OUTPUT_FILE = "data/step6_TopX.json"
TOP_X = 20  # počet najlepších akcií, ktoré vybrať

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
    Vypočíta OverallRating ako priemer FundamentalFilterRating, TechFilterRating a news_sentiment_percent
    Ak news_sentiment_percent je None, ignoruje ho a berie len dve hodnoty.
    """
    ratings = []
    if stock.get("FundamentalFilterRating") is not None:
        ratings.append(stock["FundamentalFilterRating"])
    if stock.get("TechFilterRating") is not None:
        ratings.append(stock["TechFilterRating"])
    if stock.get("news_sentiment_percent") is not None:
        ratings.append(stock["news_sentiment_percent"])
    if ratings:
        return round(sum(ratings) / len(ratings), 1)
    return 0.0

for stock in stocks:
    stock["OverallRating"] = calculate_overall(stock)

# ---------- SORT BY OVERALLRATING ----------
stocks_sorted = sorted(stocks, key=lambda x: x["OverallRating"], reverse=True)

# ---------- SELECT TOP X ----------
top_stocks = stocks_sorted[:TOP_X]

# ---------- SAVE ----------
Path("data").mkdir(exist_ok=True)
with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
    json.dump(top_stocks, f, indent=2, ensure_ascii=False)

# ---------- SUMMARY ----------
print(f"📊 Vstupný počet akcií: {total_stocks}")
print(f"📊 Počet vybraných TOP {TOP_X} akcií: {len(top_stocks)}")
print(f"💾 Výstup uložený do {OUTPUT_FILE}.")
