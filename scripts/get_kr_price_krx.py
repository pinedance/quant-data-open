# -*- coding: utf-8 -*-

from core.cons import data_url, delta_months
from core.cons import config_gsheet_tickers_req_krx as config_tickers_req
from core.message import send_telegram_message
from core.tDate import setup_date_range
from core.tIO import (
    fetch_prices,
    fetch_tickers,
    get_output_path,
    load_prev_price,
    save_df_as_tsv,
)
from core.tTable import check_nans_for_cli, post_process_price

# ETF 데이터 수집 관련 설정
OUTPUT_PATH_PRICE_D_RAW = get_output_path("KR/stocks/price/D", "raw.tsv")


def main():
    # 날짜 범위 설정
    day_start, _day_end = setup_date_range(delta_months)
    print(f"Start date: {day_start}")

    # 티커 정보 가져오기
    tickers_req_url = "https://docs.google.com/spreadsheets/d/{sheet_id}/gviz/tq?tqx=out:csv&sheet={sheet_name}".format(**config_tickers_req)
    etf_tickers_ = fetch_tickers(tickers_req_url)

    etf_tickers = list()
    for tk_ in etf_tickers_:
        try:
            tk = "{:06d}".format(int(tk_))
        except:
            print(tk_)
            tk = tk_
        etf_tickers.append(tk)
    etf_tickers = sorted(etf_tickers)

    # ETF 데이터 수집, 검증, 처리 및 저장
    try:
        prev_price = load_prev_price(data_url["krx_last"])
        price_raw_df, download_warning = fetch_prices(etf_tickers, day_start, prev_price, src="krx")
        if download_warning:
            send_telegram_message(f"⚠️ [KRX] 다운로드 실패: {download_warning}")

        # 데이터 검증
        if price_raw_df.empty:
            send_telegram_message("🚨 ETF 데이터 수집 실패\n수집된 데이터 없음")
            raise ValueError("No ETF data could be collected")

        if len(price_raw_df.columns) != len(etf_tickers):
            missing_count = len(etf_tickers) - len(price_raw_df.columns)
            send_telegram_message(f"⚠️ [KRX] {missing_count}개 티커 수집 실패")

        _price_raw = price_raw_df.rename(columns=lambda c: "A{}".format(c))
        price_raw, nan_warnings = check_nans_for_cli(_price_raw)
        if nan_warnings:
            send_telegram_message("⚠️ [KRX] 데이터 결측치(NaN) 감지 (대시보드 참조)")
        price_raw = post_process_price(price_raw.astype('float64'))
        save_df_as_tsv(price_raw, OUTPUT_PATH_PRICE_D_RAW)

        send_telegram_message("✅ [KRX] 가격 업데이트 완료")

    except Exception as e:
        send_telegram_message(f"❌ [KRX] 가격 업데이트 실패: {str(e)}")
        raise


if __name__ == "__main__":
    main()
