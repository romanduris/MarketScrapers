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

# Získanie tickers zo súboru
tickers_to_check = [item["ticker"] for item in data]

# --- Prihlásenie na API ---
r = requests.post(
    BASE + "/session",
    headers={"X-CAP-API-KEY": API_KEY, "Content-Type": "application/json"},
    json={
        "identifier": IDENTIFIER,
        "password": API_KEY_PASSWORD,
        "encryptedPassword": False
    }
)

cst = r.headers["CST"]
xsec = r.headers["X-SECURITY-TOKEN"]

# --- Výpis detailov účtu ---
r_acc = requests.get(
    BASE + "/accounts",
    headers={
        "X-CAP-API-KEY": API_KEY,
        "CST": cst,
        "X-SECURITY-TOKEN": xsec
    }
)

accounts = r_acc.json().get("accounts", [])
print("\n--- Account Information ---")
for acc in accounts:
    print(f"Account ID: {acc.get('accountId')}")
    print(f"Account Type: {acc.get('accountType')}")
    print(f"Currency: {acc.get('currency')}")
    print(f"Balance: {acc.get('balance')}")
    print("---")

print("\n--- Checking tickers ---\n")

# --- Načítanie všetkých markets ---
r = requests.get(
    BASE + "/markets",
    headers={
        "X-CAP-API-KEY": API_KEY,
        "CST": cst,
        "X-SECURITY-TOKEN": xsec
    }
)

markets = r.json().get("markets", [])

# --- Výpis EPIC pre tickery zo súboru ---
print("Ticker | Name | EPIC | Status | Offer Price")
for ticker in tickers_to_check:
    found = False
    for m in markets:
        if m.get("instrumentType") == "SHARES" and m.get("symbol") == ticker:
            print(
                f"{ticker} | "
                f"{m.get('instrumentName')} | "
                f"{m.get('epic')} | "
                f"{m.get('marketStatus')} | "
                f"{m.get('offer')}"
            )
            found = True
            break
    if not found:
        print(f"{ticker} | NOT FOUND in demo account SHARES")

# ==========================================================
# === TEST: NASTAVENIE A OVERENIE SL + TP (VŠETKY POZÍCIE) ===
# ==========================================================

print("\n--- Setting & Verifying SL and TP for ALL open positions ---\n")

# 1️⃣ Načítanie otvorených pozícií
r_pos = requests.get(
    BASE + "/positions",
    headers={
        "X-CAP-API-KEY": API_KEY,
        "CST": cst,
        "X-SECURITY-TOKEN": xsec
    }
)

positions = r_pos.json().get("positions", [])

if not positions:
    print("No open positions found.")
    exit()

results = []

# 2️⃣ Prejdi všetky pozície
for p in positions:
    pos = p["position"]
    market = p.get("market", {})

    deal_id = pos["dealId"]
    epic = market.get("epic", "UNKNOWN")
    direction = pos["direction"]
    entry_price = float(pos["level"])
    sl_existing = pos.get("stopLevel")

    # --- Výpočet TP (+10 %) a SL (−5 %)
    if direction == "BUY":
        profit_level = round(entry_price * 1.10, 2)
        stop_level = round(entry_price * 0.95, 2)
    elif direction == "SELL":
        profit_level = round(entry_price * 0.90, 2)
        stop_level = round(entry_price * 1.05, 2)
    else:
        print(f"{epic} | Unsupported direction → skipping")
        continue

    expected_sl = sl_existing if sl_existing is not None else stop_level

    print(
        f"Updating position | {epic} | "
        f"DealID: {deal_id} | "
        f"Entry: {entry_price} | "
        f"SL: {expected_sl} | "
        f"TP(profitLevel): {profit_level}"
    )

    # --- Payload: TP vždy, SL len ak chýba
    update_payload = {
        "profitLevel": profit_level
    }

    if sl_existing is None:
        update_payload["stopLevel"] = stop_level

    r_update = requests.put(
        BASE + f"/positions/{deal_id}",
        headers={
            "X-CAP-API-KEY": API_KEY,
            "CST": cst,
            "X-SECURITY-TOKEN": xsec,
            "Content-Type": "application/json"
        },
        json=update_payload
    )

    print("Update response:", r_update.status_code)

    results.append({
        "dealId": deal_id,
        "epic": epic,
        "expectedSL": expected_sl,
        "expectedTP": profit_level
    })

# 4️⃣ Overenie – retry
print("\n--- Verifying SL & TP (with retry) ---\n")

verified_map = {r["dealId"]: False for r in results}

for attempt in range(5):
    time.sleep(1.5)

    r_verify = requests.get(
        BASE + "/positions",
        headers={
            "X-CAP-API-KEY": API_KEY,
            "CST": cst,
            "X-SECURITY-TOKEN": xsec
        }
    )

    verify_positions = r_verify.json().get("positions", [])

    for vp in verify_positions:
        vpos = vp["position"]
        deal_id = vpos["dealId"]

        if deal_id not in verified_map:
            continue

        actual_sl = vpos.get("stopLevel")
        actual_tp = vpos.get("profitLevel")

        expected = next(r for r in results if r["dealId"] == deal_id)

        if actual_sl == expected["expectedSL"] and actual_tp == expected["expectedTP"]:
            if not verified_map[deal_id]:
                print(
                    f"✅ SL & TP OK | {expected['epic']} | "
                    f"SL: {actual_sl} | TP: {actual_tp}"
                )
            verified_map[deal_id] = True
        else:
            print(
                f"⏳ Waiting | {expected['epic']} | "
                f"SL actual: {actual_sl} | "
                f"TP actual: {actual_tp}"
            )

    if all(verified_map.values()):
        break

# 5️⃣ Zhrnutie
print("\n--- SUMMARY ---")
for r in results:
    status = "OK" if verified_map[r["dealId"]] else "FAILED"
    print(f"{status} | {r['epic']} | DealID: {r['dealId']}")
