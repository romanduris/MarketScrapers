"""
STEP 5 – AI Comment s TP a SL
- Top 5 akcií, ktoré boli vybrané
- Doplní current_price cez yfinance, ak chýba
- Generovanie AI reasoning
- Výpočet odporúčaného Take Profit (TP) a Stop Loss (SL)
- Výstup uložený do data/step5_ai_report.json
"""

import json
from pathlib import Path
import yfinance as yf

# ---------- FUNKCIA TP/SL ----------
def calculate_tp_sl(current_price, tp_percent=5, sl_percent=3):
    """Vypočíta odporúčané TP a SL."""
    tp_price = round(current_price * (1 + tp_percent / 100), 2)
    sl_price = round(current_price * (1 - sl_percent / 100), 2)
    return tp_price, sl_price

# ---------- Hlavná funkcia ----------
def run_ai_comment(top_stocks):
    print("📡 Generovanie AI komentárov a TP/SL pre top akcie...")

    output = []

    for i, stock in enumerate(top_stocks, start=1):
        # doplnenie current_price, ak neexistuje alebo je 0
        if "current_price" not in stock or stock["current_price"] == 0:
            ticker = stock["ticker"]
            try:
                info = yf.Ticker(ticker).info
                stock["current_price"] = info.get("regularMarketPrice", 0)
            except Exception as e:
                print(f"⚠️ Chyba pri načítaní ceny pre {ticker}: {e}")
                stock["current_price"] = 0

        # výpočet TP a SL
        tp, sl = calculate_tp_sl(stock["current_price"])

        # placeholder reasoning – tu môže prísť AI analýza (GPT4All/GPT)
        reasoning = f"""
        AI reasoning pre {stock['ticker']} ({stock.get('name', '')}):
        - Aktuálna cena: {stock['current_price']}
        - RSI: {stock.get('rsi', 'N/A')}
        - Volume: {stock.get('volume', 'N/A')}
        - Percent change: {stock.get('percent_change', 'N/A')}%
        - News sentiment: {stock.get('news_sentiment', 'N/A')}
        - Social sentiment: {stock.get('social_sentiment', 'N/A')}
        - Combined sentiment: {stock.get('combined_sentiment', 'N/A')}
        - TP (Take Profit): {tp}
        - SL (Stop Loss): {sl}
        """

        output.append({
            "rank": i,
            "ticker": stock["ticker"],
            "name": stock.get("name", ""),
            "current_price": stock["current_price"],
            "TP": tp,
            "SL": sl,
            "reasoning": reasoning.strip(),
            "rsi": stock.get("rsi", None),
            "volume": stock.get("volume", None),
            "percent_change": stock.get("percent_change", None),
            "news_sentiment": stock.get("news_sentiment", None),
            "social_sentiment": stock.get("social_sentiment", None),
            "combined_sentiment": stock.get("combined_sentiment", None)
         
        })

        print(f"✅ [{i}] {stock['ticker']} – TP: {tp}, SL: {sl}")

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
        print(f"⚠️ Subor {input_file} neexistuje. Spusť najprv step4_ranking.py")
    else:
        top_stocks = json.load(open(input_file, "r", encoding="utf-8"))
        run_ai_comment(top_stocks[:5])
