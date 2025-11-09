import re
import time
from copy import deepcopy
import requests
import pandas as pd
import FinanceDataReader as fdr
import yfinance as yf
from core.message import send_telegram_message, notice_price_status
from core.tTable import select_column_by_name
from core.tIO import download_with_retry


#%% DEAL FINANCE DATA
######################################################################

def fin_data(*arg, src="auto"):
    arg_ = list( arg )
    ticker = arg_[0]
    m_kr = re.match(r"\d{6,6}", ticker )
    m_us = re.match(r"[a-zA-Z]+", ticker )
    
    if m_kr is not None and m_kr[0] == ticker:
        ticker_type = "KR"
    elif m_us is not None and m_us[0] == ticker:
        ticker_type = "US"
    else:
        ticker_type = None

    if src == "krx":
        d = download_with_retry( *arg, src="krx" )
    elif src == "yahoo":
        d = download_with_retry( *arg, src="yahoo" )
    elif src == "auto":
        if ticker_type == "KR":   # 한국 숫자 6자리 티커
            arg_[0] = ticker + ".KS"
            d = download_with_retry( *arg_, src="yahoo" )
            if len(d) < 30:  # yahoo finance에 데이터가 없다면
                print( "There is no data in yahoo finance. Try KRX data")
                d = download_with_retry( *arg, src="krx" )
        else:
            d = download_with_retry( *arg, src="yahoo" )

    # if d.empty:
    #     m_err = "{}: Data is Empty!!!".format(ticker)
    #     send_telegram_message( m_err )
    # print( d )
    
    if 'Adj Close' in d.columns:
        print( "{}: Catching 'Adj Close'".format(ticker) )
        rst = d['Adj Close']
    else:
        print( "{}: Catching 'Close'".format(ticker) )
        rst = d['Close']
 
    return rst

def collect_etf_data(tickers, start_date, old_data, src="yahoo"):
    etf_data_raw = []
    total = len(tickers)
    
    for i, ticker in enumerate(tickers, 1):
        print(f"Collecting ETF data: {i}/{total} - {ticker}")
        # Get existing data for the ticker if available
        ticker_data = select_column_by_name(old_data, ticker)
        
        try:
            new_data = fin_data(ticker.strip(), start_date, src=src)
            if not new_data.empty:
                etf_data_raw.append(new_data)
            else:
                print(f"No new data for {ticker}, using existing data")
                if not ticker_data.empty:
                    etf_data_raw.append(ticker_data)
        except Exception as e:
            print(f"Error fetching data for {ticker}: {e}")
            if not ticker_data.empty:
                print(f"Using existing data for {ticker}")
                etf_data_raw.append(ticker_data)
    
    return etf_data_raw

def get_price_status( ticker, _hist ):

    if isinstance( _hist, pd.Series ):
        hist = _hist.to_frame()
    else:
        hist = _hist.copy()
        
    if hist.empty:
        return None
    
    # print( hist )
    # print( hist.columns )
    
    hist.columns = ['Close']

    # 5일 이동평균 및 표준편차 계산
    hist['MA005'] = hist['Close'].rolling(window=5).mean()
    hist['STD005'] = hist['Close'].rolling(window=5).std()
    
    # 200일 이동평균 및 표준편차 계산
    hist['MA200'] = hist['Close'].rolling(window=200).mean()
    hist['STD200'] = hist['Close'].rolling(window=200).std()
    
    # 최근 마지막 데이터 추출
    recent = hist.iloc[-1]
    ma200 = recent['MA200']
    std200 = recent['STD200']
    current_price = recent['MA005']
    
    # 이전 날 데이터 (돌파 판단용)
    prev_data = hist.iloc[-2]
    prev_ma200 = prev_data['MA200']
    prev_price = prev_data['MA005']
    
    # 상태 결정
    sigma = (current_price - ma200) / std200

    if current_price > ma200 and prev_price <= prev_ma200:
        status = "상향 돌파"
    elif current_price > ma200 and prev_price > prev_ma200:
        status = f"상향 지속({sigma:.1f})"
    elif current_price < ma200 and prev_price >= prev_ma200:
        status = "하향 돌파"
    elif current_price < ma200 and prev_price < prev_ma200:
        status = f"하향 지속({sigma:.1f})"
    else:
        status = "중립"
    

    rst = {
        'ticker': ticker,
        'current_price': current_price,
        'ma200': ma200,
        'std200': std200,
        'sigma': sigma,
        'status': status
    }
    
    print(f"{rst['ticker']}: {rst['current_price']:.2f} | MA200: {rst['ma200']:.2f} | 상태: {rst['status']}")
    
    return rst

def process_price_status(etf_tickers, etf_data_raw):
    status_results = []
    for i, hist in enumerate(etf_data_raw):
        try:
            status_data = get_price_status(etf_tickers[i], hist)
            if status_data:
                status_results.append(status_data)
        except Exception as e:
            error_msg = f"Error processing status for {etf_tickers[i]}: {str(e)}"
            send_telegram_message(error_msg)
    return status_results

