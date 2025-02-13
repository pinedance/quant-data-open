# %%
import os
import datetime as dt
import numpy as np
import pandas as pd
from ecos import Ecos
from cons import ecos_search_codes_monthly as ecos_search_codes
from tools import yyyymm2quarter
from dotenv import load_dotenv

# %%
# PyblicDataReader : https://github.com/WooilJeong/PublicDataReader
load_dotenv()
service_key = os.getenv("ECOS_KEY")
if service_key is None:
    raise ValueError("!!! There is no Service Key of ECOS API !!!")

api = Ecos(service_key)
print("ECOS API module is Ready.")

# %%
date_delta = dt.timedelta(days=30)
search_range = dict(
    open_M="200301",
    close_M=(dt.datetime.today() + date_delta).strftime('%Y%m'),
)
search_range["open_Q"] = yyyymm2quarter(search_range["open_M"])
search_range["close_Q"] = yyyymm2quarter(search_range["close_M"])
print("Search Range:", search_range)

# %%
search_opt = dict(
    M=dict(
        주기="M", 검색시작일자=search_range["open_M"], 검색종료일자=search_range["close_M"]
    ),
    Q=dict(
        주기="Q", 검색시작일자=search_range["open_Q"], 검색종료일자=search_range["close_Q"]
    )
)

select_cols = ["시점", "값"]

# %%
# 일평균수출액
# https://docs.google.com/spreadsheets/d/177UKIW05FImgOxOtaTeRBP-av_wFb5jCQIPkpkXpMJ8
# Tab : "DATA"

# %%
print(ecos_search_codes)
_data_M = dict()
_data_Q = dict()

# %%
for dc in ecos_search_codes:
    data_name = dc["이름"]
    _search_opt = search_opt["M"]
    _data_rp = _data_M
    if dc.get("주기") == "Q":
        _search_opt = search_opt["Q"]
        _data_rp = _data_Q
    _df = api.get_statistic_search(**dc["코드"], **_search_opt)
    _data_rp[data_name] = _df[select_cols].set_index(select_cols[0])
    print("Data Downloaded:", data_name)

# %%
df_M = pd.concat(list(_data_M.values()), axis=1)
df_M.columns = list(_data_M.keys())
df_M = df_M.astype('float64')

# %%
df_Q = pd.concat(list(_data_Q.values()), axis=1)
df_Q.columns = list(_data_Q.keys())
df_Q = df_Q.astype('float64')


# %%
html_table = df_M.to_html(na_rep='')
rst_path = os.path.join("dist", "ECOS", "economic-data-monthly.html")
with open(rst_path, "w", encoding="utf-8") as fl:
    fl.write(html_table)

# %%
html_table = df_Q.to_html(na_rep='')
rst_path = os.path.join("dist", "ECOS", "economic-data-quarterly.html")
with open(rst_path, "w", encoding="utf-8") as fl:
    fl.write(html_table)
