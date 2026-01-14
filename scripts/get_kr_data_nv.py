# URL : https://m.stock.naver.com/
# %%
import pandas as pd
from core.tIO import get_json, save_df_as_tsv
from core.tIO import get_output_path

#%%
OUTPUT_PATH = get_output_path("KR/economy/D", "markets.tsv")

#%%
def get_raw_priceDF(url, keys=["result"]):
    rstDF = pd.DataFrame.from_dict(get_json(url, keys))
    return rstDF


def get_priceDF(url, keys=["result"]):
    rstDF = get_raw_priceDF(url, keys)
    return rstDF.set_index("localDate")[["closePrice"]]

# %%
QUEUE = [
    {
        "name": "환율|달러원",
        "url": "https://m.stock.naver.com/front-api/chart/pricesByPeriod?category=exchange&reutersCode=FX_USDKRW&chartInfoType=marketindex&scriptChartType=areaYear",
        "keys": ["result", "priceInfos"]
    },
    {
        "name": "금리|한국국채10년",
        "url": "https://m.stock.naver.com/front-api/chart/pricesByPeriod?category=bond&reutersCode=KR10YT%3DRR&chartInfoType=governmentBond&scriptChartType=areaYear",
        "keys": ["result", "priceInfos"]
    },
    {
        "name": "금리|미국국채10년",
        "url": "https://m.stock.naver.com/front-api/chart/pricesByPeriod?category=bond&reutersCode=US10YT%3DRR&chartInfoType=governmentBond&scriptChartType=areaYear",
        "keys": ["result", "priceInfos"]
    },
    {
        "name": "골드|원",
        "url": "https://m.stock.naver.com/front-api/chart/pricesByPeriod?category=metals&reutersCode=CMDT_GD&chartInfoType=marketindex&scriptChartType=areaYear",
        "keys": ["result", "priceInfos"]
    },
    {
        "name": "원유|WTI",
        "url": "https://m.stock.naver.com/front-api/chart/pricesByPeriod?category=energy&reutersCode=CLcv1&chartInfoType=futures&scriptChartType=areaYear",
        "keys": ["result", "priceInfos"]
    },
    {
        "name": "주식|S&P500",
        "url": "https://api.stock.naver.com/chart/foreign/index/.INX?periodType=month&range=12",
        "keys": ["priceInfos"]
    },
    {
        "name": "주식|NASDAQ100",
        "url": "https://api.stock.naver.com/chart/foreign/index/.NDX?periodType=month&range=12",
        "keys": ["priceInfos"]
    },
    {
        "name": "KOSPI",
        "url": "https://api.stock.naver.com/chart/domestic/index/KOSPI?periodType=month&range=12",
        "keys": ["priceInfos"]
    },
    {
        "name": "KOSDAQ",
        "url": "https://api.stock.naver.com/chart/domestic/index/KOSDAQ?periodType=month&range=12",
        "keys": ["priceInfos"]
    },
]

# %%
_data_lst = list()

print("Start Downloading Data from <m.stock.naver.com>")
for elem in QUEUE:
    _df = get_priceDF(elem["url"], elem["keys"])
    _data_lst.append(_df)
    print(" - Downloaded:", elem["name"])

print("Data Download is Complete")

# %%
df_D = pd.concat(_data_lst, axis=1)
df_D.columns = [elem["name"] for elem in QUEUE]
df_D.index = pd.to_datetime(df_D.index, format='%Y%m%d')
df_D = df_D.sort_index().astype('float64')


# %%
save_df_as_tsv(df_D, OUTPUT_PATH)
