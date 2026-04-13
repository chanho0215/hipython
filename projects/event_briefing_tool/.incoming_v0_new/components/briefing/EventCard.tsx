import { ExternalLink } from "lucide-react"
import { cn } from "@/lib/utils"
import type { EventItem } from "@/lib/types"

interface Props {
  item: EventItem
  compact?: boolean
}

const SOURCE_COLORS: Record<string, string> = {
  DART: "bg-blue-500/10 text-blue-600 dark:text-blue-400 border-blue-500/20",
  NAVER: "bg-green-500/10 text-green-600 dark:text-green-400 border-green-500/20",
  뉴스: "bg-green-500/10 text-green-600 dark:text-green-400 border-green-500/20",
  공시: "bg-blue-500/10 text-blue-600 dark:text-blue-400 border-blue-500/20",
}

export function EventCard({ item, compact = false }: Props) {
  const sourceStyle = SOURCE_COLORS[item.source] || "bg-muted text-muted-foreground border-border"

  return (
    <div
      className={cn(
        "bg-card border border-border rounded-lg transition-colors hover:border-primary/20",
        compact ? "px-4 py-3" : "px-5 py-4"
      )}
    >
      <div className="flex items-start gap-3">
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 flex-wrap mb-1.5">
            <span
              className={cn(
                "inline-flex items-center px-2 py-0.5 rounded text-[10px] font-semibold border",
                sourceStyle
              )}
            >
              {item.source}
            </span>
            <span className="text-[11px] text-muted-foreground">{item.category}</span>
            <span className="text-[11px] text-muted-foreground font-mono ml-auto">{item.occurred_at}</span>
          </div>
          <div className={cn("font-semibold text-foreground leading-snug", compact ? "text-sm" : "text-sm")}>
            {item.title}
          </div>
          {item.snippet && !compact && (
            <div className="mt-2 text-sm text-muted-foreground leading-relaxed line-clamp-3">
              {item.snippet}
            </div>
          )}
        </div>
        {item.url && (
          <a
            href={item.url}
            target="_blank"
            rel="noopener noreferrer"
            className="shrink-0 text-muted-foreground hover:text-primary transition-colors mt-0.5"
          >
            <ExternalLink className="w-3.5 h-3.5" />
          </a>
        )}
      </div>
    </div>
  )
}
