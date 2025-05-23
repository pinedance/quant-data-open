delta_days = 800

# From KRX
config_gsheet_tickers_req_krx = {
    "sheet_id": '1UqlIF8aXCsRhGYPHttIgtgVDNbyUJOtOmEsM4u3q5H0',
    "sheet_name": 'TICKERS_REQ'
}

# From Yahoo Finance
config_gsheet_tickers_req_yh = {
    "sheet_id": '12zl9KtKP2QaQYvykZ7ABk30jrjuqP4KrcRiWbzn7eII',
    "sheet_name": 'TICKERS_REQ'
}

data_url = dict(
    kr_ticker_list = "https://pinedance.github.io/quant-data-open/dist/CompanyList.html",
    yh_last = "https://pinedance.github.io/quant-data-open/dist/YH/etf-adjusted-price-selected.html",
    krx_last = "https://pinedance.github.io/quant-data-open/dist/KRX/etf-price-selected.html",
    misc = "https://pinedance.github.io/quant-data-open/dist/misc.html"
)

# From Yahoo Finance
config_gsheet_tickers_req_yh2 = {
    "sheet_id": '1rG145KyiClJYEFjUlMnLv4emMNZrx5QM8jUuLXEUVdI',
    "sheet_name": 'TICKERS_REQ'
}

# KR일평균수출액
# https://docs.google.com/spreadsheets/d/177UKIW05FImgOxOtaTeRBP-av_wFb5jCQIPkpkXpMJ8
config_gsheet_average_daily_exports_kr = {
    "sheet_id": '177UKIW05FImgOxOtaTeRBP-av_wFb5jCQIPkpkXpMJ8',
    "sheet_name": 'AaverageDailyExportsKR'
}


# ECOS
ecos_search_codes_daily = [
    {
        "이름": "시장금리|MMF7일",
        "항목": ["시장금리", "MMF(7일)"],
        "코드": {"통계표코드": "817Y002", "통계항목코드1": "010501000"}
    },
    {
        "이름": "시장금리|국고채(1년)",
        "항목": ["시장금리", "국고채(1년)"],
        "코드": {"통계표코드": "817Y002", "통계항목코드1": "010190000"}
    },
    {
        "이름": "시장금리|국고채(3년)",
        "항목": ["시장금리", "국고채(3년)"],
        "코드": {"통계표코드": "817Y002", "통계항목코드1": "010200000"}
    },
    {
        "이름": "시장금리|국고채(5년)",
        "항목": ["시장금리", "국고채(5년)"],
        "코드": {"통계표코드": "817Y002", "통계항목코드1": "010200001"}
    },
    {
        "이름": "시장금리|국고채(10년)",
        "항목": ["시장금리", "국고채(10년)"],
        "코드": {"통계표코드": "817Y002", "통계항목코드1": "010210000"}
    },
    {
        "이름": "시장금리|국고채(20년)",
        "항목": ["시장금리", "국고채(20년)"],
        "코드": {"통계표코드": "817Y002", "통계항목코드1": "010220000"}
    },
    {
        "이름": "시장금리|국고채(30년)",
        "항목": ["시장금리", "국고채(30년)"],
        "코드": {"통계표코드": "817Y002", "통계항목코드1": "010230000"}
    },
]

ecos_search_codes_monthly = [
    {
        "이름": "국고채|잔액",
        "항목": ["주요 국공채 발행액/잔액", "국고채권", "잔액"],
        "코드": {"통계표코드": "191Y001", "통계항목코드1": "0200000", "통계항목코드2": "4"}
    },
    {
        "이름": "환율|달러",
        "항목": ["원화의 대미달러, 원화의 대위안/대엔 환율", "원/달러(종가)", "말일자료"],
        "코드": {"통계표코드": "731Y006", "통계항목코드1": "0000003", "통계항목코드2": "0000200"}
    },
    {
        "이름": "통화량|M2",
        "항목": ["M2 상품별 구성내역(평잔, 계절조정계열)", "M2(평잔, 계절조정계열)"],
        "코드": {"통계표코드": "101Y003", "통계항목코드1": "BBHS00"}
    },
    {
        "이름": "KOSDAQ|거래대금",
        "항목": ["주식시장(월,년)", "KOSDAQ_거래대금 일평균"],
        "코드": {"통계표코드": "901Y014", "통계항목코드1": "2080000"}
    },
    {
        "이름": "KOSDAQ|종가",
        "항목": ["주식시장(월,년)", "KOSDAQ_종가"],
        "코드": {"통계표코드": "901Y014", "통계항목코드1": "2090000"}
    },
    {
        "이름": "KOSPI|거래대금",
        "항목": ["주식시장(월,년)", "KOSPI_거래대금 일평균"],
        "코드": {"통계표코드": "901Y014", "통계항목코드1": "1060200"}
    },
    {
        "이름": "KOSPI|종가",
        "항목": ["주식시장(월,년)", "KOSPI_종가"],
        "코드": {"통계표코드": "901Y014", "통계항목코드1": "1070000"}
    },
    {
        "이름": "경기종합지수|동행지수순환변동치",
        "항목": ["경기종합지수", "동행지수순환변동치"],
        "코드": {"통계표코드": "901Y067", "통계항목코드1": "I16D"}
    },
    {
        "이름": "경기종합지수|선행지수순환변동치",
        "항목": ["경기종합지수", "선행지수순환변동치"],
        "코드": {"통계표코드": "901Y067", "통계항목코드1": "I16E"}
    },
    {
        "이름": "제조업|가동률",
        "항목": ["제조업 평균가동률", "제조업"],
        "코드": {"통계표코드": "901Y025", "통계항목코드1": "I31A"}
    },
    {
        "이름": "제조업|재고율",
        "항목": ["제조업 재고율", "제조업"],
        "코드": {"통계표코드": "901Y026", "통계항목코드1": "I33A"}
    },
    {
        "이름": "설비투자지수",
        "항목": ["설비투자지수", "계절조정지수"],
        "코드": {"통계표코드": "901Y066", "통계항목코드1": "I15B"}
    },
    {
        "이름": "수출|금액지수",
        "항목": ["수출금액지수", "총지수"],
        "코드": {"통계표코드": "403Y001", "통계항목코드1": "*AA"}
    },
    {
        "이름": "수출|물량지수",
        "항목": ["수출물량지수", "총지수"],
        "코드": {"통계표코드": "403Y002", "통계항목코드1": "*AA"}
    },
    {
        "이름": "순상품교역조건지수",
        "항목": ["교역조건지수", "순상품교역조건지수"],
        "코드": {"통계표코드": "403Y005", "통계항목코드1": "A"}
    },
    {
        "이름": "기업경기실사지수|수출전망",
        "항목": ["기업경기실사지수(매출액가중 전망)", "제조업", "수출전망"],
        "코드": {"통계표코드": "512Y016", "통계항목코드1": "C0000", "통계항목코드2": "BM"}
    },
    {
        "이름": "기업경기실사지수|업황전망",
        "항목": ["기업경기실사지수(매출액가중 전망)", "전산업", "업황전망"],
        "코드": {"통계표코드": "512Y016", "통계항목코드1": "99988", "통계항목코드2": "BA"}
    },
    {
        "이름": "기업경기실사지수|가동률전망",
        "항목": ["기업경기실사지수(매출액가중 전망)", "제조업", "가동률전망"],
        "코드": {"통계표코드": "512Y016", "통계항목코드1": "C0000", "통계항목코드2": "BK"}
    },
    {
        "이름": "경제심리지수",
        "항목": ["경제심리지수", "경제심리지수(순환변동치)"],
        "코드": {"통계표코드": "513Y001", "통계항목코드1": "E2000"}
    },
    {
        "이름": "실업률",
        "항목": ["경제활동인구", "실업률", "계절조정"],
        "코드": {"통계표코드": "901Y027", "통계항목코드1": "I61BC", "통계항목코드2": "I28B"}
    },
    {
        "이름": "고용률",
        "항목": ["경제활동인구", "고용률", "계절조정"],
        "코드": {"통계표코드": "901Y027", "통계항목코드1": "I61E", "통계항목코드2": "I28B"}
    },
    {
        "이름": "소비자물가지수",
        "항목": ["소비자물가지수", "총지수"],
        "코드": {"통계표코드": "901Y009", "통계항목코드1": "0"}
    },
    {
        "이름": "생산자물가지수",
        "항목": ["생산자물가지수(기본분류)", "총지수"],
        "코드": {"통계표코드": "404Y014", "통계항목코드1": "*AA"}
    },
    {
        "이름": "GDP|명목",
        "항목": ["경제활동별 GDP 및 GNI(계절조정, 명목, 분기)", "국내총생산(시장가격, GDP)"],
        "코드": {"통계표코드": "200Y003", "통계항목코드1": "1400"},
        "주기": "Q"
    },
    {
        "이름": "GNI|명목",
        "항목": ["경제활동별 GDP 및 GNI(계절조정, 명목, 분기)", "국민총소득(GNI)"],
        "코드": {"통계표코드": "200Y003", "통계항목코드1": "1600"},
        "주기": "Q"
    },
]
