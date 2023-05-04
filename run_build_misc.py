# -*- coding: utf-8 -*-
# pip -q install finance-datareader

# %%
from os import path
import pandas as pd
import json
import FinanceDataReader as fdr

# %%
YEARS = 5

# %%
day_end = pd.Timestamp.today().date()
day_start = day_end - pd.DateOffset(months=(YEARS * 12 + 1))
print(day_start, day_end)

# %%
us_data = fdr.DataReader("SPY", day_start, day_end)['Close']

# %%
kr_data = fdr.DataReader("069500", day_start, day_end)['Close']

# %%


def count_days_per_week(sr, years):
    last_date = sr.index[-1]
    offset = pd.DateOffset(years=years)
    first_date = last_date - offset
    target_sr = sr[sr.index > first_date]
    days_per_week = len(target_sr) / years / 52
    return days_per_week


# %%
rst = list()

rst.append({
    "key": "days_per_week_in_US",
    "value": count_days_per_week(us_data, years=YEARS)
})

rst.append({
    "key": "days_per_week_in_KR",
    "value": count_days_per_week(kr_data, years=YEARS)
})

print(rst)

# %%
rst_path = path.join("_data", "misc.json")
# rst_path = path.join("dist", "KRX", "etf-price.html")
with open(rst_path, "w", encoding="utf-8") as fl:
    json.dump(rst, fl, ensure_ascii=False)

# %%
