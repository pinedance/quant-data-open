# -*- coding: utf-8 -*-

#%%
from os import path
import pandas as pd
from datetime import date
from core.tDate import setup_date_range
from core.tIO import load_old_etf_data, fetch_tickers, save_etf_data
from core.tFinance import collect_etf_data, process_price_status
from core.tTable import check_fill_nan
from core.message import send_telegram_message, notice_price_status
from core.cons import config_gsheet_tickers_req_yh as config_tickers_req
from core.cons import delta_days, data_url

#%% ETF 데이터 수집 관련 설정
OUTPUT_PATH_PRICE_D_RAW = path.join("output", "US", "stocks", "price", "D", "raw.html")
OUTPUT_PATH_PRICE_D_EMA3 = path.join("output", "US", "stocks", "price", "D", "ema3.html")
OUTPUT_PATH_PRICE_M_RAW_EOM = path.join("output", "US", "stocks", "price", "M", "raw-eom.html")
OUTPUT_PATH_PRICE_M_EMA3_EOM = path.join("output", "US", "stocks", "price", "M", "ema3-eom.html")
OUTPUT_PATH_PRICE_M_RAW_CURRENT = path.join("output", "US", "stocks", "price", "M", "raw-current.html")
OUTPUT_PATH_PRICE_M_EMA3_CURRENT = path.join("output", "US", "stocks", "price", "M", "ema3-current.html")

"""
# ADD NEW
## daily close price -> monthly current price -> MACD line
OUTPUT_PATH_MACD_LINE_M_RAW_CURRENT = path.join("output", "US", "stocks", "signals", "MACD", "M", "raw-current-line.html")
## daily close price -> monthly current price -> MACD histogram
OUTPUT_PATH_MACD_HIST_M_RAW_CURRENT = path.join("output", "US", "stocks", "signals", "MACD", "M", "raw-current-histogram.html")
## daily close price -> daily EMA3 -> monthly current price -> MACD line
OUTPUT_PATH_MACD_LINE_M_EMA3_CURRENT = path.join("output", "US", "stocks", "signals", "MACD", "M", "ema3-current-line.html")
## daily close price -> daily EMA3 -> monthly current price -> MACD histogram
OUTPUT_PATH_MACD_HIST_M_EMA3_CURRENT = path.join("output", "US", "stocks", "signals", "MACD", "M", "ema3-current-histogram.html")
"""

#%% 날짜 범위 설정
day_start, _day_end = setup_date_range(delta_days)
print(f"Start date: {day_start}")

#%% 티커 정보 가져오기
tickers_req_url = "https://docs.google.com/spreadsheets/d/{sheet_id}/gviz/tq?tqx=out:csv&sheet={sheet_name}".format(
    **config_tickers_req)
etf_tickers = fetch_tickers(tickers_req_url)
print(f"Total tickers: {len(etf_tickers)}")
print(f"Unique tickers: {len(set(etf_tickers))}")

#%% For test
print("!!! TEST MODE !!!")
etf_tickers = etf_tickers[:10]

#%% ETF 데이터 수집 및 검증
try:
    old_etf_data = load_old_etf_data(data_url["yh_last"])
    etf_data_raw = collect_etf_data(etf_tickers, day_start, old_etf_data)

    # 데이터 검증
    if not etf_data_raw:
        error_msg = f"No ETF data could be collected"
        send_telegram_message(error_msg)
        raise ValueError(error_msg)
    
    if len(etf_data_raw) != len(etf_tickers):
        missing_count = len(etf_tickers) - len(etf_data_raw)
        send_telegram_message(f"Warning: {missing_count} tickers failed to collect data")

except Exception as e:
    error_msg = f"Error during ETF data collection: {str(e)}"
    send_telegram_message(error_msg)
    raise

#%% 가격 상태 분석
status_results = process_price_status(etf_tickers, etf_data_raw)
for status in status_results:
    notice_price_status(status, tickers=None)

#%% 데이터 처리 및 저장
try:
    _etf_data = pd.concat(etf_data_raw, axis=1)
    etf_data = check_fill_nan(_etf_data)
    etf_data = etf_data.astype('float64')

    # EMA3 데이터 생성 (datetime index 유지)
    etf_data_ema3 = etf_data.ewm(span=3).mean()

    # 월간 데이터 생성 - EOM (End of Month) 기준
    etf_data_monthly_lastday = etf_data.resample('ME').last()
    etf_data_ema3_monthly_lastday = etf_data_ema3.resample('ME').last()

    # 데이터의 마지막 날짜 기준
    current_date = etf_data.index[-1].date()
    etf_data_monthly_lastday = etf_data_monthly_lastday[etf_data_monthly_lastday.index.date <= current_date]
    etf_data_ema3_monthly_lastday = etf_data_ema3_monthly_lastday[etf_data_ema3_monthly_lastday.index.date <= current_date]

    # 월간 데이터 생성 - SAMEDAY 기준 (각 월의 current_date.day 이하 최종 데이터)
    current_day = current_date.day
    etf_data_monthly_today = etf_data.resample('ME').apply(
        lambda x: x[x.index.day <= current_day].iloc[-1] if not x[x.index.day <= current_day].empty else None
    )
    etf_data_ema3_monthly_today = etf_data_ema3.resample('ME').apply(
        lambda x: x[x.index.day <= current_day].iloc[-1] if not x[x.index.day <= current_day].empty else None
    )

    # 실제 날짜로 인덱스 교체
    daily_date_df = pd.DataFrame({'date': etf_data.index}, index=etf_data.index)
    monthly_date_df = daily_date_df.resample('ME').apply(
        lambda x: x[x.index.day <= current_day].iloc[-1] if not x[x.index.day <= current_day].empty else None
    )
    etf_data_monthly_today.index = monthly_date_df['date']
    etf_data_ema3_monthly_today.index = monthly_date_df['date']

    # index를 date로 변환 후 저장
    etf_data.index = etf_data.index.date
    etf_data_ema3.index = etf_data_ema3.index.date
    etf_data_monthly_lastday.index = etf_data_monthly_lastday.index.date
    etf_data_ema3_monthly_lastday.index = etf_data_ema3_monthly_lastday.index.date
    etf_data_monthly_today.index = etf_data_monthly_today.index.date
    etf_data_ema3_monthly_today.index = etf_data_ema3_monthly_today.index.date

    # 데이터 저장
    save_etf_data(etf_data, OUTPUT_PATH_PRICE_D_RAW)
    save_etf_data(etf_data_ema3, OUTPUT_PATH_PRICE_D_EMA3)
    save_etf_data(etf_data_monthly_lastday, OUTPUT_PATH_PRICE_M_RAW_EOM)
    save_etf_data(etf_data_ema3_monthly_lastday, OUTPUT_PATH_PRICE_M_EMA3_EOM)
    save_etf_data(etf_data_monthly_today, OUTPUT_PATH_PRICE_M_RAW_CURRENT)
    save_etf_data(etf_data_ema3_monthly_today, OUTPUT_PATH_PRICE_M_EMA3_CURRENT)

    send_telegram_message("업데이트 완료: YAHOO ETF PRICE")

except Exception as e:
    error_msg = f"Error during data processing and saving: {str(e)}"
    send_telegram_message(error_msg)
    send_telegram_message("업데이트 실패: YAHOO ETF PRICE")
    raise
