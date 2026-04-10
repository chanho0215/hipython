# 공시/뉴스 이벤트 브리핑 툴 + 공시 원문 파싱

기존 이벤트 브리핑 툴에 **DART 공시 원문 ZIP/XML 다운로드 및 본문 파싱** 기능을 추가한 버전입니다.

## 추가된 기능

- 선택한 공시에 대해 DART 원문 파일 다운로드
- ZIP 내부 XML/HTML 계열 파일 자동 탐색
- 읽기 좋은 본문 텍스트로 정리
- 섹션 단위 발췌 생성
- 원문 발췌를 AI 브리핑 프롬프트에 포함

## 파일

- `app_event_briefing_tool_with_original_filing.py`: Streamlit 앱
- `event_briefing_service_with_original_filing.py`: 데이터 수집, 원문 파싱, AI 브리핑 로직

## 실행

```bash
streamlit run app_event_briefing_tool_with_original_filing.py
```

## 사용 순서

1. 회사 검색
2. 최근 공시/뉴스 수집
3. 공시 이벤트 선택
4. `선택 공시 원문 파싱` 버튼 실행
5. `브리핑 생성` 단계에서 원문 포함 여부 선택
6. AI 브리핑 생성

## 필요 환경변수

- `DART_API_KEY` 또는 `OPENDART_API_KEY`
- `OPENAI_API_KEY`
- `NAVER_CLIENT_ID`, `NAVER_CLIENT_SECRET`는 선택

## 주의

- 공시마다 XML 구조가 달라서 파싱 품질에는 차이가 있을 수 있습니다.
- 현재 버전은 원문 전체의 완벽한 구조 복원이 아니라, 브리핑에 활용할 수 있도록 **본문 텍스트와 섹션 발췌를 안정적으로 추출**하는 방향입니다.
