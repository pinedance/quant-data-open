# -*- coding: utf-8 -*-
# pip -q install finance-datareader

# %%
import pandas as pd
from tqdm import tqdm
import FinanceDataReader as fdr
from core.cons import config_gsheet_average_daily_exports_kr as config_gsheet1
from core.tIO import get_output_path
from core.tIO import save_df_as_html_table

#%%
OUTPUT_PATH = get_output_path("KR/economy/M", "average-daily-exports.html")

# %%
# 일평균수출액
req_url = "https://docs.google.com/spreadsheets/d/{sheet_id}/gviz/tq?tqx=out:csv&sheet={sheet_name}".format(
    **config_gsheet1)

req_df = pd.read_csv(req_url)
print(req_df.head())

# %%
save_df_as_html_table(req_df, OUTPUT_PATH)
