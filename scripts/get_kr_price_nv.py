# -*- coding: utf-8 -*-

# %%
import pandas as pd
from tqdm import tqdm
import requests
from bs4 import BeautifulSoup
from core.tIO import save_df_as_tsv
from core.cons import config_gsheet_tickers_req_krx as config_tickers_req
from core.cons import delta_months
from core.tIO import get_output_path

#%%
OUTPUT_PATH_PRICE_D_RAW = get_output_path("KR/stocks/price/D", "raw-nv.tsv")

# %%
days = delta_months
days_offset = pd.Timedelta(days, unit="days")
day_end = pd.Timestamp.today().date()
day_start = day_end - days_offset
print(day_start, day_end)

# %%
tickers_req_url = "https://docs.google.com/spreadsheets/d/{sheet_id}/gviz/tq?tqx=out:csv&sheet={sheet_name}".format(
    **config_tickers_req)
tickers_req_df = pd.read_csv(tickers_req_url)
etf_tickers = list(sorted(
    ["{:06d}".format(tk) for tk in list(tickers_req_df["TICKER"])]
))
print(etf_tickers)

# %%
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


# %%
price_raw_lst = [
    get_price(ticker.strip(), days)['Close'] for ticker in etf_tickers
]

# %%
price_raw = pd.concat(price_raw_lst, axis=1)
price_raw.index = price_raw.index.date
price_raw.columns = ["A{}".format(ticker) for ticker in etf_tickers]
# etf_data.dtypes
price_raw = price_raw.astype('float64')

# %%
save_df_as_tsv(price_raw, OUTPUT_PATH_PRICE_D_RAW)
