"""
step3_sentiment_collect.py
Jednoduchý zber sentimentu pre tickery, doplnenie do existujúceho JSON.
Nevyhodnocuje ani nefiltruje, len zbiera základné hodnoty.
Možnosť filtrovať tickery podľa news_sentiment_percent prahu.
"""

import json
from pathlib import Path
from typing import List
import requests
from xml.etree import ElementTree as ET
import time
import random

# ---------- SETTINGS ----------
INPUT_FILE = "data/step4_IndicatorsFilter.json"
OUTPUT_FILE = "data/step5_SentimentFilter.json"
MAX_ITEMS = 6
USER_AGENT = "Mozilla/5.0 (compatible; scraper/1.0; +https://example.com)"
NEWS_SENTIMENT_THRESHOLD = 80  # percent, filtrovanie podľa potreby

# Lexicon pre jednoduché bodovanie sentimentu
POS_WORDS = {"gain","up","rise","beat","positive","growth","profit","upgrade","buy","surge"}
NEG_WORDS = {"drop","down","fall","miss","negative","loss","downgrade","sell","crash","decline"}

def lexicon_score(text: str) -> float:
    txt = text.lower()
    pos = sum(1 for w in POS_WORDS if w in txt)
    neg = sum(1 for w in NEG_WORDS if w in txt)
    if pos + neg == 0:
        return 0.0
    return (pos - neg)/(pos + neg)

def normalize_percent(score: float) -> float:
    return round((score + 1) * 50, 1)  # -1..1 -> 0..100%

def fetch_google_news_headlines(ticker: str) -> List[str]:
    url = f"https://news.google.com/rss/search?q={requests.utils.requote_uri(ticker+' stock')}&hl=en-US&gl=US&ceid=US:en"
    headers = {"User-Agent": USER_AGENT}
    try:
        r = requests.get(url, headers=headers, timeout=10)
        r.raise_for_status()
        xml = ET.fromstring(r.content)
        return [i.find("title").text.strip() for i in xml.findall(".//item")[:MAX_ITEMS] if i.find("title") is not None]
    except:
        return []

def fetch_reddit_headlines(ticker: str) -> List[str]:
    url = f"https://www.reddit.com/search.rss?q={requests.utils.requote_uri(ticker+' stock')}&sort=new"
    headers = {"User-Agent": USER_AGENT}
    try:
        r = requests.get(url, headers=headers, timeout=10)
        r.raise_for_status()
        xml = ET.fromstring(r.content)
        return [i.find("title").text.strip() for i in xml.findall(".//item")[:MAX_ITEMS] if i.find("title") is not None]
    except:
        return []

# ---------- LOAD ----------
if not Path(INPUT_FILE).exists():
    print(f"⚠️ Input file missing: {INPUT_FILE}")
    exit(1)

with open(INPUT_FILE,"r",encoding="utf-8") as f:
    candidates = json.load(f)

# ---------- PROCESS ----------
tickers_with_sentiment = 0
tickers_no_sentiment = 0
filtered_candidates = []

for idx, item in enumerate(candidates,1):
    ticker = item.get("ticker")
    news_titles = fetch_google_news_headlines(ticker)
    social_titles = fetch_reddit_headlines(ticker)

    news_score = normalize_percent(sum(lexicon_score(t) for t in news_titles)/len(news_titles)) if news_titles else None
    social_score = normalize_percent(sum(lexicon_score(t) for t in social_titles)/len(social_titles)) if social_titles else None

    if news_titles or social_titles:
        tickers_with_sentiment += 1
    else:
        tickers_no_sentiment += 1

    # doplni do pôvodného záznamu len sentimenty
    item.update({
        "news_sentiment_percent": news_score,
        "social_sentiment_percent": social_score
    })

    # filtrovanie podľa news_sentiment_percent
    if news_score is not None and news_score >= NEWS_SENTIMENT_THRESHOLD:
        filtered_candidates.append(item)

    # vypis do konzoly aj s percentom
    news_score_str = f"{news_score}%" if news_score is not None else "N/A"
    print(f"[{idx}/{len(candidates)}] {ticker}: news:{len(news_titles)} social:{len(social_titles)}, News Sentiment %:{news_score_str}")

    time.sleep(random.uniform(0.5,0.8))  # mierne náhodná pauza

# ---------- SAVE ----------
Path("data").mkdir(exist_ok=True)
with open(OUTPUT_FILE,"w",encoding="utf-8") as f:
    json.dump(filtered_candidates,f,indent=2,ensure_ascii=False)

# ---------- STATISTIKA ----------
print("\n📊 Štatistika sentimentu:")
print(f"🟣 Celkom tickrov vo vstupnom file: {len(candidates)}")
print(f"✅ Tickery s aspoň jedným sentimentom: {tickers_with_sentiment}")
print(f"⚠️ Tickery bez sentimentu: {tickers_no_sentiment}")
print(f"🔹 Tickery nad prah {NEWS_SENTIMENT_THRESHOLD}% news_sentiment: {len(filtered_candidates)}")
