# event_briefing_tool

국내 상장사 공시와 뉴스를 모아 주간 브리핑을 만드는 프로젝트입니다.

지금 기준의 메인 앱은 `Next.js` 버전입니다. v0/Vercel 쪽에서 만든 웹 앱은 루트에 두고, 예전 Python/Streamlit 코드는 `python_tools/` 아래로 분리해 두었습니다.

운영 주소:

- `https://v0-stock-briefing-app.vercel.app/`

## 현재 구조

- `app/`, `components/`, `hooks/`, `lib/`
  웹 앱 본체. v0/Vercel 기준으로 보는 쪽은 여기입니다.
- `app/api/*`
  회사 검색, 이벤트 로드, 브리핑 생성 API
- `python_tools/`
  Python 수집/가공 로직, Streamlit 보조 앱, Meilisearch 인덱싱 스크립트
- `.env.example`
  로컬 실행용 환경변수 예시

## 빠른 시작

### 1. 저장소 준비

```bash
git clone <your-repo-url>
cd event_briefing_tool
```

### 2. 환경변수 준비

`.env.example`을 복사해서 `.env`를 만들고 값을 채웁니다.

```bash
cp .env.example .env
```

Windows PowerShell이라면:

```powershell
Copy-Item .env.example .env
```

### 3. 웹 앱 실행

```bash
corepack pnpm install --config.node-linker=hoisted
corepack pnpm dev
```

브라우저에서 `http://localhost:3000`을 열면 됩니다.

## 환경변수

기본적으로 아래 값들이 필요합니다.

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

- 앱 검색 API는 `MEILISEARCH_API_KEY`를 우선 읽습니다.
- 인덱스 적재 스크립트는 `MEILISEARCH_MASTER_KEY`가 필요합니다.
- 인덱스 이름은 `kr_companies`로 맞춰 두는 편이 편합니다.
- `DART_LISTED_ONLY=true`면 티커가 있는 종목만 인덱싱합니다.
- `PYTHON_SERVICE_URL`을 쓰면 Next API가 외부 Python 서비스로 먼저 프록시합니다.

## 웹 앱 메모

이 프로젝트에서 보통 먼저 확인하는 쪽은 웹 앱입니다.

프로덕션 빌드 확인:

```bash
npx next build
```

Vercel에 올릴 때는 루트 디렉터리를 이 프로젝트 폴더로 잡으면 됩니다.  
루트에 있는 `app/`, `components/`, `hooks/`, `lib/`, `package.json`이 웹 앱 기준 파일입니다.

## Python 보조 도구

Python 쪽 파일도 같이 쓰려면 의존성을 먼저 설치합니다.

```bash
python -m pip install -r python_tools/requirements.txt
```

권장 패키지:

- `streamlit`
- `pandas`
- `requests`
- `python-dotenv`
- `langchain-core`
- `langchain-openai`
- `meilisearch`

## Meilisearch 인덱싱

Cloud를 쓰는 경우:

1. `.env`의 `MEILISEARCH_URL`을 Cloud URL로 설정
2. `.env`의 `MEILISEARCH_MASTER_KEY`에 Cloud Admin/Master key 입력
3. 아래 스크립트 실행

```bash
python python_tools/bootstrap_kr_companies_meili.py
```

이 스크립트는 DART 회사 목록을 읽어 `corp_code`를 primary key로 사용해 인덱스를 채웁니다.

## Streamlit 보조 앱

Next.js 앱과 별개로 Streamlit 화면이 필요하면 아래 명령으로 띄울 수 있습니다.

```bash
streamlit run python_tools/app.py
```

주로 데이터 수집 로직 확인이나 간단한 로컬 실험용으로 쓰는 편이 낫습니다.

## 배포 메모

현재는 `Vercel + Meilisearch Cloud` 조합을 기준으로 보고 있습니다.

- `Vercel`
  Next.js 앱과 `app/api/*`
- `Meilisearch Cloud`
  회사 검색 인덱스
- `OpenAI / DART / Naver`
  Vercel 환경변수로 연결

Vercel 환경변수에는 보통 아래 값들을 넣습니다.

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

회사 검색 인덱스를 새로 만들 때 primary key는 `corp_code`로 잡으면 됩니다.
