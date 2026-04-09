# 투자 보고서 작성 시스템

`Streamlit + Meilisearch + yfinance + OpenAI` 조합으로 종목 검색, 재무 데이터 확인, 투자 보고서 생성을 한 번에 처리하는 프로젝트입니다.

## 구성

- `app.py`: 메인 Streamlit 앱
- `search/bootstrap_meilisearch.py`: NASDAQ 종목 인덱스 적재 스크립트
- `search/stock_search.py`: Meilisearch 기반 종목 검색
- `stock_info/stock_info.py`: yfinance 기반 기본 정보 및 분기 재무 데이터 조회
- `report_service/investment_report.py`: OpenAI 기반 투자 보고서 생성
- `01_search_engine_setting.ipynb`: Meilisearch 연결 및 검색 테스트 노트북

## 설치

```bash
pip install -r requirements.txt
```

## 환경 변수

`.env.example`를 참고해 `.env` 파일을 준비합니다.

- `OPENAI_API_KEY`: 필수
- `OPENAI_MODEL`: 선택, 기본값 `gpt-4o`
- `OPENAI_TEMPERATURE`: 선택, 기본값 `0.4`
- `MEILISEARCH_URL`: 선택, 기본값 `http://127.0.0.1:7700`
- `MEILISEARCH_MASTER_KEY`: 선택, Meilisearch 접근 키
- `MEILISEARCH_SEARCH_KEY`: 선택, 검색 전용 키
- `MEILISEARCH_INDEX`: 선택, 기본값 `nasdaq`

## Meilisearch 인덱스 준비

```bash
python search/bootstrap_meilisearch.py
```

위 스크립트는 NASDAQ 상장 종목 목록을 내려받아 `nasdaq` 인덱스에 적재합니다.

## 실행

```bash
streamlit run app.py
```

## 사용 흐름

1. 회사명 또는 티커를 검색합니다.
2. 검색 결과에서 종목을 선택하고 데이터를 불러옵니다.
3. 검토 상황, 보고서 목표, 중점 질문을 설정합니다.
4. 기본 정보와 분기 재무 데이터를 확인합니다.
5. AI 투자 보고서를 생성하고 필요하면 마크다운으로 다운로드합니다.

## 문제 해결

- `Index nasdaq not found` 오류가 나오면 `python search/bootstrap_meilisearch.py`를 먼저 실행하세요.
- 검색이 fallback 모드로 동작하면 `.env`의 `MEILISEARCH_URL`, `MEILISEARCH_MASTER_KEY`, `MEILISEARCH_INDEX` 값을 확인하세요.
- 보고서 생성이 실패하면 `OPENAI_API_KEY`가 올바르게 설정되어 있는지 확인하세요.
