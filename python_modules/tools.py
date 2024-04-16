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
    if (keys is not None) and (len(keys) > 0):
        for k in keys:
            rst = rst[k]
    return rst


def fin_data(*arg, src="krx"):
    if src == "yahoo":
        d = yf.download(*arg)
    else:
        d = fdr.DataReader(*arg)
    if 'Adj Close' in d.columns:
        print("Catching 'Adj Close'")
        rst = d['Adj Close']
    else:
        print("Catching 'Close'")
        rst = d['Close']
    return rst
