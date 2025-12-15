import os
import requests
import time

# --- Demo API Capital.com ---
BASE = "https://demo-api-capital.backend-capital.com/api/v1"
IDENTIFIER = os.getenv("CAPITAL_IDENTIFIER")
API_KEY = os.getenv("CAPITAL_API_KEY")
API_KEY_PASSWORD = os.getenv("CAPITAL_API_PASSWORD")

# --- Prihlásenie na API ---
r = requests.post(
    BASE + "/session",
    headers={"X-CAP-API-KEY": API_KEY, "Content-Type": "application/json"},
    json={"identifier": IDENTIFIER, "password": API_KEY_PASSWORD, "encryptedPassword": False}
)
cst = r.headers["CST"]
xsec = r.headers["X-SECURITY-TOKEN"]

print("\n--- DEBUG SCRIPT: MCD MARKET BUY + TP 5% s retry GET ---\n")

# --- Hardcodované údaje ---
ticker = "MCD"
sl = 307.22
size = 1
direction = "BUY"
tp_pct = 0.05  # +5%
json_price = 316.72

# --- Získanie market data ---
r_markets = requests.get(
    BASE + "/markets",
    headers={"X-CAP-API-KEY": API_KEY, "CST": cst, "X-SECURITY-TOKEN": xsec}
)
markets = r_markets.json().get("markets", [])

market = next((m for m in markets if m.get("symbol") == ticker and m.get("instrumentType") == "SHARES"), None)
if market is None:
    raise ValueError("Nepodarilo sa nájsť MCD v demo účte")

epic = market["epic"]
instrument_name = market["instrumentName"]
status = market.get("marketStatus")
offer_price = market.get("offer")
rules = market.get("dealingRules", {})
min_dist = rules.get("minStopOrLimitDistance", {}).get("value")

print(f"Ticker: {ticker}")
print(f"EPIC: {epic}")
print(f"Instrument Name: {instrument_name}")
print(f"Market Status: {status}")
print(f"Offer Price: {offer_price}")
print(f"SL from JSON: {sl}")
print(f"dealingRules.minStopOrLimitDistance: {min_dist}")

if offer_price is None:
    raise ValueError("Offer price je None, nemôžeme pokračovať")

# --- Fallback minStopOrLimitDistance ---
if min_dist is None:
    min_dist = offer_price * 0.01
    print(f"Používam fallback minStopOrLimitDistance = {min_dist:.2f}")

# --- Adjust SL ---
sl_adj = sl
if (offer_price - sl) < min_dist:
    sl_adj = offer_price - min_dist
    print(f"SL bolo príliš blízko → upravené na {sl_adj:.2f}")
else:
    print(f"Adjusted SL: {sl_adj:.2f}")

# --- TP na +5% ---
tp_adj = offer_price * (1 + tp_pct)
tp_diff = tp_adj - offer_price
if tp_diff < min_dist:
    tp_adj = offer_price + min_dist
print(f"Adjusted TP (+5%): {tp_adj:.2f}")

# --- Payload pre MARKET BUY ---
payload = {
    "epic": epic,
    "direction": direction,
    "size": size,
    "orderType": "MARKET",
    "stopLevel": sl_adj,
    "limitLevel": tp_adj,
}
print("\nPayload for POST /positions:")
print(payload)

# --- Otvorenie pozície ---
r_order = requests.post(
    BASE + "/positions",
    headers={"X-CAP-API-KEY": API_KEY, "CST": cst, "X-SECURITY-TOKEN": xsec},
    json=payload,
)
print("\nPOST response:", r_order.status_code, r_order.text)

if r_order.status_code != 200:
    raise RuntimeError("Otvorenie pozície zlyhalo")

deal_ref = r_order.json().get("dealReference")
print("Deal Reference:", deal_ref)

# --- Loop retry GET /positions/open 10x po 10 s ---
position = None
for attempt in range(1, 11):
    print(f"\nAttempt {attempt}/10: Čakám 10 s pred GET open positions...")
    time.sleep(10)
    
    r_open = requests.get(
        BASE + "/positions/open",
        headers={"X-CAP-API-KEY": API_KEY, "CST": cst, "X-SECURITY-TOKEN": xsec},
    )
    open_positions = r_open.json().get("positions", [])
    print(f"Open positions fetched: {len(open_positions)}")

    # --- Nájdenie pozície podľa dealReference ---
    position = next((p for p in open_positions if p.get("dealReference") == deal_ref), None)
    
    if position:
        print("Pozícia nájdená v open positions!")
        current_sl = position.get("stopLevel")
        current_tp = position.get("limitLevel")
        print(f"Current SL: {current_sl}, Current TP: {current_tp}")
        
        # --- Nastavenie TP ak sa nenasetovalo ---
        if current_tp != tp_adj:
            print(f"TP nie je nastavené správne → nastavujem dodatočne na {tp_adj}")
            update_payload = {"limitLevel": tp_adj}
            deal_id = position.get("dealId")
            r_update = requests.put(
                BASE + f"/positions/{deal_id}/limit",
                headers={"X-CAP-API-KEY": API_KEY, "CST": cst, "X-SECURITY-TOKEN": xsec},
                json=update_payload,
            )
            print("PUT TP response:", r_update.status_code, r_update.text)
        else:
            print("TP je nastavené správne")
        
        # --- Kontrola SL ---
        if current_sl != sl_adj:
            print(f"SL nie je nastavené správne → nastavujem dodatočne na {sl_adj}")
            update_payload_sl = {"stopLevel": sl_adj}
            deal_id = position.get("dealId")
            r_update_sl = requests.put(
                BASE + f"/positions/{deal_id}/stop",
                headers={"X-CAP-API-KEY": API_KEY, "CST": cst, "X-SECURITY-TOKEN": xsec},
                json=update_payload_sl,
            )
            print("PUT SL response:", r_update_sl.status_code, r_update_sl.text)
        else:
            print("SL je nastavené správne")
        
        break
    else:
        print("Pozícia stále nenájdená, skúšame znova...")

if not position:
    print("\nPozícia sa po 10 pokusoch stále nenašla v open positions (demo API oneskorenie).")
