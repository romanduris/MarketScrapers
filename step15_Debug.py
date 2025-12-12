import os
import requests
import json
from pathlib import Path

# --- Cesta k vstupnému JSON ---
DATA_FILE = Path(r"data/step8_SLTP.json")

# --- Demo API Capital.com ---
BASE = "https://demo-api-capital.backend-capital.com/api/v1"
IDENTIFIER = os.getenv("CAPITAL_IDENTIFIER")
API_KEY = os.getenv("CAPITAL_API_KEY")
API_KEY_PASSWORD = os.getenv("CAPITAL_API_PASSWORD")

# --- Načítanie JSON súboru ---
with open(DATA_FILE, "r") as f:
    data = json.load(f)

# Získanie tickers zo súboru
tickers_to_check = [item["ticker"] for item in data]

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

# --- Výpis EPIC pre tickery zo súboru ---
print("Ticker | Name | EPIC | Status | Offer Price")

for ticker in tickers_to_check:
    found = False
    for m in markets:
        if m.get("instrumentType") == "SHARES" and m.get("symbol") == ticker:
            print(f"{ticker} | {m.get('instrumentName')} | {m.get('epic')} | {m.get('marketStatus')} | {m.get('offer')}")
            found = True
            break
    if not found:
        print(f"{ticker} | NOT FOUND in demo account SHARES")
