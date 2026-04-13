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
    <div
      className={cn(
        "inset-0 z-50 flex items-center justify-center",
        variant === "fixed" ? "fixed" : "absolute",
        "bg-background/80 backdrop-blur-sm transition-all duration-300 animate-in fade-in"
      )}
    >
      <div className="flex flex-col items-center gap-4 px-8 py-7 bg-card border border-border rounded-2xl shadow-xl">
        {/* Progress bar — YouTube-style */}
        <div className="w-48 h-1 bg-muted rounded-full overflow-hidden">
          <div className="h-full bg-primary rounded-full origin-left animate-progress" />
        </div>

        {/* Dots */}
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
    <span className="inline-flex items-center gap-1.5">
      <span className="w-1 h-1 rounded-full bg-current animate-bounce [animation-delay:0ms]" />
      <span className="w-1 h-1 rounded-full bg-current animate-bounce [animation-delay:120ms]" />
      <span className="w-1 h-1 rounded-full bg-current animate-bounce [animation-delay:240ms]" />
    </span>
  )
}
