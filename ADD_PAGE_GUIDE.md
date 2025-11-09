# 새 페이지 추가 가이드

## 🚀 빠른 시작

새 데이터 페이지를 추가하려면 **`config/pages.yaml` 파일만 수정**하면 됩니다!

## 📝 단계별 가이드

### 1단계: 데이터 준비

먼저 `output/data/` 디렉토리에 JSON 파일을 생성합니다:

```bash
# 예: output/data/my_new_data.json
[
  {"id": 1, "name": "Item 1", "value": 100},
  {"id": 2, "name": "Item 2", "value": 200}
]
```

### 2단계: config/pages.yaml에 설정 추가

`config/pages.yaml` 파일을 열고 `pages:` 섹션에 추가:

```yaml
pages:
  # ... 기존 페이지들 ...

  # 새 페이지 추가
  - name: my_new_data              # 파일명 (URL에 사용됨)
    title: "My New Data Table"     # 페이지 제목
    data_file: my_new_data.json    # output/data/ 폴더의 JSON 파일
    template: table                # 템플릿 종류 (table 또는 json)
    columns:                       # 테이블 컬럼 정의
      - key: id                    # JSON의 키
        label: ID                  # 테이블 헤더
      - key: name
        label: Name
      - key: value
        label: Value
```

### 3단계: 빌드 실행

```bash
uv run build.py
```

### 4단계: 결과 확인

다음 파일들이 자동으로 생성됩니다:

- `public/dist/my_new_data.html` - HTML 테이블 페이지
- `public/dist/my_new_data.json` - JSON API 엔드포인트

---

## 🎨 고급 사용법

### 중첩된 JSON 데이터 처리

JSON에 중첩 구조가 있는 경우 `data_key`를 지정:

```json
// output/data/nested_data.json
{
  "metadata": {...},
  "items": [
    {"id": 1, "name": "Item 1"},
    {"id": 2, "name": "Item 2"}
  ]
}
```

```yaml
- name: nested_data
  title: "Nested Data"
  data_file: nested_data.json
  data_key: items          # ← "items" 키의 배열만 사용
  template: table
  columns:
    - key: id
      label: ID
    - key: name
      label: Name
```

### JSON만 생성 (테이블 없이)

HTML 테이블이 필요 없고 JSON만 필요한 경우:

```yaml
- name: api_only_data
  title: "API Only Data"
  data_file: api_data.json
  template: json           # ← table 대신 json 사용
```

---

## ✅ 체크리스트

새 페이지 추가 시 확인사항:

- [ ] `output/data/` 폴더에 JSON 파일이 있는가?
- [ ] `config/pages.yaml`에 설정을 추가했는가?
- [ ] `name`이 다른 페이지와 중복되지 않는가?
- [ ] `columns`의 `key`가 JSON 데이터와 일치하는가?
- [ ] `uv run build.py` 실행 후 에러가 없는가?

---

## 🔧 트러블슈팅

### 페이지가 생성되지 않아요

1. JSON 파일 경로 확인: `output/data/your_file.json`
2. YAML 문법 확인 (들여쓰기 주의)
3. 빌드 로그에서 에러 메시지 확인

### 테이블이 비어있어요

1. `data_key` 확인 (중첩 JSON인 경우)
2. `columns`의 `key`가 실제 JSON 키와 일치하는지 확인
3. JSON 데이터가 배열 형태인지 확인

### 한글이 깨져요

JSON 파일이 UTF-8 인코딩인지 확인하세요.

---

## 📚 참고

- 기존 페이지 예시: `config/pages.yaml`의 `CompanyList`, `misc` 참고
- 범용 템플릿: `templates/pages/generic_table.html.j2`
- 빌드 스크립트: `build.py`
- 경로 설정: `config/paths.yaml`
