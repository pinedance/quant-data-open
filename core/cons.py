from core.config import ConfigManager

# Load ConfigManager singleton
_config = ConfigManager()
_constants = _config.get_constants()

# ==============================================================================
# 1. Migrated Operational Configuration Parameters (from config.yaml)
# ==============================================================================

# 5년 + buffer
delta_months = _constants.get("delta_months", 5 * 12 + 1)

# 가격 데이터 처리
PRICE_EMA_SPAN = _constants.get("PRICE_EMA_SPAN", 3)        # 일별 가격 평활화용 EMA span
RECENT_DAYS_COUNT = _constants.get("RECENT_DAYS_COUNT", 300)   # 최근 N일 데이터 저장 파일(raw-300, ema3-300)용

# ECOS API 검색 범위
ECOS_DAILY_FORWARD_DAYS = _constants.get("ECOS_DAILY_FORWARD_DAYS", 5)     # 일별 검색 종료일 여유 (일)
ECOS_DAILY_BACKWARD_DAYS = _constants.get("ECOS_DAILY_BACKWARD_DAYS", 400)  # 일별 검색 시작일 여유 (일)
ECOS_MONTHLY_FORWARD_DAYS = _constants.get("ECOS_MONTHLY_FORWARD_DAYS", 30)  # 월별 검색 종료일 여유 (일)
ECOS_DATA_START_MONTH = _constants.get("ECOS_DATA_START_MONTH", "200301")  # 월별 ECOS 데이터 수집 시작 년월

# From KRX
config_gsheet_tickers_req_krx = _constants.get("config_gsheet_tickers_req_krx", {
    "sheet_id": '1UqlIF8aXCsRhGYPHttIgtgVDNbyUJOtOmEsM4u3q5H0',
    "sheet_name": 'TICKERS_REQ'
})

# From Yahoo Finance
config_gsheet_tickers_req_yh = _constants.get("config_gsheet_tickers_req_yh", {
    "sheet_id": '12zl9KtKP2QaQYvykZ7ABk30jrjuqP4KrcRiWbzn7eII',
    "sheet_name": 'TICKERS_REQ'
})

data_url = _constants.get("data_url", dict(
    kr_ticker_list = "https://pinedance.github.io/quant-data-open/dist/CompanyList.html",
    yh_last = "http://pinedance.github.io/quant-data-open/dist/US/stocks/price/D/raw.html",
    krx_last = "http://pinedance.github.io/quant-data-open/dist/KR/stocks/price/D/raw.html",
    misc = "https://pinedance.github.io/quant-data-open/dist/misc.html"
))

# From Yahoo Finance (Alternative)
config_gsheet_tickers_req_yh2 = _constants.get("config_gsheet_tickers_req_yh2", {
    "sheet_id": '1rG145KyiClJYEFjUlMnLv4emMNZrx5QM8jUuLXEUVdI',
    "sheet_name": 'TICKERS_REQ'
})

# KR일평균수출액
# https://docs.google.com/spreadsheets/d/177UKIW05FImgOxOtaTeRBP-av_wFb5jCQIPkpkXpMJ8
config_gsheet_average_daily_exports_kr = _constants.get("config_gsheet_average_daily_exports_kr", {
    "sheet_id": '177UKIW05FImgOxOtaTeRBP-av_wFb5jCQIPkpkXpMJ8',
    "sheet_name": 'AaverageDailyExportsKR'
})

# Financial Model Parameters
MA_SHORT_WINDOW = _constants.get("MA_SHORT_WINDOW", 5)       # 단기 이동평균선 범위 (일)
MA_LONG_WINDOW = _constants.get("MA_LONG_WINDOW", 200)      # 장기 이동평균선 범위 (일)

# Alarm & Warning Parameters
SIGMA_THRESHOLD = _constants.get("SIGMA_THRESHOLD", 2.5)     # 가격 상태 알림 sigma 임계값
SUCCESS_RATE_WARNING_THRESHOLD = _constants.get("SUCCESS_RATE_WARNING_THRESHOLD", 0.5)  # 신규 다운로드 성공률 경고 기준

# Crawler Performance Controls
MAX_WORKER_THREADS = _constants.get("MAX_WORKER_THREADS", 20)   # 병렬 다운로드 최대 스레드 수

# Analytical Scope
MISC_HISTORY_YEARS = _constants.get("MISC_HISTORY_YEARS", 5)    # 기타 통계 데이터 수집 대상 년수

# Naver Economy Queue Crawler Configuration
NAVER_ECONOMY_QUEUE = _constants.get("naver_economy_queue", [])

# RSI Configuration
RSI_PERIOD = _constants.get("RSI_PERIOD", 14)               # RSI 기간
RSI_SIGNAL_PERIOD = _constants.get("RSI_SIGNAL_PERIOD", 9)  # RSI 시그널 기간 (EMA span)


# ==============================================================================
# 2. Fixed System Logic Constants (Rarely / Never Change)
# ==============================================================================

# ECOS Daily Search Codes
ecos_search_codes_daily = _constants.get("ecos_search_codes_daily", [])

# ECOS Monthly Search Codes
ecos_search_codes_monthly = _constants.get("ecos_search_codes_monthly", [])

# Telegram Message Boundary separator width
MSG_SEPARATOR_WIDTH = _constants.get("MSG_SEPARATOR_WIDTH", 20)

# Data verification minimum fallback point
MIN_DATA_POINTS = _constants.get("MIN_DATA_POINTS", 30)

# Calendar standards
WEEKS_PER_YEAR = _constants.get("WEEKS_PER_YEAR", 52)
