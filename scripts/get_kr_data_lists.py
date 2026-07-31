# -*- coding: utf-8 -*-
import io
import json
import sys
from pathlib import Path

import pandas as pd
import requests

# Add root directory to python path to load core modules
BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.append(str(BASE_DIR))

# ==============================================================================
# Constants (Data Reference URLs & Configuration)
# ==============================================================================
NAVER_STOCK_API_URL = (
    "https://stock.naver.com/api/domestic/market/stock/default?marketType=ALL&pageSize=4000"
)
KRX_KIND_URL = (
    "https://kind.krx.co.kr/corpgeneral/corpList.do?method=download&searchType=13"
)
NAVER_ETF_API_URL = "https://finance.naver.com/api/sise/etfItemList.nhn"


def format_ticker_code(raw_code):
    """Format ticker code with 'A' prefix to prevent number/string ambiguity (e.g. 238540 -> A238540)."""
    code_str = str(raw_code).strip()
    if code_str.startswith("A"):
        return code_str
    try:
        return f"A{int(code_str):06d}"
    except (ValueError, TypeError):
        return f"A{code_str}"


def fetch_all_kr_stock_lists():
    stock_list = []
    seen = set()
    headers = {"User-Agent": "Mozilla/5.0"}

    # 1. Naver Stock API (KOSPI, KOSDAQ, KONEX)
    try:
        res_naver = requests.get(NAVER_STOCK_API_URL, headers=headers, timeout=10)
        data_naver = res_naver.json()
        sosok_map = {"0": "유가", "1": "코스닥", "2": "코넥스"}
        added_naver = 0
        for item in data_naver:
            cd = format_ticker_code(item["itemcode"])
            nm = str(item["itemname"]).strip()
            gb = sosok_map.get(str(item.get("sosok")), "KRX")
            if cd not in seen:
                seen.add(cd)
                stock_list.append({"cd": cd, "nm": nm, "gb": gb})
                added_naver += 1
        print(f"✓ URL 1 (Naver Stock API): Loaded {added_naver} stocks")
    except Exception as e:
        print(f"⚠️ URL 1 Error (Naver Stock API): {e}")

    # 2. KRX KIND Listed Companies (KOSPI, KOSDAQ, KONEX Fallback/Complement)
    try:
        res_kind = requests.get(KRX_KIND_URL, headers=headers, timeout=10)
        df_kind = pd.read_html(io.BytesIO(res_kind.content), header=0)[0]
        added_kind = 0
        for _, row in df_kind.iterrows():
            cd = format_ticker_code(row["종목코드"])
            nm = str(row["회사명"]).strip()
            gb = str(row["시장구분"]).strip()
            if cd not in seen:
                seen.add(cd)
                stock_list.append({"cd": cd, "nm": nm, "gb": gb})
                added_kind += 1
        print(f"✓ URL 2 (KRX KIND): Total {len(df_kind)}, added {added_kind} new items")
    except Exception as e:
        print(f"⚠️ URL 2 Error (KRX KIND): {e}")

    # 3. Naver Finance ETF API
    try:
        res_etf = requests.get(NAVER_ETF_API_URL, headers=headers, timeout=10)
        etf_items = res_etf.json()["result"]["etfItemList"]
        added_etf = 0
        for item in etf_items:
            cd = format_ticker_code(item["itemcode"])
            nm = str(item["itemname"]).strip()
            if cd not in seen:
                seen.add(cd)
                stock_list.append({"cd": cd, "nm": nm, "gb": "ETF"})
                added_etf += 1
        print(f"✓ URL 3 (Naver ETF API): Total {len(etf_items)}, added {added_etf} new items")
    except Exception as e:
        print(f"⚠️ URL 3 Error (Naver ETF API): {e}")

    # Sort stock list in ascending order by ticker code (cd)
    stock_list.sort(key=lambda x: x["cd"])

    return stock_list


def main():
    print("Fetching integrated KR listed stock & ETF list across 3 sources...")
    stock_list = fetch_all_kr_stock_lists()

    output_dir = BASE_DIR / "output/KR/data"
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / "stocklist.json"

    output_data = {"Co": stock_list}
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(output_data, f, ensure_ascii=False, indent=2)

    print(f"✓ Integrated KR stocklist saved to {output_path} (Total: {len(stock_list)})")


if __name__ == "__main__":
    main()
