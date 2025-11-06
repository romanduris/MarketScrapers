"""
STEP 6 – AI Analyze (rozdelené na dva kroky)
- Vstup: step5_SentimentFilter.json
- Krok 1: AI doplní "AIComment" pre každú akciu
- Krok 2: AI doplní "AIScore" pre každú akciu
- Výstup uložený do data/step6_AIAnalyze.json
"""

import json
from pathlib import Path
import openai
import os
import re

# ---------- SETTINGS ----------
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
AI_MODEL = "gpt-4-turbo"
openai.api_key = OPENAI_API_KEY

INPUT_FILE = "data/step6_TopX.json"
OUTPUT_FILE = "data/step7_AIAnalyze.json"

# ---------- FUNKCIE ----------
def parse_ai_json(ai_text):
    """Skúsi parsovať JSON z textu, ak model pridá extra text."""
    try:
        return json.loads(ai_text)
    except json.JSONDecodeError:
        match = re.search(r'(\[.*\])', ai_text, re.DOTALL)
        if match:
            try:
                return json.loads(match.group(1))
            except:
                return []
        return []

def add_ai_comment(stocks):
    """Pošle zoznam akcií do OpenAI a vráti ich s doplneným AIComment."""
    prompt = f"""
Máme zoznam akcií s ich údajmi vo formáte JSON:
{json.dumps(stocks, indent=2)}

Úloha:
1. Pre každú akciu doplniť nové pole "AIComment" s krátkym odôvodnením (2-3 vety), prečo je na danom mieste.
2. Zachovať všetky pôvodné polia.
3. Vráť **len platný JSON** – pole objektov, žiadny text pred alebo za JSON.
Pri analyze ignoruj polia FundamentalFilterRating, TechFilterRating, OverallRating
"""
    try:
        response = openai.chat.completions.create(
            model=AI_MODEL,
            messages=[
                {"role": "system", "content": "Si skúsený finančný analytik a tvoríš JSON výstupy."},
                {"role": "user", "content": prompt}
            ],
            temperature=0,
            max_tokens=4000
        )
        ai_text = response.choices[0].message.content.strip()
        return parse_ai_json(ai_text)
    except Exception as e:
        print(f"⚠️ Chyba pri generovaní AIComment: {e}")
        return []

def add_ai_score(stocks):
    """Pošle zoznam akcií do OpenAI a vráti ich s doplneným AIScore (0–100)."""
    prompt = f"""
Máme zoznam akcií s ich údajmi vo formáte JSON (už obsahujú AIComment):
{json.dumps(stocks, indent=2)}

Úloha:
1. Pre každú akciu doplniť nové pole "AIScore" (0–100), kde 100 = top kúpa, 0 = veľmi nevhodná.
2. Zohľadni všetky dostupné údaje (fundamentálne, technické, sentiment).
3. Zachovať všetky pôvodné polia vrátane AIComment.
4. Vráť **len platný JSON** – pole objektov.
Pri analyze ignoruj polia FundamentalFilterRating, TechFilterRating, OverallRating
"""
    try:
        response = openai.chat.completions.create(
            model=AI_MODEL,
            messages=[
                {"role": "system", "content": "Si skúsený finančný analytik a tvoríš JSON výstupy."},
                {"role": "user", "content": prompt}
            ],
            temperature=0,
            max_tokens=4000
        )
        ai_text = response.choices[0].message.content.strip()
        return parse_ai_json(ai_text)
    except Exception as e:
        print(f"⚠️ Chyba pri generovaní AIScore: {e}")
        return []

# ---------- HLAVNÁ ČASŤ ----------
if not Path(INPUT_FILE).exists():
    print(f"⚠️ Vstupný súbor {INPUT_FILE} neexistuje.")
    exit(1)

with open(INPUT_FILE, "r", encoding="utf-8") as f:
    stocks = json.load(f)

print(f"📡 Krok 1: Posielam {len(stocks)} akcií do AI na doplnenie AIComment...")
stocks_with_comment = add_ai_comment(stocks)

if not stocks_with_comment:
    print("⚠️ AI nevrátila žiadny výsledok pri AIComment.")
    exit(1)

print(f"📡 Krok 2: Posielam {len(stocks_with_comment)} akcií do AI na doplnenie AIScore...")
stocks_with_score = add_ai_score(stocks_with_comment)

if not stocks_with_score:
    print("⚠️ AI nevrátila žiadny výsledok pri AIScore.")
    exit(1)

# ---------- ZORADENIE PODĽA AISCORE ----------
stocks_sorted = sorted(
    stocks_with_score,
    key=lambda x: x.get("AIScore", 0),
    reverse=True  # od najlepšieho po najslabšie
)

# ---------- ULOŽENIE VÝSLEDKU ----------
Path("data").mkdir(exist_ok=True)
with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
    json.dump(stocks_sorted, f, indent=2, ensure_ascii=False)

print(f"💾 Výstup uložený do {OUTPUT_FILE} ({len(stocks_sorted)} akcií).")

