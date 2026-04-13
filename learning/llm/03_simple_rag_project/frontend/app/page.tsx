"use client";

import Image from "next/image";
import { FormEvent, useEffect, useRef, useState } from "react";

type HealthState = {
  status: "loading" | "ready" | "error";
  message: string;
};

type Message = {
  id: string;
  role: "user" | "assistant";
  content: string;
};

const API_BASE_URL = process.env.NEXT_PUBLIC_RAG_API_BASE_URL ?? "http://127.0.0.1:8765";

const READY_HINTS = [
  "인증 가능한 제품 조건은 무엇인가요?",
  "지원 운영체제와 언어는 무엇인가요?",
  "카드가 연결되지 않으면 어떤 메시지가 나오나요?",
];

function BrandHomeButton({
  compact = false,
  onClick,
}: {
  compact?: boolean;
  onClick: () => void;
}) {
  return (
    <button
      className={`brand-home ${compact ? "brand-home--compact" : ""}`}
      onClick={onClick}
      type="button"
    >
      <span className="brand-mark" aria-hidden="true">
        <Image
          src="/samsung-logo.png"
          alt=""
          width={154}
          height={48}
          className="brand-mark__image"
          priority={false}
        />
      </span>
      <span className="brand-home__copy">
        <strong>삼성전자 고객지원</strong>
        <span>메모리카드 인증 유틸리티 상담 홈</span>
      </span>
    </button>
  );
}

function createMessage(role: Message["role"], content: string): Message {
  // React key와 업데이트 대상을 분리하기 위해
  // 메시지마다 가벼운 고유 id를 붙인다.
  return {
    id: `${role}-${Date.now()}-${Math.random().toString(36).slice(2, 8)}`,
    role,
    content,
  };
}

export default function Home() {
  // health는 "문서 읽는 중 / 준비 완료 / 오류" 같은
  // 앱의 진입 상태를 프론트에서 표현하는 기준이다.
  const [health, setHealth] = useState<HealthState>({
    status: "loading",
    message: "매뉴얼을 읽는 중입니다. 잠시만 기다려주세요...",
  });
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [isStreaming, setIsStreaming] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement | null>(null);
  const abortControllerRef = useRef<AbortController | null>(null);

  useEffect(() => {
    // 첫 진입 시에는 백엔드가 체인을 다 만들 때까지
    // /health를 짧게 폴링하면서 중앙 로딩 화면을 유지한다.
    let cancelled = false;
    let timeoutId: number | undefined;

    const poll = async () => {
      try {
        const response = await fetch(`${API_BASE_URL}/health`, { cache: "no-store" });
        if (!response.ok) {
          throw new Error("백엔드와 연결되지 않았습니다.");
        }

        const nextHealth = (await response.json()) as HealthState;
        if (cancelled) {
          return;
        }

        setHealth(nextHealth);

        if (nextHealth.status === "loading") {
          timeoutId = window.setTimeout(poll, 1200);
        }
      } catch (error) {
        if (cancelled) {
          return;
        }

        setHealth({
          status: "error",
          message: error instanceof Error ? error.message : "백엔드와 연결할 수 없습니다.",
        });
      }
    };

    poll();

    return () => {
      cancelled = true;
      if (timeoutId) {
        window.clearTimeout(timeoutId);
      }
    };
  }, []);

  useEffect(() => {
    // 새 메시지가 붙을 때마다 하단 입력창 위 최신 답변이 보이도록 자동 스크롤한다.
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth", block: "end" });
  }, [messages, isStreaming]);

  const canSubmit = health.status === "ready" && !isStreaming && input.trim().length > 0;

  function resetToHome() {
    abortControllerRef.current?.abort();
    abortControllerRef.current = null;
    setMessages([]);
    setInput("");
    setIsStreaming(false);
  }

  async function streamAnswer(question: string) {
    // 사용자 메시지와 비어 있는 assistant 메시지를 먼저 넣어두고
    // 스트리밍 chunk를 뒤쪽 assistant 메시지에 이어 붙이는 구조다.
    const userMessage = createMessage("user", question);
    const assistantMessage = createMessage("assistant", "");

    setMessages((current) => [...current, userMessage, assistantMessage]);
    setInput("");
    setIsStreaming(true);

    try {
      const controller = new AbortController();
      abortControllerRef.current = controller;

      const response = await fetch(`${API_BASE_URL}/chat`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ question }),
        signal: controller.signal,
      });

      if (!response.ok || !response.body) {
        const detail = await response.text();
        throw new Error(detail || "답변을 불러오지 못했습니다.");
      }

      const reader = response.body.getReader();
      const decoder = new TextDecoder("utf-8");
      let done = false;

      while (!done) {
        const result = await reader.read();
        done = result.done;

        if (!result.value) {
          continue;
        }

        const chunk = decoder.decode(result.value, { stream: !done });
        if (!chunk) {
          continue;
        }

        // assistantMessage.id를 기준으로 같은 말풍선만 계속 갱신하면
        // 타이핑하듯 이어지는 UX를 만들 수 있다.
        setMessages((current) =>
          current.map((message) =>
            message.id === assistantMessage.id
              ? { ...message, content: `${message.content}${chunk}` }
              : message,
          ),
        );
      }
    } catch (error) {
      if (error instanceof Error && error.name === "AbortError") {
        return;
      }

      const fallback =
        error instanceof Error ? error.message : "답변 생성 중 오류가 발생했습니다.";

      setMessages((current) =>
        current.map((message) =>
          message.id === assistantMessage.id ? { ...message, content: fallback } : message,
        ),
      );
    } finally {
      abortControllerRef.current = null;
      setIsStreaming(false);
    }
  }

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const question = input.trim();
    if (!question || !canSubmit) {
      return;
    }

    await streamAnswer(question);
  }

  function handleHintClick(hint: string) {
    // 추천 질문도 결국은 일반 질문과 같은 흐름을 타게 맞춘다.
    if (health.status !== "ready" || isStreaming) {
      return;
    }

    void streamAnswer(hint);
  }

  const showCenteredIntro = messages.length === 0;

  return (
    <div className="app-shell">
      <header className="service-topbar">
        <div className="service-topbar__inner">
          <span>삼성전자서비스 고객지원</span>
          <span>메모리카드 인증 유틸리티 안내</span>
        </div>
      </header>

      <div className="service-breadcrumb">
        <div className="service-breadcrumb__inner">
          <span>고객지원</span>
          <span className="service-breadcrumb__sep">/</span>
          <span>메모리카드</span>
          <span className="service-breadcrumb__sep">/</span>
          <span>인증 유틸리티 상담</span>
        </div>
      </div>

      {/* 첫 질문 전에는 중앙 소개 화면,
          질문 후에는 일반 채팅 스레드 화면으로 전환된다. */}
      <main className={`chat-stage ${showCenteredIntro ? "chat-stage--intro" : "chat-stage--thread"}`}>
        {showCenteredIntro ? (
          <section className="intro-panel">
            <div className="intro-hero">
              <div className="intro-top">
                <BrandHomeButton onClick={resetToHome} />
                <div className="intro-summary">메모리카드 인증 유틸리티 관련 문의를 매뉴얼 기준으로 안내해드립니다.</div>
              </div>

              <div className="support-kicker">고객지원 상담</div>
              <h1>삼성 메모리카드 인증 유틸리티 안내</h1>
              <p className="intro-copy">인증 유틸리티 설치, 실행, 제품 인증 조건과 같은 문의를 빠르게 확인할 수 있도록 정리했습니다.</p>

              {health.status === "loading" ? (
                <div className="status-card">
                  <div className="loader" />
                  <span>{health.message}</span>
                </div>
              ) : null}

              {health.status === "error" ? <div className="error-card">{health.message}</div> : null}

              {health.status === "ready" ? (
                <div className="hint-list">
                  {READY_HINTS.map((hint) => (
                    <button key={hint} className="hint-chip" onClick={() => handleHintClick(hint)} type="button">
                      <span className="hint-chip__label">자주 묻는 질문</span>
                      <span>{hint}</span>
                    </button>
                  ))}
                </div>
              ) : null}
            </div>
          </section>
        ) : (
          <section className="thread-panel">
            <div className="thread-head-card">
              <div className="thread-head">
                <BrandHomeButton compact onClick={resetToHome} />
                <div className="thread-copy">메모리카드 인증 유틸리티 관련 문의를 매뉴얼 기준으로 안내합니다.</div>
              </div>
            </div>

            <div className="message-list">
              {messages.map((message) => (
                <article key={message.id} className={`message message--${message.role}`}>
                  <div className="message-card">
                    <div className="message-label">
                      {message.role === "user" ? "고객 문의" : "상담 안내"}
                    </div>
                    <div className="message-bubble">
                      {message.content || (message.role === "assistant" && isStreaming ? "문의 내용을 확인하고 있습니다..." : "")}
                    </div>
                  </div>
                </article>
              ))}
              <div ref={messagesEndRef} />
            </div>
          </section>
        )}
      </main>

      <footer className="composer-shell">
        <form className="composer" onSubmit={handleSubmit}>
          <textarea
            className="composer-input"
            value={input}
            onChange={(event) => setInput(event.target.value)}
            placeholder={
              health.status === "ready"
                ? "예: 인증 가능한 제품 조건은 무엇인가요?"
                : "문서를 준비하는 동안 잠시 기다려주세요"
            }
            disabled={health.status !== "ready" || isStreaming}
            rows={1}
            onKeyDown={(event) => {
              // Shift+Enter는 줄바꿈,
              // Enter만 누르면 바로 전송되도록 ChatGPT 스타일에 가깝게 맞춘다.
              if (event.key === "Enter" && !event.shiftKey) {
                event.preventDefault();
                if (canSubmit) {
                  void streamAnswer(input.trim());
                }
              }
            }}
          />
          <button className="composer-submit" type="submit" disabled={!canSubmit}>
            문의하기
          </button>
        </form>
      </footer>
    </div>
  );
}
