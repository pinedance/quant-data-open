import re
from copy import deepcopy
import requests
import FinanceDataReader as fdr
import yfinance as yf

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
        
    if 'Adj Close' in d.columns:
        print("Catching 'Adj Close'")
        rst = d['Adj Close']
    else:
        print("Catching 'Close'")
        rst = d['Close']
        
    return rst
