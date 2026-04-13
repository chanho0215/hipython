# event_briefing_tool

상장사 공시와 뉴스를 모아 주간 브리핑을 만드는 프로젝트입니다.

지금 기준으로는 `Next.js` 웹 앱이 메인이고, 예전 Python 수집 도구와 Streamlit 확인용 화면은 `python_tools/` 아래로 분리해 두었습니다.

운영 주소:

- `https://v0-stock-briefing-app.vercel.app/`

## 폴더 한눈에 보기

```text
event_briefing_tool/
├─ app/                 Next.js 화면과 API 라우트
├─ components/          화면 컴포넌트와 공용 UI
├─ hooks/               프론트 보조 훅
├─ lib/                 타입, 날짜 계산, 공용 유틸
├─ public/              아이콘 같은 정적 파일
├─ python_tools/        Python 수집 도구와 Meilisearch 적재 스크립트
├─ styles/              레거시 스타일 파일 보관용 폴더
├─ .env.example         환경 변수 예시
├─ package.json         웹 앱 의존성과 실행 스크립트
└─ README.md            전체 안내
```

각 주요 폴더 안에도 짧은 `README.md`를 넣어 두어서, 처음 볼 때 어디부터 읽으면 되는지 바로 감이 오게 해 두었습니다.

## 어떤 흐름으로 돌아가나

1. 브라우저에서 회사를 검색합니다.
2. `app/api/search-companies`가 Meilisearch에서 회사를 찾습니다.
3. 회사를 고르면 `app/api/load-events`가 공시와 뉴스를 묶어 가져옵니다.
4. `app/api/generate-briefing`이 최종 브리핑 텍스트를 만듭니다.

Python 쪽은 웹 앱과 별개로, 회사 목록을 Meilisearch에 넣거나 예전 수집 흐름을 확인할 때 사용합니다.

## 빠르게 실행하기

### 웹 앱 실행

```bash
corepack pnpm install --config.node-linker=hoisted
corepack pnpm dev
```

브라우저에서 `http://localhost:3000`을 열면 됩니다.

빌드 확인:

```bash
npx next build
```

### Python 도구 실행

먼저 의존성을 설치합니다.

```bash
python -m pip install -r python_tools/requirements.txt
```

자주 쓰는 명령:

```bash
python python_tools/bootstrap_kr_companies_meili.py
streamlit run python_tools/app.py
```

## 환경 변수

`.env.example`를 복사해서 `.env`를 만든 뒤 값을 채우면 됩니다.

```bash
cp .env.example .env
```

PowerShell에서는:

```powershell
Copy-Item .env.example .env
```

기본 예시는 아래와 같습니다.

```bash
OPENAI_API_KEY=
OPENAI_MODEL=gpt-4o
OPENAI_TEMPERATURE=0.3

DART_API_KEY=
NAVER_CLIENT_ID=
NAVER_CLIENT_SECRET=

MEILISEARCH_URL=
MEILISEARCH_API_KEY=
MEILISEARCH_MASTER_KEY=
MEILISEARCH_COMPANY_INDEX=kr_companies
COMPANY_INDEX=kr_companies

DART_LISTED_ONLY=true
PYTHON_SERVICE_URL=
```

메모:

- 웹 앱 검색 API는 보통 `MEILISEARCH_API_KEY`를 사용합니다.
- Meilisearch 인덱스를 넣는 스크립트는 `MEILISEARCH_MASTER_KEY`가 필요합니다.
- `DART_LISTED_ONLY=true`면 티커가 있는 종목만 인덱싱합니다.
- `PYTHON_SERVICE_URL`이 있으면 Next API가 먼저 Python 서비스로 요청을 넘깁니다.

## Vercel 기준 메모

이 프로젝트는 `Vercel + Meilisearch Cloud` 조합을 기준으로 맞춰져 있습니다.

- Vercel
  Next.js 화면과 `app/api/*`
- Meilisearch Cloud
  회사 검색 인덱스
- OpenAI / DART / Naver
  Vercel 환경 변수로 연결

Vercel에 넣는 값은 보통 아래 정도면 됩니다.

```bash
OPENAI_API_KEY=
DART_API_KEY=
NAVER_CLIENT_ID=
NAVER_CLIENT_SECRET=
MEILISEARCH_URL=
MEILISEARCH_API_KEY=
MEILISEARCH_COMPANY_INDEX=kr_companies
COMPANY_INDEX=kr_companies
```

## Meilisearch 인덱싱

Cloud를 쓴다면 `.env`에 Cloud URL과 Admin 또는 Master key를 넣은 뒤 아래 명령을 실행하면 됩니다.

```bash
python python_tools/bootstrap_kr_companies_meili.py
```

이 스크립트는 DART 회사 목록을 읽어서 `corp_code`를 primary key로 `kr_companies` 인덱스를 채웁니다.

## 어디부터 보면 좋은지

- 화면 흐름부터 보고 싶다면 `app/page.tsx`, `components/briefing/`
- API 동작을 보고 싶다면 `app/api/`
- Meilisearch 적재를 보고 싶다면 `python_tools/bootstrap_kr_companies_meili.py`
- 예전 Python 로직까지 보고 싶다면 `python_tools/`
