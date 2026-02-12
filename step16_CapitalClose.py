import os
import requests
import time
from datetime import datetime, timezone
import pandas as pd

# =====================================
# CONFIG
# =====================================

BASE = "https://demo-api-capital.backend-capital.com/api/v1"

IDENTIFIER = os.getenv("CAPITAL_IDENTIFIER")
API_KEY = os.getenv("CAPITAL_API_KEY")
API_KEY_PASSWORD = os.getenv("CAPITAL_API_PASSWORD")

AUTO_CLOSE_AFTER_DAYS = 10      # Default threshold (>= znamená zatvoriť)
CLOSE_DELAY_MS = 300            # Delay medzi close requestami (ms)

# =====================================
# LOGIN
# =====================================

r = requests.post(
    BASE + "/session",
    headers={
        "X-CAP-API-KEY": API_KEY,
        "Content-Type": "application/json"
    },
    json={
        "identifier": IDENTIFIER,
        "password": API_KEY_PASSWORD,
        "encryptedPassword": False
    }
)

if r.status_code != 200:
    print("Login failed:", r.text)
    exit()

cst = r.headers["CST"]
xsec = r.headers["X-SECURITY-TOKEN"]

headers = {
    "X-CAP-API-KEY": API_KEY,
    "CST": cst,
    "X-SECURITY-TOKEN": xsec
}

# =====================================
# ACCOUNT INFO
# =====================================

print("\n================ ACCOUNT INFO ================\n")

r_account = requests.get(BASE + "/accounts", headers=headers)

if r_account.status_code != 200:
    print("Account fetch failed:", r_account.text)
    exit()

accounts = r_account.json().get("accounts", [])

for acc in accounts:
    if acc.get("preferred"):
        bal = acc.get("balance", {})
        print(f"Account ID: {acc.get('accountId')}")
        print(f"Currency: {acc.get('currency')}")
        print(f"Balance: {bal.get('balance')}")
        print(f"Equity: {bal.get('equity')}")
        print(f"Available: {bal.get('available')}")
        print(f"Margin Used: {bal.get('margin')}")
        print(f"Profit/Loss: {bal.get('profitLoss')}")
        break

# =====================================
# OPEN POSITIONS
# =====================================

print("\n================ OPEN POSITIONS ================\n")

r_positions = requests.get(BASE + "/positions", headers=headers)

if r_positions.status_code != 200:
    print("Positions fetch failed:", r_positions.text)
    exit()

positions_raw = r_positions.json().get("positions", [])

if not positions_raw:
    print("No open positions.")
    print("\n================ DONE ================\n")
    exit()

today = datetime.now(timezone.utc).date()

positions = []

# --- Príprava dát + výpočet business days ---
for p in positions_raw:
    pos = p.get("position", {})
    market = p.get("market", {})

    created_raw = pos.get("createdDate")

    created_date = datetime.strptime(
        created_raw.split(".")[0],
        "%Y-%m-%dT%H:%M:%S"
    ).date()

    business_days = len(pd.bdate_range(created_date, today)) - 1

    positions.append({
        "dealId": pos.get("dealId"),
        "direction": pos.get("direction"),
        "size": pos.get("size"),
        "open_level": pos.get("level"),
        "profit": pos.get("profit") or pos.get("upl"),
        "created_date": created_date,
        "business_days": business_days,
        "instrument": market.get("instrumentName"),
        "epic": market.get("epic"),
        "bid": market.get("bid"),
        "offer": market.get("offer")
    })

# --- ZORADENIE OD NAJKRATŠIEHO PO NAJDLHŠÍ ---
positions.sort(key=lambda x: x["business_days"])

closed_count = 0

# =====================================
# VÝPIS + AUTO CLOSE
# =====================================

for i, pos in enumerate(positions, 1):

    profit = pos["profit"]

    # fallback výpočet ak profit nie je dostupný
    if profit is None:
        if pos["direction"] == "BUY" and pos["bid"]:
            profit = (pos["bid"] - pos["open_level"]) * pos["size"]
        elif pos["direction"] == "SELL" and pos["offer"]:
            profit = (pos["open_level"] - pos["offer"]) * pos["size"]
        else:
            profit = 0.0

    print(f"[{i}] {pos['instrument']} ({pos['epic']})")
    print(f"Deal ID: {pos['dealId']}")
    print(f"Direction: {pos['direction']}")
    print(f"Size: {pos['size']}")
    print(f"Opened At: {pos['created_date']}")
    print(f"Business Days Open: {pos['business_days']}")
    print(f"Open Level: {pos['open_level']}")
    print(f"Unrealized P/L: {round(profit, 2)}")
    print("-" * 50)

    # =====================================
    # AUTO CLOSE CONDITION
    # =====================================

    if pos["business_days"] >= AUTO_CLOSE_AFTER_DAYS:

        print(f"→ Closing (>= {AUTO_CLOSE_AFTER_DAYS} business days)...")

        close_payload = {
            "dealId": pos["dealId"],
            "direction": "SELL" if pos["direction"] == "BUY" else "BUY",
            "size": pos["size"],
            "orderType": "MARKET"
        }

        r_close = requests.post(
            BASE + "/positions/otc",
            headers=headers,
            json=close_payload
        )

        if r_close.status_code == 200:
            print("✓ Position successfully closed.")
            closed_count += 1
            time.sleep(CLOSE_DELAY_MS / 1000.0)
        else:
            print("✗ Close failed:", r_close.text)

        print("-" * 50)

# =====================================
# SUMMARY
# =====================================

print("\n================ SUMMARY ================\n")
print(f"Total positions closed due to threshold ({AUTO_CLOSE_AFTER_DAYS} days): {closed_count}")
print("\n================ DONE ================\n")
