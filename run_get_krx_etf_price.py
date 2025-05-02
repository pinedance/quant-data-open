# -*- coding: utf-8 -*-

#%%
from os import path
import pandas as pd
from tDate import setup_date_range
from tIO import load_old_etf_data, fetch_tickers, save_etf_data
from tFinance import collect_etf_data, process_price_status
from tTable import check_fill_nan
from message import send_telegram_message, notice_price_status
from cons import config_gsheet_tickers_req_krx as config_tickers_req
from cons import delta_days, data_url

#%% ETF 데이터 수집 관련 설정
OUTPUT_PATH = path.join("dist", "KRX", "etf-price-selected.html")

#%% 날짜 범위 설정
day_start, _day_end = setup_date_range(delta_days)
print(f"Start date: {day_start}")

#%% 티커 정보 가져오기
tickers_req_url = "https://docs.google.com/spreadsheets/d/{sheet_id}/gviz/tq?tqx=out:csv&sheet={sheet_name}".format(
    **config_tickers_req)
etf_tickers = fetch_tickers(tickers_req_url)
etf_tickers = ["{:06d}".format(int(tk)) for tk in etf_tickers]

#%% For test
# print("!!! TEST MODE !!!")
# etf_tickers = etf_tickers[:10]

#%% ETF 데이터 수집 및 검증
try:
    old_etf_data = load_old_etf_data(data_url["krx_last"])
    etf_data_raw = collect_etf_data(etf_tickers, day_start, old_etf_data, src="krx")

    # 데이터 검증
    if not etf_data_raw:
        error_msg = "No ETF data could be collected"
        send_telegram_message(error_msg)
        raise ValueError(error_msg)
    
    if len(etf_data_raw) != len(etf_tickers):
        missing_count = len(etf_tickers) - len(etf_data_raw)
        send_telegram_message(f"Warning: {missing_count} tickers failed to collect data")

except Exception as e:
    error_msg = f"Error during ETF data collection: {str(e)}"
    send_telegram_message(error_msg)
    raise

#%% 티커 이름 정보 가져오기
try:
    tickers_all_url = "https://pinedance.github.io/quant-data-open/dist/CompanyList.json"
    tickers_all_df = pd.read_json(tickers_all_url)
    tickers_all_df.columns = ["ticker", "name", "group"]
    ticker_all_dict = tickers_all_df.set_index('ticker')['name'].to_dict()
except Exception as e:
    error_msg = f"Error fetching ticker names: {str(e)}"
    send_telegram_message(error_msg)
    ticker_all_dict = None

#%% 가격 상태 분석
status_results = process_price_status(etf_tickers, etf_data_raw)
for status in status_results:
    notice_price_status(status, tickers=ticker_all_dict)

#%% 데이터 처리 및 저장
try:
    _etf_data = pd.concat(etf_data_raw, axis=1)
    _etf_data.index = _etf_data.index.date
    _etf_data.columns = ["A{}".format(ticker) for ticker in etf_tickers]
    etf_data = check_fill_nan(_etf_data)
    etf_data = etf_data.astype('float64')

    if save_etf_data(etf_data, OUTPUT_PATH):
        send_telegram_message("업데이트 완료: KRX ETF PRICE")

except Exception as e:
    error_msg = f"Error during data processing and saving: {str(e)}"
    send_telegram_message(error_msg)
    raise