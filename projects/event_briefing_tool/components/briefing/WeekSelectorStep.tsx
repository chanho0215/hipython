"use client"

import { useState } from "react"
import { ArrowLeft, ArrowRight, ChevronDown, FileText, Newspaper, LayoutList, Settings2, AlertCircle } from "lucide-react"
import { cn } from "@/lib/utils"
import type { AppState, EventItem } from "@/lib/types"
import { validWeeksForMonth, weekLabel } from "@/lib/date-utils"
import { EventCard } from "./EventCard"

interface Props {
  state: AppState
  update: (partial: Partial<AppState>) => void
  onPrev: () => void
  onNext: () => void
}

type TabKey = "all" | "disclosures" | "news"

const TAB_CONFIG: { key: TabKey; label: string; icon: React.ElementType }[] = [
  { key: "all", label: "전체", icon: LayoutList },
  { key: "disclosures", label: "공시", icon: FileText },
  { key: "news", label: "뉴스", icon: Newspaper },
]

export function WeekSelectorStep({ state, update, onPrev, onNext }: Props) {
  const { selectedCompany, selectedYear, selectedMonth, selectedWeekNo, weeklyBundle, disclosureLimit, newsLimit } = state

  const [loading, setLoading] = useState(false)
  const [genLoading, setGenLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [activeTab, setActiveTab] = useState<TabKey>("all")
  const [showAdvanced, setShowAdvanced] = useState(false)

  const [formYear, setFormYear] = useState(selectedYear)
  const [formMonth, setFormMonth] = useState(selectedMonth)
  const [formWeek, setFormWeek] = useState(selectedWeekNo)
  const [formDiscLimit, setFormDiscLimit] = useState(disclosureLimit)
  const [formNewsLimit, setFormNewsLimit] = useState(newsLimit)

  const validWeeks = validWeeksForMonth(formYear, formMonth)

  const currentKey: [number, number, number] = [selectedYear, selectedMonth, selectedWeekNo]
  const loadedKey = state.loadedPeriodKey
  const isLoaded = loadedKey !== null &&
    loadedKey[0] === currentKey[0] &&
    loadedKey[1] === currentKey[1] &&
    loadedKey[2] === currentKey[2]
  const hasEvents = weeklyBundle.all.length > 0

  const handleLoad = async () => {
    if (!selectedCompany) return
    setLoading(true)
    setError(null)
    try {
      const res = await fetch("/api/load-events", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          corp_code: selectedCompany.corp_code,
          corp_name: selectedCompany.corp_name,
          stock_code: selectedCompany.stock_code,
          year: formYear,
          month: formMonth,
          week_no: formWeek,
          disclosure_limit: formDiscLimit,
          news_limit: formNewsLimit,
        }),
      })
      const data = await res.json()
      if (!res.ok) throw new Error(data.error || "이벤트 수집에 실패했습니다.")
      update({
        selectedYear: formYear,
        selectedMonth: formMonth,
        selectedWeekNo: formWeek,
        disclosureLimit: formDiscLimit,
        newsLimit: formNewsLimit,
        weeklyBundle: data.bundle,
        companyOverview: data.overview || null,
        loadedPeriodKey: [formYear, formMonth, formWeek],
        weekLoadAttempted: true,
        latestBriefing: null,
        latestMarkdown: null,
        generatedPeriodKey: null,
      })
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : "알 수 없는 오류가 발생했습니다.")
    } finally {
      setLoading(false)
    }
  }

  const handleGenerateBriefing = async () => {
    if (!selectedCompany || !hasEvents) return
    setGenLoading(true)
    setError(null)
    try {
      const res = await fetch("/api/generate-briefing", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          company_name: selectedCompany.corp_name,
          stock_code: selectedCompany.stock_code,
          week_label: weeklyBundle.week_label || weekLabel(selectedYear, selectedMonth, selectedWeekNo),
          overview: state.companyOverview,
          disclosures: weeklyBundle.disclosures,
          news: weeklyBundle.news,
          all_events: weeklyBundle.all,
        }),
      })
      const data = await res.json()
      if (!res.ok) throw new Error(data.error || "브리핑 생성에 실패했습니다.")
      update({
        latestBriefing: data.briefing,
        latestMarkdown: data.markdown,
        generatedPeriodKey: [selectedYear, selectedMonth, selectedWeekNo],
      })
      onNext()
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : "알 수 없는 오류가 발생했습니다.")
    } finally {
      setGenLoading(false)
    }
  }

  const tabItems: EventItem[] =
    activeTab === "all"
      ? weeklyBundle.all
      : activeTab === "disclosures"
      ? weeklyBundle.disclosures
      : weeklyBundle.news

  if (!selectedCompany) {
    return (
      <div className="flex items-center gap-3 px-4 py-4 bg-muted/40 rounded-lg border border-border text-sm text-muted-foreground">
        <AlertCircle className="w-4 h-4 shrink-0" />
        먼저 회사를 선택해 주세요.
      </div>
    )
  }

  return (
    <div className="space-y-5">
      {/* Section title */}
      <div>
        <h2 className="text-lg font-semibold text-foreground">분석 기간을 선택하세요</h2>
        <p className="text-sm text-muted-foreground mt-1">
          <span className="text-foreground font-medium">{selectedCompany.corp_name}</span>
          {selectedCompany.stock_code && (
            <span className="ml-1.5 text-xs font-mono text-muted-foreground/70">({selectedCompany.stock_code})</span>
          )}
          의 공시·뉴스 데이터를 불러올 주차를 선택하세요.
        </p>
      </div>

      {/* Period selector card */}
      <div className="bg-card border border-border rounded-lg p-5 space-y-4">
        <div className="grid grid-cols-3 gap-3">
          {/* Year */}
          <div className="space-y-1.5">
            <label className="text-xs font-semibold text-muted-foreground uppercase tracking-wider">연도</label>
            <div className="relative">
              <select
                value={formYear}
                onChange={(e) => setFormYear(Number(e.target.value))}
                className="w-full appearance-none bg-background border border-border rounded-md px-3 py-2.5 text-sm font-medium focus:outline-none focus:ring-2 focus:ring-ring pr-8"
              >
                {[2024, 2025, 2026, 2027].map((y) => (
                  <option key={y} value={y}>{y}년</option>
                ))}
              </select>
              <ChevronDown className="absolute right-2.5 top-1/2 -translate-y-1/2 w-3.5 h-3.5 text-muted-foreground pointer-events-none" />
            </div>
          </div>

          {/* Month */}
          <div className="space-y-1.5">
            <label className="text-xs font-semibold text-muted-foreground uppercase tracking-wider">월</label>
            <div className="relative">
              <select
                value={formMonth}
                onChange={(e) => {
                  const m = Number(e.target.value)
                  setFormMonth(m)
                  const weeks = validWeeksForMonth(formYear, m)
                  if (!weeks.includes(formWeek)) setFormWeek(weeks[weeks.length - 1])
                }}
                className="w-full appearance-none bg-background border border-border rounded-md px-3 py-2.5 text-sm font-medium focus:outline-none focus:ring-2 focus:ring-ring pr-8"
              >
                {Array.from({ length: 12 }, (_, i) => i + 1).map((m) => (
                  <option key={m} value={m}>{m}월</option>
                ))}
              </select>
              <ChevronDown className="absolute right-2.5 top-1/2 -translate-y-1/2 w-3.5 h-3.5 text-muted-foreground pointer-events-none" />
            </div>
          </div>

          {/* Week */}
          <div className="space-y-1.5">
            <label className="text-xs font-semibold text-muted-foreground uppercase tracking-wider">주차</label>
            <div className="relative">
              <select
                value={formWeek}
                onChange={(e) => setFormWeek(Number(e.target.value))}
                className="w-full appearance-none bg-background border border-border rounded-md px-3 py-2.5 text-sm font-medium focus:outline-none focus:ring-2 focus:ring-ring pr-8"
              >
                {validWeeks.map((w) => (
                  <option key={w} value={w}>{w}주차</option>
                ))}
              </select>
              <ChevronDown className="absolute right-2.5 top-1/2 -translate-y-1/2 w-3.5 h-3.5 text-muted-foreground pointer-events-none" />
            </div>
          </div>
        </div>

        {/* Advanced options */}
        <div>
          <button
            type="button"
            onClick={() => setShowAdvanced(!showAdvanced)}
            className="flex items-center gap-1.5 text-xs text-muted-foreground hover:text-foreground transition-colors"
          >
            <Settings2 className="w-3.5 h-3.5" />
            고급 옵션
            <ChevronDown className={cn("w-3 h-3 transition-transform", showAdvanced && "rotate-180")} />
          </button>
          {showAdvanced && (
            <div className="mt-3 grid grid-cols-2 gap-3 p-3 bg-muted/40 rounded-md">
              <div className="space-y-1">
                <label className="text-xs text-muted-foreground">공시 최대 건수</label>
                <input
                  type="number"
                  min={10}
                  max={100}
                  value={formDiscLimit}
                  onChange={(e) => setFormDiscLimit(Number(e.target.value))}
                  className="w-full bg-background border border-border rounded px-2.5 py-1.5 text-sm focus:outline-none focus:ring-2 focus:ring-ring"
                />
              </div>
              <div className="space-y-1">
                <label className="text-xs text-muted-foreground">뉴스 최대 건수</label>
                <input
                  type="number"
                  min={5}
                  max={100}
                  value={formNewsLimit}
                  onChange={(e) => setFormNewsLimit(Number(e.target.value))}
                  className="w-full bg-background border border-border rounded px-2.5 py-1.5 text-sm focus:outline-none focus:ring-2 focus:ring-ring"
                />
              </div>
            </div>
          )}
        </div>

        <button
          onClick={handleLoad}
          disabled={loading}
          className="w-full py-2.5 bg-secondary text-secondary-foreground text-sm font-semibold rounded-lg hover:bg-secondary/70 disabled:opacity-50 disabled:cursor-not-allowed transition-colors border border-border"
        >
          {loading ? "이벤트 수집 중..." : "이 주차 이벤트 불러오기"}
        </button>
      </div>

      {/* Error */}
      {error && (
        <div className="flex items-start gap-2.5 px-4 py-3 bg-destructive/10 border border-destructive/20 rounded-lg text-sm text-destructive">
          <AlertCircle className="w-4 h-4 mt-0.5 shrink-0" />
          {error}
        </div>
      )}

      {/* Events display */}
      {isLoaded && hasEvents && (
        <div className="space-y-4">
          {/* Stats row */}
          <div className="flex items-center gap-3">
            <div className="flex items-center gap-1.5 text-xs text-muted-foreground">
              <span className="w-5 h-5 rounded bg-blue-500/10 flex items-center justify-center text-blue-600 dark:text-blue-400 font-bold text-[10px]">
                {weeklyBundle.disclosures.length}
              </span>
              공시
            </div>
            <div className="flex items-center gap-1.5 text-xs text-muted-foreground">
              <span className="w-5 h-5 rounded bg-green-500/10 flex items-center justify-center text-green-600 dark:text-green-400 font-bold text-[10px]">
                {weeklyBundle.news.length}
              </span>
              뉴스
            </div>
            <div className="text-xs text-muted-foreground ml-1">
              총 {weeklyBundle.all.length}건 수집
            </div>
          </div>

          {/* Tabs */}
          <div className="flex gap-1 bg-muted/50 p-1 rounded-lg w-fit">
            {TAB_CONFIG.map(({ key, label, icon: Icon }) => (
              <button
                key={key}
                onClick={() => setActiveTab(key)}
                className={cn(
                  "flex items-center gap-1.5 px-3 py-1.5 rounded-md text-xs font-semibold transition-colors",
                  activeTab === key
                    ? "bg-card text-foreground shadow-sm"
                    : "text-muted-foreground hover:text-foreground"
                )}
              >
                <Icon className="w-3.5 h-3.5" />
                {label}
                <span className={cn(
                  "text-[10px] font-mono",
                  activeTab === key ? "text-muted-foreground" : "text-muted-foreground/50"
                )}>
                  {key === "all" ? weeklyBundle.all.length : key === "disclosures" ? weeklyBundle.disclosures.length : weeklyBundle.news.length}
                </span>
              </button>
            ))}
          </div>

          {/* Event list */}
          <div className="space-y-2 max-h-96 overflow-y-auto pr-1">
            {tabItems.length > 0 ? (
              tabItems.map((item, i) => <EventCard key={i} item={item} compact />)
            ) : (
              <div className="text-sm text-muted-foreground py-6 text-center">이 카테고리에 표시할 항목이 없습니다.</div>
            )}
          </div>
        </div>
      )}

      {isLoaded && !hasEvents && (
        <div className="flex items-center gap-3 px-4 py-4 bg-muted/40 rounded-lg border border-border text-sm text-muted-foreground">
          <AlertCircle className="w-4 h-4 shrink-0" />
          이 주차에 수집된 이벤트가 없습니다.
        </div>
      )}

      {/* Navigation */}
      <div className="flex gap-3 pt-2">
        <button
          onClick={onPrev}
          className="flex items-center gap-2 px-4 py-2.5 text-sm font-medium text-muted-foreground hover:text-foreground border border-border rounded-lg hover:bg-muted/50 transition-colors"
        >
          <ArrowLeft className="w-4 h-4" />
          회사 선택
        </button>
        <button
          onClick={handleGenerateBriefing}
          disabled={!isLoaded || !hasEvents || genLoading}
          className="flex-1 flex items-center justify-center gap-2 px-5 py-2.5 bg-primary text-primary-foreground text-sm font-semibold rounded-lg hover:bg-primary/90 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
        >
          {genLoading ? "브리핑 생성 중..." : "AI 브리핑 생성"}
          {!genLoading && <ArrowRight className="w-4 h-4" />}
        </button>
      </div>
    </div>
  )
}
