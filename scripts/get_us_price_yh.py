# -*- coding: utf-8 -*-

#%%
import pandas as pd
from datetime import date
from core.tDate import setup_date_range
from core.tIO import load_prev_price, fetch_tickers, save_df_as_tsv, fetch_prices, get_output_path
from core.tFinance import process_price_status, calculate_macd
from core.tTable import check_fill_nan, post_process_price
from core.message import send_telegram_message, notice_price_status
from core.cons import config_gsheet_tickers_req_yh as config_tickers_req
from core.cons import delta_months, data_url

#%% ETF 데이터 수집 관련 설정
OUTPUT_PATH_PRICE_D_RAW = get_output_path("US/stocks/price/D", "raw.tsv")
OUTPUT_PATH_PRICE_D_EMA3 = get_output_path("US/stocks/price/D", "ema3.tsv")
OUTPUT_PATH_PRICE_M_RAW_EOM = get_output_path("US/stocks/price/M", "raw-eom.tsv")
OUTPUT_PATH_PRICE_M_EMA3_EOM = get_output_path("US/stocks/price/M", "ema3-eom.tsv")
OUTPUT_PATH_PRICE_M_RAW_CURRENT = get_output_path("US/stocks/price/M", "raw-current.tsv")
OUTPUT_PATH_PRICE_M_EMA3_CURRENT = get_output_path("US/stocks/price/M", "ema3-current.tsv")

# MACD 출력 경로
## daily close price -> monthly current price -> MACD line
OUTPUT_PATH_MACD_LINE_M_RAW_CURRENT = get_output_path("US/stocks/signals/MACD/M", "raw-current-line.tsv")
## daily close price -> monthly current price -> MACD histogram
OUTPUT_PATH_MACD_HIST_M_RAW_CURRENT = get_output_path("US/stocks/signals/MACD/M", "raw-current-histogram.tsv")
## daily close price -> daily EMA3 -> monthly current price -> MACD line
OUTPUT_PATH_MACD_LINE_M_EMA3_CURRENT = get_output_path("US/stocks/signals/MACD/M", "ema3-current-line.tsv")
## daily close price -> daily EMA3 -> monthly current price -> MACD histogram
OUTPUT_PATH_MACD_HIST_M_EMA3_CURRENT = get_output_path("US/stocks/signals/MACD/M", "ema3-current-histogram.tsv")

# %% 날짜 범위 설정
day_start, _day_end = setup_date_range(delta_months)
print(f"Start date: {day_start}")

# %% 티커 정보 가져오기
tickers_req_url = "https://docs.google.com/spreadsheets/d/{sheet_id}/gviz/tq?tqx=out:csv&sheet={sheet_name}".format(**config_tickers_req)
etf_tickers = fetch_tickers(tickers_req_url)

# %% For test
# print("!!! TEST MODE !!!")
# etf_tickers = etf_tickers[:10]

# %% ETF 데이터 수집 및 검증
try:
    prev_price = load_prev_price(data_url["yh_last"])
    price_raw_lst = fetch_prices(etf_tickers, day_start, prev_price)

    # 데이터 검증
    if not price_raw_lst:
        error_msg = "No ETF data could be collected"
        send_telegram_message(error_msg)
        raise ValueError(error_msg)

    if len(price_raw_lst) != len(etf_tickers):
        missing_count = len(etf_tickers) - len(price_raw_lst)
        send_telegram_message(f"Warning: {missing_count} tickers failed to collect data")

except Exception as e:
    error_msg = f"Error during ETF data collection: {str(e)}"
    send_telegram_message(error_msg)
    raise

# %% 가격 상태 분석
status_results = process_price_status(etf_tickers, price_raw_lst)
for status in status_results:
    notice_price_status(status, tickers=None)

# %% 데이터 처리 및 저장
try:
    _price_raw = pd.concat(price_raw_lst, axis=1)
    price_raw = check_fill_nan(_price_raw)
    price_raw = price_raw.astype('float64')

    # EMA3 데이터 생성 (datetime index 유지)
    price_ema3 = price_raw.ewm(span=3).mean()

    # 월간 데이터 생성 - EOM (End of Month) 기준
    price_raw_monthly_eom = price_raw.resample('ME').last()
    price_ema3_monthly_eom = price_ema3.resample('ME').last()

    # 데이터의 마지막 날짜 기준
    current_date = price_raw.index[-1].date()
    price_raw_monthly_eom = price_raw_monthly_eom[price_raw_monthly_eom.index.date <= current_date]
    price_ema3_monthly_eom = price_ema3_monthly_eom[price_ema3_monthly_eom.index.date <= current_date]

    # 월간 데이터 생성
    current_day = current_date.day
    price_raw_monthly_current = price_raw.resample('ME').apply(
        lambda x: x[x.index.day <= current_day].iloc[-1] if not x[x.index.day <= current_day].empty else None
    )
    price_ema3_monthly_current = price_ema3.resample('ME').apply(
        lambda x: x[x.index.day <= current_day].iloc[-1] if not x[x.index.day <= current_day].empty else None
    )

    # 실제 날짜로 인덱스 교체
    daily_date_df = pd.DataFrame({'date': price_raw.index}, index=price_raw.index)
    monthly_date_df = daily_date_df.resample('ME').apply(
        lambda x: x[x.index.day <= current_day].iloc[-1] if not x[x.index.day <= current_day].empty else None
    )
    monthly_date_current = monthly_date_df['date']
    price_raw_monthly_current.index = monthly_date_current
    price_ema3_monthly_current.index = monthly_date_current

    # MACD 계산
    macd_line_raw, macd_hist_raw = calculate_macd(price_raw_monthly_current)
    macd_line_ema3, macd_hist_ema3 = calculate_macd(price_ema3_monthly_current)

    # dataframe 후처리
    price_raw = post_process_price(price_raw)
    price_ema3 = post_process_price(price_ema3)
    price_raw_monthly_eom = post_process_price(price_raw_monthly_eom)
    price_ema3_monthly_eom = post_process_price(price_ema3_monthly_eom)
    price_raw_monthly_current = post_process_price(price_raw_monthly_current)
    price_ema3_monthly_current = post_process_price(price_ema3_monthly_current)
    macd_line_raw = post_process_price(macd_line_raw)
    macd_hist_raw = post_process_price(macd_hist_raw)
    macd_line_ema3 = post_process_price(macd_line_ema3)
    macd_hist_ema3 = post_process_price(macd_hist_ema3)

    # 데이터 저장
    save_df_as_tsv(price_raw, OUTPUT_PATH_PRICE_D_RAW)
    save_df_as_tsv(price_ema3, OUTPUT_PATH_PRICE_D_EMA3)
    save_df_as_tsv(price_raw_monthly_eom, OUTPUT_PATH_PRICE_M_RAW_EOM)
    save_df_as_tsv(price_ema3_monthly_eom, OUTPUT_PATH_PRICE_M_EMA3_EOM)
    save_df_as_tsv(price_raw_monthly_current, OUTPUT_PATH_PRICE_M_RAW_CURRENT)
    save_df_as_tsv(price_ema3_monthly_current, OUTPUT_PATH_PRICE_M_EMA3_CURRENT)
    save_df_as_tsv(macd_line_raw, OUTPUT_PATH_MACD_LINE_M_RAW_CURRENT)
    save_df_as_tsv(macd_hist_raw, OUTPUT_PATH_MACD_HIST_M_RAW_CURRENT)
    save_df_as_tsv(macd_line_ema3, OUTPUT_PATH_MACD_LINE_M_EMA3_CURRENT)
    save_df_as_tsv(macd_hist_ema3, OUTPUT_PATH_MACD_HIST_M_EMA3_CURRENT)

    send_telegram_message("업데이트 완료: YAHOO ETF PRICE")

except Exception as e:
    error_msg = f"Error during data processing and saving: {str(e)}"
    send_telegram_message(error_msg)
    send_telegram_message("업데이트 실패: YAHOO ETF PRICE")
    raise
