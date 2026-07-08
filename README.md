# Quant Data Open - Data Branch (`output`)

이 브랜치는 `quant-data-open` 저장소의 자동화 스크립트가 수집한 **퀀트 분석용 데이터 파일**들을 전용으로 관리하고 제공하는 브랜치입니다.

## 📌 역할 및 의미

1. **관심사의 분리 (Separation of Concerns)**
   * 메인 소스 코드(`main` 브랜치)와 주기적으로 자동 갱신되는 수많은 데이터 파일들을 분리하여, 핵심 코드의 변경 이력(커밋 로그)의 가독성을 보존하고 저장소 커밋 오염을 방지합니다.
2. **GitHub Actions 자동 적재 데이터베이스**
   * GitHub Actions 워크플로우에 의해 매일/매월 주기적으로 크롤링 및 수집되는 ETF 가격 및 경제 지표 파일(JSON, TSV)들이 실시간으로 저장됩니다.
3. **GitHub Pages 빌드 원본**
   * 배포 파이프라인(`deploy.yml`)이 실행될 때, 이 브랜치에 적재된 최신 데이터 파일들을 내려받아 정적 웹 대시보드를 빌드하고 배포합니다.

## 📂 데이터 폴더 구조

* `KR/`: 국내 ETF 종가 데이터 및 한국은행 ECOS 경제 지표 데이터
* `US/`: 해외 ETF 종가 데이터 및 미국 경제 지표 데이터
* `data/`: 공통 통계 및 메타 데이터 파일 (`misc.json` 등)

## ⚙️ 로컬 개발 환경 활용법

메인 소스 코드 브랜치(`main`)에서 로컬 빌드 및 분석 시 이 데이터 브랜치를 `./output` 폴더에 마운트하여 사용합니다.

```bash
# 최초 1회 연동 설정 (main 브랜치 루트 디렉토리에서 실행)
rm -rf output
git worktree add output output
```

로컬 빌드 전 최신 데이터로 업데이트하기:
```bash
cd output
git pull
cd ..
```
