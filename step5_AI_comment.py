"""
STEP 5 – AI Summary + Analysis + TP/SL
- Všetky akcie zo vstupného súboru
- Doplní current_price cez yfinance, ak chýba
- Generovanie AI popisu a dátovej analýzy (GPT-4 / GPT-3.5)
- Výpočet odporúčaného Take Profit (TP) a Stop Loss (SL)
- Výstup uložený do data/step5_ai_report.json
"""

import json
from pathlib import Path
import yfinance as yf
import openai
import os

# ---------- SETTINGS ----------
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
AI_MODEL = "gpt-4-turbo"  # alebo "gpt-3.5-turbo" podľa prístupu
TP_PERCENT = 5
SL_PERCENT = 3

openai.api_key = OPENAI_API_KEY

# ---------- FUNKCIA TP/SL ----------
def calculate_tp_sl(current_price, tp_percent=TP_PERCENT, sl_percent=SL_PERCENT):
    tp_price = round(current_price * (1 + tp_percent / 100), 2)
    sl_price = round(current_price * (1 - sl_percent / 100), 2)
    return tp_price, sl_price


# ---------- FUNKCIA 1: AI SUMMARY ----------
def generate_ai_summary(stock):
    prompt = f"""
Napíš jednu vetu o akcii {stock.get('ticker')} ({stock.get('name', '')}), v ktorej zhrnieš, čím sa spoločnosť zaoberá
a v akom segmente pôsobí. Nepíš investičné odporúčanie.
"""
    try:
        response = openai.chat.completions.create(
            model=AI_MODEL,
            messages=[
                {"role": "system", "content": "Si skúsený finančný analytik a vieš stručne charakterizovať firmy."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.6,
            max_tokens=120
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        print(f"⚠️ Chyba pri AI summary pre {stock.get('ticker')}: {e}")
        return "Popis spoločnosti sa nepodarilo získať."


# ---------- FUNKCIA 2: AI ANALYSIS ----------
def generate_ai_analysis(stock):
    prompt = f"""
Na základe týchto údajov zhodnoť akciu {stock.get('ticker')} ({stock.get('name','')}):
- percent_change: {stock.get('percent_change', 'N/A')}
- volume_gain: {stock.get('volume_gain', 'N/A')}
- RSI: {stock.get('rsi', 'N/A')}
- MACD: {stock.get('macd', 'N/A')}
- EMA: {stock.get('ema', 'N/A')}
- news_sentiment_percent: {stock.get('news_sentiment_percent', 'N/A')}

Zohľadni aj aktuálne informácie dostupné online.
Vráť krátku, max 1 vetu, ktorá:
1. stručne zhrnie vývoj akcie,
2. obsahuje jasné odporúčanie (Buy / Hold / Sell),
3. pridaj percentuálne vyjadrenie istoty ako „Confidence: XX%“.
"""
    try:
        response = openai.chat.completions.create(
            model=AI_MODEL,
            messages=[
                {"role": "system", "content": "Si skúsený analytik akciových trhov, ktorý kombinuje dáta s aktuálnymi informáciami."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
            max_tokens=180
        )
        full_text = response.choices[0].message.content.strip()

        # extrakcia odporúčania a percent z textu
        rec_word = "Hold"
        rec_percent = 50
        for word in ["Strong Buy", "Buy", "Sell", "Strong Sell", "Hold"]:
            if word.lower() in full_text.lower():
                rec_word = word
                break

        import re
        perc_match = re.search(r"(\d{1,3})\s?%", full_text)
        if perc_match:
            rec_percent = int(perc_match.group(1))

        return full_text, rec_word, rec_percent

    except Exception as e:
        print(f"⚠️ Chyba pri AI analýze pre {stock.get('ticker')}: {e}")
        return ("Analýzu sa nepodarilo vygenerovať.", "Hold", 50)


# ---------- HLAVNÁ FUNKCIA ----------
def run_ai_comment(all_stocks):
    print("📡 Generovanie AI summary, analýzy a TP/SL pre všetky akcie...")

    output = []

    for i, stock in enumerate(all_stocks, start=1):
        ticker = stock.get("ticker")

        # doplnenie current_price ak chýba
        if "current_price" not in stock or not stock["current_price"]:
            try:
                info = yf.Ticker(ticker).info
                stock["current_price"] = info.get("regularMarketPrice", 0)
            except Exception as e:
                print(f"⚠️ Chyba pri načítaní ceny pre {ticker}: {e}")
                stock["current_price"] = 0

        # výpočet TP a SL
        tp, sl = calculate_tp_sl(stock["current_price"])

        # AI výstupy
        ai_summary = generate_ai_summary(stock)
        ai_analysis, ai_rec, ai_conf = generate_ai_analysis(stock)

        enriched = {
            **stock,  # zachová všetky pôvodné údaje
            "TP": tp,
            "SL": sl,
            "ai_summary": ai_summary,
            "ai_analysis": ai_analysis,
            "ai_recommendation": ai_rec,
            "ai_recommendation_percent": ai_conf
        }
        output.append(enriched)

        print(f"✅ [{i}] {ticker} – TP: {tp}, SL: {sl}, AI rec: {ai_rec} ({ai_conf}%)")

    # uloženie do JSON
    Path("data").mkdir(exist_ok=True)
    output_file = Path("data/step5_ai_report.json")
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(output, f, indent=2, ensure_ascii=False)

    print(f"\n💾 Step 5 výstup uložený do: {output_file} ({len(output)} akcií)")
    return output


# ---------- MAIN ----------
if __name__ == "__main__":
    input_file = Path("data/step4_top10.json")
    if not input_file.exists():
        print(f"⚠️ Súbor {input_file} neexistuje. Spusť najprv step4_ranking_keep_all.py")
    else:
        with open(input_file, "r", encoding="utf-8") as f:
            data_json = json.load(f)
            # ak máš formát ako {"total_candidates":.., "ranked_candidates":[...]}:
            all_stocks = data_json.get("ranked_candidates", data_json)
        run_ai_comment(all_stocks)
