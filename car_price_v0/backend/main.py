from pathlib import Path
import pickle
import numpy as np
import pandas as pd

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from preprocess import build_model_input

BASE_DIR = Path(__file__).resolve().parent
MODEL_PATH = BASE_DIR / "models" / "xgb_quantile_models.pkl"
FEATURE_PATH = BASE_DIR / "models" / "model_features.pkl"

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class PredictRequest(BaseModel):
    manufacturer: str
    model: str
    trim: str = ""
    year: str
    displacement: str
    fuel: str
    transmission: str
    vehicleClass: str
    seats: str
    color: str
    mileage: str
    accident: str
    exchangeCount: str = "없음"
    paintCount: str = "없음"
    insuranceCount: str = "없음"
    corrosion: str = "없음"
    options: list[str] = []

def load_artifacts():
    with open(MODEL_PATH, "rb") as f:
        models = pickle.load(f)

    with open(FEATURE_PATH, "rb") as f:
        model_features = pickle.load(f)

    return models, model_features

@app.get("/health")
def health():
    return {"status": "ok"}

@app.post("/predict")
def predict(req: PredictRequest):
    if req.fuel == "전기":
        raise HTTPException(status_code=400, detail="현재 전기차는 지원하지 않습니다.")

    try:
        models, model_features = load_artifacts()
        form_data = req.model_dump()

        row = build_model_input(form_data, model_features)
        X_input = pd.DataFrame([[row[col] for col in model_features]], columns=model_features)

        pred_fast = float(np.expm1(models[0.05].predict(X_input)[0]))
        pred_mid = float(np.expm1(models[0.5].predict(X_input)[0]))
        pred_high = float(np.expm1(models[0.95].predict(X_input)[0]))

        preds = sorted([pred_fast, pred_mid, pred_high])

        return {
            "fastPrice": round(preds[0], 0),
            "fairPrice": round(preds[1], 0),
            "highPrice": round(preds[2], 0),
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))