# -*- coding: utf-8 -*-
# pip -q install finance-datareader

# %%
import pandas as pd
import json
from core.tFinance import fin_data
from core.paths import get_data_path, ensure_output_dirs

# %%
YEARS = 5

# %%
day_end = pd.Timestamp.today().date()
day_start = day_end - pd.DateOffset(months=(YEARS * 12 + 1))
print(day_start, day_end)

# %%
us_data = fin_data("SPY", day_start, day_end, src="yahoo")

# %%
kr_data = fin_data("069500", day_start, day_end, src="krx")

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
ensure_output_dirs()
rst_path = get_data_path("misc.json")
with open(rst_path, "w", encoding="utf-8") as fl:
    json.dump(rst, fl, ensure_ascii=False)

# %%
