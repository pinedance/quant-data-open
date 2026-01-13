# %%
import os
import datetime as dt
import numpy as np
import pandas as pd
from core.ecos import Ecos
from core.cons import ecos_search_codes_daily as ecos_search_codes
from core.tDate import yyyymm2quarter
from core.tIO import save_df_as_html_table
from core.tIO import get_output_path
from dotenv import load_dotenv

#%%
OUTPUT_PATH_D = get_output_path("KR/economy/D", "ECOS.html")

# %%
# PyblicDataReader : https://github.com/WooilJeong/PublicDataReader
load_dotenv()
service_key = os.getenv("ECOS_KEY")
if service_key is None:
    raise ValueError("!!! There is no Service Key of ECOS API !!!")

api = Ecos(service_key)
print("ECOS API module is Ready.")

# %%
date_delta_f = dt.timedelta(days=5)
date_delta_b = dt.timedelta(days=400)
search_range = dict()
search_range['close_D'] = (dt.datetime.today() + date_delta_f).strftime('%Y%m%d')
search_range['open_D'] = (dt.datetime.today() - date_delta_b).strftime('%Y%m%d')

print("Search Range:", search_range)

# %%
search_opt = dict(
    D=dict(
        주기="D", 검색시작일자=search_range["open_D"], 검색종료일자=search_range["close_D"]
    ),
)

select_cols = ["시점", "값"]

# %%
print(ecos_search_codes)
_data_D = dict()

# %%
for dc in ecos_search_codes:
    data_name = dc["이름"]
    _search_opt = search_opt["D"]
    _data_rp = _data_D
    _df = api.get_statistic_search(**dc["코드"], **_search_opt)
    if _df is None:
        print( "!!! 데이터가 없습니다.", data_name )
        continue
    _data_rp[data_name] = _df[select_cols].set_index(select_cols[0])
    print("* Data Downloaded:", data_name)

#%%
if len(_data_D) == 0:
    raise ValueError("!!! There is no Data Downloaded from ECOS API !!!")

# %%
df_D = pd.concat(list(_data_D.values()), axis=1)
df_D.columns = list(_data_D.keys())
df_D = df_D.astype('float64')


# %%
save_df_as_html_table(df_D, OUTPUT_PATH_D)
