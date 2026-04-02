# -*- coding: utf-8 -*-

# %%
import pandas as pd
from core.tDate import setup_date_range
from core.tIO import load_prev_price, fetch_tickers, save_df_as_tsv, fetch_prices, get_output_path
from core.tFinance import process_price_status, calculate_macd
from core.tTable import check_fill_nan, post_process_price, resample_monthly
from core.message import send_telegram_message, notice_price_status_batch
from core.cons import config_gsheet_tickers_req_krx as config_tickers_req
from core.cons import delta_months, data_url

# %% ETF 데이터 수집 관련 설정
OUTPUT_PATH_PRICE_D_RAW = get_output_path("KR/stocks/price/D", "raw.tsv")
OUTPUT_PATH_PRICE_D_EMA3 = get_output_path("KR/stocks/price/D", "ema3.tsv")
OUTPUT_PATH_PRICE_D_RAW_300 = get_output_path("KR/stocks/price/D", "raw-300.tsv")
OUTPUT_PATH_PRICE_D_EMA3_300 = get_output_path("KR/stocks/price/D", "ema3-300.tsv")

OUTPUT_PATH_PRICE_M_RAW_EOM = get_output_path("KR/stocks/price/M", "raw-eom.tsv")
OUTPUT_PATH_PRICE_M_EMA3_EOM = get_output_path("KR/stocks/price/M", "ema3-eom.tsv")
OUTPUT_PATH_PRICE_M_RAW_CURRENT = get_output_path("KR/stocks/price/M", "raw-current.tsv")
OUTPUT_PATH_PRICE_M_EMA3_CURRENT = get_output_path("KR/stocks/price/M", "ema3-current.tsv")

# MACD 출력 경로
# daily close price -> monthly current price -> MACD line
OUTPUT_PATH_MACD_LINE_M_RAW_CURRENT = get_output_path("KR/stocks/signals/MACD/M", "raw-current-line.tsv")
# daily close price -> monthly current price -> MACD histogram
OUTPUT_PATH_MACD_HIST_M_RAW_CURRENT = get_output_path("KR/stocks/signals/MACD/M", "raw-current-histogram.tsv")
# daily close price -> daily EMA3 -> monthly current price -> MACD line
OUTPUT_PATH_MACD_LINE_M_EMA3_CURRENT = get_output_path("KR/stocks/signals/MACD/M", "ema3-current-line.tsv")
# daily close price -> daily EMA3 -> monthly current price -> MACD histogram
OUTPUT_PATH_MACD_HIST_M_EMA3_CURRENT = get_output_path("KR/stocks/signals/MACD/M", "ema3-current-histogram.tsv")

# %% 날짜 범위 설정
day_start, _day_end = setup_date_range(delta_months)
print(f"Start date: {day_start}")

# %% 티커 정보 가져오기
tickers_req_url = "https://docs.google.com/spreadsheets/d/{sheet_id}/gviz/tq?tqx=out:csv&sheet={sheet_name}".format(**config_tickers_req)
etf_tickers_ = fetch_tickers(tickers_req_url)
# print(etf_tickers_)

# %%
etf_tickers = list()
for tk_ in etf_tickers_:
    try:
        tk = "{:06d}".format(int(tk_))
    except:
        print(tk_)
        tk = tk_
    etf_tickers.append(tk)
etf_tickers = sorted(etf_tickers)

# %% For test
# print("!!! TEST MODE !!!")
# etf_tickers = etf_tickers[:10]

#%%
etf_tickers_new = ["A{}".format(ticker) for ticker in etf_tickers]

# %% ETF 데이터 수집 및 검증
try:
    prev_price = load_prev_price(data_url["krx_last"])
    price_raw_df = fetch_prices(etf_tickers, day_start, prev_price, src="krx")

    # 데이터 검증
    if price_raw_df.empty:
        send_telegram_message("🚨 ETF 데이터 수집 실패\n수집된 데이터 없음")
        raise ValueError("No ETF data could be collected")

    if len(price_raw_df.columns) != len(etf_tickers):
        missing_count = len(etf_tickers) - len(price_raw_df.columns)
        send_telegram_message(f"⚠️ {missing_count}개 티커 수집 실패")

except Exception as e:
    send_telegram_message(f"🚨 ETF 데이터 수집 오류\n{str(e)}")
    raise

# %% 티커 이름 정보 가져오기
try:
    tickers_all_url = "https://pinedance.github.io/quant-data-open/dist/CompanyList.json"
    tickers_all_df = pd.read_json(tickers_all_url)
    tickers_all_df.columns = ["ticker", "name", "group"]
    ticker_all_dict = tickers_all_df.set_index('ticker')['name'].to_dict()
except Exception as e:
    send_telegram_message(f"⚠️ 티커 이름 로드 실패\n{str(e)}")
    ticker_all_dict = None

# %% 가격 상태 분석
status_results = process_price_status(list(price_raw_df.columns), [price_raw_df[c] for c in price_raw_df.columns])
notice_price_status_batch(status_results, tickers=ticker_all_dict)

# %% 데이터 처리 및 저장
try:
    _price_raw = price_raw_df.rename(columns=lambda c: "A{}".format(c))
    price_raw = check_fill_nan(_price_raw)
    price_raw = price_raw.astype('float64')

    # EMA3 데이터 생성 (datetime index 유지)
    price_ema3 = price_raw.ewm(span=3).mean()

    # 월간 데이터 생성
    price_raw_monthly_eom = resample_monthly(price_raw, method='eom')
    price_ema3_monthly_eom = resample_monthly(price_ema3, method='eom')
    price_raw_monthly_current = resample_monthly(price_raw, method='current')
    price_ema3_monthly_current = resample_monthly(price_ema3, method='current')

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
    save_df_as_tsv(price_raw.tail(300), OUTPUT_PATH_PRICE_D_RAW_300)
    save_df_as_tsv(price_ema3.tail(300), OUTPUT_PATH_PRICE_D_EMA3_300)

    save_df_as_tsv(price_raw_monthly_eom, OUTPUT_PATH_PRICE_M_RAW_EOM)
    save_df_as_tsv(price_ema3_monthly_eom, OUTPUT_PATH_PRICE_M_EMA3_EOM)
    save_df_as_tsv(price_raw_monthly_current, OUTPUT_PATH_PRICE_M_RAW_CURRENT)
    save_df_as_tsv(price_ema3_monthly_current, OUTPUT_PATH_PRICE_M_EMA3_CURRENT)

    save_df_as_tsv(macd_line_raw, OUTPUT_PATH_MACD_LINE_M_RAW_CURRENT)
    save_df_as_tsv(macd_hist_raw, OUTPUT_PATH_MACD_HIST_M_RAW_CURRENT)
    save_df_as_tsv(macd_line_ema3, OUTPUT_PATH_MACD_LINE_M_EMA3_CURRENT)
    save_df_as_tsv(macd_hist_ema3, OUTPUT_PATH_MACD_HIST_M_EMA3_CURRENT)

    send_telegram_message("✅ KRX ETF PRICE 업데이트 완료")

except Exception as e:
    send_telegram_message(f"❌ KRX ETF PRICE 업데이트 실패\n{str(e)}")
    raise
