import json
from pathlib import Path
from datetime import datetime

INPUT_FILE = "data/step8_SLTP.json"
OUTPUT_FILE = "docs/ai_report.html"

# ---------- Helper pre farebne zobrazenie ----------
def colorize_rating(value):
    if value is None:
        return "N/A"
    if value >= 90:
        color = "#2ecc71"  # svetlozelená
    elif value >= 80:
        color = "#27ae60"  # tmavozelená
    elif value >= 70:
        color = "#f39c12"  # oranžová
    elif value >= 60:
        color = "#e67e22"  # tmavo oranžová
    elif value >= 50:
        color = "#e74c3c"  # červená
    else:
        color = "#c0392b"  # tmavočervená
    return f"<b style='color:{color}'>{value}</b>"

def generate_html(data):
    today = datetime.now().strftime("%Y-%m-%d %H:%M")
    rows = ""

    for stock in data:
        ticker = stock.get("ticker", "")
        name = stock.get("name", "")
        price = round(stock.get("price", 0))
        SL10 = round(stock.get("SL10", 0), 2)
        TP10 = round(stock.get("TP10", 0), 2)
        ai_score = stock.get("AIScore", 0)
        overall = stock.get("OverallRating", 0)
        ff_rating = stock.get("FundamentalFilterRating", "N/A")
        tf_rating = stock.get("TechFilterRating", "N/A")
        news_sent = stock.get("news_sentiment_percent", "N/A")
        ai_comment = stock.get("AIComment", "")

        # prvý riadok: hodnoty
        row1 = f"""
        <tr>
            <td rowspan="2" style="text-align:center; vertical-align:middle;"><b>{ticker}</b><br><small>{name}</small></td>
            <td style="text-align:center;">{price}</td>
            <td style="text-align:center;">{SL10}</td>
            <td style="text-align:center;">{TP10}</td>
            <td style="text-align:center;">{colorize_rating(ai_score)}</td>
            <td style="text-align:center;">{colorize_rating(overall)}</td>
            <td style="text-align:center;">{ff_rating}</td>
            <td style="text-align:center;">{tf_rating}</td>
            <td style="text-align:center;">{news_sent}</td>
        </tr>"""

        # druhý riadok: AIComment cez všetky stĺpce okrem ticker/name
        row2 = f"""
        <tr>
            <td colspan="8">{ai_comment}</td>
        </tr>"""

        rows += row1 + row2

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
                <th>SL10</th>
                <th>TP10</th>
                <th>AIScore</th>
                <th>OverallRating</th>
                <th>FundamentalFilterRating</th>
                <th>TechFilterRating</th>
                <th>News Sentiment</th>
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
