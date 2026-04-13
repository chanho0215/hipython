import { BarChart2 } from "lucide-react"

export function AppHeader() {
  return (
    // 상단 바는 기능을 많이 담기보다 "지금 어떤 도구를 쓰고 있는지"만 분명히 보여 준다.
    <header className="sticky top-0 z-10 flex items-center gap-3 px-6 py-3.5 bg-card border-b border-border">
      <div className="flex items-center gap-2.5">
        <div className="w-7 h-7 rounded-md bg-primary flex items-center justify-center">
          <BarChart2 className="w-4 h-4 text-primary-foreground" />
        </div>
        <span className="text-sm font-semibold text-foreground tracking-tight">주간 공시·뉴스 브리핑</span>
      </div>

    </header>
  )
}
