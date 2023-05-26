# -*- coding: utf-8 -*-
# pip -q install finance-datareader

# %%
from os import path
import pandas as pd
from tqdm import tqdm
import FinanceDataReader as fdr
from cons import config_gsheet_average_daily_exports_kr as config_gsheet1

# %%
# 일평균수출액
req_url = "https://docs.google.com/spreadsheets/d/{sheet_id}/gviz/tq?tqx=out:csv&sheet={sheet_name}".format(
    **config_gsheet1)

req_df = pd.read_csv(req_url)
print(req_df.head())

# %%
html_table = req_df.to_html(na_rep='')

# %%
rst_path = path.join("dist", "M", "average_daily_exports_kr.html")
# rst_path = path.join("dist", "KRX", "etf-price.html")
with open(rst_path, "w", encoding="utf-8") as fl:
    fl.write(html_table)

