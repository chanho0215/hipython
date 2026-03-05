from fastapi import FastAPI, HTTPException
import pandas as pd

from backend.schemas import PredictInput, PredictOutput
from backend.model_utils import predict_count
from backend.db import init_db, save_log
from backend.weather import get_weather

app = FastAPI(title="Bike Demand API")

init_db()

@app.get("/health")
def health():
    return {"status": "ok"}

@app.get("/weather")
def weather(city: str, date: str, hour: int):
    try:
        return get_weather(city, date, hour)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/predict", response_model=PredictOutput)
def predict(payload: PredictInput):
    try:
        df = pd.DataFrame([payload.model_dump()])
        pred = predict_count(df)
        save_log(payload.model_dump(), pred)
        return PredictOutput(predicted_count=pred)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
      
from backend.db import init_db, save_log, get_logs  # get_logs 추가

@app.get("/logs")
def logs(limit: int = 50):
    return get_logs(limit)