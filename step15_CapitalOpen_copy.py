import os
import requests
import time

# =========================
# CONFIG
# =========================
BASE = "https://demo-api-capital.backend-capital.com/api/v1"

IDENTIFIER = os.getenv("CAPITAL_IDENTIFIER")
API_KEY = os.getenv("CAPITAL_API_KEY")
API_PASSWORD = os.getenv("CAPITAL_API_PASSWORD")

if not all([IDENTIFIER, API_KEY, API_PASSWORD]):
    raise RuntimeError("Missing Capital.com API credentials")

HEADERS_BASE = {
    "X-CAP-API-KEY": API_KEY,
    "Content-Type": "application/json",
}

# =========================
# LOGIN
# =========================
r = requests.post(
    BASE + "/session",
    headers=HEADERS_BASE,
    json={
        "identifier": IDENTIFIER,
        "password": API_PASSWORD,
        "encryptedPassword": False,
    },
)
r.raise_for_status()

CST = r.headers["CST"]
XSEC = r.headers["X-SECURITY-TOKEN"]
HEADERS = {**HEADERS_BASE, "CST": CST, "X-SECURITY-TOKEN": XSEC}
print("LOGIN OK")

# =========================
# LOAD MARKETS
# =========================
r = requests.get(BASE + "/markets", headers=HEADERS)
r.raise_for_status()
all_markets = r.json().get("markets", [])
print(f"Total markets loaded: {len(all_markets)}")

# =========================
# FILTER: TRADEABLE SHARES, price > 100 USD, relevant market (USA/EU)
# =========================
tradeable_shares = [
    m for m in all_markets
    if m.get("instrumentType") == "SHARES"
    and m.get("marketStatus") == "TRADEABLE"
    and m.get("offer") and m.get("offer") > 100
]


if not tradeable_shares:
    raise RuntimeError("No tradeable SHARES found with offer > 50 USD on USA/EU markets")

# Print top 5
print("\nTop 5 tradable SHARES (price >50 USD, USA/EU, demo):")
top_5 = tradeable_shares[:5]
for i, m in enumerate(top_5, start=1):
    print(f"[{i}] EPIC: {m['epic']} | Name: {m['instrumentName']} | Bid/Offer: {m.get('bid')}/{m.get('offer')}")

# Vyberieme prvú akciu pre obchodovanie
selected = top_5[0]
epic = selected["epic"]
name = selected["instrumentName"]
offer = selected.get("offer")
print(f"\nSelected for trading: {epic} | {name} | Offer: {offer}")

# =========================
# TRADE PARAMETERS
# =========================
direction = "BUY"
size = 10  # Ak cena >100 USD, size=1 je väčšinou OK

# Stop Loss = −10%
stop_loss = round(offer * 0.90, 2)

# Take Profit = +10%
take_profit = round(offer * 1.10, 2)

print(f"Preparing MARKET BUY for {epic}: SL={stop_loss}, TP={take_profit}")

payload = {
    "epic": epic,
    "direction": direction,
    "size": size,
    "orderType": "MARKET",
    "stopLevel": stop_loss,
    "limitLevel": take_profit
}

# =========================
# PLACE ORDER
# =========================
r = requests.post(BASE + "/positions", headers=HEADERS, json=payload)
r.raise_for_status()
order = r.json()
deal_reference = order["dealReference"]
print(f"Order sent. Deal reference: {deal_reference}")

# =========================
# CONFIRM
# =========================
time.sleep(1)
r = requests.get(BASE + f"/confirms/{deal_reference}", headers=HEADERS)
r.raise_for_status()
confirm = r.json()

print("\nConfirmation results:")
print(f"Status: {confirm.get('dealStatus')}")
print(f"EPIC: {confirm.get('epic')}")
print(f"Entry level: {confirm.get('level')}")
print(f"SL: {confirm.get('stopLevel')}")
print(f"TP: {confirm.get('limitLevel')}")

print("\n--- Script completed ---")
