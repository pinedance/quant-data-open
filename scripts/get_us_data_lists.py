# -*- coding: utf-8 -*-
import json
import sys
from pathlib import Path

import yfinance as yf

# Add root directory to python path to load core modules
BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.append(str(BASE_DIR))

from core.cons import config_gsheet_tickers_req_yh as config_tickers_req
from core.tIO import fetch_tickers


def main():
    print("Fetching US tickers from Google Sheet...")
    tickers_req_url = "https://docs.google.com/spreadsheets/d/{sheet_id}/gviz/tq?tqx=out:csv&sheet={sheet_name}".format(**config_tickers_req)
    tickers = fetch_tickers(tickers_req_url)
    print(f"Found {len(tickers)} tickers. Resolving names via yfinance...")

    stock_list = []
    # Fetch in small groups to be safe, or print progress
    for idx, ticker in enumerate(tickers, 1):
        print(f"[{idx}/{len(tickers)}] Fetching info for {ticker}...")
        try:
            t_obj = yf.Ticker(ticker)
            info = t_obj.info
            name = info.get("longName") or info.get("shortName") or ticker
            stock_list.append({"cd": ticker, "nm": name, "gb": "US"})
        except Exception as e:
            print(f"⚠️ Error fetching {ticker}: {e}")
            stock_list.append({"cd": ticker, "nm": ticker, "gb": "US"})

    output_dir = BASE_DIR / "output/US/data"
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / "stocklist.json"
    
    output_data = {"Co": stock_list}
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(output_data, f, ensure_ascii=False, indent=2)
    print(f"✓ US stocklist saved to {output_path}")

if __name__ == "__main__":
    main()
