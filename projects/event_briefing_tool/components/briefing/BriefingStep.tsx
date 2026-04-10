"use client"

import { useState } from "react"
import {
  ArrowLeft,
  RefreshCcw,
  Download,
  TrendingUp,
  TrendingDown,
  FileText,
  Newspaper,
  Layers,
  AlertCircle,
  CheckCircle2,
  Target,
  BookOpen,
} from "lucide-react"
import { cn } from "@/lib/utils"
import type { AppState, WeeklyBriefing } from "@/lib/types"
import { weekLabel } from "@/lib/date-utils"

interface Props {
  state: AppState
  update: (partial: Partial<AppState>) => void
  onPrev: () => void
  onRestart: () => void
}

interface BriefingSectionProps {
  icon: React.ElementType
  title: string
  items: string[]
  accent?: "default" | "positive" | "negative"
  className?: string
}

function BriefingSection({ icon: Icon, title, items, accent = "default", className }: BriefingSectionProps) {
  const accentStyles = {
    default: {
      header: "text-foreground",
      iconBg: "bg-primary/10 text-primary",
      bullet: "bg-primary/20",
    },
    positive: {
      header: "text-positive",
      iconBg: "bg-positive/10 text-positive",
      bullet: "bg-positive/30",
    },
    negative: {
      header: "text-negative",
      iconBg: "bg-negative/10 text-negative",
      bullet: "bg-negative/30",
    },
  }
  const styles = accentStyles[accent]

  return (
    <div className={cn("bg-card border border-border rounded-lg p-5", className)}>
      <div className="flex items-center gap-2.5 mb-4">
        <div className={cn("w-7 h-7 rounded-md flex items-center justify-center shrink-0", styles.iconBg)}>
          <Icon className="w-4 h-4" />
        </div>
        <h3 className={cn("text-sm font-semibold", styles.header)}>{title}</h3>
      </div>
      {items.length > 0 ? (
        <ul className="space-y-2.5">
          {items.map((item, i) => (
            <li key={i} className="flex items-start gap-2.5">
              <span className={cn("mt-2 w-1.5 h-1.5 rounded-full shrink-0", styles.bullet)} />
              <span className="text-sm text-muted-foreground leading-relaxed">{item}</span>
            </li>
          ))}
        </ul>
      ) : (
        <p className="text-sm text-muted-foreground/50 italic">해당 사항 없음</p>
      )}
    </div>
  )
}

function SplitSection({
  title,
  leftTitle,
  leftItems,
  rightTitle,
  rightItems,
}: {
  title: string
  leftTitle: string
  leftItems: string[]
  rightTitle: string
  rightItems: string[]
}) {
  return (
    <div className="bg-card border border-border rounded-lg p-5">
      <h3 className="text-sm font-semibold text-foreground mb-4">{title}</h3>
      <div className="grid grid-cols-2 gap-4">
        <div>
          <div className="flex items-center gap-1.5 mb-2.5">
            <TrendingUp className="w-3.5 h-3.5 text-positive" />
            <span className="text-xs font-semibold text-positive uppercase tracking-wider">{leftTitle}</span>
          </div>
          {leftItems.length > 0 ? (
            <ul className="space-y-2">
              {leftItems.map((item, i) => (
                <li key={i} className="flex items-start gap-2">
                  <span className="mt-2 w-1.5 h-1.5 rounded-full bg-positive/30 shrink-0" />
                  <span className="text-sm text-muted-foreground leading-relaxed">{item}</span>
                </li>
              ))}
            </ul>
          ) : (
            <p className="text-sm text-muted-foreground/50 italic">해당 없음</p>
          )}
        </div>
        <div className="border-l border-border pl-4">
          <div className="flex items-center gap-1.5 mb-2.5">
            <TrendingDown className="w-3.5 h-3.5 text-negative" />
            <span className="text-xs font-semibold text-negative uppercase tracking-wider">{rightTitle}</span>
          </div>
          {rightItems.length > 0 ? (
            <ul className="space-y-2">
              {rightItems.map((item, i) => (
                <li key={i} className="flex items-start gap-2">
                  <span className="mt-2 w-1.5 h-1.5 rounded-full bg-negative/30 shrink-0" />
                  <span className="text-sm text-muted-foreground leading-relaxed">{item}</span>
                </li>
              ))}
            </ul>
          ) : (
            <p className="text-sm text-muted-foreground/50 italic">해당 없음</p>
          )}
        </div>
      </div>
    </div>
  )
}

export function BriefingStep({ state, update, onPrev, onRestart }: Props) {
  const { selectedCompany, selectedYear, selectedMonth, selectedWeekNo, latestBriefing, latestMarkdown } = state
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const wLabel = latestBriefing?.week_label || weekLabel(selectedYear, selectedMonth, selectedWeekNo)

  const handleRegenerate = async () => {
    if (!selectedCompany) return
    setLoading(true)
    setError(null)
    try {
      const res = await fetch("/api/generate-briefing", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          company_name: selectedCompany.corp_name,
          stock_code: selectedCompany.stock_code,
          week_label: wLabel,
          overview: state.companyOverview,
          disclosures: state.weeklyBundle.disclosures,
          news: state.weeklyBundle.news,
          all_events: state.weeklyBundle.all,
        }),
      })
      const data = await res.json()
      if (!res.ok) throw new Error(data.error || "브리핑 생성에 실패했습니다.")
      update({
        latestBriefing: data.briefing,
        latestMarkdown: data.markdown,
        generatedPeriodKey: [selectedYear, selectedMonth, selectedWeekNo],
      })
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : "알 수 없는 오류가 발생했습니다.")
    } finally {
      setLoading(false)
    }
  }

  const handleDownload = () => {
    if (!latestMarkdown || !selectedCompany) return
    const blob = new Blob([latestMarkdown], { type: "text/markdown;charset=utf-8" })
    const url = URL.createObjectURL(blob)
    const a = document.createElement("a")
    a.href = url
    a.download = `briefing_${selectedCompany.stock_code}_${selectedYear}_${selectedMonth}_${selectedWeekNo}.md`
    a.click()
    URL.revokeObjectURL(url)
  }

  if (!selectedCompany) {
    return (
      <div className="flex items-center gap-3 px-4 py-4 bg-muted/40 rounded-lg border border-border text-sm text-muted-foreground">
        <AlertCircle className="w-4 h-4 shrink-0" />
        먼저 회사와 주차를 선택해 주세요.
      </div>
    )
  }

  const briefing: WeeklyBriefing | null = latestBriefing

  return (
    <div className="space-y-5">
      {/* Header actions */}
      <div className="flex items-start justify-between gap-3">
        <div>
          <h2 className="text-lg font-semibold text-foreground">주간 브리핑</h2>
          <p className="text-sm text-muted-foreground mt-0.5">
            {selectedCompany.corp_name} · {wLabel}
          </p>
        </div>
        <div className="flex items-center gap-2">
          {latestMarkdown && (
            <button
              onClick={handleDownload}
              className="flex items-center gap-1.5 px-3 py-2 text-xs font-medium text-muted-foreground border border-border rounded-lg hover:bg-muted/50 transition-colors"
            >
              <Download className="w-3.5 h-3.5" />
              MD 다운로드
            </button>
          )}
          <button
            onClick={handleRegenerate}
            disabled={loading}
            className="flex items-center gap-1.5 px-3 py-2 text-xs font-semibold text-primary border border-primary/30 rounded-lg hover:bg-primary/5 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
          >
            <RefreshCcw className={cn("w-3.5 h-3.5", loading && "animate-spin")} />
            {loading ? "생성 중..." : "다시 생성"}
          </button>
        </div>
      </div>

      {/* Error */}
      {error && (
        <div className="flex items-start gap-2.5 px-4 py-3 bg-destructive/10 border border-destructive/20 rounded-lg text-sm text-destructive">
          <AlertCircle className="w-4 h-4 mt-0.5 shrink-0" />
          {error}
        </div>
      )}

      {briefing ? (
        <div className="space-y-4">
          {/* Hero summary card */}
          <div className="bg-primary rounded-xl px-6 py-5 text-primary-foreground">
            <div className="text-xs font-semibold uppercase tracking-widest opacity-60 mb-2">{wLabel}</div>
            <h3 className="text-xl font-bold leading-snug mb-2 text-balance">{briefing.title}</h3>
            <p className="text-sm leading-relaxed opacity-80">{briefing.one_line_summary}</p>
          </div>

          {/* Key sections grid */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <BriefingSection
              icon={Target}
              title="핵심 이슈 TOP 3"
              items={briefing.top_themes}
            />
            <BriefingSection
              icon={FileText}
              title="공시 하이라이트"
              items={briefing.disclosure_highlights}
            />
            <BriefingSection
              icon={Newspaper}
              title="뉴스 하이라이트"
              items={briefing.news_highlights}
            />
            <BriefingSection
              icon={Layers}
              title="종합 해석"
              items={briefing.combined_read}
            />
          </div>

          {/* Positives / Risks split */}
          <SplitSection
            title="긍정 요인 / 부담 요인"
            leftTitle="긍정 요인"
            leftItems={briefing.positives}
            rightTitle="부담 요인"
            rightItems={briefing.risks}
          />

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <BriefingSection
              icon={CheckCircle2}
              title="다음 주 체크포인트"
              items={briefing.checks_next_week}
            />
            <BriefingSection
              icon={BookOpen}
              title="이 주의 요약"
              items={briefing.meeting_summary}
            />
          </div>

          {/* Disclaimer */}
          <div className="px-4 py-3 bg-muted/40 border border-border rounded-lg text-xs text-muted-foreground leading-relaxed">
            본 브리핑은 AI가 공시·뉴스 데이터를 기반으로 자동 생성한 참고 자료입니다.
            투자 결정의 최종 책임은 투자자 본인에게 있으며, 전문가 자문을 병행하시기 바랍니다.
          </div>
        </div>
      ) : (
        <div className="flex flex-col items-center justify-center py-16 gap-4 text-center">
          <div className="w-14 h-14 rounded-full bg-muted flex items-center justify-center">
            <FileText className="w-7 h-7 text-muted-foreground" />
          </div>
          <div>
            <div className="text-sm font-semibold text-foreground">브리핑이 없습니다</div>
            <div className="text-xs text-muted-foreground mt-1">위 버튼으로 브리핑을 생성하거나 이전 단계로 돌아가세요.</div>
          </div>
        </div>
      )}

      {/* Navigation */}
      <div className="flex gap-3 pt-2">
        <button
          onClick={onPrev}
          className="flex items-center gap-2 px-4 py-2.5 text-sm font-medium text-muted-foreground hover:text-foreground border border-border rounded-lg hover:bg-muted/50 transition-colors"
        >
          <ArrowLeft className="w-4 h-4" />
          다른 주차 보기
        </button>
        <button
          onClick={onRestart}
          className="flex items-center gap-2 px-4 py-2.5 text-sm font-medium text-muted-foreground hover:text-foreground border border-border rounded-lg hover:bg-muted/50 transition-colors"
        >
          회사 다시 선택
        </button>
      </div>
    </div>
  )
}
