"""
step3_sentiment_noapi.py
Sentiment bez potreby registrovania / API kľúčov.

Zdroje:
 - Google News RSS: https://news.google.com/rss/search?q=<TICKER>+stock
 - Reddit search RSS: https://www.reddit.com/search.rss?q=<TICKER>

Metodika:
 - Pokusí sa použiť Hugging Face model (cardiffnlp/twitter-roberta-base-sentiment).
 - Ak transformers nie sú dostupné, fallback na VADER (nltk).
 - Ak ani VADER nie je dostupný, fallback na jednoduchý lexikón (+/- words).
"""
import json
import time
from pathlib import Path
from datetime import date
from typing import List, Dict
import requests
from xml.etree import ElementTree as ET

# SETTINGS
INPUT_FILE = "data/step2_filtered.json"
OUTPUT_FILE = "data/step3_sentiment.json"
MAX_ITEMS = 6           # počet headlineov z každého zdroja na ticker
USER_AGENT = "Mozilla/5.0 (compatible; scraper/1.0; +https://example.com)"

# Try to import transformers; if missing, we'll try to install it at runtime.
USE_TRANSFORMERS = False
TRANSFORMER_MODEL = "cardiffnlp/twitter-roberta-base-sentiment"  # finančný twitter model (good general)
nlp = None

def try_init_transformers():
    global USE_TRANSFORMERS, nlp
    try:
        from transformers import pipeline, AutoTokenizer, AutoModelForSequenceClassification
        # initialize pipeline
        print("🔁 Initializing transformers pipeline...")
        tokenizer = AutoTokenizer.from_pretrained(TRANSFORMER_MODEL, use_fast=True)
        model = AutoModelForSequenceClassification.from_pretrained(TRANSFORMER_MODEL)
        nlp = pipeline("sentiment-analysis", model=model, tokenizer=tokenizer)
        USE_TRANSFORMERS = True
        print("✅ transformers pipeline ready")
    except Exception as e:
        print(f"⚠️ transformers init failed: {e}. Will fallback to VADER/lexicon.")
        USE_TRANSFORMERS = False

# Try VADER as secondary fallback
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
        print(f"⚠️ VADER init failed: {e}. Will fallback to simple lexicon.")
        USE_VADER = False

# simple lexicon fallback
POS_WORDS = {"gain", "up", "rise", "beat", "positive", "growth", "profit", "upgrade", "buy", "surge"}
NEG_WORDS = {"drop", "down", "fall", "miss", "negative", "loss", "downgrade", "sell", "crash", "decline"}

def lexicon_score(text: str) -> float:
    txt = text.lower()
    pos = sum(1 for w in POS_WORDS if w in txt)
    neg = sum(1 for w in NEG_WORDS if w in txt)
    if pos + neg == 0:
        return 0.0
    return (pos - neg) / (pos + neg)  # in [-1,1]

# RSS helpers
def fetch_google_news_headlines(ticker: str, max_items: int = MAX_ITEMS) -> List[str]:
    # Google News RSS search — include 'stock' to bias results
    q = f"{ticker} stock"
    url = f"https://news.google.com/rss/search?q={requests.utils.requote_uri(q)}&hl=en-US&gl=US&ceid=US:en"
    headers = {"User-Agent": USER_AGENT}
    try:
        r = requests.get(url, headers=headers, timeout=10)
        r.raise_for_status()
        xml = ET.fromstring(r.content)
        items = xml.findall(".//item")
        titles = []
        for it in items[:max_items]:
            t = it.find("title")
            if t is not None and t.text:
                titles.append(t.text.strip())
        return titles
    except Exception as e:
        print(f"⚠️ Google News RSS failed for {ticker}: {e}")
        return []

def fetch_reddit_headlines(ticker: str, max_items: int = MAX_ITEMS) -> List[str]:
    # Reddit search RSS
    q = f"{ticker}"
    url = f"https://www.reddit.com/search.rss?q={requests.utils.requote_uri(q)}&sort=new"
    headers = {"User-Agent": USER_AGENT}
    try:
        r = requests.get(url, headers=headers, timeout=10)
        r.raise_for_status()
        xml = ET.fromstring(r.content)
        items = xml.findall(".//item")
        titles = []
        for it in items[:max_items]:
            t = it.find("title")
            if t is not None and t.text:
                titles.append(t.text.strip())
        return titles
    except Exception as e:
        # Reddit often blocks if no User-Agent; above we set one, but still might block
        # fallback: return empty and don't crash
        # print(f"⚠️ Reddit RSS failed for {ticker}: {e}")
        return []

# scoring helpers
def score_texts_with_transformer(texts: List[str]) -> float:
    if not texts:
        return 0.0
    try:
        results = nlp(texts)  # returns list of dicts with 'label' and 'score'
        # cardiffnlp labels are usually 'LABEL_0'.. - map roughly: LABEL_0 negative, LABEL_2 positive
        # We'll map by checking label strings or rely on label names if present.
        label_map = {}
        # Normalize results: some pipelines return 'NEGATIVE'/'POSITIVE' etc.
        scores = []
        for r in results:
            lab = r.get("label", "")
            sc = r.get("score", 0.0)
            # heuristics for known label sets:
            if lab.upper() in ("NEGATIVE", "LABEL_0"):
                scores.append(-sc)
            elif lab.upper() in ("NEUTRAL", "LABEL_1"):
                scores.append(0.0)
            elif lab.upper() in ("POSITIVE", "LABEL_2"):
                scores.append(sc)
            else:
                # unknown label: skip or use score with sign heuristics
                scores.append(0.0)
        if not scores:
            return 0.0
        avg = sum(scores) / len(scores)
        return float(round(avg, 3))
    except Exception as e:
        print(f"⚠️ Transformer scoring failed: {e}")
        return 0.0

def score_texts_with_vader(texts: List[str]) -> float:
    if not texts:
        return 0.0
    scores = []
    for t in texts:
        s = sia.polarity_scores(t)["compound"]
        scores.append(s)
    return float(round(sum(scores) / len(scores), 3))

def score_texts_lexicon(texts: List[str]) -> float:
    if not texts:
        return 0.0
    scores = [lexicon_score(t) for t in texts]
    return float(round(sum(scores) / len(scores), 3))

# Main processing
def process_tickers():
    # initialize best available analyzer
    try_init_transformers()
    if not USE_TRANSFORMERS:
        try_init_vader()

    if not Path(INPUT_FILE).exists():
        print(f"⚠️ Input file missing: {INPUT_FILE}. Run step2 first.")
        return

    with open(INPUT_FILE, "r", encoding="utf-8") as f:
        tickers = json.load(f)

    out = []
    idx = 0
    for item in tickers:
        idx += 1
        ticker = item.get("ticker")
        print(f"\n📡 [{idx}] Processing {ticker} ...")

        # fetch headlines
        news_titles = fetch_google_news_headlines(ticker, MAX_ITEMS)
        reddit_titles = fetch_reddit_headlines(ticker, MAX_ITEMS)

        # combine sources (we'll keep them separate for metrics)
        all_titles = news_titles + reddit_titles

        # compute scores using best available method
        if USE_TRANSFORMERS and nlp is not None:
            news_score = score_texts_with_transformer(news_titles)
            social_score = score_texts_with_transformer(reddit_titles)
        elif USE_VADER and sia is not None:
            news_score = score_texts_with_vader(news_titles)
            social_score = score_texts_with_vader(reddit_titles)
        else:
            news_score = score_texts_lexicon(news_titles)
            social_score = score_texts_lexicon(reddit_titles)

        # combined (weights: news 0.7, social 0.3)
        combined = round(0.7 * news_score + 0.3 * social_score, 3)

        # mentions counts
        mentions = len(all_titles)
        social_mentions = len(reddit_titles)
        news_mentions = len(news_titles)

        # attach
        out_item = dict(item)  # copy original fields
        out_item.update({
            "news_sentiment": news_score,
            "social_sentiment": social_score,
            "combined_sentiment": combined,
            "news_mentions": news_mentions,
            "social_mentions": social_mentions,
            "total_mentions": mentions,
            "sentiment_date": str(date.today())
        })
        out.append(out_item)

        print(f"   news:{news_mentions} (score={news_score}) | social:{social_mentions} (score={social_score}) -> combined={combined}")
        # polite pause
        time.sleep(0.8)

    # save
    Path("data").mkdir(exist_ok=True)
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(out, f, indent=2, ensure_ascii=False)

    print(f"\n💾 Saved sentiment results to {OUTPUT_FILE} ({len(out)} tickers)")

if __name__ == "__main__":
    process_tickers()
