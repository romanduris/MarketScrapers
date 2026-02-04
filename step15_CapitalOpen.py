import os
import requests
import json
from pathlib import Path

# --- Cesta k vstupnému JSON ---
DATA_FILE = Path(r"data/step9_Normalize.json")

# --- Demo API Capital.com ---
BASE = "https://demo-api-capital.backend-capital.com/api/v1"
IDENTIFIER = os.getenv("CAPITAL_IDENTIFIER")
API_KEY = os.getenv("CAPITAL_API_KEY")
API_KEY_PASSWORD = os.getenv("CAPITAL_API_PASSWORD")

# --- Načítanie JSON súboru ---
with open(DATA_FILE, "r") as f:
    data = json.load(f)

# --- Prihlásenie na API ---
r = requests.post(
    BASE + "/session",
    headers={"X-CAP-API-KEY": API_KEY, "Content-Type": "application/json"},
    json={"identifier": IDENTIFIER, "password": API_KEY_PASSWORD, "encryptedPassword": False}
)
cst = r.headers["CST"]
xsec = r.headers["X-SECURITY-TOKEN"]

# --- Načítanie všetkých markets ---
r = requests.get(
    BASE + "/markets",
    headers={"X-CAP-API-KEY": API_KEY, "CST": cst, "X-SECURITY-TOKEN": xsec},
)
markets = r.json().get("markets", [])
market_dict = {m["symbol"]: m for m in markets if m.get("instrumentType") == "SHARES"}

print("\n--- Starting Trading (CFD, US shares only) ---\n")

count = 0
for item in data:
    ticker = item["ticker"]

    if ticker not in market_dict:
        print(f"{ticker} | NOT FOUND in demo account SHARES → skipping")
        continue

    market = market_dict[ticker]
    epic = market["epic"]
    name = market["instrumentName"]
    status = market["marketStatus"]
    offer_price = market.get("offer")

    print(f"[{count+1}] TICKER: {ticker} | NAME: {name}")
    print("-" * 50)
    print(f"Status: {status} | EPIC: {epic} | Offer Price: {offer_price}")

    if status != "TRADEABLE":
        print("Market not TRADEABLE → skipping\n")
        count += 1
        if count >= 5:
            break
        continue

    # --- Parametre z JSON ---
    size = item.get("Normalize", 1)  # použitie Normalize parametra pre size CFD
    sl = item.get("SL")
    tp = item.get("TP")
    json_price = item.get("price")

    # --- Vytvorenie pozície (BUY CFD) ---
    payload = {
        "epic": epic,
        "direction": "BUY",
        "size": size,
        "orderType": "MARKET",
        "stopLevel": sl,
        "profitLevel": tp,
    }

    r_order = requests.post(
        BASE + "/positions",
        headers={"X-CAP-API-KEY": API_KEY, "CST": cst, "X-SECURITY-TOKEN": xsec},
        json=payload,
    )

    if r_order.status_code == 200:
       print(
        f"BUY executed | Offer: {offer_price} | JSON Price: {json_price} | "
        f"SL: {sl} | TP: {tp} | "
         f"Normalize Factor: {item.get('Normalize', 1):.4f} | Size(CFD): {size:.4f}"
        )
    else:
        print(f"Order failed | Response: {r_order.text}\n")

    count += 1
    if count >= 5:
        break

print("--- FINISHED ---")
