# app

Next.js App Router 기준으로 웹 앱이 실제로 시작되는 폴더입니다.

여기서 보면 되는 파일은 크게 두 갈래입니다.

- `page.tsx`
  전체 화면 흐름을 잡는 메인 페이지
- `layout.tsx`, `globals.css`
  공통 레이아웃과 전역 스타일
- `api/`
  브라우저에서 호출하는 서버 API

처음 구조를 볼 때는 `page.tsx`를 먼저 보고, 그 다음 `api/`로 내려가면 흐름이 잘 잡힙니다.
