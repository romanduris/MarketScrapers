import json
from pathlib import Path

# --- Cesta k vstupnému JSON ---
DATA_FILE = Path(r"data/step8_SLTP.json")
OUTPUT_FILE = Path(r"data/step9_Normalize.json")

# --- Parametre ---
LEVERAGE = 5  # páka 1:5
MAX_POSITIONS = 50  # maximálny počet obchodov
FIXED_BALANCE = 5000  # demo účet fixný balance

# --- Načítanie JSON súboru ---
with open(DATA_FILE, "r") as f:
    data = json.load(f)

# --- Použitie fixného demo balansu ---
available_balance = FIXED_BALANCE
print(f"Using fixed demo balance: {available_balance} €")

# --- Max hodnota jednej pozície pri plnom využití účtu ---
target_value_per_trade = (available_balance * LEVERAGE) / MAX_POSITIONS
print(f"Target value per trade (maximálna hodnota jednej akcie): {target_value_per_trade} €")

# --- Výpočet normalizačného faktora pre každú akciu ---
for item in data:
    ticker = item["ticker"]
    offer_price = float(item.get("price", 0))  # použijeme cenu z JSON

    if offer_price <= 0:
        print(f"{ticker} | Price invalid → skipping")
        continue

    normalize_factor = target_value_per_trade / offer_price
    normalize_factor = round(normalize_factor, 1)  # zaokrúhlenie na jednu desatinu
    normalized_price = offer_price * normalize_factor

    # Pridanie do JSON objektu
    item["Normalize"] = normalize_factor

    print(f"Ticker: {ticker} | Offer Price: {offer_price} € | Normalize Factor: {normalize_factor:.1f} | Normalized Price: {normalized_price:.2f} €")

# --- Uloženie do nového JSON súboru ---
with open(OUTPUT_FILE, "w") as f:
    json.dump(data, f, indent=4)

print(f"Normalized data saved to {OUTPUT_FILE}")
