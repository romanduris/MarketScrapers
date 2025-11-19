import json
import yfinance as yf
import os
import datetime
import time

# ---------- CONFIG ----------
INPUT_FILE = r"data/step5_SentimentFilter.json"
OUTPUT_FILE = r"data/step6_MarketInfo.json"
MARKET_INDEX = "^GSPC"   # S&P 500

# Mapovanie sektorov na ETF tickre
SECTOR_ETF = {
    "Technology": "XLK",
    "Healthcare": "XLV",
    "Financial Services": "XLF",
    "Financial": "XLF",
    "Energy": "XLE",
    "Industrials": "XLI",
    "Utilities": "XLU",
    "Real Estate": "XLRE",
    "Consumer Defensive": "XLP",
    "Consumer Staples": "XLP",
    "Consumer Cyclical": "XLY",
    "Basic Materials": "XLB",
    "Materials": "XLB",
    "Communication Services": "XLC"
}


def calculate_trend(change):
    if change is None:
        return None
    if change > 1.0:
        return "up"
    elif change < -1.0:
        return "down"
    return "neutral"


def get_multi_trend(ticker):
    data = yf.Ticker(ticker)
    hist = data.history(period="30d")

    if len(hist) < 21:
        return None, None, None

    close = hist["Close"]

    change_1d = ((close.iloc[-1] / close.iloc[-2]) - 1) * 100
    change_5d = ((close.iloc[-1] / close.iloc[-6]) - 1) * 100
    change_20d = ((close.iloc[-1] / close.iloc[-21]) - 1) * 100

    return change_1d, change_5d, change_20d


def get_sector(ticker):
    info = yf.Ticker(ticker).info
    return info.get("sector")


def main():
    start_time = time.time()

    with open(INPUT_FILE, "r", encoding="utf-8") as f:
        stocks = json.load(f)

    total = len(stocks)
    sector_ok = 0
    sector_trend_ok = 0

    # Market trend values
    market_1d, market_5d, market_20d = get_multi_trend(MARKET_INDEX)
    market_final = calculate_trend(market_5d)

    updated = []

    for stock in stocks:
        ticker = stock["ticker"]

        # ------ SECTOR ------
        sector = get_sector(ticker)
        stock["sector"] = sector

        if sector:
            sector_ok += 1

        # ------ SECTOR TREND ------
        if sector in SECTOR_ETF:
            etf = SECTOR_ETF[sector]
            sec_1d, sec_5d, sec_20d = get_multi_trend(etf)
            sector_final = calculate_trend(sec_5d)

            stock["sector_name"] = etf  # <––– ADDED

            if sec_5d is not None:
                sector_trend_ok += 1
        else:
            stock["sector_name"] = None  # <––– ADDED
            sec_1d = sec_5d = sec_20d = None
            sector_final = None

        # update market info
        stock["market_change_1d"] = market_1d
        stock["market_change_5d"] = market_5d
        stock["market_change_20d"] = market_20d
        stock["market_trend"] = market_final

        # update sector info
        stock["sector_change_1d"] = sec_1d
        stock["sector_change_5d"] = sec_5d
        stock["sector_change_20d"] = sec_20d
        stock["sector_trend"] = sector_final

        updated.append(stock)

    # Save output file
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(updated, f, indent=2, ensure_ascii=False)

    end_time = time.time()
    elapsed = round(end_time - start_time, 2)

    # -------- SUMMARY --------
    print("\n========== SUMMARY REPORT ==========")
    print(f"Input file:  {INPUT_FILE}")
    print(f"Output file: {OUTPUT_FILE}")
    print("------------------------------------")
    print(f"Total stocks analyzed:        {total}")
    print(f"Sectors successfully found:   {sector_ok} / {total}")
    print(f"Sectors with trend computed:  {sector_trend_ok} / {total}")
    print(f"Market trend computed:        YES")
    print("------------------------------------")
    print(f"Processing time: {elapsed} seconds")
    print("====================================\n")


if __name__ == "__main__":
    main()
