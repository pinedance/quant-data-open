# URL : https://m.stock.naver.com/

import pandas as pd
from core.tIO import get_json, save_df_as_tsv
from core.tIO import get_output_path
from core.cons import NAVER_ECONOMY_QUEUE as QUEUE

OUTPUT_PATH = get_output_path("KR/economy/D", "markets.tsv")

def get_raw_priceDF(url, keys=["result"]):
    rstDF = pd.DataFrame.from_dict(get_json(url, keys))
    return rstDF


def get_priceDF(url, keys=["result"]):
    rstDF = get_raw_priceDF(url, keys)
    return rstDF.set_index("localDate")[["closePrice"]]


def main():
    _data_lst = list()

    print("Start Downloading Data from <m.stock.naver.com>")
    for elem in QUEUE:
        _df = get_priceDF(elem["url"], elem["keys"])
        _data_lst.append(_df)
        print(" - Downloaded:", elem["name"])

    print("Data Download is Complete")

    df_D = pd.concat(_data_lst, axis=1)
    df_D.columns = [elem["name"] for elem in QUEUE]
    df_D.index = pd.to_datetime(df_D.index, format='%Y%m%d')
    df_D = df_D.sort_index().astype('float64')

    save_df_as_tsv(df_D, OUTPUT_PATH)
    print("Successfully completed Naver economic indices update.")


if __name__ == "__main__":
    main()
