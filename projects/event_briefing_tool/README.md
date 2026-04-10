# event_briefing_tool

국내 상장사 공시와 뉴스를 모아 주간 브리핑을 만드는 프로젝트입니다.

지금 기준의 메인 앱은 `Next.js` 버전입니다. 예전 Python/Streamlit 코드는 완전히 버리지는 않았고, 데이터 수집 로직 확인이나 로컬 실험용으로 같이 두고 있습니다.

운영 주소:

- `https://v0-stock-briefing-app.vercel.app/`

## 현재 구조

- `app/`, `components/`, `hooks/`, `lib/`
  Next.js 앱 본체
- `app/api/*`
  회사 검색, 이벤트 로드, 브리핑 생성 API
- `event_weekly_briefing_service.py`, `event_briefing_service_refined.py`
  예전 Python 쪽 수집/가공 로직
- `bootstrap_kr_companies_meili.py`
  Meilisearch 인덱스 적재 스크립트
- `kr_companies_cache.json`
  회사 코드 캐시
- `app.py`
  Streamlit으로 빠르게 확인할 때 쓰는 보조 앱

## 로컬 실행

```bash
corepack pnpm install --config.node-linker=hoisted
corepack pnpm dev
```

브라우저에서 `http://localhost:3000`을 열면 됩니다.

프로덕션 빌드 확인은 아래처럼 하면 됩니다.

```bash
npx next build
```

## 환경변수

기본적으로 아래 값들이 필요합니다.

```bash
OPENAI_API_KEY=
DART_API_KEY=
NAVER_CLIENT_ID=
NAVER_CLIENT_SECRET=

MEILISEARCH_URL=
MEILISEARCH_API_KEY=
MEILISEARCH_MASTER_KEY=
MEILISEARCH_COMPANY_INDEX=kr_companies
COMPANY_INDEX=kr_companies
```

메모:

- 앱 검색 API는 `MEILISEARCH_API_KEY`를 우선 읽습니다.
- 인덱스 적재 스크립트는 `MEILISEARCH_MASTER_KEY`가 필요합니다.
- 인덱스 이름은 `kr_companies`로 맞춰 두는 편이 편합니다.
- `PYTHON_SERVICE_URL`을 쓰면 Next API가 외부 Python 서비스로 먼저 프록시합니다.

## 배포

지금은 `Vercel + Meilisearch Cloud` 조합을 기준으로 보고 있습니다.

- `Vercel`
  Next.js 앱과 `app/api/*`
- `Meilisearch Cloud`
  회사 검색 인덱스
- `OpenAI / DART / Naver`
  Vercel 환경변수로 연결

회사 검색 인덱스를 새로 만들 때 primary key는 `corp_code`로 잡으면 됩니다.

## Meilisearch 인덱싱

캐시 파일을 그대로 올리거나, 아래 스크립트로 다시 적재하면 됩니다.

```bash
python bootstrap_kr_companies_meili.py
```

이 스크립트는 회사 목록을 읽어 `corp_code`를 primary key로 사용해 인덱스를 채웁니다.

## Python 보조 앱

Next.js 앱과 별개로 Streamlit 화면이 필요하면 아래 명령으로 띄울 수 있습니다.

```bash
streamlit run app.py
```

다만 실제 운영 기준으로는 Next.js 쪽을 먼저 보는 편이 맞습니다.
