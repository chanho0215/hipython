# 투자보고서작성시스템

PDF와 스크린샷의 흐름도를 기준으로 만든 `Streamlit + Meilisearch + yfinance + ChatOpenAI` 투자보고서 생성 시스템입니다.

## 구성

- `app.py`: 웹 인터페이스와 전체 오케스트레이션
- `검색_인덱싱준비.ipynb`: Meilisearch 인덱싱 준비 노트북
- `search/stock_search.py`: Meilisearch 기반 종목 검색
- `search/bootstrap_meilisearch.py`: NASDAQ 종목 인덱스 적재 스크립트
- `stock_info/stock_info.py`: `yfinance` 기반 기본정보와 분기 재무 수집
- `report_service/investment_report.py`: ChatOpenAI 기반 투자 보고서 생성
- `.env.example`: 환경변수 예시
- `requirements.txt`: 실행 의존성

## 설치

```bash
pip install -r requirements.txt
```

## 환경변수

`.env.example`을 참고해 `.env`를 준비합니다.

- `OPENAI_API_KEY`: 필수
- `OPENAI_MODEL`: 기본값 `gpt-4o`
- `MEILISEARCH_URL`, `MEILISEARCH_MASTER_KEY`, `MEILISEARCH_INDEX`: 검색엔진 사용 시 필요

## Meilisearch 인덱스 준비

```bash
python search/bootstrap_meilisearch.py
```

이 스크립트는 NASDAQ Trader 목록을 내려받아 `nasdaq` 인덱스에 적재합니다.

## 실행

```bash
streamlit run app.py
```

## Meilisearch 오류 메모

`Index nasdaq not found`가 뜨면 아직 인덱스가 만들어지지 않은 상태입니다.

```bash
cd c:\Users\Admin\hipython\llm\투자보고서작성시스템
python search/bootstrap_meilisearch.py
```

실행 후에도 계속 실패하면 `hipython/llm/.env`의 `MEILISEARCH_URL`, `MEILISEARCH_MASTER_KEY`, `MEILISEARCH_INDEX` 값을 확인합니다.

## 서비스 흐름

1. 회사명 또는 키워드 입력
2. Meilisearch로 검색 쿼리 전송
3. 관련 종목 후보 반환
4. 웹 인터페이스가 선택 목록 제공
5. 특정 종목 선택
6. `yfinance`로 기본 정보 및 재무 데이터 요청
7. 데이터 반환
8. 보고서 생성 버튼 클릭
9. ChatOpenAI에 수집 데이터 전달 및 분석 요청
10. 완성된 투자 보고서 반환
11. 최종 결과 화면 출력
