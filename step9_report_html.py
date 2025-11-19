import json
from pathlib import Path
from datetime import datetime

INPUT_FILE = "data/step8_SLTP.json"
OUTPUT_FILE = "docs/ai_report.html"

# ---------- Helper pre farebne zobrazenie trendu so šípkou ----------
def colorize_trend(trend):
    if trend is None:
        color = "#f39c12"  # oranžová pre neutral/unknown
        text = "→ N/A"
    elif trend.lower() == "up":
        color = "#2ecc71"  # zelená
        text = "▲ UP"
    elif trend.lower() == "down":
        color = "#e74c3c"  # červená
        text = "▼ DOWN"
    else:
        color = "#f39c12"  # oranžová
        text = f"→ {trend.upper()}"
    return f"<b style='color:{color}'>{text}</b>"

def colorize_rating(value):
    if value is None:
        return "N/A"
    if value >= 90:
        color = "#2ecc71"
    elif value >= 80:
        color = "#27ae60"
    elif value >= 70:
        color = "#f39c12"
    elif value >= 60:
        color = "#e67e22"
    elif value >= 50:
        color = "#e74c3c"
    else:
        color = "#c0392b"
    return f"<b style='color:{color}'>{value}</b>"

def generate_html(data):
    today = datetime.now().strftime("%Y-%m-%d %H:%M")
    rows = ""

    for stock in data:
        ticker = stock.get("ticker", "")
        name = stock.get("name", "")
        price = round(stock.get("price", 0), 2)
        SL = round(stock.get("SL", 0), 2)
        TP = round(stock.get("TP", 0), 2)
        ai_score = stock.get("AIScore", 0)
        overall = stock.get("OverallRating", 0)
        market_trend = colorize_trend(stock.get("market_trend"))
        sector_trend = colorize_trend(stock.get("sector_trend"))
        aiticker = stock.get("AITicker", "")
        ai_comment = stock.get("AIComment", "")

        # prvý riadok: hodnoty
        row1 = f"""
        <tr>
            <td rowspan="3" style="text-align:center; vertical-align:middle;"><b>{ticker}</b><br><small>{name}</small></td>
            <td style="text-align:center;">{price}</td>
            <td style="text-align:center;">{SL}</td>
            <td style="text-align:center;">{TP}</td>
            <td style="text-align:center;">{colorize_rating(ai_score)}</td>
            <td style="text-align:center;">{colorize_rating(overall)}</td>
            <td style="text-align:center;">{market_trend}</td>
            <td style="text-align:center;">{sector_trend}</td>
        </tr>"""

        # druhý riadok: AITicker
        row2 = f"""
        <tr>
            <td colspan="8">{aiticker}</td>
        </tr>"""

        # tretí riadok: AIComment
        row3 = f"""
        <tr>
            <td colspan="8">{ai_comment}</td>
        </tr>"""

        rows += row1 + row2 + row3

    html = f"""
    <html>
    <head>
        <meta charset="utf-8">
        <title>AI Stock Report</title>
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
                <th>Ticker / Name</th>
                <th>Price</th>
                <th>SL</th>
                <th>TP</th>
                <th>AIScore</th>
                <th>OverallRating</th>
                <th>Market Trend</th>
                <th>Sector Trend</th>
            </tr>
            {rows}
        </table>
        <div class="footer">
            <p>Generated automatically by MarketScraper system 🧠 | HTML Report</p>
        </div>
    </body>
    </html>
    """
    return html

def run_html_report():
    print("🧾 Generujem HTML report...")

    Path("docs").mkdir(exist_ok=True)

    try:
        with open(INPUT_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
    except Exception as e:
        print(f"⚠️ Chyba pri načítaní vstupu {INPUT_FILE}: {e}")
        return

    # zoradiť podľa AIScore
    data = sorted(data, key=lambda x: x.get("AIScore", 0), reverse=True)

    html = generate_html(data)

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        f.write(html)

    print(f"✅ HTML report uložený do: {OUTPUT_FILE}")

if __name__ == "__main__":
    run_html_report()
