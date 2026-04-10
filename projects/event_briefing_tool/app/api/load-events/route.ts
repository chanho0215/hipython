import { NextRequest, NextResponse } from "next/server"
import type { EventItem, WeeklyBundle } from "@/lib/types"

const PYTHON_SERVICE_URL = process.env.PYTHON_SERVICE_URL || ""
const DART_API_KEY = process.env.DART_API_KEY || ""
const NAVER_CLIENT_ID = process.env.NAVER_CLIENT_ID || ""
const NAVER_CLIENT_SECRET = process.env.NAVER_CLIENT_SECRET || ""

function weekDateRange(year: number, month: number, weekNo: number) {
  const startDay = (weekNo - 1) * 7 + 1
  const daysInMonth = new Date(year, month, 0).getDate()
  const endDay = Math.min(startDay + 6, daysInMonth)
  const pad = (n: number) => String(n).padStart(2, "0")
  return {
    start: `${year}-${pad(month)}-${pad(startDay)}`,
    end: `${year}-${pad(month)}-${pad(endDay)}`,
  }
}

function weekLabel(year: number, month: number, weekNo: number) {
  const start = (weekNo - 1) * 7 + 1
  const daysInMonth = new Date(year, month, 0).getDate()
  const end = Math.min(start + 6, daysInMonth)
  return `${year}년 ${month}월 ${weekNo}주 (${month}/${start}~${month}/${end})`
}

async function fetchDartDisclosures(
  corpCode: string,
  startDate: string,
  endDate: string,
  limit: number
): Promise<EventItem[]> {
  if (!DART_API_KEY) return []
  try {
    const params = new URLSearchParams({
      crtfc_key: DART_API_KEY,
      corp_code: corpCode,
      bgn_de: startDate.replace(/-/g, ""),
      end_de: endDate.replace(/-/g, ""),
      page_count: String(limit),
    })
    const res = await fetch(`https://opendart.fss.or.kr/api/list.json?${params}`, {
      signal: AbortSignal.timeout(8000),
    })
    if (!res.ok) return []
    const data = await res.json()
    if (data.status !== "000") return []
    return (data.list || []).slice(0, limit).map((item: Record<string, string>) => ({
      source: "DART",
      category: item.pblntf_detail_ty || item.pblntf_ty || "공시",
      occurred_at: item.rcept_dt
        ? `${item.rcept_dt.slice(0, 4)}-${item.rcept_dt.slice(4, 6)}-${item.rcept_dt.slice(6, 8)}`
        : startDate,
      title: item.report_nm || "제목 없음",
      snippet: item.flr_nm ? `제출인: ${item.flr_nm}` : undefined,
      url: item.rcept_no
        ? `https://dart.fss.or.kr/dsaf001/main.do?rcpNo=${item.rcept_no}`
        : undefined,
    }))
  } catch {
    return []
  }
}

function stripHtml(text: string) {
  return text.replace(/<[^>]+>/g, "").replace(/&quot;/g, '"').replace(/&amp;/g, "&")
}

function buildNewsQueries(companyName: string, stockCode: string) {
  const queries = [
    companyName,
    `"${companyName}"`,
    `"${companyName}" 공시`,
    `"${companyName}" 실적`,
  ]

  if (stockCode) {
    queries.push(`"${companyName}" ${stockCode}`)
    queries.push(`${companyName} ${stockCode}`)
  }

  return Array.from(new Set(queries.map((query) => query.trim()).filter(Boolean)))
}

async function fetchNaverNews(
  companyName: string,
  stockCode: string,
  startDate: string,
  endDate: string,
  limit: number
): Promise<{ items: EventItem[]; debug: Record<string, unknown> }> {
  const debug: Record<string, unknown> = {
    enabled: Boolean(NAVER_CLIENT_ID && NAVER_CLIENT_SECRET),
    warning: "",
    queries: [],
    errors: [],
    matched: 0,
  }

  if (!NAVER_CLIENT_ID || !NAVER_CLIENT_SECRET) {
    debug.warning = "NAVER_CLIENT_ID 또는 NAVER_CLIENT_SECRET이 설정되지 않았습니다."
    return { items: [], debug }
  }

  try {
    const start = new Date(startDate)
    const end = new Date(endDate)
    end.setDate(end.getDate() + 1)
    const seen = new Set<string>()
    const collected: EventItem[] = []

    for (const queryText of buildNewsQueries(companyName, stockCode)) {
      const query = encodeURIComponent(queryText)
      try {
        const res = await fetch(
          `https://openapi.naver.com/v1/search/news.json?query=${query}&display=${Math.min(
            Math.max(limit * 2, 20),
            100
          )}&sort=date`,
          {
            headers: {
              "X-Naver-Client-Id": NAVER_CLIENT_ID,
              "X-Naver-Client-Secret": NAVER_CLIENT_SECRET,
            },
            signal: AbortSignal.timeout(8000),
          }
        )

        if (!res.ok) {
          const body = await res.text()
          ;(debug.errors as unknown[]).push({
            query: queryText,
            status: res.status,
            body: body.slice(0, 300),
          })
          continue
        }

        const data = await res.json()
        ;(debug.queries as unknown[]).push({ query: queryText, total: (data.items || []).length })

        for (const item of data.items || []) {
          const pubDate = new Date(item.pubDate)
          if (Number.isNaN(pubDate.getTime()) || pubDate < start || pubDate > end) continue

          const title = stripHtml(item.title || "")
          const key = `${pubDate.toISOString().slice(0, 10)}::${title}`
          if (seen.has(key)) continue

          seen.add(key)
          collected.push({
            source: "뉴스",
            category: "뉴스",
            occurred_at: pubDate.toISOString().slice(0, 10),
            title,
            snippet: stripHtml(item.description || ""),
            url: item.originallink || item.link,
          })

          if (collected.length >= limit) break
        }

        if (collected.length >= limit) break
      } catch (error) {
        ;(debug.errors as unknown[]).push({
          query: queryText,
          error: error instanceof Error ? error.message : "unknown error",
        })
      }
    }

    debug.matched = collected.length
    if (collected.length === 0 && !(debug.errors as unknown[]).length) {
      debug.warning = "뉴스 API 호출은 성공했지만 선택한 기간에 맞는 뉴스가 없었습니다."
    }

    return { items: collected, debug }
  } catch (error) {
    debug.warning = error instanceof Error ? error.message : "뉴스 수집 중 알 수 없는 오류가 발생했습니다."
    return { items: [], debug }
  }
}

export async function POST(req: NextRequest) {
  try {
    const body = await req.json()
    const { corp_code, corp_name, stock_code, year, month, week_no, disclosure_limit = 40, news_limit = 30 } = body

    if (!corp_code || !corp_name) {
      return NextResponse.json({ error: "corp_code와 corp_name은 필수입니다." }, { status: 400 })
    }

    // If an external Python service is configured, proxy to it
    if (PYTHON_SERVICE_URL) {
      try {
        const res = await fetch(`${PYTHON_SERVICE_URL}/load-events`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(body),
          signal: AbortSignal.timeout(30000),
        })
        if (res.ok) {
          const data = await res.json()
          return NextResponse.json(data)
        }
      } catch {
        // Fall through to direct fetch
      }
    }

    const { start, end } = weekDateRange(year, month, week_no)
    const wLabel = weekLabel(year, month, week_no)

    const [disclosures, newsResult] = await Promise.all([
      fetchDartDisclosures(corp_code, start, end, disclosure_limit),
      fetchNaverNews(corp_name, stock_code, start, end, news_limit),
    ])
    const news = newsResult.items

    const all: EventItem[] = [
      ...disclosures.map((d) => ({ ...d })),
      ...news.map((n) => ({ ...n })),
    ].sort((a, b) => b.occurred_at.localeCompare(a.occurred_at))

    const bundle: WeeklyBundle = {
      all,
      disclosures,
      news,
      news_debug: newsResult.debug,
      week_label: wLabel,
    }

    return NextResponse.json({ bundle, overview: null })
  } catch (e: unknown) {
    return NextResponse.json(
      { error: e instanceof Error ? e.message : "서버 오류가 발생했습니다." },
      { status: 500 }
    )
  }
}
