# app/api

웹 앱에서 직접 호출하는 API 라우트 폴더입니다.

파일 역할은 아래처럼 나뉩니다.

- `search-companies/route.ts`
  Meilisearch를 이용한 회사 검색
- `load-events/route.ts`
  선택한 기간의 공시와 뉴스 로드
- `generate-briefing/route.ts`
  브리핑 문장 생성

Vercel에 배포하면 이 폴더의 라우트들이 각각 서버 함수처럼 동작합니다.
