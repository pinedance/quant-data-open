# 의존성 관리

## 프로젝트 의존성

이 프로젝트의 모든 의존성은 `pyproject.toml`에 명시되어 있습니다.

## 설치 방법

```bash
# uv를 사용한 의존성 설치
uv sync

# 개발 의존성 포함 설치
uv sync --all-extras
```

## 의존성 목록

### 데이터 수집
- **finance-datareader** (>=0.9.50): 한국 금융 데이터 수집
- **yfinance** (>=0.2.59): Yahoo Finance 데이터 수집
- **requests** (>=2.31.0): HTTP 요청

### 데이터 처리
- **pandas** (>=2.0.0): 데이터 분석 및 처리
- **numpy** (>=1.24.0): 수치 연산

### 웹 스크래핑
- **beautifulsoup4** (>=4.12.0): HTML 파싱
- **lxml** (>=4.9.0): BeautifulSoup용 파서

### 템플릿 & 설정
- **jinja2** (>=3.1.2): HTML 템플릿 엔진
- **pyyaml** (>=6.0.1): YAML 설정 파일 파싱

### 유틸리티
- **python-dotenv** (>=1.0.0): 환경변수 관리
- **tqdm** (>=4.66.0): 진행률 표시

### 시각화 (선택)
- **plotly** (>=5.18.0): 인터랙티브 차트 (향후 사용 예정)

## 개발 의존성

```bash
uv sync --extra dev
```

- **jupyter** (>=1.0.0): 노트북 환경
- **autopep8** (>=2.0.2): 코드 포매팅

## 의존성 업데이트

```bash
# 의존성 최신 버전으로 업데이트
uv sync --upgrade

# 특정 패키지만 업데이트
uv sync --upgrade-package pandas
```

## 의존성 추가

새로운 라이브러리를 추가할 때:

1. `pyproject.toml`의 `dependencies`에 추가
2. `uv sync` 실행
3. 정상 동작 확인 후 커밋

## 버전 고정

`uv.lock` 파일이 정확한 의존성 버전을 관리합니다.
이 파일은 git에 포함되어 모든 환경에서 동일한 버전을 사용하도록 보장합니다.

## 문제 해결

### 의존성 충돌 시
```bash
# 캐시 삭제 후 재설치
uv cache clean
uv sync
```

### 특정 버전 설치가 필요한 경우
`pyproject.toml`에서 버전을 정확히 지정:
```toml
dependencies = [
    "pandas==2.0.3",  # 특정 버전
]
```
