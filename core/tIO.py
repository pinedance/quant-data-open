import os
import re
import time
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

def get_json(url, keys=["result"]):
    d = requests.get(url)
    rst = d.json()
    # print( rst )
    if (keys is not None) and (len(keys) > 0):
        for k in keys:
            rst = rst[k]
    return rst

def fetch_tickers(tickers_req_url):
    try:
        tickers_req_df = pd.read_csv(tickers_req_url)
        if tickers_req_df.empty:
            error_msg = f"Empty data received from Google Spreadsheet"
            send_telegram_message(error_msg)
            raise ValueError(error_msg)
        
        etf_tickers = list(sorted(set(tickers_req_df["TICKER"].astype("str"))))
        print(f"Successfully loaded {len(etf_tickers)} tickers")
        return etf_tickers
    
    except Exception as e:
        error_msg = f"Failed to load tickers from Google Spreadsheet: {str(e)}"
        send_telegram_message(error_msg)
        raise

def load_prev_price(url):
    try:
        return pd.read_html(url, index_col=0, header=0)[0]
    except Exception as e:
        print(f"Error loading prev data: {e}")
        return pd.DataFrame()

def download_with_retry( *arg, src="yahoo", max_retries=3, delay=3):
    arg_ = list( arg )
    ticker = arg_[0]
    retries = 0
    while retries < max_retries:
        try:
            if src == "yahoo":
                data = yf.download( *arg, auto_adjust=True, progress=False )
            else:
                data = fdr.DataReader( *arg )
            if data.empty:
                m_err = f"No data found for {ticker}"
                # send_telegram_message( m_err )
                # print(m_err)
                raise ValueError( m_err )
            return data
        except Exception as e:
            retries += 1
            m_err = f"Attempt {retries} failed: {e}"
            # send_telegram_message( m_err )
            print(m_err)
            if retries < max_retries:
                time.sleep(delay)

    m_err = f"Failed to download {ticker} after {max_retries} attempts"
    send_telegram_message( m_err )
    raise Exception( m_err )

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

    # if d.empty:
    #     m_err = "{}: Data is Empty!!!".format(ticker)
    #     send_telegram_message( m_err )
    # print( d )

    if 'Adj Close' in d.columns:
        print(f"{ticker}: Using Adj Close")
        rst = d['Adj Close']
    else:
        print(f"{ticker}: Using Close")
        rst = d['Close']

    return rst

def fetch_prices(tickers, start_date, old_data, src="yahoo"):
    price_data = []
    total = len(tickers)

    for i, ticker in enumerate(tickers, 1):
        print(f"Fetching price: {i}/{total} - {ticker}")

        try:
            new_data = get_ticker_data(ticker.strip(), start_date, src=src)
            if not new_data.empty:
                price_data.append(new_data)
            else:
                # 새 데이터 없으면 old_data 사용
                ticker_data = select_column_by_name(old_data, ticker)
                if not ticker_data.empty:
                    print(f"No new data for {ticker}, using existing data")
                    price_data.append(ticker_data)
        except Exception as e:
            # 에러 발생 시 old_data 사용
            print(f"Error fetching {ticker}: {e}")
            ticker_data = select_column_by_name(old_data, ticker)
            if not ticker_data.empty:
                print(f"Using existing data for {ticker}")
                price_data.append(ticker_data)

    return price_data

def save_df_as_html_table( df, output_path):
    try:
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        html_table = df.to_html(na_rep='')
        with open(output_path, "w", encoding="utf-8") as fl:
            fl.write(html_table)
        return True
    except Exception as e:
        error_msg = f"Error saving data: {str(e)}"
        send_telegram_message(error_msg)
        return False

def save_df_as_tsv(df, output_path):
    """DataFrame을 TSV 형식으로 저장"""
    try:
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        df.to_csv(output_path, sep='\t', encoding='utf-8', index=True)
        return True
    except Exception as e:
        error_msg = f"Error saving data: {str(e)}"
        send_telegram_message(error_msg)
        return False