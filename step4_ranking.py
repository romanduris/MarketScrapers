"""
step4_ranking.py
Kombinuje technické a sentimentálne dáta a vyberá top 10 akcií.
Výstup: JSON s top 10 akciami vrátane všetkých relevantných metrík.
"""
import json
from pathlib import Path

# ---------- SETTINGS ----------
STEP2_FILE = "data/step2_filtered.json"  # technické filtre
STEP3_FILE = "data/step3_sentiment.json" # sentiment
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

# ---------- LOAD DATA ----------
if not Path(STEP2_FILE).exists() or not Path(STEP3_FILE).exists():
    print("⚠️ Chýba vstupný súbor Step2 alebo Step3. Spusti najprv predchádzajúce kroky.")
    exit(1)

with open(STEP2_FILE, "r", encoding="utf-8") as f:
    tech_data = json.load(f)

with open(STEP3_FILE, "r", encoding="utf-8") as f:
    sentiment_data = json.load(f)

# ---------- MERGE DATA ----------
# vytvor dict pre rýchly lookup sentimentu
sent_dict = {item['ticker']: item for item in sentiment_data}

merged = []
for t in tech_data:
    ticker = t['ticker']
    s = sent_dict.get(ticker, {})
    merged_item = dict(t)  # skopíruj technické dáta
    merged_item.update({
        "news_sentiment": s.get("news_sentiment", 0.0),
        "social_sentiment": s.get("social_sentiment", 0.0),
        "combined_sentiment": s.get("combined_sentiment", 0.0),
        "news_mentions": s.get("news_mentions", 0),
        "social_mentions": s.get("social_mentions", 0),
        "total_mentions": s.get("total_mentions", 0),
        "sentiment_date": s.get("sentiment_date", None)
    })
    merged.append(merged_item)

# ---------- SCORE CALCULATION ----------
# váhy: combined_sentiment 0.5, percent_change 0.3, total_mentions 0.2
sentiments = [m["combined_sentiment"] for m in merged]
percent_changes = [m.get("percent_change", 0.0) for m in merged]
mentions = [m.get("total_mentions", 0) for m in merged]

norm_sent = normalize_minmax(sentiments)
norm_pct = normalize_minmax(percent_changes)
norm_mentions = normalize_minmax(mentions)

for i, m in enumerate(merged):
    # celkové skóre vážený súčet
    m["score"] = round(norm_sent[i]*0.5 + norm_pct[i]*0.3 + norm_mentions[i]*0.2, 3)

# ---------- SORT AND SELECT TOP 10 ----------
merged_sorted = sorted(merged, key=lambda x: x["score"], reverse=True)
top10 = merged_sorted[:TOP_N]

# ---------- SAVE OUTPUT ----------
Path("data").mkdir(exist_ok=True)
with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
    json.dump(top10, f, indent=2, ensure_ascii=False)

print(f"💾 Top {TOP_N} tickery uložené do {OUTPUT_FILE}")
for idx, t in enumerate(top10, 1):
    print(f"{idx}. {t['ticker']} - score: {t['score']}, sentiment: {t['combined_sentiment']}, %change: {t.get('percent_change',0)}, mentions: {t.get('total_mentions',0)}")
