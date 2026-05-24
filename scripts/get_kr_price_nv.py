# -*- coding: utf-8 -*-

import time
import pandas as pd
from tqdm import tqdm
import requests
from bs4 import BeautifulSoup
from core.tIO import save_df_as_tsv
from core.cons import config_gsheet_tickers_req_krx as config_tickers_req
from core.cons import delta_months
from core.tIO import get_output_path

OUTPUT_PATH_PRICE_D_RAW = get_output_path("KR/stocks/price/D", "raw-nv.tsv")

def get_price(ticker, days):
    url = f"https://fchart.stock.naver.com/sise.nhn?symbol={ticker}&timeframe=day&count={days}&requestType=0"
    
    # 3회 재시도 및 개별 연결(Session throttling 방지) 적용
    for attempt in range(1, 4):
        try:
            get_result = requests.get(url, timeout=30)
            get_result.raise_for_status()
            
            bs_obj = BeautifulSoup(get_result.content, "xml")
            inf = bs_obj.select('item')
            columns = ['Date', 'Open', 'High', 'Low', 'Close', 'Volume']
            df_inf = pd.DataFrame([], columns=columns, index=range(len(inf)))

            for i in range(len(inf)):
                df_inf.iloc[i] = str(inf[i]['data']).split('|')

            df_inf.index = pd.to_datetime(df_inf['Date'])
            return df_inf.drop('Date', axis=1).astype(float)
            
        except Exception as e:
            print(f"\n⚠️ [{ticker}] {attempt}차 수집 실패: {e}")
            if attempt < 3:
                time.sleep(2)  # 2초 휴식 후 재시도
            else:
                raise RuntimeError(f"Naver fchart fetch failed for {ticker} after 3 attempts")


def main():
    days = delta_months
    days_offset = pd.Timedelta(days, unit="days")
    day_end = pd.Timestamp.today().date()
    day_start = day_end - days_offset
    print("Start Date:", day_start, "End Date:", day_end)

    tickers_req_url = "https://docs.google.com/spreadsheets/d/{sheet_id}/gviz/tq?tqx=out:csv&sheet={sheet_name}".format(
        **config_tickers_req)
    tickers_req_df = pd.read_csv(tickers_req_url)
    etf_tickers = list(sorted(
        ["{:06d}".format(tk) for tk in list(tickers_req_df["TICKER"])]
    ))
    print("Tickers to fetch:", etf_tickers)

    print("Fetching Naver price data...")
    price_raw_lst = []
    for ticker in tqdm(etf_tickers):
        price_raw_lst.append(get_price(ticker.strip(), days)['Close'])

    price_raw = pd.concat(price_raw_lst, axis=1)
    price_raw.index = price_raw.index.date
    price_raw.columns = ["A{}".format(ticker) for ticker in etf_tickers]
    price_raw = price_raw.astype('float64')

    save_df_as_tsv(price_raw, OUTPUT_PATH_PRICE_D_RAW)
    print("Successfully completed Naver price data update.")


if __name__ == "__main__":
    main()
