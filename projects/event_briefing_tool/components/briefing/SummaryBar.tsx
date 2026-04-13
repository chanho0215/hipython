import type { AppState } from "@/lib/types"
import { weekLabel } from "@/lib/date-utils"

interface Props {
  state: AppState
}

export function SummaryBar({ state }: Props) {
  // welcome 화면은 도입 성격이라 작업 요약 바를 잠깐 숨긴다.
  if (state.step === "welcome") return null

  const { selectedCompany, selectedYear, selectedMonth, selectedWeekNo, weeklyBundle } = state
  const label = weeklyBundle.week_label || weekLabel(selectedYear, selectedMonth, selectedWeekNo)

  const items = [
    {
      label: "분석 대상",
      value: selectedCompany ? selectedCompany.corp_name : "—",
      sub: selectedCompany?.stock_code ? `KRX ${selectedCompany.stock_code}` : undefined,
    },
    {
      label: "분석 기간",
      value: label,
    },
    {
      label: "공시",
      value: weeklyBundle.disclosures.length > 0 ? `${weeklyBundle.disclosures.length}건` : "—",
    },
    {
      label: "뉴스",
      value: weeklyBundle.news.length > 0 ? `${weeklyBundle.news.length}건` : "—",
    },
  ]

  return (
    // 본문 위쪽에서 지금 선택된 맥락을 짧게 붙잡아 주는 역할을 한다.
    <div className="grid grid-cols-2 md:grid-cols-4 gap-3 mb-2">
      {items.map((item) => (
        <div
          key={item.label}
          className="bg-card border border-border rounded-lg px-4 py-3"
        >
          <div className="text-[10px] font-semibold text-muted-foreground uppercase tracking-wider mb-1">
            {item.label}
          </div>
          <div className="text-sm font-semibold text-foreground leading-tight">{item.value}</div>
          {item.sub && (
            <div className="text-[10px] text-muted-foreground mt-0.5 font-mono">{item.sub}</div>
          )}
        </div>
      ))}
    </div>
  )
}
