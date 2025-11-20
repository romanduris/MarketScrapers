import json
from pathlib import Path
from collections import defaultdict

INPUT_FILE = "data/step12_Analyze.json"
OUTPUT_FILE = Path("docs/ai_analyze.html")
OUTPUT_FILE.parent.mkdir(exist_ok=True)

# ---------- načítanie dát ----------
if not Path(INPUT_FILE).exists():
    print(f"❌ Súbor {INPUT_FILE} neexistuje.")
    exit(1)

with open(INPUT_FILE, "r", encoding="utf-8") as f:
    trades = json.load(f)

# ---------- zoskupenie podľa dátumu ----------
columns = defaultdict(list)
dates = set()

for trade in trades:
    purchase_dt = trade["purchase_dt"]
    dates.add(purchase_dt)
    columns[purchase_dt].append(trade)

dates = sorted(dates)

# ---------- HTML header ----------
html = """
<html>
<head>
<title>Trade Analysis Report</title>
<style>
body { font-family: Arial, sans-serif; font-size: 14px; background-color: #f4f4f4; color: #333; }
h2 { color: #fff; background-color: #2c3e50; padding: 12px; border-radius: 4px; }
table { border-collapse: collapse; width: 100%; margin-top: 20px; background-color: #fff; box-shadow: 0 2px 8px rgba(0,0,0,0.1); }
td, th { border: 1px solid #ccc; padding: 6px 10px; text-align: center; }
th { background-color: #34495e; color: #fff; }
.green { color: #2ecc71; font-weight: bold; }
.red { color: #e74c3c; font-weight: bold; }
.orange { color: #f39c12; font-weight: bold; }
hr { border: 0; border-top: 1px solid #ccc; margin: 4px 0; }
</style>
</head>
<body>
<h2>📊 Trade Profit Analysis Report</h2>
<p>Tento report zobrazuje profit pre jednotlivé obchody podľa dátumu kúpy. Oranžová = otvorený obchod, zelená = TP, červená = SL. Na konci každého stĺpca je súčet uzavretých obchodov (TP + SL).</p>
<table>
<tr>
"""

# ---------- dátumy ako hlavička ----------
for dt in dates:
    html += f"<th>{dt}</th>"
html += "</tr>\n<tr>"

# ---------- hodnoty profit ----------
for dt in dates:
    column_trades = columns[dt]
    col_html = ""
    sum_profit = 0
    for t in column_trades:
        profit = t.get("profit", 0)
        status = t.get("status", "OPEN")
        color_class = "orange" if status=="OPEN" else ("green" if status=="TP" else "red")
        col_html += f"<div class='{color_class}'>{profit}</div>"
        if status in ["TP", "SL"]:
            sum_profit += profit
    col_html += f"<hr><div><b>SUM: {round(sum_profit)}</b></div>"
    html += f"<td>{col_html}</td>"

html += "</tr></table></body></html>"

# ---------- uloženie ----------
with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
    f.write(html)

print(f"✅ HTML report uložený do {OUTPUT_FILE}")
