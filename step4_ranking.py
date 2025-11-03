"""
step4_ranking_keep_all.py
Kombinuje technické a sentimentálne dáta, počíta percentuálne skóre a vyhodnocuje "buy_score_percent".
Zachováva všetky akcie vo výstupe a navyše zobrazí top 10 v konzole.
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

# ---------- NORMALIZE FEATURES ----------
sentiments = [d.get("combined_sentiment", 0) for d in data]
percent_changes = [d.get("percent_change", 0.0) for d in data]
mentions = [d.get("total_mentions", 0) for d in data]
recommendations = [recommendation_to_score(d.get("recommendation", "Hold")) for d in data]
volume_gain = [d.get("volume_gain", 0.0) for d in data]

norm_sent = normalize_minmax(sentiments)
norm_pct = normalize_minmax(percent_changes)
norm_mentions = normalize_minmax(mentions)
norm_rec = normalize_minmax(recommendations)
norm_vol = normalize_minmax(volume_gain)

# ---------- CALCULATE NEW BUY_SCORE_PERCENT ----------
# váhy pre novú metriku (možno upraviť)
W_SENT = 0.35
W_REC = 0.25
W_PCT = 0.20
W_VOL = 0.20

for i, d in enumerate(data):
    score = (norm_sent[i]*W_SENT + norm_rec[i]*W_REC + norm_pct[i]*W_PCT + norm_vol[i]*W_VOL) * 100
    d["buy_score_percent"] = round(score, 2)

    if score >= 70:
        d["final_recommendation"] = "Strong Buy"
    elif score >= 50:
        d["final_recommendation"] = "Buy"
    else:
        d["final_recommendation"] = "Hold / Avoid"

# ---------- SORT FOR DISPLAY ----------
sorted_all = sorted(data, key=lambda x: x["buy_score_percent"], reverse=True)
top10 = sorted_all[:TOP_N]

# ---------- SAVE OUTPUT ----------
Path("data").mkdir(exist_ok=True)
out_data = {
    "total_candidates": len(data),
    "ranked_candidates": sorted_all  # všetky zoradené podľa buy_score_percent
}

with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
    json.dump(out_data, f, indent=2, ensure_ascii=False)

# ---------- PRINT SUMMARY ----------
print(f"💾 Výstup uložený do {OUTPUT_FILE}")
print(f"🔵 Celkom kandidátov zo Step3: {len(data)}")
print(f"✅ TOP {TOP_N} tickery podľa novej percentuálnej metriky:\n")

for idx, t in enumerate(top10, 1):
    print(f"{idx}. {t['ticker']} | buy_score_percent: {t['buy_score_percent']}% | "
          f"final_recommendation: {t['final_recommendation']} | "
          f"combined_sentiment: {t.get('combined_sentiment', 0)} | "
          f"percent_change: {t.get('percent_change', 0)} | "
          f"volume_gain: {t.get('volume_gain', 0)}")

print("\n✅ Všetky akcie (zoradené podľa buy_score_percent) boli uložené do výstupného JSON súboru.")
