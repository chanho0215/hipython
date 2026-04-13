import { NextRequest, NextResponse } from "next/server"
import type { EventItem, WeeklyBundle } from "@/lib/types"

const PYTHON_SERVICE_URL = process.env.PYTHON_SERVICE_URL || ""
const DART_API_KEY = process.env.DART_API_KEY || ""
const NAVER_CLIENT_ID = process.env.NAVER_CLIENT_ID || ""
const NAVER_CLIENT_SECRET = process.env.NAVER_CLIENT_SECRET || ""

const NAVER_QUERY_TEMPLATES = [
  `"{company_name}" {stock_code}`,
  `"{company_name}" {stock_code} 공시`,
  `"{company_name}" {stock_code} 실적`,
  `"{company_name}" 공시`,
  `"{company_name}" 실적`,
  `"{company_name}" 주가`,
  `"{company_name}" {month_token}`,
  `"{company_name}" {year_month_token}`,
  `"{company_name}"`,
  `{company_name}`,
]

const NAVER_PAGE_SIZE = 100
const NAVER_MAX_PAGES_PER_QUERY = 10

function pad2(n: number) {
  return String(n).padStart(2, "0")
}

// 주차 기준이 "달의 1~7일 / 8~14일 ..." 형태라서 화면과 API가 같은 계산을 쓰게 맞춘다.
function weekDateRange(year: number, month: number, weekNo: number) {
  const startDay = (weekNo - 1) * 7 + 1
  const daysInMonth = new Date(year, month, 0).getDate()
  const endDay = Math.min(startDay + 6, daysInMonth)

  return {
    start: `${year}-${pad2(month)}-${pad2(startDay)}`,
    end: `${year}-${pad2(month)}-${pad2(endDay)}`,
  }
}

function weekLabel(year: number, month: number, weekNo: number) {
  return `${year}년 ${month}월 ${weekNo}주차`
}

// 네이버 뉴스는 HTML 태그가 섞여 내려오므로 저장 전에 한번 정리한다.
function stripHtml(text: string) {
  return (text || "")
    .replace(/<[^>]+>/g, "")
    .replace(/&quot;/g, '"')
    .replace(/&amp;/g, "&")
    .replace(/&#39;/g, "'")
    .replace(/&lt;/g, "<")
    .replace(/&gt;/g, ">")
    .trim()
}

function parseNaverDate(pubDate: string) {
  const date = new Date(pubDate)
  return Number.isNaN(date.getTime()) ? null : date
}

// 기사 날짜 필터는 inclusive로 두어 주차 마지막 날 기사도 빠지지 않게 한다.
function isWithinInclusive(target: Date, start: Date, end: Date) {
  return target.getTime() >= start.getTime() && target.getTime() <= end.getTime()
}

// 쿼리 템플릿을 한 번 거쳐 두면 종목명/월/티커 조합을 여러 군데서 따로 만들 필요가 없다.
function fillTemplate(
  template: string,
  {
    companyName,
    stockCode,
    year,
    month,
  }: {
    companyName: string
    stockCode: string
    year: number
    month: number
  }
) {
  return template
    .replaceAll("{company_name}", companyName)
    .replaceAll("{stock_code}", stockCode || "")
    .replaceAll("{month_token}", `${month}월`)
    .replaceAll("{year_month_token}", `${year}년 ${month}월`)
    .replaceAll("{year}", String(year))
    .replaceAll("{month}", String(month))
    .replace(/\s+/g, " ")
    .trim()
}

function buildNewsQueries(companyName: string, stockCode: string, year: number, month: number) {
  const queries = NAVER_QUERY_TEMPLATES.map((template) =>
    fillTemplate(template, { companyName, stockCode, year, month })
  ).filter(Boolean)

  // 중복 쿼리는 네이버 호출 횟수만 늘리기 때문에 여기서 바로 정리한다.
  return Array.from(new Set(queries))
}

async function fetchDartDisclosures(
  corpCode: string,
  startDate: string,
  endDate: string,
  limit: number
): Promise<EventItem[]> {
  if (!DART_API_KEY) return []

  try {
    // 최근 공시를 주차 범위로 다시 한번 걸러 쓰기 때문에, 응답은 넉넉하게 받아 온다.
    const params = new URLSearchParams({
      crtfc_key: DART_API_KEY,
      corp_code: corpCode,
      bgn_de: startDate.replace(/-/g, ""),
      end_de: endDate.replace(/-/g, ""),
      page_count: String(limit),
      sort: "date",
      sort_mth: "desc",
      last_reprt_at: "Y",
    })

    const res = await fetch(`https://opendart.fss.or.kr/api/list.json?${params}`, {
      signal: AbortSignal.timeout(10000),
      cache: "no-store",
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

async function fetchNaverNews(
  companyName: string,
  stockCode: string,
  year: number,
  month: number,
  startDate: string,
  endDate: string,
  limit: number
): Promise<{ items: EventItem[]; debug: Record<string, unknown> }> {
  const debugQueries: string[] = []
  const debugErrors: string[] = []

  // 프론트에서 "왜 뉴스가 비었는지" 볼 수 있도록 디버그 정보를 같이 내려준다.
  const debug: Record<string, unknown> = {
    enabled: Boolean(NAVER_CLIENT_ID && NAVER_CLIENT_SECRET),
    warning: "",
    queries: debugQueries,
    errors: debugErrors,
    matched: 0,
  }

  if (!NAVER_CLIENT_ID || !NAVER_CLIENT_SECRET) {
    debug.warning = "NAVER_CLIENT_ID 또는 NAVER_CLIENT_SECRET이 설정되지 않았습니다."
    return { items: [], debug }
  }

  const start = new Date(`${startDate}T00:00:00+09:00`)
  const end = new Date(`${endDate}T23:59:59+09:00`)

  const seen = new Set<string>()
  const collected: EventItem[] = []

  // 단일 회사명 쿼리만으로는 누락이 많아서, 종목코드/공시/실적 키워드를 같이 돈다.
  const queries = buildNewsQueries(companyName, stockCode, year, month)

  outer: for (const queryText of queries) {
    let addedForQuery = 0
    let oldestPubDate = ""
    let apiTotal = 0

    for (let page = 1; page <= NAVER_MAX_PAGES_PER_QUERY; page++) {
      const startParam = (page - 1) * NAVER_PAGE_SIZE + 1
      if (startParam > 1000) break

      try {
        const params = new URLSearchParams({
          query: queryText,
          display: String(NAVER_PAGE_SIZE),
          start: String(startParam),
          sort: "date",
        })

        const res = await fetch(`https://openapi.naver.com/v1/search/news.json?${params.toString()}`, {
          headers: {
            "X-Naver-Client-Id": NAVER_CLIENT_ID,
            "X-Naver-Client-Secret": NAVER_CLIENT_SECRET,
          },
          signal: AbortSignal.timeout(10000),
          cache: "no-store",
        })

        if (!res.ok) {
          const body = await res.text()
          debugErrors.push(`[${queryText}] page=${page} status=${res.status} body=${body.slice(0, 150)}`)
          break
        }

        const data = await res.json()
        const items = Array.isArray(data.items) ? data.items : []
        apiTotal = Number(data.total || 0)

        if (!items.length) break

        for (const item of items) {
          const pubDate = parseNaverDate(item.pubDate)
          if (!pubDate) continue

          oldestPubDate = pubDate.toISOString().slice(0, 10)

          if (pubDate < start) {
            continue
          }

          if (!isWithinInclusive(pubDate, start, end)) {
            continue
          }

          const title = stripHtml(item.title || "")
          const snippet = stripHtml(item.description || "")
          const key = `${pubDate.toISOString().slice(0, 10)}::${title}`

          // 같은 기사가 여러 쿼리에서 반복해서 잡히는 경우가 많아 날짜+제목 기준으로 묶는다.
          if (!title || seen.has(key)) continue

          seen.add(key)
          collected.push({
            source: "뉴스",
            category: "뉴스",
            occurred_at: pubDate.toISOString().slice(0, 10),
            title,
            snippet,
            url: item.originallink || item.link,
          })
          addedForQuery += 1

          if (collected.length >= limit) {
            debugQueries.push(
              `${queryText} | total=${apiTotal} | added=${addedForQuery} | oldest=${oldestPubDate || "-"} | stop=limit`
            )
            break outer
          }
        }

        const lastItem = items[items.length - 1]
        const lastPubDate = parseNaverDate(lastItem?.pubDate || "")
        // 날짜순 정렬이라 마지막 기사가 시작일보다 이전이면 더 뒤 페이지는 볼 필요가 없다.
        if (lastPubDate && lastPubDate < start) {
          break
        }
      } catch (error) {
        debugErrors.push(
          `[${queryText}] page=${page} error=${error instanceof Error ? error.message : "unknown error"}`
        )
        break
      }
    }

    debugQueries.push(
      `${queryText} | total=${apiTotal} | added=${addedForQuery} | oldest=${oldestPubDate || "-"}`
    )
  }

  debug.matched = collected.length

  if (collected.length === 0 && debugErrors.length === 0) {
    debug.warning = "뉴스 API 호출은 성공했지만 선택한 주차에 맞는 뉴스가 없었습니다."
  }

  return {
    items: collected
      .sort((a, b) => b.occurred_at.localeCompare(a.occurred_at))
      .slice(0, limit),
    debug,
  }
}

export async function POST(req: NextRequest) {
  try {
    const body = await req.json()
    const {
      corp_code,
      corp_name,
      stock_code,
      year,
      month,
      week_no,
      disclosure_limit = 40,
      news_limit = 30,
    } = body

    if (!corp_code || !corp_name || !year || !month || !week_no) {
      return NextResponse.json(
        { error: "corp_code, corp_name, year, month, week_no는 필수입니다." },
        { status: 400 }
      )
    }

    // 외부 Python 서비스를 여전히 쓰고 싶을 때를 위해 프록시 경로는 남겨 둔다.
    // 다만 지금 기본 운영은 Next API 단독 실행을 기준으로 본다.
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
        // 외부 서비스가 잠시 죽어 있어도 직접 수집으로 바로 내려간다.
      }
    }

    const { start, end } = weekDateRange(Number(year), Number(month), Number(week_no))
    const wLabel = weekLabel(Number(year), Number(month), Number(week_no))

    // 공시와 뉴스는 서로 독립적이라 병렬로 받아 시간을 줄인다.
    const [disclosures, newsResult] = await Promise.all([
      fetchDartDisclosures(corp_code, start, end, Number(disclosure_limit)),
      fetchNaverNews(
        corp_name,
        stock_code || "",
        Number(year),
        Number(month),
        start,
        end,
        Number(news_limit)
      ),
    ])

    const news = newsResult.items

    // 화면에서는 소스가 섞인 타임라인이 필요해서 마지막에 한 번 합친다.
    const all: EventItem[] = [...disclosures, ...news].sort((a, b) =>
      b.occurred_at.localeCompare(a.occurred_at)
    )

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
