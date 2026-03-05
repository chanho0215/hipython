from pathlib import Path
import joblib
import pandas as pd
from lightgbm import LGBMRegressor
from sklearn.model_selection import train_test_split

# 1. 데이터 불러오기
bike_pd = pd.read_csv("train.csv")  # 네 파일명에 맞게 수정

# 2. 피처 생성 함수
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

bike_pd = build_features(bike_pd)

# 3. X, y 분리
X = bike_pd.drop(columns=["datetime", "count", "casual", "registered"])
y = bike_pd["count"]

# 4. train / test 분리
X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, shuffle=False
)

# 5. 최종 모델 학습
lgbm = LGBMRegressor(
    n_estimators=500,
    learning_rate=0.05,
    max_depth=-1,
    num_leaves=31,
    subsample=0.8,
    colsample_bytree=0.8,
    random_state=0,
    n_jobs=-1
)

lgbm.fit(X_train, y_train)

# 6. 저장
model_dir = Path("models")
model_dir.mkdir(exist_ok=True)

joblib.dump(lgbm, model_dir / "lgbm_model.joblib")
joblib.dump(list(X_train.columns), model_dir / "feature_cols.joblib")

print("모델 저장 완료")
print("저장된 feature columns:")
print(list(X_train.columns))