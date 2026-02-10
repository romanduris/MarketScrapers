import json
from pathlib import Path
from datetime import datetime

INPUT_FILE = Path("data/step9_Normalize.json")
ARCHIVE_DIR = Path("history")

def archive_sltp():
    # Kontrola existencie vstupného súboru
    if not INPUT_FILE.exists():
        print(f"❌ Súbor {INPUT_FILE} neexistuje.")
        return

    # Načítaj aktuálne dáta
    with open(INPUT_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)

    # Priprav archívny priečinok
    ARCHIVE_DIR.mkdir(exist_ok=True)

    # Vytvor názov súboru s dátumom aj časom
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    archive_file = ARCHIVE_DIR / f"{timestamp}.json"

    # Ulož archív
    with open(archive_file, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

    print(f"📦 Archivácia hotová → {archive_file}")

if __name__ == "__main__":
    archive_sltp()
