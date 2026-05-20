# Quant Data Open

퀀트 투자를 위한 기본 데이터를 수집하고 제공하는 저장소입니다.

## ⚠️ 면책 조항

- 본 저장소는 개인 공부 및 연구 목적으로 운용되고 있습니다
- 데이터는 공개된 온라인 자료를 수집하여 가공한 것입니다
- **데이터의 정확성을 보증하지 않습니다**
- **데이터 사용에 따른 모든 책임은 사용자 본인에게 있습니다**
- 개인적이고 비상업적인 목적으로만 사용하시기를 권장합니다

---

## 🚀 시작하기

### 요구사항

- Python 3.12+
- [uv](https://docs.astral.sh/uv/) (패키지 매니저)

### 설치

```bash
git clone https://github.com/pinedance/quant-data-open.git
cd quant-data-open
uv sync
```

### 환경 설정

`.env` 파일을 생성하고 API 키를 입력합니다:

```bash
# .env
ECOS_KEY="your_ecos_api_key_here"
```

**API 키 발급**:
- `ECOS_KEY`: [한국은행 경제통계시스템](https://ecos.bok.or.kr/) 회원가입 후 발급

### 빌드

`output/` 디렉토리의 데이터(git에 포함)로 바로 사이트를 빌드할 수 있습니다:

```bash
uv run build.py
```

빌드 결과는 `public/dist/`에 생성됩니다. 로컬에서 확인하려면:

```bash
python -m http.server 8000 --directory public
# http://localhost:8000/dist/ 에서 확인
```

### 데이터 수집 (선택)

최신 데이터를 직접 수집하려면 각 스크립트를 실행합니다:

```bash
# 국내 ETF 가격
uv run scripts/get_kr_price_krx.py
uv run scripts/get_kr_price_nv.py

# 해외 ETF 가격
uv run scripts/get_us_price_yh.py

# 경기 지표
uv run scripts/get_kr_data_ecos_daily.py   # ECOS_KEY 필요
uv run scripts/get_kr_data_ecos_monthly.py  # ECOS_KEY 필요
uv run scripts/get_kr_data_nv.py
uv run scripts/get_us_data_yh.py
```

---

## 📊 제공 데이터

### 상장 주식

**국내 상장 주식 목록** (현재 기준)
- 전체: [Table](https://pinedance.github.io/quant-data-open/dist/CompanyList.html) | [JSON](https://pinedance.github.io/quant-data-open/dist/CompanyList.json)

### ETF 가격 데이터

**국내 ETF 가격** (종가, 약 1.5년)
- 일간 (KRX): [Table](https://pinedance.github.io/quant-data-open/dist/KR/stocks/price/D/raw.html)
- 일간 (Naver): [Table](https://pinedance.github.io/quant-data-open/dist/KR/stocks/price/D/raw-nv.html)
- 일간 EMA3: [Table](https://pinedance.github.io/quant-data-open/dist/KR/stocks/price/D/ema3.html)
- 월간 (현재): [Table](https://pinedance.github.io/quant-data-open/dist/KR/stocks/price/M/raw-current.html)
- 월간 (월말): [Table](https://pinedance.github.io/quant-data-open/dist/KR/stocks/price/M/raw-eom.html)
- 월간 EMA3 (현재): [Table](https://pinedance.github.io/quant-data-open/dist/KR/stocks/price/M/ema3-current.html)
- 월간 EMA3 (월말): [Table](https://pinedance.github.io/quant-data-open/dist/KR/stocks/price/M/ema3-eom.html)

**국내 ETF MACD 시그널** (월간)
- Raw Histogram: [Table](https://pinedance.github.io/quant-data-open/dist/KR/stocks/signals/MACD/M/raw-current-histogram.html)
- Raw Line: [Table](https://pinedance.github.io/quant-data-open/dist/KR/stocks/signals/MACD/M/raw-current-line.html)
- EMA3 Histogram: [Table](https://pinedance.github.io/quant-data-open/dist/KR/stocks/signals/MACD/M/ema3-current-histogram.html)
- EMA3 Line: [Table](https://pinedance.github.io/quant-data-open/dist/KR/stocks/signals/MACD/M/ema3-current-line.html)

**해외 ETF 가격** (종가, 약 1.5년)
- 일간 (Yahoo Finance): [Table](https://pinedance.github.io/quant-data-open/dist/US/stocks/price/D/raw.html)
- 일간 EMA3: [Table](https://pinedance.github.io/quant-data-open/dist/US/stocks/price/D/ema3.html)
- 월간 (현재): [Table](https://pinedance.github.io/quant-data-open/dist/US/stocks/price/M/raw-current.html)
- 월간 (월말): [Table](https://pinedance.github.io/quant-data-open/dist/US/stocks/price/M/raw-eom.html)
- 월간 EMA3 (현재): [Table](https://pinedance.github.io/quant-data-open/dist/US/stocks/price/M/ema3-current.html)
- 월간 EMA3 (월말): [Table](https://pinedance.github.io/quant-data-open/dist/US/stocks/price/M/ema3-eom.html)

**해외 ETF MACD 시그널** (월간)
- Raw Histogram: [Table](https://pinedance.github.io/quant-data-open/dist/US/stocks/signals/MACD/M/raw-current-histogram.html)
- Raw Line: [Table](https://pinedance.github.io/quant-data-open/dist/US/stocks/signals/MACD/M/raw-current-line.html)
- EMA3 Histogram: [Table](https://pinedance.github.io/quant-data-open/dist/US/stocks/signals/MACD/M/ema3-current-histogram.html)
- EMA3 Line: [Table](https://pinedance.github.io/quant-data-open/dist/US/stocks/signals/MACD/M/ema3-current-line.html)

### 경기 지표

**[월간 경기 지표](https://pinedance.github.io/quant-data-open/dist/KR/economy/M/ECOS.html)**
- 국고채 잔액, 환율(달러), 통화량(M2)
- KOSPI/KOSDAQ 종가 및 거래대금
- 경기종합지수(동행/선행 순환변동치)
- 제조업 가동률, 재고율, 설비투자지수
- 수출 금액/물량 지수, 순상품교역조건지수
- 기업경기실사지수(수출/업황/가동률 전망)
- 경제심리지수
- 실업률, 고용률
- 소비자물가지수, 생산자물가지수

**[일간 경기 지표 (ECOS)](https://pinedance.github.io/quant-data-open/dist/KR/economy/D/ECOS.html)** (약 1.5년)
- 시장금리: MMF 7일, 국고채(1년/3년/5년/10년/20년/30년)

**[일간 시장 지표](https://pinedance.github.io/quant-data-open/dist/KR/economy/D/markets.html)** (약 1년)
- 환율(달러-원), 금리(한국/미국 국채 10년)
- 골드(원), 원유(WTI)
- 주식(S&P500, NASDAQ100, KOSPI, KOSDAQ)

**[일간 미국 경제 지표](https://pinedance.github.io/quant-data-open/dist/US/economy/D/data.html)**
- 달러 인덱스(DX-Y), 달러원 환율(KRW=X)

### 기타 데이터

- [일평균 수출액 (월간)](https://pinedance.github.io/quant-data-open/dist/KR/economy/M/average-daily-exports.html)
- 기타: [Table](https://pinedance.github.io/quant-data-open/dist/misc.html) | [JSON](https://pinedance.github.io/quant-data-open/dist/misc.json)

---

## 📈 실시간 지표 링크 (외부)

### 채권

- [금리 | 미국국채 10년](https://m.stock.naver.com/marketindex/bond/US10YT=RR)
- [금리 | 한국국채 10년](https://m.stock.naver.com/marketindex/bond/KR10YT=RR)

### 주식

- 미국: [S&P500](https://m.stock.naver.com/worldstock/index/.INX/total) | [NASDAQ100](https://m.stock.naver.com/worldstock/index/.NDX/total) | [VIX](https://m.stock.naver.com/worldstock/index/.VIX/total)
- 한국: [KOSPI](https://m.stock.naver.com/domestic/index/KOSPI/total) | [KOSDAQ](https://m.stock.naver.com/domestic/index/KOSDAQ/total)

### 원자재 & 환율

- [골드 (원)](https://m.stock.naver.com/marketindex/metals/CMDT_GD)
- [원유 (WTI)](https://m.stock.naver.com/marketindex/energy/CLcv1)
- [환율 | 달러](https://m.stock.naver.com/marketindex/exchange/FX_USDKRW)
- [환율 | 일본엔](https://m.stock.naver.com/marketindex/exchange/FX_JPYKRW)

---

## 📚 데이터 출처 및 참고 링크

### 공공 데이터

**e-나라지표**
- [메인](http://www.index.go.kr) | [수출입동향](http://www.index.go.kr/potal/main/EachDtlPageDetail.do?idx_cd=1066)

**국가통계포털**
- [KOSIS](https://kosis.kr/)

**한국은행**
- [경제통계시스템 (ECOS)](https://ecos.bok.or.kr/): 통화량M2, 물가지수, 경제심리지수, 뉴스심리지수(예정)

**산업통상자원부**
- [수출입 동향](https://www.motie.go.kr/)
- [산업통계 분석시스템 (ISTANS)](https://www.istans.or.kr/mainMenu.do): [경기종합지수](https://www.istans.or.kr/su/newSuTab.do?scode=S99)
- [무역통계 (K-STAT)](https://stat.kita.net/stat/kts/sum/SumImpExpTotalList.screen)

**한국거래소 (KRX)**
- [정보데이터 시스템](http://data.krx.co.kr/)
- [보도자료](http://open.krx.co.kr/contents/OPN/05/05000000/OPN05000000.jsp)

**금융투자협회**
- [전자공시 시스템](https://dis.kofia.or.kr/)
- [펀드 다모아](https://dis.kofia.or.kr/websquare/index.jsp?w2xPath=/wq/damoa/DISFundAnnFundUnit.xml&divisionId=MDIS08006000000000&serviceId=SDIS08006000000)

### 민간 데이터

**FnGuide**
- [Company Guide](https://comp.fnguide.com)
- [FnIndex](http://www.fnindex.co.kr/overview/I/MIS) | [WiseIndex](https://www.wiseindex.com/Index/Index#/WMI500)

**기타**
- [네이버 금융](https://finance.naver.com/)
- [Yahoo Finance](https://finance.yahoo.com/)

---

## 🔧 기술 스택 및 구조

### 프로젝트 구조

```
quant-data-open/
├── core/              # Python 유틸리티 모듈
├── scripts/           # 데이터 수집 스크립트
├── config/            # 설정 파일 (pages.yaml, paths.yaml)
├── templates/         # Jinja2 템플릿
│   ├── layouts/      # 레이아웃 템플릿
│   └── pages/        # 페이지 템플릿
├── DOCS/              # 문서
├── output/            # 생성된 데이터 (git 포함)
│   └── data/         # JSON 데이터 파일
├── public/            # 최종 빌드 결과 (GitHub Pages, git 제외)
│   └── dist/         # 정적 사이트 (HTML, JSON)
└── build.py           # 빌드 스크립트
```

### 빌드 시스템

**템플릿 엔진**: Jinja2
- 설정 기반 페이지 생성 시스템
- `config/pages.yaml` 수정만으로 새 페이지 추가 가능
- 자세한 내용: [ADD_PAGE_GUIDE.md](./DOCS/ADD_PAGE_GUIDE.md)

**빌드 명령**:
```bash
uv run build.py
```

### 자동화 (GitHub Actions)

**데이터 수집 및 배포 자동화**
- 월간 경기지표 업데이트 (매주 금요일)
- 일간 데이터 업데이트 (매일)
- 가격 데이터 업데이트 (매일)
- GitHub Pages 자동 배포

**주요 워크플로우**:
- `.github/workflows/update-data-monthly.yml`: 월간 경기지표
- `.github/workflows/update-data-daily.yml`: 일간 경기지표
- `.github/workflows/update-price-daily.yml`: ETF 가격
- `.github/workflows/deploy.yml`: 사이트 빌드 및 배포

**Fork 후 GitHub Actions 실행 시 필요한 Secrets**:

| Secret | 필수 | 설명 |
|---|---|---|
| `ECOS_KEY` | 필수 | 한국은행 ECOS API 키 |
| `TELEGRAM_BOT_TOKEN` | 선택 | Telegram 알림용 봇 토큰 |
| `TELEGRAM_CHAT_ID` | 선택 | Telegram 알림용 채팅 ID |

> Secrets는 GitHub 저장소 Settings → Secrets and variables → Actions 에서 등록합니다.

### ETF Ticker 관리

국내 ETF는 선별된 ticker만 수집합니다.

**관리 방법**:
- Google Sheets: [KOREA_ETF_TICKERS_FOR_DATA](https://docs.google.com/spreadsheets/d/1UqlIF8aXCsRhGYPHttIgtgVDNbyUJOtOmEsM4u3q5H0/)
- 시트 이름: `TICKERS_REQ`
- Ticker 수정 후 [GitHub Actions](https://github.com/pinedance/quant-data-open/actions)에서 수동 실행 가능

### 환경 변수

`.env` 파일에 필요한 키를 설정합니다 (로컬 실행용).

```bash
# .env
ECOS_KEY="your_ecos_api_key_here"
```

---

## 📄 라이선스

[MIT License](./LICENSE)

Copyright (c) 2024 Junho
