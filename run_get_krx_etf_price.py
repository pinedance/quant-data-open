# -*- coding: utf-8 -*-
# pip -q install finance-datareader

# %%
from os import path
import pandas as pd
from tqdm import tqdm
import FinanceDataReader as fdr

# %%
days_offset = pd.Timedelta(380, unit="days")
day_end = pd.Timestamp.today().date()
day_start = day_end - days_offset
print(day_start, day_end)

# fdr.DataReader("005930", day_start, day_end)

# %%
URL = dict(
    stock_list="https://pinedance.github.io/quant-data-open/dist/CompanyList.html"
)
id_group = 770

# %%
stock_list = pd.read_html(URL["stock_list"])[0]
# stock_list.head(10)

etf_list = stock_list[stock_list["GROUP"] == id_group]
# etf_list.head(10)

# %%time

etf_data_raw = [
    fdr.DataReader(ticker[1:], day_start, day_end)['Close'] for idx, ticker, name, group in etf_list.itertuples()
]
# etf_data_raw = [
#     fdr.DataReader(ticker, day_start, day_end)['Close'] for ticker in tickers
# ]

# %%
etf_data = pd.concat(etf_data_raw, axis=1)

etf_data.columns = [
    ticker for idx, ticker, name, group in etf_list.itertuples()
]

# etf_data.head(10)

# %%
html_table = etf_data.to_html()

# %%
rst_path = path.join("dist", "KRX", "etf-price.html")
with open(rst_path, "w", encoding="utf-8") as fl:
    fl.write(html_table)

############################################################################
# %%
tickers = [
    "148070", "195970", "195980", "203780", "218420", "251350", "273130", "276000", "278530", "283580",
    "305080", "329750", "332620", "357870", "371160", "371470", "379800", "379810", "385560", "390390", "394660", "394670", "396510", "399580",
    "411060", "414270", "414780", "418670", "419420", "419430", "430500", "437080", "438330", "448300"
]

tickersA = ["A{}".format(t) for t in tickers]
# %%
etf_data_selected = etf_data[tickersA]
html_table_selected = etf_data_selected.to_html()

# %%
rst_path2 = path.join("dist", "KRX", "etf-price-selected.html")
with open(rst_path2, "w", encoding="utf-8") as fl:
    fl.write(html_table_selected)
