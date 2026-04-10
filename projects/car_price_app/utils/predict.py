import pickle
import numpy as np
import pandas as pd
from utils.preprocess import build_model_input

MODEL_PATH = "models/xgb_quantile_models.pkl"
FEATURE_PATH = "models/model_features.pkl"

def load_artifacts():
    with open(MODEL_PATH, "rb") as f:
        models = pickle.load(f)

    with open(FEATURE_PATH, "rb") as f:
        model_features = pickle.load(f)

    return models, model_features

def predict_prices(form_data: dict):
    models, model_features = load_artifacts()

    row = build_model_input(form_data, model_features)
    X_input = pd.DataFrame([[row[col] for col in model_features]], columns=model_features)

    # 모델 예측값은 log(현재가격_만원) 스케일이므로 원래 스케일로 되돌려야 함
    pred_fast = float(np.expm1(models[0.05].predict(X_input)[0]))
    pred_mid = float(np.expm1(models[0.5].predict(X_input)[0]))
    pred_high = float(np.expm1(models[0.95].predict(X_input)[0]))

    # 혹시 분위수 순서가 꼬이는 경우를 방지
    preds = sorted([pred_fast, pred_mid, pred_high])

    return {
        "빠른 판매": round(preds[0], 0),
        "적정 판매": round(preds[1], 0),
        "최대 수익": round(preds[2], 0),
    }