import argparse
from datetime import datetime
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from sklearn.dummy import DummyClassifier
from sklearn.ensemble import ExtraTreesClassifier, GradientBoostingClassifier, RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    accuracy_score,
    average_precision_score,
    confusion_matrix,
    f1_score,
    precision_recall_curve,
    precision_score,
    recall_score,
    roc_auc_score,
)
from sklearn.model_selection import StratifiedKFold, cross_val_score, train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

RANDOM_STATE = 42


def dataframe_to_markdown_table(df: pd.DataFrame) -> str:
    cols = list(df.columns)
    header = "| " + " | ".join(cols) + " |"
    sep = "| " + " | ".join(["---"] * len(cols)) + " |"

    rows = []
    for _, row in df.iterrows():
        vals = []
        for c in cols:
            v = row[c]
            if isinstance(v, float):
                vals.append(f"{v:.6f}")
            else:
                vals.append(str(v))
        rows.append("| " + " | ".join(vals) + " |")

    return "\n".join([header, sep, *rows])


def load_credit_data(data_path: Path) -> tuple[pd.DataFrame, pd.Series]:
    df = pd.read_csv(data_path)

    # Original UCI file uses this column name before renaming.
    if "default payment next month" in df.columns:
        df = df.rename(columns={"default payment next month": "default"})

    if "default" not in df.columns:
        raise ValueError("Target column not found. Expected 'default' or 'default payment next month'.")

    if "ID" in df.columns:
        df = df.drop(columns=["ID"])

    y = df["default"].astype(int)
    X = df.drop(columns=["default"])
    return X, y


def evaluate_at_threshold(y_true: pd.Series, y_proba: np.ndarray, threshold: float) -> dict:
    y_pred = (y_proba >= threshold).astype(int)
    tn, fp, fn, tp = confusion_matrix(y_true, y_pred).ravel()

    return {
        "threshold": threshold,
        "accuracy": accuracy_score(y_true, y_pred),
        "precision": precision_score(y_true, y_pred, zero_division=0),
        "recall": recall_score(y_true, y_pred, zero_division=0),
        "f1": f1_score(y_true, y_pred, zero_division=0),
        "tn": int(tn),
        "fp": int(fp),
        "fn": int(fn),
        "tp": int(tp),
    }


def best_f1_threshold(y_true: pd.Series, y_proba: np.ndarray) -> tuple[float, float]:
    precision, recall, thresholds = precision_recall_curve(y_true, y_proba)
    # precision_recall_curve returns len(thresholds)+1 points for precision/recall.
    f1_values = (2 * precision[:-1] * recall[:-1]) / (precision[:-1] + recall[:-1] + 1e-12)
    best_idx = int(np.argmax(f1_values))
    return float(thresholds[best_idx]), float(f1_values[best_idx])


def build_models() -> dict[str, object]:
    return {
        "dummy_most_frequent": DummyClassifier(strategy="most_frequent"),
        "logistic_regression": Pipeline(
            steps=[
                ("scaler", StandardScaler()),
                (
                    "model",
                    LogisticRegression(
                        max_iter=2000,
                        class_weight="balanced",
                        random_state=RANDOM_STATE,
                    ),
                ),
            ]
        ),
        "random_forest": RandomForestClassifier(
            n_estimators=350,
            max_depth=None,
            min_samples_leaf=2,
            class_weight="balanced_subsample",
            random_state=RANDOM_STATE,
            n_jobs=1,
        ),
        "extra_trees": ExtraTreesClassifier(
            n_estimators=400,
            min_samples_leaf=2,
            class_weight="balanced",
            random_state=RANDOM_STATE,
            n_jobs=1,
        ),
        "gradient_boosting": GradientBoostingClassifier(
            n_estimators=350,
            learning_rate=0.05,
            random_state=RANDOM_STATE,
        ),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Train and compare credit-default classification models.")
    parser.add_argument(
        "--data",
        type=Path,
        default=Path("ml/data/UCI_Credit_Card.csv"),
        help="Path to the training data CSV.",
    )
    parser.add_argument(
        "--report-dir",
        type=Path,
        default=Path("ml/reports/credit_default"),
        help="Directory to save reports and best model artifacts.",
    )
    args = parser.parse_args()

    X, y = load_credit_data(args.data)

    X_train, X_test, y_train, y_test = train_test_split(
        X,
        y,
        test_size=0.2,
        stratify=y,
        random_state=RANDOM_STATE,
    )

    cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=RANDOM_STATE)
    models = build_models()

    rows = []
    fitted_models = {}

    for model_name, model in models.items():
        model.fit(X_train, y_train)
        y_proba = model.predict_proba(X_test)[:, 1]

        roc_auc = roc_auc_score(y_test, y_proba)
        pr_auc = average_precision_score(y_test, y_proba)
        cv_roc_auc = float(np.mean(cross_val_score(model, X_train, y_train, scoring="roc_auc", cv=cv, n_jobs=1)))

        thr_f1, best_f1 = best_f1_threshold(y_test, y_proba)
        metrics_05 = evaluate_at_threshold(y_test, y_proba, threshold=0.50)
        metrics_best = evaluate_at_threshold(y_test, y_proba, threshold=thr_f1)

        row = {
            "model": model_name,
            "test_roc_auc": roc_auc,
            "test_pr_auc": pr_auc,
            "cv_roc_auc_mean": cv_roc_auc,
            "positive_rate_pred@0.5": float((y_proba >= 0.5).mean()),
            "accuracy@0.5": metrics_05["accuracy"],
            "precision@0.5": metrics_05["precision"],
            "recall@0.5": metrics_05["recall"],
            "f1@0.5": metrics_05["f1"],
            "best_f1_threshold": thr_f1,
            "precision@best_f1": metrics_best["precision"],
            "recall@best_f1": metrics_best["recall"],
            "f1@best_f1": best_f1,
            "tn@0.5": metrics_05["tn"],
            "fp@0.5": metrics_05["fp"],
            "fn@0.5": metrics_05["fn"],
            "tp@0.5": metrics_05["tp"],
        }
        rows.append(row)
        fitted_models[model_name] = model

    results = pd.DataFrame(rows).sort_values(by=["test_roc_auc", "test_pr_auc"], ascending=False)

    best_model_name = results.iloc[0]["model"]
    best_model = fitted_models[best_model_name]

    args.report_dir.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    csv_path = args.report_dir / f"model_comparison_{timestamp}.csv"
    md_path = args.report_dir / f"model_comparison_{timestamp}.md"
    model_path = args.report_dir / f"best_model_{best_model_name}_{timestamp}.joblib"

    results.to_csv(csv_path, index=False)
    joblib.dump(best_model, model_path)

    lines = [
        "# Credit Default Model Comparison",
        "",
        f"- Data: `{args.data}`",
        f"- Train size: {len(X_train):,}",
        f"- Test size: {len(X_test):,}",
        f"- Target positive ratio (default=1): {y.mean():.4f}",
        f"- Best model by ROC-AUC: `{best_model_name}`",
        f"- Best model file: `{model_path}`",
        "",
        "## Metrics",
        "",
        dataframe_to_markdown_table(results),
    ]
    md_path.write_text("\n".join(lines), encoding="utf-8")

    print(f"Saved CSV report: {csv_path}")
    print(f"Saved Markdown report: {md_path}")
    print(f"Saved best model: {model_path}")


if __name__ == "__main__":
    main()
