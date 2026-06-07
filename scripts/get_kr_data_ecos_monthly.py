# %%
import datetime as dt
import os
import sys

import pandas as pd
from dotenv import load_dotenv

from core.cons import ECOS_DATA_START_MONTH, ECOS_MONTHLY_FORWARD_DAYS
from core.cons import ecos_search_codes_monthly as ecos_search_codes
from core.ecos import Ecos
from core.tDate import yyyymm2quarter
from core.tIO import get_output_path, save_df_as_tsv

#%%
OUTPUT_PATH_M = get_output_path("KR/economy/M", "ECOS.tsv")
OUTPUT_PATH_Q = get_output_path("KR/economy/Q", "ECOS.tsv")

# %%
# PyblicDataReader : https://github.com/WooilJeong/PublicDataReader
load_dotenv()
service_key = os.getenv("ECOS_KEY")
if service_key is None:
    raise ValueError("!!! There is no Service Key of ECOS API !!!")

api = Ecos(service_key)
print("ECOS API module is Ready.")

# %%
date_delta = dt.timedelta(days=ECOS_MONTHLY_FORWARD_DAYS)
search_range = dict(
    open_M=ECOS_DATA_START_MONTH,
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
        try:
            _df = api.get_statistic_search(**dc["코드"], **_search_opt)
        except Exception as e:
            _df = None
            
        # 미래 분기 데이터 미발표 등으로 데이터가 없을 시 최대 4분기 이전까지 순차 검색
        if _df is None:
            close_q = _search_opt["검색종료일자"]
            for attempt in range(4):
                try:
                    year = int(close_q[:4])
                    q = int(close_q[5])
                    print(f"Checking BOK quarterly data for {data_name} at {close_q}...")
                    fallback_opt = _search_opt.copy()
                    fallback_opt["검색종료일자"] = close_q
                    _df = api.get_statistic_search(**dc["코드"], **fallback_opt)
                    if _df is not None and not _df.empty:
                        print(f"✓ Found published quarterly data at {close_q} for {data_name}")
                        break
                except Exception:
                    _df = None
                
                # Step back one quarter
                if q > 1:
                    close_q = f"{year}Q{q-1}"
                else:
                    close_q = f"{year-1}Q4"
    else:
        try:
            _df = api.get_statistic_search(**dc["코드"], **_search_opt)
        except Exception as e:
            print(f"!!! 데이터 수집 실패: {data_name} — {e}")
            continue
            
    if _df is None:
        print("!!! 데이터가 없습니다.", data_name)
        continue
    _data_rp[data_name] = _df[select_cols].set_index(select_cols[0])
    print("Data Downloaded:", data_name)

#%%
if len(_data_M) == 0:
    print("!!! There is no Data Downloaded from ECOS API !!!", "Monthly")
    sys.exit()
else:
    df_M = pd.concat(list(_data_M.values()), axis=1)
    df_M.columns = list(_data_M.keys())
    df_M = df_M.astype('float64')
    save_df_as_tsv( df_M, OUTPUT_PATH_M)

if len(_data_Q) == 0:
    print("!!! There is no Data Downloaded from ECOS API !!!", "Quarterly")
    sys.exit()
else:
    df_Q = pd.concat(list(_data_Q.values()), axis=1)
    df_Q.columns = list(_data_Q.keys())
    df_Q = df_Q.astype('float64')
    save_df_as_tsv(df_Q, OUTPUT_PATH_Q)
