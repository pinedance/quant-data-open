import os
import time
import pandas as pd
import requests
import yfinance as yf
import FinanceDataReader as fdr
from message import send_telegram_message

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

def load_old_etf_data(url):
    try:
        return pd.read_html(url, index_col=0, header=0)[0]
    except Exception as e:
        print(f"Error loading old ETF data: {e}")
        return pd.DataFrame()

def download_with_retry( *arg, src="yahoo", max_retries=3, delay=3):
    arg_ = list( arg )
    ticker = arg_[0]
    retries = 0
    while retries < max_retries:
        try:
            data = yf.download( *arg, auto_adjust=True ) if (src == "yahoo") else fdr.DataReader( *arg )
            if data.empty:
                m_err = f"No data found for {ticker}"
                send_telegram_message( m_err )
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

def save_etf_data(etf_data, output_path):
    try:
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        html_table = etf_data.to_html(na_rep='')
        with open(output_path, "w", encoding="utf-8") as fl:
            fl.write(html_table)
        return True
    except Exception as e:
        error_msg = f"Error saving ETF data: {str(e)}"
        send_telegram_message(error_msg)
        return False