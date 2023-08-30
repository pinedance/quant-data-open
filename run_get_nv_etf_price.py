# -*- coding: utf-8 -*-

# %%
from os import path
import pandas as pd
from tqdm import tqdm
import requests
from bs4 import BeautifulSoup
from cons import config_gsheet_tickers_req_krx as config_tickers_req
from cons import delta_days

# %%
days = delta_days
days_offset = pd.Timedelta(days, unit="days")
day_end = pd.Timestamp.today().date()
day_start = day_end - days_offset
print(day_start, day_end)

# %%
tickers_req_url = "https://docs.google.com/spreadsheets/d/{sheet_id}/gviz/tq?tqx=out:csv&sheet={sheet_name}".format(
    **config_tickers_req)
tickers_req_df = pd.read_csv(tickers_req_url)
etf_tickers = list( sorted ( tickers_req_df["TICKER"].astype("str") ) )
print(etf_tickers)

#%%
# 네이버 금융에서 종목 가격정보와 거래량을 가져오는 함수: get_price
def get_price(ticker, days):
    # count=3000에서 3000은 과거 3,000 영업일간의 데이터를 의미. 사용자가 조절 가능
    url = f"https://fchart.stock.naver.com/sise.nhn?symbol={ticker}&timeframe=day&count={days}&requestType=0"
    get_result = requests.get(url)
    bs_obj = BeautifulSoup(get_result.content, "xml")

    # information
    inf = bs_obj.select('item')
    columns = ['Date', 'Open', 'High', 'Low', 'Close', 'Volume']
    df_inf = pd.DataFrame([], columns=columns, index=range(len(inf)))

    for i in range(len(inf)):
        df_inf.iloc[i] = str(inf[i]['data']).split('|')

    df_inf.index = pd.to_datetime(df_inf['Date'])

    return df_inf.drop('Date', axis=1).astype(float)

#%%
etf_data_raw = [
    get_price(ticker.strip(), days)['Close'] for ticker in etf_tickers
]

# %%
etf_data = pd.concat(etf_data_raw, axis=1)
etf_data.columns = ["A{}".format(ticker) for ticker in etf_tickers]
# etf_data.dtypes
etf_data = etf_data.astype('float64')

# %%
html_table = etf_data.to_html(na_rep='')

# %%
rst_path = path.join("dist", "NV", "etf-price-selected.html")
with open(rst_path, "w", encoding="utf-8") as fl:
    fl.write(html_table)

# %%
