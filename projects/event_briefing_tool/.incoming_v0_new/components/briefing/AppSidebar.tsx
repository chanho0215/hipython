"use client"

import { Building2, CalendarRange, FileText, RotateCcw, ChevronRight } from "lucide-react"
import { cn } from "@/lib/utils"
import type { AppState } from "@/lib/types"
import { weekLabel } from "@/lib/date-utils"

const NAV_ITEMS = [
  { key: "search" as const, label: "회사 선택", icon: Building2, step: 1 },
  { key: "week" as const, label: "주차 선택", icon: CalendarRange, step: 2 },
  { key: "briefing" as const, label: "브리핑", icon: FileText, step: 3 },
]

interface Props {
  state: AppState
  onNavigate: (step: AppState["step"]) => void
  onReset: () => void
}

export function AppSidebar({ state, onNavigate, onReset }: Props) {
  const { step, selectedCompany, selectedYear, selectedMonth, selectedWeekNo } = state
  // welcome step is before the nav items, so currentStepIdx will be -1
  const currentStepIdx = NAV_ITEMS.findIndex((n) => n.key === step)

  return (
    <aside className="hidden lg:flex w-56 flex-col bg-sidebar border-r border-sidebar-border shrink-0">
      {/* Logo area */}
      <div className="px-5 py-5 border-b border-sidebar-border">
        <div className="text-xs font-semibold text-sidebar-foreground/50 uppercase tracking-widest">Research Tool</div>
        <div className="mt-1 text-sm font-semibold text-sidebar-primary">공시·뉴스 분석기</div>
      </div>

      {/* Navigation */}
      <nav className="flex-1 px-3 py-4 flex flex-col gap-0.5">
        <div className="text-[10px] font-semibold text-sidebar-foreground/40 uppercase tracking-widest px-2 mb-2">
          분석 단계
        </div>
        {NAV_ITEMS.map((item, idx) => {
          const Icon = item.icon
          const isActive = step === item.key
          const isDone = idx < currentStepIdx
          return (
            <button
              key={item.key}
              onClick={() => onNavigate(item.key)}
              className={cn(
                "w-full flex items-center gap-2.5 px-3 py-2.5 rounded-md text-left transition-colors text-sm",
                isActive
                  ? "bg-sidebar-accent text-sidebar-primary font-semibold"
                  : isDone
                  ? "text-sidebar-foreground/60 hover:bg-sidebar-accent/60 hover:text-sidebar-foreground"
                  : "text-sidebar-foreground/40 cursor-not-allowed"
              )}
              disabled={!isActive && !isDone}
            >
              <div
                className={cn(
                  "w-5 h-5 rounded flex items-center justify-center text-[10px] font-bold shrink-0",
                  isActive
                    ? "bg-sidebar-primary text-sidebar-primary-foreground"
                    : isDone
                    ? "bg-sidebar-accent/80 text-sidebar-foreground/60"
                    : "bg-sidebar-accent/30 text-sidebar-foreground/30"
                )}
              >
                {isDone ? "✓" : item.step}
              </div>
              <span className="truncate">{item.label}</span>
              {isActive && <ChevronRight className="ml-auto w-3.5 h-3.5 opacity-60" />}
            </button>
          )
        })}
      </nav>

      {/* Current selection info */}
      <div className="px-4 py-4 border-t border-sidebar-border space-y-2">
        <div className="text-[10px] font-semibold text-sidebar-foreground/40 uppercase tracking-widest mb-2">
          현재 선택
        </div>
        <div className="space-y-1.5">
          <div className="flex items-start gap-1.5">
            <span className="text-[10px] font-medium text-sidebar-foreground/40 mt-0.5 w-8 shrink-0">회사</span>
            <span className="text-xs text-sidebar-foreground/80 break-all leading-relaxed">
              {selectedCompany ? selectedCompany.corp_name : "선택 전"}
            </span>
          </div>
          {selectedCompany?.stock_code && (
            <div className="flex items-center gap-1.5">
              <span className="text-[10px] font-medium text-sidebar-foreground/40 w-8 shrink-0">코드</span>
              <span className="text-xs font-mono text-sidebar-foreground/60">{selectedCompany.stock_code}</span>
            </div>
          )}
          <div className="flex items-start gap-1.5">
            <span className="text-[10px] font-medium text-sidebar-foreground/40 mt-0.5 w-8 shrink-0">주차</span>
            <span className="text-xs text-sidebar-foreground/80">
              {weekLabel(selectedYear, selectedMonth, selectedWeekNo)}
            </span>
          </div>
        </div>
      </div>

      {/* Reset */}
      <div className="px-3 pb-4">
        <button
          onClick={onReset}
          className="w-full flex items-center justify-center gap-2 text-xs text-sidebar-foreground/40 hover:text-sidebar-foreground/70 transition-colors py-2 rounded-md hover:bg-sidebar-accent/40"
        >
          <RotateCcw className="w-3 h-3" />
          전체 초기화
        </button>
      </div>
    </aside>
  )
}
