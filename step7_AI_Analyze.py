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

# Rate limiting
SLEEP_BETWEEN_REQUESTS = 1.2
SLEEP_BETWEEN_STOCKS = 0.7

# ---------- FUNCTIONS ----------

def build_prompt(stock):
    """
    Vytvorí textový prompt, ktorý zahrnie všetky dostupné info vrátane market a sector trendov.
    """
    return f"""
Analyzuj túto akciu na obchod 2–10 dní a vytvor AIComment, AIScore a AITicker:

Ticker: {stock.get("ticker")}
Názov: {stock.get("name")}
Sector: {stock.get("sector")} ({stock.get("sector_name")})
Market Trend (5d): {stock.get("market_trend")}, Market Change 5d: {stock.get("market_change_5d")}
Sector Trend (5d): {stock.get("sector_trend")}, Sector Change 5d: {stock.get("sector_change_5d")}
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
Trend Market: {stock.get("market_trend")}
Trend Sector: {stock.get("sector_trend")}

ÚLOHY:
1. Doplň pole "AITicker" – jednou vetou zhrň, čo je to za firmu a čomu sa venuje.
2. Doplň pole "AIComment" – 2–3 vety o tom, či je akcia vhodná / nevhodná na obchod 2–10 dní, zohľadni trhový a sektorový trend.
3. Doplň pole "AIScore" – hodnota 0–100, kde 100 = ideálna krátkodobá príležitosť.
4. Vráť čistý JSON objekt:
5. Odpovedaj po anglicky

{{
    "AITicker": "...",
    "AIComment": "...",
    "AIScore": číslo
}}

Bez ďalšieho textu.
"""

def ask_openai(prompt):
    """
    Odošle prompt do OpenAI a vráti JSON odpoveď.
    """
    try:
        response = openai.chat.completions.create(
            model=AI_MODEL,
            messages=[
                {"role": "system", "content": "Si skúsený finančný analytik. Vždy vraciaš čistý JSON."},
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

# ---------- MAIN ----------

if not Path(INPUT_FILE).exists():
    print(f"⚠️ Súbor {INPUT_FILE} neexistuje.")
    exit(1)

with open(INPUT_FILE, "r", encoding="utf-8") as f:
    stocks = json.load(f)

results = []

for stock in stocks:
    prompt = build_prompt(stock)
    ai_data = ask_openai(prompt)
    time.sleep(SLEEP_BETWEEN_REQUESTS)

    if ai_data:
        stock["AITicker"] = ai_data.get("AITicker")
        stock["AIComment"] = ai_data.get("AIComment")
        stock["AIScore"] = ai_data.get("AIScore")
        print(f"✅ {stock['ticker']} – AIScore {stock['AIScore']}")
    else:
        stock["AITicker"] = f"{stock.get('ticker')}: Info unavailable"
        stock["AIComment"] = "Error"
        stock["AIScore"] = 0
        print(f"⚠️ {stock['ticker']} – AI ERROR, priradené AIScore = 0")

    results.append(stock)
    time.sleep(SLEEP_BETWEEN_STOCKS)

# Zoradíme podľa AIScore
results_sorted = sorted(results, key=lambda x: x.get("AIScore", 0), reverse=True)

# Uložíme výstup
Path("data").mkdir(exist_ok=True)
with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
    json.dump(results_sorted, f, indent=2, ensure_ascii=False)

print(f"💾 Výstup uložený do {OUTPUT_FILE} ({len(results_sorted)} akcií, zoradené podľa AIScore).")
