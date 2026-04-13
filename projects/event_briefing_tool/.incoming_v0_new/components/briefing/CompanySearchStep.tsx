"use client"

import { useState } from "react"
import { Search, ArrowRight, Check, Building2, AlertCircle, Info, Database } from "lucide-react"
import { cn } from "@/lib/utils"
import type { AppState, CompanyHit } from "@/lib/types"
import { ButtonSpinner } from "./LoadingOverlay"

interface Props {
  state: AppState
  update: (partial: Partial<AppState>) => void
  onNext: () => void
}

interface FeedbackState {
  level: "success" | "warning" | "info" | "error"
  message: string
}

function FeedbackBanner({ level, message }: FeedbackState) {
  const styles = {
    success: "bg-positive/10 border-positive/20 text-positive",
    warning: "bg-yellow-500/10 border-yellow-500/20 text-yellow-600 dark:text-yellow-400",
    info: "bg-primary/5 border-primary/15 text-primary",
    error: "bg-destructive/10 border-destructive/20 text-destructive",
  }
  const Icon = level === "success" ? Check : level === "error" ? AlertCircle : Info
  return (
    <div className={cn("flex items-start gap-2.5 px-4 py-3 rounded-lg border text-sm", styles[level])}>
      <Icon className="w-4 h-4 mt-0.5 shrink-0" />
      <span>{message}</span>
    </div>
  )
}

export function CompanySearchStep({ state, update, onNext }: Props) {
  const [query, setQuery] = useState(state.companyQuery)
  const [loading, setLoading] = useState(false)
  const [feedback, setFeedback] = useState<FeedbackState | null>(null)
  const [selectedIdx, setSelectedIdx] = useState(0)

  const handleSearch = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!query.trim()) return
    setLoading(true)
    setFeedback(null)
    try {
      const res = await fetch(`/api/search-companies?q=${encodeURIComponent(query)}`)
      const data = await res.json()
      const hits: CompanyHit[] = (data.hits || [])
      update({ companyQuery: query, companyHits: hits })
      setSelectedIdx(0)

      if (data.source === "meilisearch") {
        setFeedback({ level: "success", message: `${hits.length}개 회사를 찾았습니다.` })
      } else if (data.source === "cache") {
        setFeedback({ level: "warning", message: "로컬 캐시로 검색했습니다." })
      } else if (data.source === "unavailable") {
        setFeedback({ level: "warning", message: "검색 인덱스를 찾지 못해 데모 데이터를 표시합니다." })
      } else {
        setFeedback({ level: "info", message: data.message || "검색 결과를 확인하세요." })
      }
    } catch {
      setFeedback({ level: "error", message: "검색 중 오류가 발생했습니다." })
    } finally {
      setLoading(false)
    }
  }

  const handleSelect = (hit: CompanyHit) => {
    update({
      selectedCompany: hit,
      companyOverview: null,
      weeklyBundle: { all: [], disclosures: [], news: [], news_debug: {} },
      latestBriefing: null,
      latestMarkdown: null,
      generatedPeriodKey: null,
      weekLoadAttempted: false,
      loadedPeriodKey: null,
    })
    onNext()
  }

  return (
    <div className="max-w-2xl space-y-5">
      {/* Section title */}
      <div>
        <h2 className="text-lg font-semibold text-foreground">분석할 회사를 선택하세요</h2>
        <p className="text-sm text-muted-foreground mt-1 leading-relaxed">
          회사명 또는 종목코드로 검색하면 DART 공시 및 뉴스 데이터를 분석합니다.
        </p>
      </div>

      {/* Search form */}
      <form onSubmit={handleSearch} className="flex gap-2">
        <div className="relative flex-1">
          <Search className="absolute left-3.5 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground pointer-events-none" />
          <input
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="예: 삼성전자, 카카오, 005930"
            className="w-full pl-10 pr-4 py-2.5 text-sm bg-card border border-border rounded-lg focus:outline-none focus:ring-2 focus:ring-ring focus:border-transparent placeholder:text-muted-foreground/60 transition-all"
          />
        </div>
        <button
          type="submit"
          disabled={loading || !query.trim()}
          className="px-5 py-2.5 bg-primary text-primary-foreground text-sm font-semibold rounded-lg hover:bg-primary/90 disabled:opacity-50 disabled:cursor-not-allowed transition-colors whitespace-nowrap"
        >
          {loading ? <><ButtonSpinner /> 검색 중...</> : "검색"}
        </button>
      </form>

      {/* Feedback */}
      {feedback && <FeedbackBanner {...feedback} />}

      {/* Results */}
      {state.companyHits.length > 0 && (
        <div className="space-y-2">
          <div className="text-xs font-semibold text-muted-foreground uppercase tracking-wider">검색 결과</div>
          <div className="space-y-1.5">
            {state.companyHits.map((hit, idx) => (
              <button
                key={hit.corp_code}
                onClick={() => setSelectedIdx(idx)}
                className={cn(
                  "w-full flex items-center gap-3 px-4 py-3 rounded-lg border text-left transition-all",
                  selectedIdx === idx
                    ? "bg-primary/5 border-primary/30 ring-1 ring-primary/20"
                    : "bg-card border-border hover:border-primary/20 hover:bg-muted/50"
                )}
              >
                <div
                  className={cn(
                    "w-8 h-8 rounded-md flex items-center justify-center shrink-0",
                    selectedIdx === idx ? "bg-primary/10" : "bg-muted"
                  )}
                >
                  {selectedIdx === idx ? (
                    <Check className="w-4 h-4 text-primary" />
                  ) : (
                    <Building2 className="w-4 h-4 text-muted-foreground" />
                  )}
                </div>
                <div className="min-w-0">
                  <div className="text-sm font-semibold text-foreground">{hit.corp_name}</div>
                  {hit.stock_code && (
                    <div className="text-xs text-muted-foreground font-mono mt-0.5">{hit.stock_code}</div>
                  )}
                </div>
                {selectedIdx === idx && (
                  <div className="ml-auto text-xs font-medium text-primary">선택됨</div>
                )}
              </button>
            ))}
          </div>

          <button
            onClick={() => handleSelect(state.companyHits[selectedIdx])}
            className="w-full flex items-center justify-center gap-2 mt-4 px-5 py-3 bg-primary text-primary-foreground text-sm font-semibold rounded-lg hover:bg-primary/90 transition-colors"
          >
            {state.companyHits[selectedIdx]?.corp_name} 분석 시작
            <ArrowRight className="w-4 h-4" />
          </button>
        </div>
      )}

      {/* Empty state hint */}
      {state.companyHits.length === 0 && !feedback && (
        <div className="flex items-start gap-3 px-4 py-4 bg-muted/40 rounded-lg border border-border">
          <Database className="w-4 h-4 text-muted-foreground mt-0.5 shrink-0" />
          <div className="text-sm text-muted-foreground leading-relaxed">
            회사명 또는 6자리 종목코드를 입력하고 검색하세요. DART에 등록된 모든 상장 기업을 지원합니다.
          </div>
        </div>
      )}
    </div>
  )
}
