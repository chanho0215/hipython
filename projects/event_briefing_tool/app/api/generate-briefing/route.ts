import { NextRequest, NextResponse } from "next/server"
import type { EventItem, WeeklyBriefing } from "@/lib/types"

const PYTHON_SERVICE_URL = process.env.PYTHON_SERVICE_URL || ""

// 내려받기용 마크다운은 화면에서 보이는 섹션 순서와 최대한 맞춘다.
function briefingToMarkdown(briefing: WeeklyBriefing): string {
  const lines: string[] = [
    `# ${briefing.title}`,
    `**${briefing.week_label}** — ${briefing.one_line_summary}`,
    "",
    "## 핵심 이슈 TOP 3",
    ...briefing.top_themes.map((t) => `- ${t}`),
    "",
    "## 공시 하이라이트",
    ...briefing.disclosure_highlights.map((t) => `- ${t}`),
    "",
    "## 뉴스 하이라이트",
    ...briefing.news_highlights.map((t) => `- ${t}`),
    "",
    "## 종합 해석",
    ...briefing.combined_read.map((t) => `- ${t}`),
    "",
    "## 긍정 요인",
    ...briefing.positives.map((t) => `- ${t}`),
    "",
    "## 부담 요인",
    ...briefing.risks.map((t) => `- ${t}`),
    "",
    "## 다음 주 체크포인트",
    ...briefing.checks_next_week.map((t) => `- ${t}`),
    "",
    "## 요약",
    ...briefing.meeting_summary.map((t) => `- ${t}`),
    "",
    "---",
    "_본 브리핑은 AI가 공시·뉴스 데이터를 기반으로 자동 생성한 참고 자료입니다. 투자 결정의 최종 책임은 투자자 본인에게 있습니다._",
  ]
  return lines.join("\n")
}

function generateFallbackBriefing(
  companyName: string,
  wLabel: string,
  disclosures: EventItem[],
  news: EventItem[]
): WeeklyBriefing {
  const discTitles = disclosures.slice(0, 3).map((d) => d.title)
  const newsTitles = news.slice(0, 3).map((n) => n.title)

  // AI가 죽어도 최소한 회의용 텍스트는 남도록 단순한 구조화 결과를 만들어 둔다.
  return {
    title: `${companyName} 주간 공시·뉴스 브리핑`,
    week_label: wLabel,
    one_line_summary: `${wLabel} 기간 공시 ${disclosures.length}건, 뉴스 ${news.length}건이 수집되었습니다.`,
    top_themes: [
      disclosures.length > 0 ? `공시 ${disclosures.length}건 접수` : "이 주차 공시 없음",
      news.length > 0 ? `뉴스 ${news.length}건 수집` : "이 주차 뉴스 없음",
      "AI 브리핑 서비스 연결 전 — 상세 분석은 API 연동 후 이용 가능",
    ],
    disclosure_highlights: discTitles.length > 0 ? discTitles : ["수집된 공시 없음"],
    news_highlights: newsTitles.length > 0 ? newsTitles : ["수집된 뉴스 없음"],
    combined_read: [
      "현재 AI 분석 서비스가 연결되지 않았습니다.",
      "OPENAI_API_KEY 또는 외부 Python 서비스를 설정하면 상세 AI 브리핑을 이용할 수 있습니다.",
    ],
    positives: ["데이터 수집 완료"],
    risks: ["AI 분석 서비스 미연결"],
    checks_next_week: ["AI 서비스 연결 후 체크포인트 확인 가능"],
    meeting_summary: [
      `${companyName}의 ${wLabel} 데이터가 수집되었으나 AI 분석 서비스 연결이 필요합니다.`,
    ],
  }
}

async function generateWithOpenAI(
  companyName: string,
  stockCode: string,
  wLabel: string,
  disclosures: EventItem[],
  news: EventItem[]
): Promise<WeeklyBriefing> {
  const OPENAI_API_KEY = process.env.OPENAI_API_KEY
  if (!OPENAI_API_KEY) throw new Error("OPENAI_API_KEY not set")

  // 원문 전체를 넘기면 길이가 금방 커지므로, 화면에서 본 핵심 항목만 압축해서 보낸다.
  const discSummary = disclosures
    .slice(0, 20)
    .map((d) => `[공시] ${d.occurred_at} ${d.title}${d.snippet ? ": " + d.snippet : ""}`)
    .join("\n")
  const newsSummary = news
    .slice(0, 20)
    .map((n) => `[뉴스] ${n.occurred_at} ${n.title}${n.snippet ? ": " + n.snippet : ""}`)
    .join("\n")

  const prompt = `당신은 전문 주식 리서치 애널리스트입니다. 아래 데이터를 분석하여 투자자를 위한 주간 브리핑을 JSON 형식으로 작성해주세요.

회사: ${companyName} (${stockCode})
기간: ${wLabel}

공시 내역:
${discSummary || "없음"}

뉴스 내역:
${newsSummary || "없음"}

다음 JSON 형식으로 응답하세요 (한국어로 작성):
{
  "title": "브리핑 제목 (회사명+주차 포함)",
  "one_line_summary": "한 줄 요약",
  "top_themes": ["핵심이슈1", "핵심이슈2", "핵심이슈3"],
  "disclosure_highlights": ["공시하이라이트1", "공시하이라이트2", "공시하이라이트3"],
  "news_highlights": ["뉴스하이라이트1", "뉴스하이라이트2", "뉴스하이라이트3"],
  "combined_read": ["종합해석1", "종합해석2"],
  "positives": ["긍정요인1", "긍정요인2"],
  "risks": ["부담요인1", "부담요인2"],
  "checks_next_week": ["체크포인트1", "체크포인트2"],
  "meeting_summary": ["최종요약1", "최종요약2"]
}`

  const res = await fetch("https://api.openai.com/v1/chat/completions", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${OPENAI_API_KEY}`,
    },
    body: JSON.stringify({
      model: "gpt-4o-mini",
      messages: [{ role: "user", content: prompt }],
      temperature: 0.4,
      response_format: { type: "json_object" },
    }),
    signal: AbortSignal.timeout(30000),
  })

  if (!res.ok) {
    const err = await res.text()
    throw new Error(`OpenAI API error: ${err}`)
  }

  const data = await res.json()
  const parsed = JSON.parse(data.choices[0].message.content)
  return {
    title: parsed.title || `${companyName} 주간 브리핑`,
    week_label: wLabel,
    one_line_summary: parsed.one_line_summary || "",
    top_themes: parsed.top_themes || [],
    disclosure_highlights: parsed.disclosure_highlights || [],
    news_highlights: parsed.news_highlights || [],
    combined_read: parsed.combined_read || [],
    positives: parsed.positives || [],
    risks: parsed.risks || [],
    checks_next_week: parsed.checks_next_week || [],
    meeting_summary: parsed.meeting_summary || [],
  }
}

export async function POST(req: NextRequest) {
  try {
    const body = await req.json()
    const { company_name, stock_code, week_label, overview, disclosures = [], news = [], all_events = [] } = body

    if (!company_name) {
      return NextResponse.json({ error: "company_name은 필수입니다." }, { status: 400 })
    }

    // 기존 Python 파이프라인을 계속 쓰고 싶을 때는 여기로 넘긴다.
    if (PYTHON_SERVICE_URL) {
      try {
        const res = await fetch(`${PYTHON_SERVICE_URL}/generate-briefing`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(body),
          signal: AbortSignal.timeout(60000),
        })
        if (res.ok) {
          const data = await res.json()
          return NextResponse.json(data)
        }
      } catch {
        // Fall through
      }
    }

    let briefing: WeeklyBriefing

    // OpenAI 호출이 실패해도 응답 자체는 끊기지 않게 fallback을 바로 붙여 둔다.
    try {
      briefing = await generateWithOpenAI(company_name, stock_code, week_label, disclosures, news)
    } catch {
      briefing = generateFallbackBriefing(company_name, week_label, disclosures, news)
    }

    const markdown = briefingToMarkdown(briefing)
    return NextResponse.json({ briefing, markdown })
  } catch (e: unknown) {
    return NextResponse.json(
      { error: e instanceof Error ? e.message : "서버 오류가 발생했습니다." },
      { status: 500 }
    )
  }
}
