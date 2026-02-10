import json
from pathlib import Path

# --- Cesty ---
HISTORY_DIR = Path("history")

# --- Konštanty ---
LEVERAGE = 5
MAX_POSITIONS = 50
FIXED_BALANCE = 5000

# --- Výpočet cieľovej hodnoty na obchod ---
target_value_per_trade = (FIXED_BALANCE * LEVERAGE) / MAX_POSITIONS
print(f"Target value per trade: {target_value_per_trade:.2f} €")

# --- Kontrola adresára ---
if not HISTORY_DIR.exists() or not HISTORY_DIR.is_dir():
    raise FileNotFoundError(f"Directory not found: {HISTORY_DIR}")

# --- Spracovanie súborov ---
for json_file in HISTORY_DIR.iterdir():

    # iba JSON súbory priamo v history/
    if not json_file.is_file() or json_file.suffix.lower() != ".json":
        continue

    print(f"\nProcessing file: {json_file.name}")

    with open(json_file, "r", encoding="utf-8") as f:
        try:
            data = json.load(f)
        except json.JSONDecodeError:
            print("  ❌ Invalid JSON → skipping file")
            continue

    if not isinstance(data, list):
        print("  ❌ Not a list → skipping file")
        continue

    modified = False

    for item in data:
        if not isinstance(item, dict):
            continue

        # ak Normalize už existuje → nerišime
        if "Normalize" in item:
            continue

        price = item.get("price")

        # validácia ceny
        if price is None or not isinstance(price, (int, float)) or price <= 0:
            ticker = item.get("ticker", "UNKNOWN")
            print(f"  ⚠ {ticker} | Invalid price → skipped")
            continue

        normalize = round(target_value_per_trade / float(price), 1)
        item["Normalize"] = normalize
        modified = True

        ticker = item.get("ticker", "UNKNOWN")
        print(f"  ✔ {ticker} | price: {price:.2f} → Normalize: {normalize}")

    # --- Zápis späť len ak sa niečo zmenilo ---
    if modified:
        with open(json_file, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4)
        print("  💾 File updated")
    else:
        print("  ℹ No changes needed")

print("\n✅ Normalize completed for all history files")
