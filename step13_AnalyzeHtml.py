import json
from pathlib import Path
from collections import defaultdict
from datetime import datetime
import math  # pridané pre kontrolu NaN

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

# ---------- farebné šípky pre market trend ----------
def colorize_trend(trend):
    trend = trend.lower() if trend else "neutral"
    if trend == "up":
        return "<b style='color:#2ecc71'>▲ UP</b>"
    elif trend == "down":
        return "<b style='color:#e74c3c'>▼ DOWN</b>"
    elif trend == "neutral":
        return "<b style='color:#f39c12'>→ NEUTRAL</b>"
    else:
        return f"<b>{trend.upper()}</b>"

# ---------- HTML header ----------
now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
html = f"""
<html>
<head>
<title>Trade Analysis Report</title>
<style>
body {{ font-family: Arial, sans-serif; font-size: 14px; background-color: #f4f4f4; color: #333; }}
h2 {{ color: #fff; background-color: #2c3e50; padding: 12px; border-radius: 4px; }}
table {{ border-collapse: collapse; width: 100%; margin-top: 20px; background-color: #fff; box-shadow: 0 2px 8px rgba(0,0,0,0.1); }}
td, th {{ border: 1px solid #ccc; padding: 6px 10px; text-align: center; }}
th {{ background-color: #34495e; color: #fff; }}
.green {{ color: #2ecc71; font-weight: bold; }}
.red {{ color: #e74c3c; font-weight: bold; }}
.orange {{ color: #f39c12; font-weight: bold; }}
.blue {{ color: #3498db; font-weight: bold; }}
.black {{ color: #000000; font-weight: bold; }}
.small {{ font-size: 10px; color: #555; }}
hr {{ border: 0; border-top: 1px solid #ccc; margin: 4px 0; }}
</style>
</head>
<body>
<h2>📊 Trade Profit Analysis Report (AI ANALYZE 2) - {now_str}</h2>
<p>
<b style="color:#f39c12;">OPEN</b> = otvorený obchod, 
<b style="color:#2ecc71;">TP</b> = Take Profit, 
<b style="color:#e74c3c;">SL</b> = Stop Loss, 
<b style="color:#000000;">TIME_EXIT</b> = Time Exit.<br>
Pod stĺpcom Success Rate = % uzavretých obchodov s profitom > 0.<br>
Pod tabuľkou je celková suma všetkých uzavretých obchodov a otvorených obchodov.
</p>
<table>
<tr>
"""

# ---------- 1. riadok hlavičky: dátumy ----------
for dt in dates:
    date_part = dt.split()[0]
    html += f"<th>{date_part}</th>"
html += "</tr>\n<tr>"

# ---------- 2. riadok hlavičky: časy ----------
for dt in dates:
    time_part = dt.split()[1]
    html += f"<th>{time_part}</th>"
html += "</tr>\n<tr>"

# ---------- 3. riadok hlavičky: market trend ----------
for dt in dates:
    trades_for_date = columns[dt]
    market_trend = trades_for_date[0].get("market_trend", "neutral")
    html += f"<th>{colorize_trend(market_trend)}</th>"
html += "</tr>\n<tr>"

# ---------- funkcia pre bezpečné round pre open_sum ----------
def safe_round(value):
    if value is None or (isinstance(value, float) and math.isnan(value)):
        return 0
    return round(value)

# ---------- hlavná tabuľka hodnoty profit + SUM, OPEN nad Rate ----------
total_sum_all = 0
total_open_all = 0

for dt in dates:
    column_trades = columns[dt]
    col_html = ""
    sum_profit = 0
    closed_count = 0
    profitable_count = 0
    open_sum = 0

    for t in column_trades:
        profit = t.get("profit", 0)
        status = t.get("status", "OPEN")
        if status == "OPEN":
            color_class = "orange"
            open_sum += profit
        elif status == "TP":
            color_class = "green"
        elif status == "SL":
            color_class = "red"
        elif status == "TIME_EXIT":
            color_class = "black"
        else:
            color_class = "blue"
        col_html += f"<div class='{color_class}'>{profit}</div>"
        if status in ["TP","SL","TIME_EXIT"]:
            sum_profit += profit
            closed_count += 1
            if profit>0:
                profitable_count += 1

    total_sum_all += sum_profit
    total_open_all += open_sum
    col_html += f"<hr><div><b>SUM: {safe_round(sum_profit)}</b></div>"

    # diagnostika
    print(f"DEBUG: open_sum = {open_sum}, type = {type(open_sum)}")

    col_html += f"<div class='small' style='color:#f39c12; font-weight:bold;'>OPEN: {safe_round(open_sum)}</div>"
    success_rate = round((profitable_count / closed_count * 100)) if closed_count>0 else 0
    col_html += f"<div class='small blue'>Rate: {success_rate}%</div>"
    html += f"<td>{col_html}</td>"

html += "</tr>"
html += f"<tr><td colspan='{len(dates)}' style='text-align:center; font-weight:bold; background-color:#ecf0f1;'>Total SUM of all closed trades: {safe_round(total_sum_all)} (OPEN: {safe_round(total_open_all)})</td></tr>"

# ---------- pod tabuľkou prvých 10 obchodov ----------
total_sum_first10 = 0
total_open_first10 = 0

html += "<tr>"
for dt in dates:
    column_trades = columns[dt][:10]  # prvých 10 obchodov
    col_html = ""
    sum_profit = 0
    closed_count = 0
    profitable_count = 0
    open_sum = 0

    for t in column_trades:
        profit = t.get("profit",0)
        status = t.get("status","OPEN")
        if status == "OPEN":
            color_class="orange"
            open_sum += profit
        elif status=="TP":
            color_class="green"
        elif status=="SL":
            color_class="red"
        elif status=="TIME_EXIT":
            color_class="black"
        else:
            color_class="blue"
        col_html += f"<div class='{color_class}'>{profit}</div>"
        if status in ["TP","SL","TIME_EXIT"]:
            sum_profit += profit
            closed_count += 1
            if profit>0:
                profitable_count +=1

    total_sum_first10 += sum_profit
    total_open_first10 += open_sum

    col_html += f"<hr><div><b>SUM: {safe_round(sum_profit)}</b></div>"
    col_html += f"<div class='small' style='color:#f39c12; font-weight:bold;'>OPEN: {safe_round(open_sum)}</div>"
    success_rate = round((profitable_count/closed_count*100)) if closed_count>0 else 0
    col_html += f"<div class='small blue'>Rate: {success_rate}%</div>"

    html += f"<td>{col_html}</td>"
html += "</tr>"
html += f"<tr><td colspan='{len(dates)}' style='text-align:center; font-weight:bold; background-color:#ecf0f1;'>Total SUM of first 10 trades: {safe_round(total_sum_first10)} (OPEN: {safe_round(total_open_first10)})</td></tr>"

# ---------- pod tabuľkou prvých 5 obchodov ----------
total_sum_first5 = 0
total_open_first5 = 0

html += "<tr>"
for dt in dates:
    column_trades = columns[dt][:5]  # prvých 5 obchodov
    col_html = ""
    sum_profit = 0
    closed_count = 0
    profitable_count = 0
    open_sum = 0

    for t in column_trades:
        profit = t.get("profit",0)
        status = t.get("status","OPEN")
        if status == "OPEN":
            color_class="orange"
            open_sum += profit
        elif status=="TP":
            color_class="green"
        elif status=="SL":
            color_class="red"
        elif status=="TIME_EXIT":
            color_class="black"
        else:
            color_class="blue"
        col_html += f"<div class='{color_class}'>{profit}</div>"
        if status in ["TP","SL","TIME_EXIT"]:
            sum_profit += profit
            closed_count += 1
            if profit>0:
                profitable_count +=1

    total_sum_first5 += sum_profit
    total_open_first5 += open_sum

    col_html += f"<hr><div><b>SUM: {safe_round(sum_profit)}</b></div>"
    col_html += f"<div class='small' style='color:#f39c12; font-weight:bold;'>OPEN: {safe_round(open_sum)}</div>"
    success_rate = round((profitable_count/closed_count*100)) if closed_count>0 else 0
    col_html += f"<div class='small blue'>Rate: {success_rate}%</div>"

    html += f"<td>{col_html}</td>"
html += "</tr>"
html += f"<tr><td colspan='{len(dates)}' style='text-align:center; font-weight:bold; background-color:#ecf0f1;'>Total SUM of first 5 trades: {safe_round(total_sum_first5)} (OPEN: {safe_round(total_open_first5)})</td></tr>"

# ---------- pod tabuľkou prvá akcia ----------
total_sum_first1 = 0
total_open_first1 = 0

html += "<tr>"
for dt in dates:
    column_trades = columns[dt][:1]  # prvá akcia
    col_html = ""
    sum_profit = 0
    closed_count = 0
    profitable_count = 0
    open_sum = 0

    for t in column_trades:
        profit = t.get("profit",0)
        status = t.get("status","OPEN")
        if status == "OPEN":
            color_class="orange"
            open_sum += profit
        elif status=="TP":
            color_class="green"
        elif status=="SL":
            color_class="red"
        elif status=="TIME_EXIT":
            color_class="black"
        else:
            color_class="blue"
        col_html += f"<div class='{color_class}'>{profit}</div>"
        if status in ["TP","SL","TIME_EXIT"]:
            sum_profit += profit
            closed_count += 1
            if profit>0:
                profitable_count +=1

    total_sum_first1 += sum_profit
    total_open_first1 += open_sum

    col_html += f"<hr><div><b>SUM: {safe_round(sum_profit)}</b></div>"
    col_html += f"<div class='small' style='color:#f39c12; font-weight:bold;'>OPEN: {safe_round(open_sum)}</div>"
    success_rate = round((profitable_count/closed_count*100)) if closed_count>0 else 0
    col_html += f"<div class='small blue'>Rate: {success_rate}%</div>"

    html += f"<td>{col_html}</td>"
html += "</tr>"
html += f"<tr><td colspan='{len(dates)}' style='text-align:center; font-weight:bold; background-color:#ecf0f1;'>Total SUM of first 1 trade: {safe_round(total_sum_first1)} (OPEN: {safe_round(total_open_first1)})</td></tr>"

html += "</table></body></html>"

with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
    f.write(html)

print(f"✅ HTML report uložený do {OUTPUT_FILE}")
