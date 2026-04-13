import type { Metadata } from "next";
import { Noto_Sans_KR, JetBrains_Mono } from "next/font/google";
import "./globals.css";

// 본문용 한글 폰트와 코드/상태 표현용 모노 폰트를 분리해서
// 채팅 UI가 조금 더 제품 화면처럼 보이게 한다.
const notoSansKr = Noto_Sans_KR({
  variable: "--font-body",
  subsets: ["latin"],
  weight: ["400", "500", "700"],
});

const jetBrainsMono = JetBrains_Mono({
  variable: "--font-mono",
  subsets: ["latin"],
  weight: ["400", "500"],
});

export const metadata: Metadata = {
  title: "삼성 메모리카드 매뉴얼 챗봇",
  description: "매뉴얼 기반 RAG 챗봇 프론트엔드",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="ko" className={`${notoSansKr.variable} ${jetBrainsMono.variable}`}>
      {/* 일부 브라우저 확장 프로그램이 body 속성을 주입해서
          dev 환경 hydration warning이 나는 경우가 있어 완화해둔다. */}
      <body suppressHydrationWarning>{children}</body>
    </html>
  );
}
