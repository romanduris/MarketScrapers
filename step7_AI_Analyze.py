import json
from pathlib import Path
import openai
import os
import time

# ---------- SETTINGS ----------
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
AI_MODEL = "gpt-4-turbo"
openai.api_key = OPENAI_API_KEY

INPUT_FILE = "data/step6_TopX.json"
OUTPUT_FILE = "data/step7_AIAnalyze.json"

# ✅ Rate limiting settings
SLEEP_BETWEEN_REQUESTS = 1.2
SLEEP_BETWEEN_STOCKS = 0.7

# ---------- FUNKCIE ----------

def build_prompt(stock):
    """Vytvorí textový prompt (nie JSON)."""

    return f"""
Analyzuj túto akciu na obchod 2–10 dní a vytvor AIComment a AIScore:

Ticker: {stock.get("ticker")}
Názov: {stock.get("name")}
MarketCap: {stock.get("marketCap")}
RevenueGrowth: {stock.get("revenueGrowth")}
DebtToEquity: {stock.get("debtToEquity")}
TrailingPE: {stock.get("trailingPE")}

Momentum 2m: {stock.get("momentum_2m")}
Momentum 1w: {stock.get("momentum_1w")}

Cena: {stock.get("price")}
RSI (14): {stock.get("RSI (14)")}
EMA(20): {stock.get("EMA (20)")}
MACD: {stock.get("MACD (12,26,9)")}
MACD Signal: {stock.get("MACD_Signal (12,26,9)")}

Percent Change: {stock.get("percent_change")}
News Sentiment: {stock.get("news_sentiment_percent")}

ÚLOHY:
1. Doplň pole "AIComment" – 2–3 vety o tom, či je akcia vhodná / nevhodná na obchod 2–10 dní.
2. Doplň pole "AIScore" – hodnota 0–100, kde 100 = ideálna krátkodobá príležitosť.
3. Vráť **čistý JSON objekt**:

{{
    "AIComment": "...",
    "AIScore": číslo
}}

Bez ďalšieho textu.
"""

def ask_openai(prompt):
    """Odošle prompt do OpenAI a vráti JSON odpoveď."""
    try:
        response = openai.chat.completions.create(
            model=AI_MODEL,
            messages=[
                {"role": "system", "content": "Si skúsený finančný analytik. Vždy vraciaš čistný JSON."},
                {"role": "user", "content": prompt}
            ],
            temperature=0,
            max_tokens=500
        )
        text = response.choices[0].message.content.strip()
        return json.loads(text)

    except Exception as e:
        print(f"❌ AI chyba: {e}")
        return None

# ---------- HLAVNÁ ČASŤ ----------

if not Path(INPUT_FILE).exists():
    print(f"⚠️ Súbor {INPUT_FILE} neexistuje.")
    exit(1)

# Načítame pôvodný JSON
with open(INPUT_FILE, "r", encoding="utf-8") as f:
    stocks = json.load(f)

results = []

for stock in stocks:

    prompt = build_prompt(stock)

    ai_data = ask_openai(prompt)

    time.sleep(SLEEP_BETWEEN_REQUESTS)

    if ai_data:
        stock["AIComment"] = ai_data.get("AIComment")
        stock["AIScore"] = ai_data.get("AIScore")
        print(f"✅ {stock['ticker']} – AIScore {stock['AIScore']}")
    else:
        stock["AIComment"] = "Error"
        stock["AIScore"] = 0
        print(f"⚠️ {stock['ticker']} – AI ERROR, priradené AIScore = 0")

    results.append(stock)

    time.sleep(SLEEP_BETWEEN_STOCKS)

# ✅ ZORADENIE PODĽA AIScore
results_sorted = sorted(
    results,
    key=lambda x: x.get("AIScore", 0),
    reverse=True
)

# ✅ uložíme výstup — presne ako vstup + 2 polia, len zoradené
Path("data").mkdir(exist_ok=True)
with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
    json.dump(results_sorted, f, indent=2, ensure_ascii=False)

print(f"💾 Výstup uložený do {OUTPUT_FILE} ({len(results_sorted)} akcií, zoradené podľa AIScore).")
