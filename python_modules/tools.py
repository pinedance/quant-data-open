import re
from copy import deepcopy
import requests
import FinanceDataReader as fdr
import yfinance as yf
import pandas as pd
from message import send_telegram_message

month2quarter_dict = {
    '01': 'Q1', '02': 'Q1', '03': 'Q1', '04': 'Q2', '05': 'Q2', '06': 'Q2',
    '07': 'Q3', '08': 'Q3', '09': 'Q3', '10': 'Q4', '11': 'Q4', '12': 'Q4'
}


def yyyymm2quarter(yyyymm, q_dict=month2quarter_dict):
    y = yyyymm[:4]
    m = yyyymm[4:]
    q = q_dict[m]
    return f"{y}{q}"


def get_json(url, keys=["result"]):
    d = requests.get(url)
    rst = d.json()
    # print( rst )
    if (keys is not None) and (len(keys) > 0):
        for k in keys:
            rst = rst[k]
    return rst


def fin_data(*arg, src="auto"):
    arg_ = list( arg )
    ticker = arg_[0]
    m_kr = re.match(r"\d{6,6}", ticker )
    m_us = re.match(r"[a-zA-Z]+", ticker )
    
    if m_kr is not None and m_kr[0] == ticker:
        ticker_type = "KR"
    elif m_us is not None and m_us[0] == "ticker":
        ticker_type = "US"
    else:
        ticker_type = None

    if src == "krx":
        d = fdr.DataReader( *arg )
    elif src == "yahoo":
        d = yf.download( *arg )
    elif src == "auto":
        if ticker_type == "KR":   # 한국 숫자 6자리 티커
            arg_[0] = ticker + ".KS"
            d = yf.download( *arg_ )
            if len(d) < 30:  # yahoo finance에 데이터가 없다면
                print( "There is no data in yahoo finance. Try KRX data")
                d = fdr.DataReader( *arg )
        else:
            d = yf.download( *arg )
        
    if d.empty:
        send_telegram_message( "{}: Data is Empty!!!".format(ticker) )
        
    if 'Adj Close' in d.columns:
        print( "{}: Catching 'Adj Close'".format(ticker) )
        rst = d['Adj Close']
    else:
        print( "{}: Catching 'Close'".format(ticker) )
        rst = d['Close']
 
    return rst

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
    # 200일 이동평균 및 표준편차 계산
    hist['MA200'] = hist['Close'].rolling(window=200).mean()
    hist['STD200'] = hist['Close'].rolling(window=200).std()
    
    # 최근 마지막 데이터 추출
    recent = hist.iloc[-1]
    ma200 = recent['MA200']
    std200 = recent['STD200']
    current_price = recent['Close']
    
    # 이전 날 데이터 (돌파 판단용)
    prev_data = hist.iloc[-2]
    prev_ma200 = prev_data['MA200']
    prev_price = prev_data['Close']
    
    # 상태 결정
    if current_price > ma200 and prev_price <= prev_ma200:
        status = "상향 돌파"
    elif current_price > ma200 and prev_price > prev_ma200:
        sigma = (current_price - ma200) / std200
        status = f"상향 지속({sigma:.1f})"
    elif current_price < ma200 and prev_price >= prev_ma200:
        status = "하향 돌파"
    elif current_price < ma200 and prev_price < prev_ma200:
        sigma = (current_price - ma200) / std200
        status = f"하향 지속({sigma:.1f})"
    else:
        status = "중립"
    
    rst = {
        'ticker': ticker,
        'current_price': current_price,
        'ma200': ma200,
        'std200': std200,
        'status': status
    }
    
    print(f"{rst['ticker']}: {rst['current_price']:.2f} | MA200: {rst['ma200']:.2f} | 상태: {rst['status']}")
    
    return rst