"""
Step 2 – Filtering (S&P 500)
- Načítanie raw dát a aplikovanie filtrov
- Uloženie finálnych kandidátov
- Výpis štatistiky pre každý aktívny filter (nezávisle)
- Bodovací systém (percentuálne hodnotenie podľa počtu splnených filtrov)
- Možnosť nastaviť prahovú hodnotu, pod ktorou sa akcia neuloží
"""

import json
from pathlib import Path

RAW_FILE = "data/step1_raw.json"
OUTPUT_FILE = "data/step2_FundamentalFilter.json"

# =========================================
# ⚙️ Nastavenia filtrov
# =========================================
ENABLE_MARKETCAP_FILTER = True
ENABLE_REVENUE_GROWTH_FILTER = True
ENABLE_DEBT_EQUITY_FILTER = True
ENABLE_PE_FILTER = True
ENABLE_MOMENTUM_2M_FILTER = True
ENABLE_MOMENTUM_1W_FILTER = True

# Percentuálna hodnota (0-100) pod ktorou sa akcia NEULOŽÍ
MIN_FUNDAMENTAL_RATING = 80  # % filtrov splnenych

FILTERS = {
    # ===========================================
    # 🟩 FUNDAMENTÁLNE – najspoľahlivejšie
    # ===========================================

    # 1. MarketCap ≥ 10B
    #   • Veľké stabilné firmy = menšie riziko
    #   • Overený, veľmi spoľahlivý filter
    "MarketCap ≥ 10B": (
        "MarketCap ≥ 10B, veľké stabilné firmy",
        lambda info: info.get("marketCap") is not None and info.get("marketCap") >= 10_000_000_000,
        ENABLE_MARKETCAP_FILTER
    ),

    # 2. RevenueGrowth ≥ 3%
    #   • Rast tržieb = rastúci biznis
    #   • Miernejší limit (3%) umožní vybrať viac kvalitných firiem
    "RevenueGrowth ≥ 3%": (
        "Firma má rast tržieb ≥ 3%",
        lambda info: info.get("revenueGrowth") is not None and info.get("revenueGrowth") >= 0.03,
        ENABLE_REVENUE_GROWTH_FILTER
    ),

    # 3. Debt/Equity < 6
    #   • Nižšie riziko, ale miernejší limit než pôvodných 1.5
    "Debt/Equity < 6": (
        "Zadlženie firmy < 3, stále relatívne bezpečná štruktúra",
        lambda info: info.get("debtToEquity") is not None and info.get("debtToEquity") < 6,
        ENABLE_DEBT_EQUITY_FILTER
    ),

    # 4. P/E medzi 10 a 35
    #   • Primeraná valuácia
    "P/E 10–35": (
        "Primeraná valuácia (P/E 10–35)",
        lambda info: info.get("trailingPE") is not None and 10 <= info.get("trailingPE") <= 35,
        ENABLE_PE_FILTER
    ),

    # ===========================================
    # 🟨 TRENDOVÉ – potvrdzujú krátkodobý rast
    # ===========================================

    # 5. Momentum 2m > 2%
    #   • Strednodobý rast
    #   • Miernejší limit (2%) získa viac kandidátov
    "Momentum 2m > 2%": (
        "2-mesačný rast ceny > 2%",
        lambda info: info.get("momentum_2m") is not None and info.get("momentum_2m") > 0.02,
        ENABLE_MOMENTUM_2M_FILTER
    ),

    # 6. Momentum 1w > 0%
    #   • Krátkodobé potvrdenie trendu
    "Momentum 1w > 0%": (
        "1-týždňový rast ceny > 0%",
        lambda info: info.get("momentum_1w") is not None and info.get("momentum_1w") > 0,
        ENABLE_MOMENTUM_1W_FILTER
    )
}

def run_filtering():
    # Načítanie raw dát
    with open(RAW_FILE, "r", encoding="utf-8") as f:
        raw_data = json.load(f)

    results = []
    total = len(raw_data)
    progress_step = max(total // 10, 1)

    # Štatistika pre každý aktívny filter (nezávisle)
    filter_stats = {key: {"passed": 0, "failed": 0, "enabled": enabled} for key, (_, _, enabled) in FILTERS.items()}
    active_filters = [key for key, (_, _, enabled) in FILTERS.items() if enabled]
    num_active_filters = len(active_filters)

    for idx, info in enumerate(raw_data, 1):
        passes_count = 0  # počet splnených filtrov pre bodovanie

        # Pre každý filter (nezávisle)
        for key, (desc, rule, enabled) in FILTERS.items():
            if enabled:
                if rule(info):
                    filter_stats[key]["passed"] += 1
                    passes_count += 1
                else:
                    filter_stats[key]["failed"] += 1

        # Percentuálne hodnotenie
        if num_active_filters > 0:
            fundamental_rating = int((passes_count / num_active_filters) * 100)
        else:
            fundamental_rating = 100  # žiadne filtre = 100%

        # Uložíme len ak splní minimálny rating
        if fundamental_rating >= MIN_FUNDAMENTAL_RATING:
            info["FundamentalFilterRating"] = fundamental_rating
            results.append(info)

       # if idx % progress_step == 0 or idx == total:
       #     print(f"⏳ Spracovaných {int(idx/total*100)}% ({idx}/{total})")

    # Uloženie výsledkov
    Path("data").mkdir(exist_ok=True)
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)

    # Výpis štatistiky
    print(f"\n📊 Vyhovujúce akcie: {len(results)} / {total}")
    print("🔎 Štatistika podľa aktívnych filtrov (nezávisle):")
    for key, stats in filter_stats.items():
        if stats["enabled"]:
            print(f"   • {key}: ✅ {stats['passed']} prešlo, ❌ {stats['failed']} neprešlo")

    print(f"💾 Výstup uložený do: {OUTPUT_FILE}")


if __name__ == "__main__":
    run_filtering()
