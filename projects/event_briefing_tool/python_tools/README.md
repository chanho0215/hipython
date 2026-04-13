# python_tools

예전 Python 기반 수집 도구와 보조 스크립트를 모아 둔 폴더입니다.

웹 앱이 메인인 지금도 아래 작업 때문에 종종 씁니다.

- Meilisearch 인덱스 다시 만들기
- Streamlit으로 수집 흐름 빠르게 확인하기
- 예전 Python 로직 참고하기

파일 역할:

- `app.py`
  Streamlit 보조 앱
- `event_weekly_briefing_service.py`
  주차 기준 공시와 뉴스 수집, 브리핑 생성
- `event_briefing_service_refined.py`
  회사 검색, 공시 원문 처리, 캐시 생성 같은 저수준 로직
- `bootstrap_kr_companies_meili.py`
  DART 회사 목록을 Meilisearch에 적재
- `kr_companies_cache.json`
  회사 코드 캐시
- `requirements.txt`
  Python 의존성

자주 쓰는 명령:

```bash
python -m pip install -r python_tools/requirements.txt
python python_tools/bootstrap_kr_companies_meili.py
streamlit run python_tools/app.py
```
