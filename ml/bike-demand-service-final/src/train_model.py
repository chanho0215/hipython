from pathlib import Path
import joblib
import numpy as np
import pandas as pd

from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score

import lightgbm as lgb


# -----------------------
# 경로
# -----------------------
BASE_DIR = Path(__file__).resolve().parent
DATA_PATH = BASE_DIR / "train.csv"   # ✅ 너 데이터 파일 위치에 맞춰 수정
MODEL_DIR = BASE_DIR / "models"
MODEL_DIR.mkdir(exist_ok=True)

MODEL_PATH = MODEL_DIR / "lgbm_model.joblib"
FEATURE_PATH = MODEL_DIR / "feature_cols.joblib"


# -----------------------
# 데이터 로드
# -----------------------
df = pd.read_csv(DATA_PATH, encoding="euc-kr")

# datetime 처리
df["datetime"] = pd.to_datetime(df["datetime"])
df["year"] = df["datetime"].dt.year
df["month"] = df["datetime"].dt.month
df["day"] = df["datetime"].dt.day
df["hour"] = df["datetime"].dt.hour
df["dayofweek"] = df["datetime"].dt.dayofweek
df["is_weekend"] = (df["dayofweek"] >= 5).astype(int)

# 타겟
y = df["count"].values

# 피처 선택 (count 제외, datetime 제외)
drop_cols = ["count", "datetime", "casual", "registered"]  # 원본 데이터에 있을 경우 대비
X = df.drop(columns=[c for c in drop_cols if c in df.columns])

feature_cols = list(X.columns)

# train/test split (시간 순서 유지하고 싶으면 shuffle=False)
X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, shuffle=False
)

# -----------------------
# 모델 학습
# -----------------------
model = lgb.LGBMRegressor(
    n_estimators=800,
    learning_rate=0.05,
    max_depth=-1,
    num_leaves=63,
    subsample=0.9,
    colsample_bytree=0.9,
    random_state=0
)

model.fit(X_train, y_train)

# -----------------------
# 평가
# -----------------------
pred = model.predict(X_test)
mae = mean_absolute_error(y_test, pred)
rmse = np.sqrt(mean_squared_error(y_test, pred))
r2 = r2_score(y_test, pred)

print("MAE:", round(mae, 4))
print("RMSE:", round(rmse, 4))
print("R2:", round(r2, 4))

# -----------------------
# 저장
# -----------------------
joblib.dump(model, MODEL_PATH)
joblib.dump(feature_cols, FEATURE_PATH)

print("Saved model to:", MODEL_PATH, "size:", MODEL_PATH.stat().st_size)
print("Saved feature cols to:", FEATURE_PATH, "size:", FEATURE_PATH.stat().st_size)