# -*- coding: utf-8 -*-
import io
import json
import sys
from pathlib import Path
from typing import Any

import pandas as pd
import requests

# Add root directory to python path to load core modules
BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.append(str(BASE_DIR))

# ==============================================================================
# Constants (Data Reference URLs & Configuration)
# ==============================================================================
URL_NAVER_STOCK = (
    "https://stock.naver.com/api/domestic/market/stock/default?marketType=ALL&pageSize=4000"
)
URL_KRX_KIND = (
    "https://kind.krx.co.kr/corpgeneral/corpList.do?method=download&searchType=13"
)
URL_NAVER_ETF = "https://finance.naver.com/api/sise/etfItemList.nhn"
URL_NAVER_ETN = "https://finance.naver.com/api/sise/etnItemList.nhn"

DEFAULT_HEADERS = {"User-Agent": "Mozilla/5.0"}
DEFAULT_TIMEOUT_SECONDS = 10
NAVER_SOSOK_MARKET_MAP = {"0": "유가", "1": "코스닥", "2": "코넥스"}


# ==============================================================================
# Helper Functions
# ==============================================================================
def format_ticker_code(raw_code: Any) -> str:
    """Format ticker code with 'A' prefix to prevent number/string ambiguity (e.g. 238540 -> A238540)."""
    code_str = str(raw_code).strip()
    if code_str.startswith("A"):
        return code_str
    try:
        return f"A{int(code_str):06d}"
    except (ValueError, TypeError):
        return f"A{code_str}"


# ==============================================================================
# Data Fetchers
# ==============================================================================
def fetch_naver_stock_items(
    session: requests.Session, seen_codes: set[str]
) -> list[dict[str, str]]:
    """Fetch KOSPI, KOSDAQ, and KONEX stock list from Naver Stock API."""
    items: list[dict[str, str]] = []
    try:
        response = session.get(
            URL_NAVER_STOCK, headers=DEFAULT_HEADERS, timeout=DEFAULT_TIMEOUT_SECONDS
        )
        response.raise_for_status()
        raw_items = response.json()
    except (requests.RequestException, ValueError) as e:
        print(f"⚠️ URL 1 Error (Naver Stock API): {e}")
        return items

    added_count = 0
    for raw_item in raw_items:
        code = format_ticker_code(raw_item.get("itemcode", ""))
        name = str(raw_item.get("itemname", "")).strip()
        market_category = NAVER_SOSOK_MARKET_MAP.get(str(raw_item.get("sosok")), "KRX")
        if code and code not in seen_codes:
            seen_codes.add(code)
            items.append({"cd": code, "nm": name, "gb": market_category})
            added_count += 1

    print(f"✓ URL 1 (Naver Stock API): Loaded {added_count} stocks")
    return items


def fetch_krx_kind_items(
    session: requests.Session, seen_codes: set[str]
) -> list[dict[str, str]]:
    """Fetch KRX KIND listed companies as a fallback/complement."""
    items: list[dict[str, str]] = []
    try:
        response = session.get(
            URL_KRX_KIND, headers=DEFAULT_HEADERS, timeout=DEFAULT_TIMEOUT_SECONDS
        )
        response.raise_for_status()
        data_frames = pd.read_html(io.BytesIO(response.content), header=0)
        if not data_frames:
            return items
        df_kind = data_frames[0]
    except (requests.RequestException, ValueError, Exception) as e:
        print(f"⚠️ URL 2 Error (KRX KIND): {e}")
        return items

    added_count = 0
    for _, row in df_kind.iterrows():
        code = format_ticker_code(row["종목코드"])
        name = str(row["회사명"]).strip()
        market_category = str(row["시장구분"]).strip()
        if code and code not in seen_codes:
            seen_codes.add(code)
            items.append({"cd": code, "nm": name, "gb": market_category})
            added_count += 1

    print(f"✓ URL 2 (KRX KIND): Total {len(df_kind)}, added {added_count} new items")
    return items


def fetch_naver_etf_or_etn_items(
    session: requests.Session,
    url: str,
    item_list_key: str,
    market_category: str,
    seen_codes: set[str],
    source_label: str,
) -> list[dict[str, str]]:
    """Fetch ETF or ETN item list from Naver Finance API."""
    items: list[dict[str, str]] = []
    try:
        response = session.get(
            url, headers=DEFAULT_HEADERS, timeout=DEFAULT_TIMEOUT_SECONDS
        )
        response.raise_for_status()
        json_data = response.json()
        raw_items = json_data.get("result", {}).get(item_list_key, [])
    except (requests.RequestException, ValueError, KeyError) as e:
        print(f"⚠️ {source_label} Error: {e}")
        return items

    added_count = 0
    for raw_item in raw_items:
        code = format_ticker_code(raw_item.get("itemcode", ""))
        name = str(raw_item.get("itemname", "")).strip()
        if code and code not in seen_codes:
            seen_codes.add(code)
            items.append({"cd": code, "nm": name, "gb": market_category})
            added_count += 1

    print(f"✓ {source_label}: Total {len(raw_items)}, added {added_count} new items")
    return items


# ==============================================================================
# Orchestrator & Main Entry Point
# ==============================================================================
def fetch_all_kr_stock_lists() -> list[dict[str, str]]:
    """Orchestrate stock, ETF, and ETN data collection from 4 sources."""
    stock_items: list[dict[str, str]] = []
    seen_codes: set[str] = set()

    with requests.Session() as session:
        stock_items.extend(fetch_naver_stock_items(session, seen_codes))
        stock_items.extend(fetch_krx_kind_items(session, seen_codes))
        stock_items.extend(
            fetch_naver_etf_or_etn_items(
                session=session,
                url=URL_NAVER_ETF,
                item_list_key="etfItemList",
                market_category="ETF",
                seen_codes=seen_codes,
                source_label="URL 3 (Naver ETF API)",
            )
        )
        stock_items.extend(
            fetch_naver_etf_or_etn_items(
                session=session,
                url=URL_NAVER_ETN,
                item_list_key="etnItemList",
                market_category="ETN",
                seen_codes=seen_codes,
                source_label="URL 4 (Naver ETN API)",
            )
        )

    stock_items.sort(key=lambda item: item["cd"])
    return stock_items


def main() -> None:
    print("Fetching integrated KR listed stock, ETF & ETN list across 4 sources...")
    stock_items = fetch_all_kr_stock_lists()

    output_dir = BASE_DIR / "output/KR/data"
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / "stocklist.json"

    output_data = {"Co": stock_items}
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(output_data, f, ensure_ascii=False, indent=2)

    print(f"✓ Integrated KR stocklist saved to {output_path} (Total: {len(stock_items)})")


if __name__ == "__main__":
    main()
