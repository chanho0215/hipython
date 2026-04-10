from pathlib import Path
import joblib
import pandas as pd
from src.features import build_features

BASE_DIR = Path(__file__).resolve().parent.parent   # 프로젝트 루트
MODEL_DIR = BASE_DIR / "models"
MODEL_PATH = MODEL_DIR / "lgbm_model.joblib"
FEATURE_PATH = MODEL_DIR / "feature_cols.joblib"

def _safe_load(path: Path):
    if not path.exists():
        raise FileNotFoundError(f"파일 없음: {path}")
    if path.stat().st_size == 0:
        raise RuntimeError(f"파일이 비어있음(0 bytes): {path}")
    return joblib.load(path)

@joblib.memory.Memory(location=None, verbose=0).cache
def load_artifacts():
    model = _safe_load(MODEL_PATH)
    feature_cols = _safe_load(FEATURE_PATH)
    return model, feature_cols

def prepare_input(raw: dict) -> pd.DataFrame:
    df = pd.DataFrame([raw])
    df = build_features(df)

    _, feature_cols = load_artifacts()
    X = df.reindex(columns=feature_cols, fill_value=0)
    return X

def predict_count(raw: dict) -> float:
    model, _ = load_artifacts()
    X = prepare_input(raw)
    pred = float(model.predict(X)[0])
    return max(0.0, round(pred, 2))