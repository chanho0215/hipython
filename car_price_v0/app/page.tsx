"use client"

import { useEffect, useState } from "react"
import { VehicleInputScreen } from "@/components/screens/vehicle-input-screen"
import { SummaryScreen } from "@/components/screens/summary-screen"
import { PriceResultScreen } from "@/components/screens/price-result-screen"

type VehicleFormData = {
  manufacturer: string
  model: string
  trim: string
  year: string
  displacement: string
  fuel: string
  transmission: string
  vehicleClass: string
  seats: string
  color: string
  mileage: string
  accident: string
  exchangeCount: string
  paintCount: string
  insuranceCount: string
  corrosion: string
  options: string[]
}

type PredictionData = {
  fastPrice: number
  fairPrice: number
  highPrice: number
}

const initialVehicleData: VehicleFormData = {
  manufacturer: "",
  model: "",
  trim: "",
  year: "",
  displacement: "",
  fuel: "",
  transmission: "",
  vehicleClass: "",
  seats: "",
  color: "",
  mileage: "",
  accident: "",
  exchangeCount: "",
  paintCount: "",
  insuranceCount: "",
  corrosion: "",
  options: [],
}

export default function Home() {
  const [currentScreen, setCurrentScreen] = useState<1 | 2 | 3>(1)
  const [vehicleData, setVehicleData] = useState<VehicleFormData>(initialVehicleData)
  const [prediction, setPrediction] = useState<PredictionData | null>(null)
  const [isLoading, setIsLoading] = useState(false)

  useEffect(() => {
    window.scrollTo({ top: 0, behavior: "smooth" })
  }, [currentScreen])
  const handleVehicleNext = (data: VehicleFormData) => {
    setVehicleData(data)
    setCurrentScreen(2)
  }

  const handleSummaryNext = async () => {
    try {
      setIsLoading(true)

      const res = await fetch("http://127.0.0.1:8000/predict", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify(vehicleData),
      })

      const result = await res.json()

      if (!res.ok) {
        throw new Error(result.detail || "예측 요청에 실패했습니다.")
      }

      setPrediction(result)
      setCurrentScreen(3)
    } catch (error) {
      const message =
        error instanceof Error ? error.message : "알 수 없는 오류가 발생했습니다."
      alert(message)
    } finally {
      setIsLoading(false)
    }
  }

  return (
    <div className="mx-auto max-w-[430px] min-h-screen bg-background shadow-2xl relative">
      <div className="absolute top-0 left-1/2 -translate-x-1/2 w-[120px] h-[30px] bg-foreground rounded-b-2xl z-50 pointer-events-none" />

      <div className="pt-[30px]">
        {currentScreen === 1 && (
          <VehicleInputScreen onNext={handleVehicleNext} />
        )}

        {currentScreen === 2 && (
          <SummaryScreen
            vehicleData={vehicleData}
            isLoading={isLoading}
            onBack={() => setCurrentScreen(1)}
            onNext={handleSummaryNext}
          />
        )}

        {currentScreen === 3 && (
          <PriceResultScreen
            vehicleData={vehicleData}
            prediction={prediction}
            onBack={() => setCurrentScreen(2)}
            onRegister={() => alert("등록 기능은 프로토타입에서 지원하지 않아요")}
          />
        )}
      </div>

      <div className="fixed bottom-4 left-1/2 -translate-x-1/2 z-50 flex items-center gap-2 px-4 py-2 bg-foreground/90 backdrop-blur-sm rounded-full shadow-lg">
        {[1, 2, 3].map((screen) => (
          <button
            key={screen}
            onClick={() => setCurrentScreen(screen as 1 | 2 | 3)}
            className={`w-8 h-8 rounded-full text-sm font-medium transition-all ${
              currentScreen === screen
                ? "bg-primary text-primary-foreground"
                : "bg-card/20 text-card hover:bg-card/30"
            }`}
          >
            {screen}
          </button>
        ))}
      </div>
    </div>
  )
}