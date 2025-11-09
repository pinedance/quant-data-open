# -*- coding: utf-8 -*-
# pip -q install finance-datareader

# %%
import pandas as pd
from tqdm import tqdm
import FinanceDataReader as fdr
from core.cons import config_gsheet_average_daily_exports_kr as config_gsheet1
from core.paths import get_output_path, ensure_output_dirs

# %%
# 일평균수출액
req_url = "https://docs.google.com/spreadsheets/d/{sheet_id}/gviz/tq?tqx=out:csv&sheet={sheet_name}".format(
    **config_gsheet1)

req_df = pd.read_csv(req_url)
print(req_df.head())

# %%
html_table = req_df.to_html(na_rep='')

# %%
ensure_output_dirs()
rst_path = get_output_path("M", "average-daily-exports-kr.html")
with open(rst_path, "w", encoding="utf-8") as fl:
    fl.write(html_table)
