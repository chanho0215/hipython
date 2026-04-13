"use client"

import { cn } from "@/lib/utils"

interface Props {
  show: boolean
  message?: string
  /** "overlay" = 부모 기준 절대 포지션 (relative 부모 필요)
   *  "fixed"   = 뷰포트 전체 덮음 (브리핑 생성 등) */
  variant?: "overlay" | "fixed"
}

export function LoadingOverlay({ show, message = "처리 중입니다", variant = "overlay" }: Props) {
  if (!show) return null

  return (
    // spinner 하나보다 "지금 기다리는 중"이라는 체감이 더 잘 드는 방향으로 구성했다.
    <div
      className={cn(
        "inset-0 z-50 flex items-center justify-center",
        variant === "fixed" ? "fixed" : "absolute",
        "bg-background/80 backdrop-blur-sm transition-all duration-300 animate-in fade-in"
      )}
    >
      <div className="flex flex-col items-center gap-4 px-8 py-7 bg-card border border-border rounded-2xl shadow-xl">
        {/* 얇은 진행 바를 먼저 보여 주면 화면이 멈춘 느낌이 덜하다. */}
        <div className="w-48 h-1 bg-muted rounded-full overflow-hidden">
          <div className="h-full bg-primary rounded-full origin-left animate-progress" />
        </div>

        {/* 점 애니메이션은 버튼 안 스피너와 리듬을 맞춰 둔 정도의 장식이다. */}
        <div className="flex items-center gap-1.5">
          <span className="w-1.5 h-1.5 rounded-full bg-primary animate-bounce [animation-delay:0ms]" />
          <span className="w-1.5 h-1.5 rounded-full bg-primary animate-bounce [animation-delay:150ms]" />
          <span className="w-1.5 h-1.5 rounded-full bg-primary animate-bounce [animation-delay:300ms]" />
        </div>

        <p className="text-sm font-medium text-foreground">{message}</p>
      </div>
    </div>
  )
}

/** 버튼 내부에 들어가는 인라인 스피너 */
export function ButtonSpinner() {
  return (
    // 버튼 안에서는 높이를 거의 건드리지 않는 작은 스피너가 편하다.
    <span className="inline-flex items-center gap-1.5">
      <span className="w-1 h-1 rounded-full bg-current animate-bounce [animation-delay:0ms]" />
      <span className="w-1 h-1 rounded-full bg-current animate-bounce [animation-delay:120ms]" />
      <span className="w-1 h-1 rounded-full bg-current animate-bounce [animation-delay:240ms]" />
    </span>
  )
}
