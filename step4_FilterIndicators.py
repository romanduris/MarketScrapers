"""
step2_techFilter.py: Vyhodnotí TechFilterRating pre tickery zo Step2 Collect
- Neodfiltruje, iba boduje
- Štatistika pre každý filter
- Percentuálne hodnotenie splnenia filtrov
- Volume filter odstránený
- Možnosť nastaviť prah TechFilterRating pre uloženie do výstupu
"""

import json
from pathlib import Path
import logging

INPUT_FILE = "data/step3_IndicatorsData.json"
OUTPUT_FILE = "data/step4_IndicatorsFilter.json"

# ---------- SETTINGS ----------
TECHFILTER_THRESHOLD = 80.0  # percento, nad ktorým sa akcia uloží do výstupu

# Váhy a aktivované filtre
ENABLE_PERCENT_CHANGE_FILTER = True
ENABLE_RSI_FILTER = True
ENABLE_EMA_FILTER = True
ENABLE_MACD_FILTER = True

MIN_PERCENT_CHANGE = 0.5
RSI_PERIOD = 14
RSI_LOW = 30
RSI_HIGH = 70
EMA_PERIOD = 20
MACD_FAST = 12
MACD_SLOW = 26
MACD_SIGNAL = 9

# Logovanie
Path("logs").mkdir(exist_ok=True)
logging.basicConfig(
    filename="logs/step2_techFilter.log",
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

# ---------- FILTERS ----------
FILTERS = {
    f"Percent Change ≥ {MIN_PERCENT_CHANGE}%": (
        lambda c: abs(c.get("percent_change",0)) >= MIN_PERCENT_CHANGE,
        ENABLE_PERCENT_CHANGE_FILTER
    ),
    f"RSI ({RSI_PERIOD}) 30-70": (
        lambda c: c.get(f"RSI ({RSI_PERIOD})") is not None and RSI_LOW <= c.get(f"RSI ({RSI_PERIOD})") <= RSI_HIGH,
        ENABLE_RSI_FILTER
    ),
    f"EMA ({EMA_PERIOD}) < Price": (
        lambda c: c.get(f"EMA ({EMA_PERIOD})") is not None and c.get("price") > c.get(f"EMA ({EMA_PERIOD})"),
        ENABLE_EMA_FILTER
    ),
    f"MACD ({MACD_FAST},{MACD_SLOW},{MACD_SIGNAL}) > Signal": (
        lambda c: c.get(f"MACD ({MACD_FAST},{MACD_SLOW},{MACD_SIGNAL})") is not None and c.get(f"MACD ({MACD_FAST},{MACD_SLOW},{MACD_SIGNAL})") > c.get(f"MACD_Signal ({MACD_FAST},{MACD_SLOW},{MACD_SIGNAL})"),
        ENABLE_MACD_FILTER
    )
}

# ---------- LOAD ----------
if not Path(INPUT_FILE).exists():
    print(f"⚠️ Súbor {INPUT_FILE} neexistuje!")
    exit(1)

with open(INPUT_FILE,"r",encoding="utf-8") as f:
    candidates = json.load(f)

results = []
filter_stats = {k: {"passed":0,"failed":0,"enabled":v[1]} for k,v in FILTERS.items()}

# ---------- PROCESS ----------
total_enabled = sum(1 for _,v in FILTERS.items() if v[1])

for idx, c in enumerate(candidates,1):
    passed_count = 0
    for key,(rule, enabled) in FILTERS.items():
        if enabled:
            if rule(c):
                filter_stats[key]["passed"] += 1
                passed_count += 1
            else:
                filter_stats[key]["failed"] += 1

    c["TechFilterRating"] = round(passed_count / total_enabled * 100,1) if total_enabled>0 else 0

    # uložíme len ak splní prah
    if c["TechFilterRating"] >= TECHFILTER_THRESHOLD:
        results.append(c)

    logging.info(f"{idx}/{len(candidates)} {c['ticker']} | TechFilterRating: {c['TechFilterRating']}%")

# ---------- SAVE ----------
Path("data").mkdir(exist_ok=True)
with open(OUTPUT_FILE,"w",encoding="utf-8") as f:
    json.dump(results,f,indent=2,ensure_ascii=False)

# ---------- STATISTIKA ----------
print("\n📊 ŠTATISTIKA STEP 2 - TechFilterRating")
print(f"🟣 Celkom kandidátov: {len(candidates)}")
print(f"🔵 Po analýze (nad prah {TECHFILTER_THRESHOLD}%): {len(results)}")
print("🔎 Štatistika podľa filtrov (nezávisle):")
for key,stats in filter_stats.items():
    if stats["enabled"]:
        print(f"   • {key}: ✅ {stats['passed']} prešlo, ❌ {stats['failed']} neprešlo")

print(f"💾 Výstup uložený do: {OUTPUT_FILE}")
print("✅ Step 2 Filter: Hotovo")
