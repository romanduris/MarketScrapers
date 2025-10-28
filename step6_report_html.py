"""
Step 6 – HTML Report
Vytvorí vizuálne atraktívny HTML report z AI hodnotenia akcií.
Vhodné aj ako príloha pre e-mail briefing.
"""

import json
from pathlib import Path
from datetime import datetime

INPUT_FILE = "data/step5_ai_report.json"
OUTPUT_FILE = "data/ai_report.html"

def get_rating_color(rating: str) -> str:
    """Farby pre rating"""
    if "BUY" in rating:
        return "#00c853"  # zelená
    elif "WATCH" in rating:
        return "#ffb300"  # oranžová
    elif "HOLD" in rating:
        return "#03a9f4"  # modrá
    else:
        return "#d50000"  # červená

def generate_html(data):
    """Generuje HTML report ako string"""
    today = datetime.now().strftime("%Y-%m-%d %H:%M")

    rows = ""
    for i, stock in enumerate(data, start=1):
        # farebné zvýraznenie ratingu (ak existuje)
        color = get_rating_color(stock.get("ai_rating", ""))
        reasoning_html = "<br>".join(stock.get("reasoning", "").splitlines())
        rows += f"""
        <tr>
            <td style="text-align:center;">{i}</td>
            <td><b>{stock.get('ticker','')}</b></td>
            <td>{stock.get('name','')}</td>
            <td style="text-align:center;">{stock.get('rsi','N/A')}</td>
            <td style="text-align:center;">{stock.get('volume','N/A'):,}</td>
            <td style="text-align:center;">{stock.get('percent_change','N/A')}%</td>
            <td style="text-align:center;">{stock.get('news_sentiment',0.0):.3f}</td>
            <td style="text-align:center;">{stock.get('combined_sentiment',0.0):.3f}</td>
            <td style="text-align:center; color:{color}; font-weight:bold;">{stock.get('ai_rating','')}</td>
            <td>
                <b>TP:</b> {stock.get('TP',0)} | <b>SL:</b> {stock.get('SL',0)}<br>
                <small>{reasoning_html}</small>
            </td>
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
                <th>Company</th>
                <th>RSI</th>
                <th>Volume</th>
                <th>% Change</th>
                <th>News Sent.</th>
                <th>Comb. Sent.</th>
                <th>AI Rating</th>
                <th>AI Reasoning</th>
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

    # zoradenie podľa score alebo combined_sentiment
    data = sorted(data, key=lambda x: x.get("score", x.get("combined_sentiment", 0)), reverse=True)

    html = generate_html(data)

    Path("data").mkdir(exist_ok=True)
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        f.write(html)

    print(f"✅ HTML report uložený do: {OUTPUT_FILE}")
    print("📬 Pripravené na odoslanie e-mailom alebo otvorenie v prehliadači.")

if __name__ == "__main__":
    run_html_report()
