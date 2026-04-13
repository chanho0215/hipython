"use client"

import { ArrowRight, FileText, Newspaper, Sparkles, TrendingUp, Shield, Clock } from "lucide-react"
import { Button } from "@/components/ui/button"

interface Props {
  onStart: () => void
}

const FEATURES = [
  {
    icon: FileText,
    title: "DART 공시 분석",
    description: "전자공시시스템에서 최신 공시를 자동으로 수집하고 핵심 내용을 요약합니다.",
  },
  {
    icon: Newspaper,
    title: "뉴스 모니터링",
    description: "네이버 뉴스에서 관련 기사를 검색하여 시장 반응과 이슈를 파악합니다.",
  },
  {
    icon: Sparkles,
    title: "AI 브리핑 생성",
    description: "수집된 정보를 AI가 분석하여 투자 판단에 필요한 핵심 포인트를 정리합니다.",
  },
]

const BENEFITS = [
  { icon: TrendingUp, text: "주요 이슈를 한눈에 파악" },
  { icon: Shield, text: "리스크 요인 사전 점검" },
  { icon: Clock, text: "분석 시간 대폭 단축" },
]

export function WelcomeStep({ onStart }: Props) {
  return (
    <div className="min-h-[80vh] flex items-center justify-center px-4">
      <div className="max-w-2xl w-full text-center">
        {/* Hero */}
        <div className="mb-10">
          <div className="inline-flex items-center gap-2 px-3 py-1.5 rounded-full bg-primary/10 text-primary text-xs font-semibold mb-6">
            <Sparkles className="w-3.5 h-3.5" />
            AI 기반 투자 리서치 도구
          </div>
          <h1 className="text-3xl md:text-4xl font-bold text-foreground leading-tight mb-4">
            주간 공시 · 뉴스 브리핑
          </h1>
          <p className="text-base text-muted-foreground leading-relaxed max-w-lg mx-auto">
            관심 종목의 DART 공시와 뉴스를 자동으로 수집하고,
            AI가 핵심 내용을 정리하여 투자 판단에 필요한 인사이트를 제공합니다.
          </p>
        </div>

        {/* Features */}
        <div className="grid md:grid-cols-3 gap-4 mb-10">
          {FEATURES.map((feature) => (
            <div
              key={feature.title}
              className="bg-card border border-border rounded-xl p-5 text-left"
            >
              <div className="w-9 h-9 rounded-lg bg-primary/10 flex items-center justify-center mb-3">
                <feature.icon className="w-4.5 h-4.5 text-primary" />
              </div>
              <h3 className="font-semibold text-foreground text-sm mb-1.5">{feature.title}</h3>
              <p className="text-xs text-muted-foreground leading-relaxed">{feature.description}</p>
            </div>
          ))}
        </div>

        {/* Benefits */}
        <div className="flex items-center justify-center gap-6 mb-10 flex-wrap">
          {BENEFITS.map((benefit) => (
            <div key={benefit.text} className="flex items-center gap-2 text-sm text-muted-foreground">
              <benefit.icon className="w-4 h-4 text-primary/70" />
              <span>{benefit.text}</span>
            </div>
          ))}
        </div>

        {/* CTA */}
        <Button size="lg" onClick={onStart} className="px-8 gap-2">
          시작하기
          <ArrowRight className="w-4 h-4" />
        </Button>

        <p className="text-xs text-muted-foreground mt-6">
          API 키 설정 없이도 데모 데이터로 체험할 수 있습니다.
        </p>
      </div>
    </div>
  )
}
