# -*- coding: utf-8 -*-
# pip -q install finance-datareader

# %%
from os import path
import pandas as pd
from tqdm import tqdm
from tFinance import fin_data
from cons import config_gsheet_tickers_req_yh2 as config_tickers_req
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
etf_tickers = list(sorted(set(tickers_req_df["TICKER"].astype("str"))))
print(etf_tickers)

# %%time
etf_data_raw = [
    fin_data(ticker.strip(), day_start, src="yahoo") for ticker in etf_tickers
]

etf_data_raw = [
    sr[~sr.index.duplicated(keep='first')] for sr in etf_data_raw
]

# %%
etf_data = pd.concat(etf_data_raw, axis=1, join="inner")
etf_data.index = etf_data.index.date
etf_data.columns = ["{}".format(ticker) for ticker in etf_tickers]
# etf_data.dtypes
etf_data = etf_data.astype('float64')

# %%
# html_table = etf_data.to_html(na_rep='')
html_table = etf_data.dropna(axis=0).to_html(na_rep='')

# %%
rst_path = path.join("dist", "YH", "economic-data-daily.html")
with open(rst_path, "w", encoding="utf-8") as fl:
    fl.write(html_table)
