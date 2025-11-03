"""
Step 6 – HTML Report (v2)
Vytvorí vizuálne prehľadný HTML report s AI analýzou a odporúčaniami.
Obsahuje: ticker, ai_summary, current_price, TP, SL, BuyScore, Combined sentiment, AI analysis, ai_recommendation
"""

import json
from pathlib import Path
from datetime import datetime

# ---------- SETTINGS ----------
INPUT_FILE = "data/step5_ai_report.json"
OUTPUT_FILE = "docs/ai_report.html"

# ---------- HELPER ----------
def colorize_recommendation(rec, conf=0):
    """Vráti HTML s farebným označením podľa typu odporúčania"""
    rec_lower = rec.lower()
    if "strong buy" in rec_lower or ("buy" in rec_lower and conf >= 70):
        color = "#2ecc71"  # green
    elif "buy" in rec_lower:
        color = "#27ae60"  # light green
    elif "hold" in rec_lower:
        color = "#f1c40f"  # orange
    elif "sell" in rec_lower:
        color = "#e74c3c"  # red
    else:
        color = "#95a5a6"  # gray
    return f"<b style='color:{color}'>{rec}</b> ({conf}%)"


def colorize_score(value):
    """Vráti farebný štýl pre percentuálne alebo skóre hodnoty"""
    if value >= 0.7:
        color = "#2ecc71"
    elif value >= 0.4:
        color = "#f1c40f"
    else:
        color = "#e74c3c"
    return f"<b style='color:{color}'>{value:.3f}</b>"


def generate_html(data):
    """Generuje HTML report ako string"""
    today = datetime.now().strftime("%Y-%m-%d %H:%M")

    rows = ""
    for stock in data:
        ai_summary = stock.get("ai_summary", "N/A")
        ai_analysis = stock.get("ai_analysis", "N/A")
        rec = stock.get("ai_recommendation", "N/A")
        conf = stock.get("ai_recommendation_percent", 0)
        buy_score = stock.get("buy_score_percent", stock.get("buy_score", 0))
        combined_sent = stock.get("combined_sentiment", 0)

        rows += f"""
        <tr>
            <td><b>{stock.get('ticker','')}</b></td>
            <td>{ai_summary}</td>
            <td style="text-align:center;">{stock.get('current_price',0):.2f}</td>
            <td style="text-align:center;">{stock.get('TP',0):.2f}</td>
            <td style="text-align:center;">{stock.get('SL',0):.2f}</td>
            <td style="text-align:center;">{colorize_score(buy_score/100 if buy_score > 1 else buy_score)}</td>
            <td style="text-align:center;">{colorize_score(combined_sent)}</td>
            <td>{ai_analysis}</td>
            <td style="text-align:center;">{colorize_recommendation(rec, conf)}</td>
        </tr>
        """

    html = f"""
    <html>
    <head>
        <meta charset="utf-8">
        <title>AI Stock Analysis Report</title>
        <style>
            body {{
                font-family: 'Segoe UI', Roboto, Arial, sans-serif;
                background: #f7f9fb;
                color: #333;
                margin: 40px;
            }}
            h1 {{
                color: #2c3e50;
            }}
            table {{
                width: 100%;
                border-collapse: collapse;
                margin-top: 20px;
                background: white;
                box-shadow: 0 0 10px rgba(0,0,0,0.05);
                border-radius: 12px;
                overflow: hidden;
            }}
            th {{
                background: #34495e;
                color: white;
                text-align: center;
                padding: 10px;
                font-size: 14px;
            }}
            td {{
                border-bottom: 1px solid #ecf0f1;
                padding: 10px;
                vertical-align: top;
                font-size: 14px;
            }}
            tr:hover {{
                background-color: #f0f3f6;
            }}
            b {{
                font-weight: 600;
            }}
            small {{
                color: #555;
                display: block;
                line-height: 1.4;
            }}
            .footer {{
                margin-top: 40px;
                text-align: center;
                font-size: 12px;
                color: #888;
            }}
        </style>
    </head>
    <body>
        <h1>📊 AI Stock Recommendation Report</h1>
        <p>Generated: <b>{today}</b></p>
        <table>
            <tr>
                <th>Ticker</th>
                <th>AI Summary</th>
                <th>Current Price</th>
                <th>TP</th>
                <th>SL</th>
                <th>Buy Score</th>
                <th>Combined Sentiment</th>
                <th>AI Analysis</th>
                <th>AI Recommendation</th>
            </tr>
            {rows}
        </table>
        <div class="footer">
            <p>Generated automatically by MarketScraper AI system 🧠 | Step 6 Report</p>
        </div>
    </body>
    </html>
    """
    return html


def run_html_report():
    print("🧾 Step 6: Generujem HTML report...")

    Path("docs").mkdir(exist_ok=True)

    try:
        with open(INPUT_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
    except Exception as e:
        print(f"⚠️ Chyba pri načítaní vstupu {INPUT_FILE}: {e}")
        return

    # ak je vstup dict z predchádzajúcich krokov
    if isinstance(data, dict):
        data = data.get("top_candidates") or data.get("ranked_candidates") or data

    # zoradenie podľa buy_score_percent, ak je
    data = sorted(data, key=lambda x: x.get("buy_score_percent", 0), reverse=True)

    html = generate_html(data)

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        f.write(html)

    print(f"✅ HTML report uložený do: {OUTPUT_FILE}")
    print("📬 Report pripravený na GitHub Pages alebo lokálne otvorenie v prehliadači.")


if __name__ == "__main__":
    run_html_report()
