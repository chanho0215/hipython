import { cn } from "@/lib/utils"
import type { Step } from "@/lib/types"

const STEPS: { key: Step; label: string }[] = [
  { key: "search", label: "회사 선택" },
  { key: "week", label: "주차 선택" },
  { key: "briefing", label: "브리핑 생성" },
]

interface Props {
  current: Step
}

export function StepIndicator({ current }: Props) {
  // Hide on welcome step
  if (current === "welcome") return null

  const currentIdx = STEPS.findIndex((s) => s.key === current)

  return (
    <div className="flex items-center gap-0 mb-6">
      {STEPS.map((step, idx) => {
        const isActive = idx === currentIdx
        const isDone = idx < currentIdx
        const isLast = idx === STEPS.length - 1

        return (
          <div key={step.key} className="flex items-center">
            <div className="flex items-center gap-2">
              <div
                className={cn(
                  "w-6 h-6 rounded-full flex items-center justify-center text-[11px] font-bold transition-all",
                  isActive
                    ? "bg-primary text-primary-foreground"
                    : isDone
                    ? "bg-primary/20 text-primary"
                    : "bg-muted text-muted-foreground"
                )}
              >
                {isDone ? (
                  <svg width="10" height="10" viewBox="0 0 10 10" fill="none">
                    <path d="M2 5.5L4 7.5L8 3" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" />
                  </svg>
                ) : (
                  idx + 1
                )}
              </div>
              <span
                className={cn(
                  "text-xs font-medium transition-colors",
                  isActive ? "text-foreground" : isDone ? "text-muted-foreground" : "text-muted-foreground/50"
                )}
              >
                {step.label}
              </span>
            </div>
            {!isLast && (
              <div
                className={cn(
                  "mx-3 h-px w-8 transition-colors",
                  idx < currentIdx ? "bg-primary/40" : "bg-border"
                )}
              />
            )}
          </div>
        )
      })}
    </div>
  )
}
