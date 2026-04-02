import os
import re
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
import pandas as pd
import requests
import yfinance as yf
import FinanceDataReader as fdr
from pathlib import Path
from core.message import send_telegram_message
from core.tTable import select_column_by_name

#%% CONSTANTS
######################################################################

MIN_DATA_POINTS = 30  # Yahoo Finance fallback 판단 기준 (약 1개월치)
PROJECT_ROOT = Path(__file__).parent.parent
OUTPUT_ROOT = PROJECT_ROOT / "output"

#%% PATH UTILITIES
######################################################################

def get_output_path(subdir, filename):
    """
    서브디렉토리의 출력 파일 경로 반환
    예: get_output_path("US/stocks/price/D", "raw.html")
    """
    base_path = OUTPUT_ROOT / subdir
    base_path.mkdir(parents=True, exist_ok=True)
    return base_path / filename

#%% GET DATA
######################################################################

def get_json(url, keys=None):
    if keys is None:
        keys = ["result"]
    response = requests.get(url)
    response.raise_for_status()
    rst = response.json()
    for k in keys:
        rst = rst[k]
    return rst

def fetch_tickers(tickers_req_url):
    try:
        tickers_req_df = pd.read_csv(tickers_req_url)
        if tickers_req_df.empty:
            error_msg = "Google Spreadsheet 데이터 없음"
            send_telegram_message(f"⚠️ {error_msg}")
            raise ValueError(error_msg)
        
        etf_tickers = list(sorted(set(tickers_req_df["TICKER"].astype("str"))))
        print(f"Successfully loaded {len(etf_tickers)} tickers")
        return etf_tickers
    
    except Exception as e:
        send_telegram_message(f"🚨 티커 목록 로드 실패\n{str(e)}")
        raise

def load_prev_price(url):
    try:
        return pd.read_html(url, index_col=0, header=0)[0]
    except Exception as e:
        print(f"Error loading prev data: {e}")
        return pd.DataFrame()

def download_with_retry(*arg, src="yahoo", max_retries=3, delay=1):
    ticker = arg[0]
    for attempt in range(1, max_retries + 1):
        try:
            if src == "yahoo":
                start = arg[1] if len(arg) > 1 else None
                end = arg[2] if len(arg) > 2 else None
                data = yf.Ticker(ticker).history(start=start, end=end, auto_adjust=True)
                if data.index.tz is not None:
                    data.index = data.index.tz_localize(None)
            else:
                data = fdr.DataReader(*arg)
            if data.empty:
                raise ValueError(f"No data found for {ticker}")
            return data
        except Exception as e:
            print(f"[{ticker}] Attempt {attempt}/{max_retries} failed: {e}")
            if attempt < max_retries:
                time.sleep(delay)

    m_err = f"다운로드 실패: {ticker} ({max_retries}회 시도)"
    send_telegram_message(f"⚠️ {m_err}")
    raise Exception(m_err)

def get_ticker_data(*arg, src="auto"):
    arg_ = list(arg)
    ticker = arg_[0]
    m_kr = re.match(r"[0-9a-zA-Z]{6,6}", ticker)
    m_us = re.match(r"[a-zA-Z]+", ticker)

    if m_kr is not None and m_kr[0] == ticker:
        ticker_type = "KR"
    elif m_us is not None and m_us[0] == ticker:
        ticker_type = "US"
    else:
        ticker_type = None

    if src == "krx":
        d = download_with_retry(*arg, src="krx")
    elif src == "yahoo":
        d = download_with_retry(*arg, src="yahoo")
    elif src == "auto":
        if ticker_type == "KR":   # 한국 숫자 6자리 티커
            arg_[0] = ticker + ".KS"
            d = download_with_retry(*arg_, src="yahoo")
            if len(d) < MIN_DATA_POINTS:  # yahoo finance에 데이터가 없다면
                print(f"No data in Yahoo Finance for {ticker}, trying KRX")
                d = download_with_retry(*arg, src="krx")
        else:
            d = download_with_retry(*arg, src="yahoo")
    else:
        raise ValueError(f"Unknown src: '{src}'. Expected: 'krx', 'yahoo', 'auto'")

    if 'Adj Close' in d.columns:
        rst = d['Adj Close']
    else:
        rst = d['Close']

    if isinstance(rst, pd.DataFrame):
        rst = rst.iloc[:, 0]

    rst.name = ticker
    return rst

def _fetch_single_price(ticker, start_date, old_data, src):
    try:
        new_data = get_ticker_data(ticker.strip(), start_date, src=src)
        if not new_data.empty and not new_data.isna().all():
            return ticker, new_data, False
    except Exception as e:
        print(f"Error fetching {ticker}: {e}")

    ticker_data = select_column_by_name(old_data, ticker)
    if not ticker_data.empty:
        print(f"[{ticker}] Using existing data (fallback)")
        return ticker, ticker_data, True

    return ticker, None, True

def fetch_prices(tickers, start_date, old_data, src="yahoo", max_workers=None):
    if not tickers:
        raise ValueError("tickers is empty")
    total = len(tickers)
    if max_workers is None:
        max_workers = min((os.cpu_count() or 1) * 2, 20)

    print(f"Fetching {total} tickers (parallel, workers={max_workers})")

    ticker_to_data = {}
    success_cnt = 0
    fallback_cnt = 0
    failed_cnt = 0

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        future_to_ticker = {
            executor.submit(_fetch_single_price, ticker, start_date, old_data, src): ticker
            for ticker in tickers
        }
        for i, future in enumerate(as_completed(future_to_ticker), 1):
            ticker, data, used_fallback = future.result()
            print(f"[{i}/{total}] {ticker}: {'fallback' if used_fallback else 'ok'}")
            if data is not None:
                ticker_to_data[ticker] = data
                if used_fallback:
                    fallback_cnt += 1
                else:
                    success_cnt += 1
            else:
                failed_cnt += 1

    if success_cnt + fallback_cnt == 0:
        raise RuntimeError("가격 데이터를 단 1개도 다운로드하지 못했습니다")

    if success_cnt / total < 0.5:
        msg = f"신규 다운로드 성공률 낮음\n성공 {success_cnt}/{total}  ·  fallback {fallback_cnt}  ·  실패 {failed_cnt}"
        print(msg)
        send_telegram_message(f"⚠️ {msg}")
    else:
        print(f"Download complete — 성공 {success_cnt}, fallback {fallback_cnt}, 실패 {failed_cnt} (total {total})")

    available = [t for t in tickers if t in ticker_to_data]
    return pd.DataFrame({t: ticker_to_data[t] for t in available})

def save_df_as_html_table(df, output_path):
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    html_table = df.to_html(na_rep='')
    with open(output_path, "w", encoding="utf-8") as fl:
        fl.write(html_table)

def save_df_as_tsv(df, output_path):
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    df.to_csv(output_path, sep='\t', encoding='utf-8', index=True)