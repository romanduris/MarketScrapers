"""
step4_ranking.py
Kombinuje technické a sentimentálne dáta a vyhodnocuje "buy_score".
Výstup: JSON s top 10 akciami vrátane všetkých relevantných metrík.
"""
import json
from pathlib import Path

# ---------- SETTINGS ----------
STEP3_FILE = "data/step3_sentiment.json"  # sentiment + technické dáta
OUTPUT_FILE = "data/step4_top10.json"
TOP_N = 10

# ---------- HELPER FUNCTIONS ----------
def normalize_minmax(values):
    """Min-max normalizácia zoznamu hodnôt do [0,1]"""
    if not values:
        return []
    min_v = min(values)
    max_v = max(values)
    if max_v - min_v == 0:
        return [0.5]*len(values)  # rovnaké hodnoty -> stred
    return [(v - min_v)/(max_v - min_v) for v in values]

def recommendation_to_score(rec):
    """Prevádza recommendation text na číselnú hodnotu"""
    mapping = {
        "Strong Buy": 1.0,
        "Buy": 0.8,
        "Hold": 0.5,
        "Sell": 0.2,
        "Strong Sell": 0.0
    }
    return mapping.get(rec, 0.5)  # default stred

# ---------- LOAD DATA ----------
if not Path(STEP3_FILE).exists():
    print("⚠️ Chýba vstupný súbor Step3. Spusti najprv predchádzajúce kroky.")
    exit(1)

with open(STEP3_FILE, "r", encoding="utf-8") as f:
    data = json.load(f)

# ---------- FILTER OUT NEGATIVE OR ZERO COMBINED SENTIMENT ----------
filtered = [d for d in data if d.get("combined_sentiment",0) > 0 and d.get("news_mentions",0) > 0]

if not filtered:
    print("⚠️ Žiadne vhodné tickery na základe sentimentu.")
    exit(1)

# ---------- NORMALIZE FEATURES ----------
sentiments = [d["combined_sentiment"] for d in filtered]
percent_changes = [d.get("percent_change",0.0) for d in filtered]
mentions = [d.get("total_mentions",0) for d in filtered]
recommendations = [recommendation_to_score(d.get("recommendation","Hold")) for d in filtered]

norm_sent = normalize_minmax(sentiments)
norm_pct = normalize_minmax(percent_changes)
norm_mentions = normalize_minmax(mentions)
norm_rec = normalize_minmax(recommendations)

# ---------- CALCULATE BUY SCORE ----------
for i, d in enumerate(filtered):
    d["buy_score"] = round(
        norm_sent[i]*0.4 +  # váha sentimentu
        norm_rec[i]*0.3 +   # váha recommendation
        norm_pct[i]*0.2 +   # váha percent change
        norm_mentions[i]*0.1, # váha mentions
        3
    )

# ---------- SORT AND SELECT TOP 10 ----------
top10 = sorted(filtered, key=lambda x: x["buy_score"], reverse=True)[:TOP_N]

# ---------- SAVE OUTPUT ----------
Path("data").mkdir(exist_ok=True)
with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
    json.dump(top10, f, indent=2, ensure_ascii=False)

# ---------- PRINT SUMMARY ----------
print(f"💾 Top {TOP_N} tickery uložené do {OUTPUT_FILE}")
for idx, t in enumerate(top10, 1):
    print(f"{idx}. {t['ticker']} - buy_score: {t['buy_score']}, sentiment: {t.get('combined_sentiment',0)}, "
          f"recommendation: {t.get('recommendation','NA')}, %change: {t.get('percent_change',0)}, "
          f"mentions: {t.get('total_mentions',0)}")
