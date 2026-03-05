from pathlib import Path
import joblib
import pandas as pd

BASE_DIR = Path(__file__).resolve().parent          # backend/
MODEL_DIR = BASE_DIR / "models"                    # backend/models
MODEL_PATH = MODEL_DIR / "lgbm_model.joblib"
FEATURE_PATH = MODEL_DIR / "feature_cols.joblib"

def _safe_load(path: Path):
    if not path.exists():
        raise RuntimeError(f"파일 없음: {path}")
    if path.stat().st_size == 0:
        raise RuntimeError(f"파일이 비어있음(0 bytes): {path}")
    return joblib.load(path)

model = _safe_load(MODEL_PATH)
feature_cols = _safe_load(FEATURE_PATH)

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

def prepare_input(df: pd.DataFrame) -> pd.DataFrame:
    df = build_features(df)
    return df.reindex(columns=feature_cols, fill_value=0)

def predict_count(df: pd.DataFrame) -> float:
    X = prepare_input(df)
    pred = float(model.predict(X)[0])
    return max(0.0, round(pred, 2))