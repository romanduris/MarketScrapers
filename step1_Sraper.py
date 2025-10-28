"""Scraper Krok 1: dynamický zoznam kandidátov - Yahoo Finance"""
import json
from pathlib import Path
from datetime import date
import requests
from bs4 import BeautifulSoup

print("✅ Scraper Krok 1: Start")

# ---------- SETTINGS ----------
OUTPUT_FILE = "data/step1_candidates.json"
BASE_URL = "https://finance.yahoo.com"
SECTIONS = {
    "most_active": "/most-active",
    "gainers": "/gainers"
}
MAX_PER_SECTION = 50  # počet tickrov na sekciu

# ---------- SCRAPER ----------
def get_yahoo_table(url):
    """Načíta tickery z Yahoo Finance HTML tabuľky"""
    tickers = []
    try:
        resp = requests.get(url, headers={"User-Agent": "Mozilla/5.0"}, timeout=10)
        if resp.status_code != 200:
            print(f"⚠️ Nepodarilo sa načítať {url}: HTTP {resp.status_code}")
            return tickers
        soup = BeautifulSoup(resp.text, "html.parser")
        rows = soup.select("table tbody tr")
        for row in rows[:MAX_PER_SECTION]:
            cols = row.find_all("td")
            if len(cols) < 2:
                continue
            ticker = cols[0].text.strip()
            name = cols[1].text.strip()
            # percent change je vo 3. alebo 4. stlpci podľa sekcie
            percent_change = cols[2].text.strip().replace("%","")
            try:
                percent_change = float(percent_change)
            except:
                percent_change = 0.0
            tickers.append({
                "ticker": ticker,
                "name": name,
                "source": url,
                "percent_change": percent_change,
                "date": str(date.today())
            })
    except Exception as e:
        print(f"⚠️ Chyba pri scraping {url}: {e}")
    return tickers

def run_scraper():
    print("🚀 Zbierame kandidátov z Yahoo Finance...")
    all_data = []
    for sec, path in SECTIONS.items():
        url = BASE_URL + path
        print(f"📡 Zbieram {sec} tickery z {url}")
        tickers = get_yahoo_table(url)
        print(f"✅ Získaných {len(tickers)} tickrov z {sec}")
        all_data.extend(tickers)

    # deduplikácia podľa tickeru
    unique = {}
    for item in all_data:
        t = item["ticker"]
        if t not in unique:
            unique[t] = item
    all_data = list(unique.values())

    Path("data").mkdir(exist_ok=True)
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(all_data, f, indent=2, ensure_ascii=False)

    print(f"\n💾 Kandidáti uložený do: {OUTPUT_FILE} ({len(all_data)} unikátnych tickrov)")
    print("✅ Scraper Krok 1: Hotovo")
    return all_data

# ---------- MAIN ----------
if __name__ == "__main__":
    run_scraper()
