"use client"

import { useState, useCallback } from "react"
import type { AppState, CompanyHit, WeeklyBundle, WeeklyBriefing } from "@/lib/types"
import { AppHeader } from "@/components/briefing/AppHeader"
import { AppSidebar } from "@/components/briefing/AppSidebar"
import { StepIndicator } from "@/components/briefing/StepIndicator"
import { SummaryBar } from "@/components/briefing/SummaryBar"
import { CompanySearchStep } from "@/components/briefing/CompanySearchStep"
import { WeekSelectorStep } from "@/components/briefing/WeekSelectorStep"
import { BriefingStep } from "@/components/briefing/BriefingStep"

const EMPTY_BUNDLE: WeeklyBundle = {
  all: [],
  disclosures: [],
  news: [],
  news_debug: {},
}

const now = new Date()

const INITIAL_STATE: AppState = {
  step: "search",
  companyQuery: "삼성전자",
  companyHits: [],
  selectedCompany: null,
  companyOverview: null,
  selectedYear: now.getFullYear(),
  selectedMonth: now.getMonth() + 1,
  selectedWeekNo: 1,
  weeklyBundle: EMPTY_BUNDLE,
  latestBriefing: null,
  latestMarkdown: null,
  disclosureLimit: 40,
  newsLimit: 30,
  weekLoadAttempted: false,
  loadedPeriodKey: null,
  generatedPeriodKey: null,
}

export default function Home() {
  const [state, setState] = useState<AppState>(INITIAL_STATE)

  const update = useCallback((partial: Partial<AppState>) => {
    setState((prev) => ({ ...prev, ...partial }))
  }, [])

  const goTo = useCallback((step: AppState["step"]) => {
    setState((prev) => ({ ...prev, step }))
  }, [])

  const reset = useCallback(() => {
    setState(INITIAL_STATE)
  }, [])

  return (
    <div className="min-h-screen bg-background flex">
      <AppSidebar state={state} onNavigate={goTo} onReset={reset} />
      <div className="flex-1 flex flex-col min-w-0">
        <AppHeader />
        <main className="flex-1 px-6 py-6 max-w-5xl w-full mx-auto">
          <StepIndicator current={state.step} />
          <SummaryBar state={state} />

          <div className="mt-6">
            {state.step === "search" && (
              <CompanySearchStep state={state} update={update} onNext={() => goTo("week")} />
            )}
            {state.step === "week" && (
              <WeekSelectorStep
                state={state}
                update={update}
                onPrev={() => goTo("search")}
                onNext={() => goTo("briefing")}
              />
            )}
            {state.step === "briefing" && (
              <BriefingStep
                state={state}
                update={update}
                onPrev={() => goTo("week")}
                onRestart={() => goTo("search")}
              />
            )}
          </div>
        </main>
      </div>
    </div>
  )
}
