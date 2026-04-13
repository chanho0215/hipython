import { NextRequest, NextResponse } from "next/server"

// Demo data fallback when the Python service is not available
const DEMO_HITS = [
  { corp_code: "00126380", corp_name: "삼성전자", stock_code: "005930", label: "삼성전자 (005930)" },
  { corp_code: "00164779", corp_name: "SK하이닉스", stock_code: "000660", label: "SK하이닉스 (000660)" },
  { corp_code: "00356361", corp_name: "LG에너지솔루션", stock_code: "373220", label: "LG에너지솔루션 (373220)" },
  { corp_code: "00401731", corp_name: "삼성바이오로직스", stock_code: "207940", label: "삼성바이오로직스 (207940)" },
  { corp_code: "00266961", corp_name: "현대차", stock_code: "005380", label: "현대차 (005380)" },
  { corp_code: "00164742", corp_name: "POSCO홀딩스", stock_code: "005490", label: "POSCO홀딩스 (005490)" },
  { corp_code: "00159643", corp_name: "NAVER", stock_code: "035420", label: "NAVER (035420)" },
  { corp_code: "00293887", corp_name: "카카오", stock_code: "035720", label: "카카오 (035720)" },
  { corp_code: "00116031", corp_name: "LG화학", stock_code: "051910", label: "LG화학 (051910)" },
  { corp_code: "00126186", corp_name: "KB금융", stock_code: "105560", label: "KB금융 (105560)" },
]

const MEILI_URL = process.env.MEILISEARCH_URL || process.env.DEFAULT_MEILI_URL || "http://localhost:7700"
// 운영에서는 search key를 쓰고, 로컬 정비할 때는 master key로도 붙을 수 있게 열어 둔다.
const MEILI_KEY = process.env.MEILISEARCH_API_KEY || process.env.MEILISEARCH_MASTER_KEY || ""
const COMPANY_INDEX = process.env.COMPANY_INDEX || process.env.MEILISEARCH_COMPANY_INDEX || "kr_companies"

export async function GET(req: NextRequest) {
  const q = req.nextUrl.searchParams.get("q") || ""

  // 검색 UX는 인덱스 유무에 따라 체감이 크게 달라서, Meilisearch를 먼저 시도한다.
  try {
    const url = `${MEILI_URL}/indexes/${COMPANY_INDEX}/search`
    const res = await fetch(url, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        ...(MEILI_KEY ? { Authorization: `Bearer ${MEILI_KEY}` } : {}),
      },
      body: JSON.stringify({ q, limit: 15 }),
      signal: AbortSignal.timeout(3000),
    })
    if (res.ok) {
      const data = await res.json()
      return NextResponse.json({ hits: data.hits || [], source: "meilisearch" })
    }
  } catch {
    // 검색 서버가 비어 있어도 첫 화면이 막히지 않게 데모 데이터로 내려간다.
  }

  // 마지막 안전장치. 초기 세팅 중에도 검색 UI는 살아 있어야 한다.
  const lower = q.toLowerCase().trim()
  const hits = lower
    ? DEMO_HITS.filter(
        (h) =>
          h.corp_name.toLowerCase().includes(lower) ||
          h.stock_code.includes(lower) ||
          h.corp_code.includes(lower)
      )
    : DEMO_HITS

  return NextResponse.json({
    hits,
    source: "unavailable",
    message: "검색 인덱스를 연결할 수 없어 데모 데이터를 표시합니다.",
  })
}
