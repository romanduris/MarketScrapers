"""
Step 6 – HTML Report
Vytvorí vizuálne atraktívny HTML report z AI hodnotenia akcií.
Výstup obsahuje: rank, ticker, current_price, TP, SL, buy_score, combined_sentiment, recommendation, reasoning.
"""

import json
from pathlib import Path
from datetime import datetime

INPUT_FILE = "data/step5_ai_report.json"
OUTPUT_FILE = "data/ai_report.html"

def generate_html(data):
    """Generuje HTML report ako string"""
    today = datetime.now().strftime("%Y-%m-%d %H:%M")

    rows = ""
    for stock in data:
        reasoning_html = "<br>".join(stock.get("reasoning", "").splitlines())
        rows += f"""
        <tr>
            <td style="text-align:center;">{stock.get('rank','')}</td>
            <td><b>{stock.get('ticker','')}</b></td>
            <td style="text-align:center;">{stock.get('current_price',0):.2f}</td>
            <td style="text-align:center;">{stock.get('TP',0):.2f}</td>
            <td style="text-align:center;">{stock.get('SL',0):.2f}</td>
            <td style="text-align:center;">{stock.get('buy_score',0):.3f}</td>
            <td style="text-align:center;">{stock.get('combined_sentiment',0):.3f}</td>
            <td style="text-align:center;">{stock.get('recommendation','')}</td>
            <td><small>{reasoning_html}</small></td>
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
                background: #f5f7fa;
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
                border-radius: 10px;
                overflow: hidden;
            }}
            th {{
                background: #3949ab;
                color: white;
                text-align: center;
                padding: 10px;
            }}
            td {{
                border-bottom: 1px solid #e0e0e0;
                padding: 8px 10px;
                vertical-align: top;
            }}
            tr:hover {{
                background-color: #f1f1f1;
            }}
            small {{
                color: #555;
                display: block;
                margin-top: 5px;
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
                <th>#</th>
                <th>Ticker</th>
                <th>Current Price</th>
                <th>TP</th>
                <th>SL</th>
                <th>Buy Score</th>
                <th>Combined Sent.</th>
                <th>Recommendation</th>
                <th>Reasoning</th>
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

    try:
        with open(INPUT_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
    except Exception as e:
        print(f"⚠️ Chyba pri načítaní vstupu {INPUT_FILE}: {e}")
        return

    # Zoradenie podľa rank
    data = sorted(data, key=lambda x: x.get("rank", 0))

    html = generate_html(data)

    Path("data").mkdir(exist_ok=True)
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        f.write(html)

    print(f"✅ HTML report uložený do: {OUTPUT_FILE}")
    print("📬 Pripravené na odoslanie e-mailom alebo otvorenie v prehliadači.")

if __name__ == "__main__":
    run_html_report()
