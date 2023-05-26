# -*- coding: utf-8 -*-
# pip -q install finance-datareader

# %%
from os import path
import pandas as pd
from tqdm import tqdm
import FinanceDataReader as fdr
from cons import config_gsheet_tickers_req_krx as config_tickers_req

# %%
days_offset = pd.Timedelta(400, unit="days")
day_end = pd.Timestamp.today().date()
day_start = day_end - days_offset
print(day_start, day_end)

# fdr.DataReader("005930", day_start, day_end)

# %%
# URL = dict(
#     stock_list="https://pinedance.github.io/quant-data-open/dist/CompanyList.html"
# )
# id_group = 770
# stock_list = pd.read_html(URL["stock_list"])[0]
# etf_list = stock_list[stock_list["GROUP"] == id_group]

# %%
tickers_req_url = "https://docs.google.com/spreadsheets/d/{sheet_id}/gviz/tq?tqx=out:csv&sheet={sheet_name}".format(
    **config_tickers_req)
tickers_req_df = pd.read_csv(tickers_req_url)
etf_tickers = list(tickers_req_df["TICKER"].astype("str"))
print(etf_tickers)

# %%time
# etf_data_raw = [
#     fdr.DataReader(ticker[1:], day_start, day_end)['Close'] for idx, ticker, name, group in etf_list.itertuples()
# ]

etf_data_raw = [
    fdr.DataReader(ticker, day_start, day_end)['Close'] for ticker in etf_tickers
]

# %%
etf_data = pd.concat(etf_data_raw, axis=1)
etf_data.columns = ["A{}".format(ticker) for ticker in etf_tickers]
# etf_data.dtypes
etf_data = etf_data.astype('float64')

# %%
html_table = etf_data.to_html(na_rep='')

# %%
rst_path = path.join("dist", "KRX", "etf-price-selected.html")
# rst_path = path.join("dist", "KRX", "etf-price.html")
with open(rst_path, "w", encoding="utf-8") as fl:
    fl.write(html_table)

# %%
