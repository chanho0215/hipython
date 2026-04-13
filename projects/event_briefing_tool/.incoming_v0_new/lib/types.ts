export interface CompanyHit {
  corp_code: string
  corp_name: string
  stock_code: string
  label: string
}

export interface EventItem {
  source: string
  category: string
  occurred_at: string
  title: string
  snippet?: string
  url?: string
}

export interface WeeklyBundle {
  all: EventItem[]
  disclosures: EventItem[]
  news: EventItem[]
  news_debug: Record<string, unknown>
  week_label?: string
}

export interface WeeklyBriefing {
  title: string
  week_label: string
  one_line_summary: string
  top_themes: string[]
  disclosure_highlights: string[]
  news_highlights: string[]
  combined_read: string[]
  positives: string[]
  risks: string[]
  checks_next_week: string[]
  meeting_summary: string[]
}

export type Step = 'welcome' | 'search' | 'week' | 'briefing'

export interface AppState {
  step: Step
  companyQuery: string
  companyHits: CompanyHit[]
  selectedCompany: CompanyHit | null
  companyOverview: Record<string, string> | null
  selectedYear: number
  selectedMonth: number
  selectedWeekNo: number
  weeklyBundle: WeeklyBundle
  latestBriefing: WeeklyBriefing | null
  latestMarkdown: string | null
  disclosureLimit: number
  newsLimit: number
  weekLoadAttempted: boolean
  loadedPeriodKey: [number, number, number] | null
  generatedPeriodKey: [number, number, number] | null
}
