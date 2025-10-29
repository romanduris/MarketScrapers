"""
STEP 5 – AI Comment s TP a SL
- Všetky akcie zo vstupného súboru
- Doplní current_price cez yfinance, ak chýba
- Generovanie AI reasoning cez OpenAI API (nová syntax >=1.0.0)
- Výpočet odporúčaného Take Profit (TP) a Stop Loss (SL)
- Výstup uložený do data/step5_ai_report.json
"""

import json
from pathlib import Path
import yfinance as yf
import openai

# ---------- SETTINGS ----------
OPENAI_API_KEY = "REMOVED_SECRET"  # nastav svoj token
AI_MODEL = "gpt-3.5-turbo"  # alebo "gpt-4" ak máš prístup
TP_PERCENT = 5
SL_PERCENT = 3

openai.api_key = OPENAI_API_KEY

# ---------- FUNKCIA TP/SL ----------
def calculate_tp_sl(current_price, tp_percent=TP_PERCENT, sl_percent=SL_PERCENT):
    tp_price = round(current_price * (1 + tp_percent / 100), 2)
    sl_price = round(current_price * (1 - sl_percent / 100), 2)
    return tp_price, sl_price

# ---------- FUNKCIA AI COMMENT ----------
def generate_ai_reasoning(stock):
    prompt = f"""
Si skúsený finančný analytik. Zhodnoť túto akciu
Akcia: {stock.get('ticker', '')} ({stock.get('name', '')})
Napíš stručný opis podniku, prečo by mohol byť vhodný na kúpu a čo sú riziká. max jedna veta alebo 2 ktatke vety
"""
    try:
        response = openai.chat.completions.create(
            model=AI_MODEL,
            messages=[
                {"role": "system", "content": "Si skúsený finančný analytik."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
            max_tokens=300
        )
        # nová syntax pre získanie textu
        return response.choices[0].message.content.strip()
    except Exception as e:
        print(f"⚠️ Chyba pri generovaní AI reasoning pre {stock.get('ticker','N/A')}: {e}")
        return "AI reasoning sa nepodarilo vygenerovať."

# ---------- HLAVNÁ FUNKCIA ----------
def run_ai_comment(all_stocks):
    print("📡 Generovanie AI komentárov a TP/SL pre všetky akcie...")

    output = []

    for i, stock in enumerate(all_stocks, start=1):
        # doplnenie current_price
        if "current_price" not in stock or stock["current_price"] in (0, None):
            ticker = stock["ticker"]
            try:
                info = yf.Ticker(ticker).info
                stock["current_price"] = info.get("regularMarketPrice", 0)
            except Exception as e:
                print(f"⚠️ Chyba pri načítaní ceny pre {ticker}: {e}")
                stock["current_price"] = 0

        # výpočet TP a SL
        tp, sl = calculate_tp_sl(stock["current_price"])

        # AI reasoning
        reasoning = generate_ai_reasoning(stock)

        output.append({
            "rank": i,
            "ticker": stock["ticker"],
            "name": stock.get("name", ""),
            "current_price": stock["current_price"],
            "TP": tp,
            "SL": sl,
            "reasoning": reasoning,
            "rsi": stock.get("rsi"),
            "volume": stock.get("volume"),
            "percent_change": stock.get("percent_change"),
            "market_cap": stock.get("market_cap"),
            "news_sentiment": stock.get("news_sentiment"),
            "social_sentiment": stock.get("social_sentiment"),
            "combined_sentiment": stock.get("combined_sentiment"),
            "buy_score": stock.get("buy_score"),
            "recommendation": stock.get("recommendation")
        })

        print(f"✅ [{i}] {stock['ticker']} – Cena: {stock['current_price']}, TP: {tp}, SL: {sl}")

    # uloženie do JSON
    Path("data").mkdir(exist_ok=True)
    output_file = Path("data/step5_ai_report.json")
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(output, f, indent=2, ensure_ascii=False)

    print(f"\n💾 Step 5 output uložený do: {output_file} ({len(output)} akcií)")
    return output

# ---------- MAIN ----------
if __name__ == "__main__":
    input_file = Path("data/step4_top10.json")
    if not input_file.exists():
        print(f"⚠️ Súbor {input_file} neexistuje. Spusť najprv step4_ranking.py")
    else:
        all_stocks = json.load(open(input_file, "r", encoding="utf-8"))
        run_ai_comment(all_stocks)
