from pathlib import Path
import joblib
import pandas as pd
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

app = FastAPI(
    title="Bike Demand Prediction API",
    version="1.0.0",
    description="LightGBM 기반 자전거 대여 수요 예측 API"
)

MODEL_DIR = Path("models")
MODEL_PATH = MODEL_DIR / "lgbm_model.joblib"
FEATURE_PATH = MODEL_DIR / "feature_cols.joblib"

# 서버 시작 시 모델 로드
if not MODEL_PATH.exists() or not FEATURE_PATH.exists():
    raise RuntimeError("모델 파일이 없습니다. 먼저 train_service_model.py를 실행하세요.")

model = joblib.load(MODEL_PATH)
feature_cols = joblib.load(FEATURE_PATH)

class PredictInput(BaseModel):
    datetime: str = Field(..., example="2012-12-19 17:00:00")
    season: int = Field(..., example=4)
    holiday: int = Field(..., example=0)
    workingday: int = Field(..., example=1)
    weather: int = Field(..., example=1)
    temp: float = Field(..., example=10.66)
    atemp: float = Field(..., example=11.365)
    humidity: float = Field(..., example=56.0)
    windspeed: float = Field(..., example=26.0027)

class PredictOutput(BaseModel):
    predicted_count: float

def build_features(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df["datetime"] = pd.to_datetime(df["datetime"])

    df["year"] = df["datetime"].dt.year
    df["month"] = df["datetime"].dt.month
    df["day"] = df["datetime"].dt.day
    df["hour"] = df["datetime"].dt.hour
    df["dayofweek"] = df["datetime"].dt.dayofweek
    df["is_weekend"] = (df["dayofweek"] >= 5).astype(int)

    return df

@app.get("/health")
def health_check():
    return {"status": "ok"}

@app.post("/predict", response_model=PredictOutput)
def predict(payload: PredictInput):
    try:
        input_df = pd.DataFrame([payload.model_dump()])
        input_df = build_features(input_df)

        X = input_df.reindex(columns=feature_cols, fill_value=0)
        prediction = float(model.predict(X)[0])

        # 음수 예측 방지
        prediction = max(0.0, prediction)

        return PredictOutput(predicted_count=round(prediction, 2))

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"예측 중 오류 발생: {str(e)}")