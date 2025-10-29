"""
step3_sentiment_noapi.py
Sentiment analýza bez API kľúčov, robustnejšia verzia.

Zdroje:
 - Google News RSS: https://news.google.com/rss/search?q=<TICKER>+stock
 - Reddit search RSS: https://www.reddit.com/search.rss?q=<TICKER>

Metodika:
 - Pokusí sa použiť Hugging Face model (cardiffnlp/twitter-roberta-base-sentiment).
 - Fallback na VADER alebo jednoduchý lexikón.
"""

import json
import time
from pathlib import Path
from datetime import date
from typing import List
import requests
from xml.etree import ElementTree as ET

# SETTINGS
INPUT_FILE = "data/step2_filtered.json"
OUTPUT_FILE = "data/step3_sentiment.json"
MAX_ITEMS = 6
USER_AGENT = "Mozilla/5.0 (compatible; scraper/1.0; +https://example.com)"

# Transformers
USE_TRANSFORMERS = False
nlp = None
TRANSFORMER_MODEL = "cardiffnlp/twitter-roberta-base-sentiment"

def try_init_transformers():
    global USE_TRANSFORMERS, nlp
    try:
        from transformers import pipeline, AutoTokenizer, AutoModelForSequenceClassification
        print("🔁 Initializing transformers pipeline...")
        tokenizer = AutoTokenizer.from_pretrained(TRANSFORMER_MODEL, use_fast=True)
        model = AutoModelForSequenceClassification.from_pretrained(TRANSFORMER_MODEL)
        nlp = pipeline("sentiment-analysis", model=model, tokenizer=tokenizer)
        USE_TRANSFORMERS = True
        print("✅ Transformers pipeline ready")
    except Exception as e:
        print(f"⚠️ Transformers init failed: {e}, fallback to VADER/lexicon")
        USE_TRANSFORMERS = False

# VADER fallback
USE_VADER = False
sia = None
def try_init_vader():
    global USE_VADER, sia
    try:
        import nltk
        nltk.download('vader_lexicon', quiet=True)
        from nltk.sentiment.vader import SentimentIntensityAnalyzer
        sia = SentimentIntensityAnalyzer()
        USE_VADER = True
        print("✅ VADER ready")
    except Exception as e:
        print(f"⚠️ VADER init failed: {e}")
        USE_VADER = False

# Lexicon fallback
POS_WORDS = {"gain","up","rise","beat","positive","growth","profit","upgrade","buy","surge"}
NEG_WORDS = {"drop","down","fall","miss","negative","loss","downgrade","sell","crash","decline"}

def lexicon_score(text: str) -> float:
    txt = text.lower()
    pos = sum(1 for w in POS_WORDS if w in txt)
    neg = sum(1 for w in NEG_WORDS if w in txt)
    if pos + neg == 0: return 0.0
    return (pos - neg)/(pos + neg)

# RSS helpers
def fetch_google_news_headlines(ticker: str) -> List[str]:
    url = f"https://news.google.com/rss/search?q={requests.utils.requote_uri(ticker+' stock')}&hl=en-US&gl=US&ceid=US:en"
    headers = {"User-Agent": USER_AGENT}
    try:
        r = requests.get(url, headers=headers, timeout=10)
        r.raise_for_status()
        xml = ET.fromstring(r.content)
        return [i.find("title").text.strip() for i in xml.findall(".//item")[:MAX_ITEMS] if i.find("title") is not None]
    except: return []

def fetch_reddit_headlines(ticker: str) -> List[str]:
    url = f"https://www.reddit.com/search.rss?q={requests.utils.requote_uri(ticker)}&sort=new"
    headers = {"User-Agent": USER_AGENT}
    try:
        r = requests.get(url, headers=headers, timeout=10)
        r.raise_for_status()
        xml = ET.fromstring(r.content)
        return [i.find("title").text.strip() for i in xml.findall(".//item")[:MAX_ITEMS] if i.find("title") is not None]
    except: return []

# Scoring helpers
def score_texts_transformer(texts: List[str]) -> float:
    if not texts or not USE_TRANSFORMERS: return 0.0
    try:
        results = nlp(texts)
        scores = []
        for r in results:
            lab = r.get("label","").upper()
            sc = r.get("score",0)
            if lab in ("NEGATIVE","LABEL_0"): scores.append(-sc)
            elif lab in ("NEUTRAL","LABEL_1"): scores.append(0)
            elif lab in ("POSITIVE","LABEL_2"): scores.append(sc)
            else: scores.append(0)
        return round(sum(scores)/len(scores),3) if scores else 0.0
    except: return 0.0

def score_texts_vader(texts: List[str]) -> float:
    if not texts or not USE_VADER: return 0.0
    scores = [sia.polarity_scores(t)["compound"] for t in texts]
    return round(sum(scores)/len(scores),3) if scores else 0.0

def score_texts_lexicon(texts: List[str]) -> float:
    scores = [lexicon_score(t) for t in texts]
    return round(sum(scores)/len(scores),3) if scores else 0.0

# ---------- MAIN PROCESS ----------
def process_tickers():
    try_init_transformers()
    if not USE_TRANSFORMERS:
        try_init_vader()

    if not Path(INPUT_FILE).exists():
        print(f"⚠️ Input file missing: {INPUT_FILE}")
        return

    with open(INPUT_FILE, "r", encoding="utf-8") as f:
        tickers = json.load(f)

    out = []
    tickers_with_sentiment = 0
    tickers_no_sentiment = 0

    for idx, item in enumerate(tickers,1):
        ticker = item.get("ticker")
        news_titles = [t for t in fetch_google_news_headlines(ticker) if t.strip()]
        reddit_titles = [t for t in fetch_reddit_headlines(ticker) if t.strip()]

        if not news_titles:
            tickers_no_sentiment += 1
            continue

        # scoring
        if USE_TRANSFORMERS and nlp: 
            news_score = score_texts_transformer(news_titles)
            social_score = score_texts_transformer(reddit_titles)
        elif USE_VADER and sia:
            news_score = score_texts_vader(news_titles)
            social_score = score_texts_vader(reddit_titles)
        else:
            news_score = score_texts_lexicon(news_titles)
            social_score = score_texts_lexicon(reddit_titles)

        combined = round(0.7*news_score + 0.3*social_score,3)

        # filtrovanie nulových alebo záporných kombinovaných sentimentov
        if combined <= 0:
            tickers_no_sentiment += 1
            continue

        tickers_with_sentiment += 1
        out_item = dict(item)
        out_item.update({
            "news_sentiment": news_score,
            "combined_sentiment": combined,
            "news_mentions": len(news_titles),
            "total_mentions": len(news_titles) + len(reddit_titles),
            "sentiment_date": str(date.today())
        })

        # zahrnúť social len ak je relevantný
        if social_score != 0 and reddit_titles:
            out_item.update({
                "social_sentiment": social_score,
                "social_mentions": len(reddit_titles)
            })

        out.append(out_item)

        # print in single line
        line = f"📡 [{idx}] Processing {ticker}: news:{len(news_titles)} score:{news_score}"
        if social_score != 0 and reddit_titles:
            line += f" | social:{len(reddit_titles)} score:{social_score}"
        line += f" -> combined:{combined}"
        print(line)

        time.sleep(0.7)

    # save
    Path("data").mkdir(exist_ok=True)
    with open(OUTPUT_FILE,"w",encoding="utf-8") as f:
        json.dump(out,f,indent=2,ensure_ascii=False)

    # stats
    print("\n📊 ŠTATISTIKA STEP 3 - SENTIMENT")
    print(f"🟣 Celkom tickrov: {len(tickers)}")
    print(f"✅ Tickery s pozitívnym sentimentom: {tickers_with_sentiment}")
    print(f"⚠️ Tickery s nulovým alebo záporným sentimentom: {tickers_no_sentiment}")
    print(f"💾 Výstup uložený do: {OUTPUT_FILE}")

if __name__ == "__main__":
    process_tickers()
