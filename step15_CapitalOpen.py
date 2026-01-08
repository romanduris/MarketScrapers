import os
import requests
import json
import time
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

# --- Mapping ticker -> market data ---
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
    print("-" * 60)
    print(f"Status: {status} | EPIC: {epic} | Offer Price: {offer_price}")

    if status != "TRADEABLE":
        print("Market not TRADEABLE → skipping\n")
        count += 1
        if count >= 5:
            break
        continue

    # --- Parametre z JSON ---
    size = 1
    sl_json = item.get("SL")
    tp_json = item.get("TP")
    json_price = item.get("price")

    # --- CREATE POSITION (BUY CFD) ---
    payload = {
        "epic": epic,
        "direction": "BUY",
        "size": size,
        "orderType": "MARKET",
    }

    # --- POST pozície najprv bez SL/TP ---
    r_order = requests.post(
        BASE + "/positions",
        headers={"X-CAP-API-KEY": API_KEY, "CST": cst, "X-SECURITY-TOKEN": xsec},
        json=payload,
    )

    if r_order.status_code != 200:
        print(f"Order failed | Response: {r_order.text}\n")
        continue

    deal_ref = r_order.json().get("dealReference")
    print(f"BUY executed | DealRef: {deal_ref}")

    # --- Zisti aktuálne SL/TP pre túto pozíciu ---
    r_pos = requests.get(
        BASE + "/positions",
        headers={"X-CAP-API-KEY": API_KEY, "CST": cst, "X-SECURITY-TOKEN": xsec},
    )
    positions = r_pos.json().get("positions", [])

    sl_actual = None
    tp_actual = None
    for p in positions:
        pos = p.get("position", {})
        if pos.get("dealReference") == deal_ref:
            sl_actual = pos.get("stopLevel")
            tp_actual = pos.get("profitLevel")
            break

    # --- Len ak ešte nie sú nastavené ---
    update_payload = {}
    if sl_actual is None and sl_json is not None:
        update_payload["stopLevel"] = sl_json
    if tp_actual is None and tp_json is not None:
        update_payload["profitLevel"] = tp_json

    if update_payload:
        r_update = requests.put(
            BASE + f"/positions/{deal_ref}",
            headers={"X-CAP-API-KEY": API_KEY, "CST": cst, "X-SECURITY-TOKEN": xsec,
                     "Content-Type": "application/json"},
            json=update_payload,
        )
        print(f"Updated SL/TP | Payload: {update_payload} | Status: {r_update.status_code}")
    else:
        print("SL/TP already set → skipping update")

    # --- VERIFIKÁCIA SL / TP (retry) ---
    print("\n--- Verifying SL & TP ---")
    verified = False

    for attempt in range(5):
        time.sleep(1.5)

        r_pos = requests.get(
            BASE + "/positions",
            headers={"X-CAP-API-KEY": API_KEY, "CST": cst, "X-SECURITY-TOKEN": xsec},
        )
        positions = r_pos.json().get("positions", [])

        for p in positions:
            pos = p.get("position", {})
            if pos.get("dealReference") == deal_ref:
                sl_check = pos.get("stopLevel")
                tp_check = pos.get("profitLevel")

                print(
                    f"Attempt {attempt+1} | "
                    f"SL actual: {sl_check} | TP actual: {tp_check}"
                )

                if ((sl_json is None or sl_check == sl_json) and
                    (tp_json is None or tp_check == tp_json)):
                    print("✅ SL & TP SET CORRECTLY\n")
                    verified = True
                else:
                    print("⏳ Waiting for propagation...\n")
                break

        if verified:
            break

    if not verified:
        print("⚠️ SL / TP NOT CONFIRMED AFTER RETRIES\n")

    count += 1
    if count >= 5:
        break

print("--- FINISHED ---")
