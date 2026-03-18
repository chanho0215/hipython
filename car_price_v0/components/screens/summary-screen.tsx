"use client"

import { ChevronLeft, Car, Gauge, Fuel, Calendar, Shield, AlertTriangle, FileText, Droplets, Activity, Cog, Users, Palette, Settings, Edit3, Sun, Lightbulb, ParkingCircle, Video, Wind, Key, Navigation, Flame, Snowflake, Armchair, CheckCircle2 } from "lucide-react"

interface SummaryScreenProps {
  onBack: () => void
  onNext: () => void
  vehicleData: any
  isLoading?: boolean
}

const optionIcons: Record<string, typeof Sun> = {
  sunroof: Sun,
  ledHeadlamp: Lightbulb,
  parkingSensor: ParkingCircle,
  rearCamera: Video,
  autoAC: Wind,
  smartKey: Key,
  navigation: Navigation,
  heatedSeat: Flame,
  ventilatedSeat: Snowflake,
  leatherSeat: Armchair,
}

const optionLabels: Record<string, string> = {
  sunroof: "선루프",
  ledHeadlamp: "LED 헤드램프",
  parkingSensor: "주차감지센서",
  rearCamera: "후방카메라",
  autoAC: "자동에어컨",
  smartKey: "스마트키",
  navigation: "내비게이션",
  heatedSeat: "열선시트",
  ventilatedSeat: "통풍시트",
  leatherSeat: "가죽시트",
}

export function SummaryScreen({ onBack, onNext, vehicleData, isLoading = false }: SummaryScreenProps) {

  const InfoRow = ({ 
    icon: Icon, 
    label, 
    value, 
    alert = false,
    empty = false 
  }: { 
    icon: typeof Car
    label: string
    value: string
    alert?: boolean
    empty?: boolean
  }) => (
    <div className="flex items-center justify-between py-2.5">
      <div className="flex items-center gap-3">
        <Icon className={`w-4 h-4 ${alert ? "text-amber-500" : "text-muted-foreground"}`} />
        <span className="text-sm text-muted-foreground">{label}</span>
      </div>
      <span className={`text-sm font-medium ${
        alert ? "text-amber-600" : empty ? "text-muted-foreground/50" : "text-foreground"
      }`}>
        {empty ? "-" : value}
      </span>
    </div>
  )

  const SectionCard = ({ 
    title, 
    children,
    onEdit
  }: { 
    title: string
    children: React.ReactNode
    onEdit?: () => void
  }) => (
    <div className="bg-card rounded-2xl border border-border overflow-hidden">
      <div className="flex items-center justify-between px-5 py-3.5 bg-muted/30 border-b border-border">
        <h3 className="text-sm font-semibold text-foreground">{title}</h3>
        {onEdit && (
          <button 
            onClick={onEdit}
            className="flex items-center gap-1.5 text-xs font-medium text-primary hover:text-primary/80 transition-colors"
          >
            <Edit3 className="w-3.5 h-3.5" />
            수정
          </button>
        )}
      </div>
      <div className="px-5 py-2 divide-y divide-border/50">
        {children}
      </div>
    </div>
  )

  return (
    <div className="flex flex-col min-h-screen bg-background">
      {/* Header */}
      <header className="sticky top-0 z-10 bg-card/95 backdrop-blur-sm border-b border-border">
        <div className="flex items-center h-14 px-4">
          <button onClick={onBack} className="p-2 -ml-2 text-foreground" aria-label="뒤로가기">
            <ChevronLeft className="w-6 h-6" />
          </button>
          <h1 className="flex-1 text-center text-base font-semibold text-foreground">입력 정보 확인</h1>
          <div className="w-10" />
        </div>
        {/* Progress */}
        <div className="px-4 pb-4">
          <div className="flex items-center justify-between text-xs mb-2">
            <span className="text-muted-foreground">
              <span className="text-primary font-semibold">14</span>
              <span className="mx-1">/</span>
              <span>15</span>
            </span>
            <span className="text-muted-foreground">93%</span>
          </div>
          <div className="h-1.5 bg-muted rounded-full overflow-hidden">
            <div className="h-full bg-primary rounded-full" style={{ width: "93%" }} />
          </div>
        </div>
      </header>

      {/* Content */}
      <main className="flex-1 overflow-y-auto pb-28">
        <div className="p-4 space-y-4">
          {/* Vehicle Summary Header */}
          <div className="flex items-center gap-4 p-4 bg-card rounded-2xl border border-border">
            <div className="w-14 h-14 bg-primary/10 rounded-2xl flex items-center justify-center">
              <Car className="w-7 h-7 text-primary" />
            </div>
            <div className="flex-1">
              <h2 className="text-lg font-bold text-foreground">{vehicleData.manufacturer} {vehicleData.model}</h2>
              <p className="text-sm text-muted-foreground">
                {vehicleData.trim ? `${vehicleData.trim} · ` : ""}{vehicleData.year}년식 · {Number(vehicleData.mileage).toLocaleString()}km
              </p>
            </div>
          </div>

          {/* Basic Info */}
          <SectionCard title="차량 기본 정보" onEdit={onBack}>
            <InfoRow icon={Car} label="제조사" value={vehicleData.manufacturer} />
            <InfoRow icon={Car} label="모델" value={vehicleData.model} />
            <InfoRow icon={Settings} label="트림" value={vehicleData.trim} empty={!vehicleData.trim} />
            <InfoRow icon={Calendar} label="연식" value={`${vehicleData.year}년식`} />
            <InfoRow icon={Activity} label="배기량" value={`${Number(vehicleData.displacement).toLocaleString()}cc`} />
            <InfoRow icon={Fuel} label="연료" value={vehicleData.fuel} />
            <InfoRow icon={Cog} label="변속기" value={vehicleData.transmission} />
            <InfoRow icon={Settings} label="차급" value={vehicleData.vehicleClass} />
            <InfoRow icon={Users} label="좌석수" value={vehicleData.seats} />
            <InfoRow icon={Palette} label="색상" value={vehicleData.color} />
          </SectionCard>

          {/* Vehicle Status */}
          <SectionCard title="차량 상태" onEdit={onBack}>
            <InfoRow icon={Gauge} label="주행거리" value={`${Number(vehicleData.mileage).toLocaleString()}km`} />
            <InfoRow 
              icon={Shield} 
              label="사고 이력" 
              value={vehicleData.accident === "무사고" ? "무사고" : "있음"} 
              alert={vehicleData.accident !== "무사고"}
            />
          </SectionCard>

          {/* Accident Details */}
          {vehicleData.accident === "사고 이력 있음" && (
            <SectionCard title="사고 관련 정보" onEdit={onBack}>
              <InfoRow icon={AlertTriangle} label="교환 부위" value={vehicleData.exchangeCount} alert />
              <InfoRow icon={AlertTriangle} label="판금 부위" value={vehicleData.paintCount} alert />
              <InfoRow 
                icon={FileText} 
                label="보험 이력" 
                value={vehicleData.insuranceCount} 
                alert={vehicleData.insuranceCount !== "0건"}
              />
              <InfoRow 
                icon={Droplets} 
                label="부식 여부" 
                value={vehicleData.corrosion} 
                alert={vehicleData.corrosion !== "없음"}
              />
            </SectionCard>
          )}

          {/* Options */}
          <SectionCard title={`주요 옵션 (${vehicleData.options.length}개)`} onEdit={onBack}>
            {vehicleData.options.length > 0 ? (
              <div className="py-3">
                <div className="flex flex-wrap gap-2">
                  {vehicleData.options.map((optionId) => {
                    const Icon = optionIcons[optionId]
                    return (
                      <span key={optionId} className="inline-flex items-center gap-1.5 px-3 py-2 bg-primary/10 text-primary text-sm rounded-xl font-medium">
                        {Icon && <Icon className="w-4 h-4" />}
                        {optionLabels[optionId]}
                      </span>
                    )
                  })}
                </div>
              </div>
            ) : (
              <div className="py-4 text-center">
                <p className="text-sm text-muted-foreground">선택된 옵션이 없습니다</p>
              </div>
            )}
          </SectionCard>

          {/* Confirmation Note */}
          <div className="flex items-start gap-3 p-4 bg-primary/5 rounded-2xl border border-primary/20">
            <CheckCircle2 className="w-5 h-5 text-primary shrink-0 mt-0.5" />
            <div>
              <p className="text-sm font-semibold text-foreground mb-1">마지막으로 정보를 확인해주세요</p>
              <p className="text-xs text-muted-foreground leading-relaxed">
                입력한 정보를 바탕으로 AI가 적정 판매가를 분석합니다. 
                정확한 정보일수록 더 정밀한 가격을 받아볼 수 있어요.
              </p>
            </div>
          </div>
        </div>
      </main>

      {/* Bottom Buttons */}
            <div className="fixed bottom-0 left-0 right-0 bg-background border-t border-border p-4">
        <div className="max-w-[430px] mx-auto flex gap-3">
          <button
            type="button"
            onClick={onBack}
            className="flex-1 h-14 bg-muted text-foreground font-semibold rounded-2xl hover:bg-muted/80 transition-colors"
          >
            수정하기
          </button>

          <button
            type="button"
            onClick={onNext}
            disabled={isLoading}
            className="flex-1 h-14 bg-primary text-primary-foreground font-semibold rounded-2xl shadow-lg shadow-primary/20 hover:bg-primary/90 transition-colors disabled:opacity-60"
          >
            {isLoading ? "가격 계산 중..." : "가격 조회하기"}
          </button>
        </div>
      </div>
    </div>
  )
}