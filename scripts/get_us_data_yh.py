# %%
import pandas as pd
from tqdm import tqdm
from core.tIO import get_ticker_data, save_df_as_tsv, get_output_path
from core.cons import config_gsheet_tickers_req_yh2 as config_tickers_req
from core.cons import delta_months

# %%
OUTPUT_PATH = get_output_path("US/economy/D", "data.tsv")

#%%
days = delta_months
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
    get_ticker_data(ticker.strip(), day_start, src="yahoo") for ticker in etf_tickers
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
save_df_as_tsv(etf_data, OUTPUT_PATH)