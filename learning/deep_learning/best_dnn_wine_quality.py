import argparse
import json
import os
import random
import warnings
from dataclasses import dataclass
from pathlib import Path

os.environ.setdefault("TF_CPP_MIN_LOG_LEVEL", "2")

warnings.filterwarnings("ignore")

import numpy as np
import pandas as pd
import tensorflow as tf
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix
from sklearn.model_selection import StratifiedKFold, train_test_split
from sklearn.preprocessing import RobustScaler, StandardScaler
from sklearn.utils.class_weight import compute_class_weight
from tensorflow import keras
from tensorflow.keras import layers, regularizers


DEFAULT_URL = (
    "https://archive.ics.uci.edu/ml/machine-learning-databases/"
    "wine-quality/winequality-red.csv"
)


@dataclass(frozen=True)
class FamilySpec:
    name: str
    mode: str
    scaler: str
    seeds: tuple[int, ...]
    hidden_units: tuple[int, ...]
    dropout: tuple[float, ...]
    l2_reg: float
    learning_rate: float
    batch_size: int
    noise: float


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Deep-learning-only high-accuracy pipeline for wine quality."
    )
    parser.add_argument("--data-path", type=str, default="")
    parser.add_argument("--test-size", type=float, default=0.20)
    parser.add_argument("--folds", type=int, default=7)
    parser.add_argument("--epochs", type=int, default=180)
    parser.add_argument("--base-seed", type=int, default=42)
    parser.add_argument("--output-json", type=str, default="best_dnn_wine_quality_results.json")
    parser.add_argument("--summary-dir", type=str, default="model_summaries")
    return parser.parse_args()


def set_seed(seed: int) -> None:
    os.environ["PYTHONHASHSEED"] = str(seed)
    random.seed(seed)
    np.random.seed(seed)
    tf.keras.utils.set_random_seed(seed)


def load_data(data_path: str) -> pd.DataFrame:
    if data_path and os.path.exists(data_path):
        df = pd.read_csv(data_path)
    else:
        try:
            df = pd.read_csv(DEFAULT_URL, sep=";")
        except Exception:
            if not data_path:
                raise
            df = pd.read_csv(data_path)
    df.columns = df.columns.str.strip()
    return df


def add_features(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()

    if {"fixed acidity", "volatile acidity", "citric acid"}.issubset(out.columns):
        out["total_acidity"] = (
            out["fixed acidity"] + out["volatile acidity"] + out["citric acid"]
        )
        out["fixed_to_volatile_ratio"] = out["fixed acidity"] / (
            out["volatile acidity"] + 1e-6
        )

    if {"free sulfur dioxide", "total sulfur dioxide"}.issubset(out.columns):
        out["sulfur_ratio"] = out["free sulfur dioxide"] / (
            out["total sulfur dioxide"] + 1.0
        )
        out["bound_sulfur"] = (
            out["total sulfur dioxide"] - out["free sulfur dioxide"]
        )

    if {"alcohol", "residual sugar"}.issubset(out.columns):
        out["alcohol_sugar_ratio"] = out["alcohol"] / (out["residual sugar"] + 1.0)

    if {"density", "alcohol"}.issubset(out.columns):
        out["density_alcohol_interaction"] = out["density"] * out["alcohol"]
        out["density_inverse"] = 1.0 / (out["density"] + 1e-6)

    if {"sulphates", "chlorides"}.issubset(out.columns):
        out["sulphates_chlorides_ratio"] = out["sulphates"] / (
            out["chlorides"] + 1e-6
        )

    if {"citric acid", "fixed acidity"}.issubset(out.columns):
        out["citric_fixed_ratio"] = out["citric acid"] / (
            out["fixed acidity"] + 1e-6
        )

    if {"alcohol", "sulphates"}.issubset(out.columns):
        out["alcohol_sulphates_interaction"] = out["alcohol"] * out["sulphates"]

    if {"pH", "fixed acidity"}.issubset(out.columns):
        out["acidity_ph_interaction"] = out["fixed acidity"] / (out["pH"] + 1e-6)

    if {"volatile acidity", "citric acid"}.issubset(out.columns):
        out["volatile_citric_balance"] = out["volatile acidity"] / (
            out["citric acid"] + 1e-6
        )

    if {"chlorides", "density"}.issubset(out.columns):
        out["chlorides_density_interaction"] = out["chlorides"] * out["density"]

    return out


def to_ordinal_targets(y: np.ndarray, classes: np.ndarray) -> np.ndarray:
    thresholds = classes[:-1]
    return (y[:, None] > thresholds[None, :]).astype(np.float32)


def ordinal_probs_to_score(probs: np.ndarray, classes: np.ndarray) -> np.ndarray:
    return np.full(probs.shape[0], classes.min(), dtype=np.float32) + probs.sum(axis=1)


def softmax_probs_to_score(probs: np.ndarray, classes: np.ndarray) -> np.ndarray:
    return (probs * classes[None, :]).sum(axis=1)


def scores_to_classes(scores: np.ndarray, thresholds: np.ndarray, classes: np.ndarray) -> np.ndarray:
    ordered_thresholds = np.sort(np.asarray(thresholds, dtype=np.float32))
    idx = np.digitize(scores, ordered_thresholds)
    return classes[idx]


def optimize_score_thresholds(
    scores: np.ndarray,
    y_true: np.ndarray,
    classes: np.ndarray,
    rounds: int = 8,
    grid_size: int = 81,
) -> tuple[np.ndarray, float]:
    thresholds = np.array(
        [(classes[i] + classes[i + 1]) / 2.0 for i in range(len(classes) - 1)],
        dtype=np.float32,
    )
    search_margin = 0.75
    best_acc = accuracy_score(y_true, scores_to_classes(scores, thresholds, classes))

    for _ in range(rounds):
        improved = False
        for idx in range(len(thresholds)):
            left_limit = classes.min() - 0.5 if idx == 0 else thresholds[idx - 1] + 0.02
            right_limit = (
                classes.max() + 0.5 if idx == len(thresholds) - 1 else thresholds[idx + 1] - 0.02
            )
            low = max(left_limit, thresholds[idx] - search_margin)
            high = min(right_limit, thresholds[idx] + search_margin)
            if low >= high:
                continue

            grid = np.linspace(low, high, grid_size)
            local_best_cut = thresholds[idx]
            local_best_acc = best_acc

            for cut in grid:
                candidate = thresholds.copy()
                candidate[idx] = cut
                pred = scores_to_classes(scores, candidate, classes)
                acc = accuracy_score(y_true, pred)
                if acc > local_best_acc:
                    local_best_acc = acc
                    local_best_cut = cut

            if local_best_acc > best_acc:
                thresholds[idx] = local_best_cut
                best_acc = local_best_acc
                improved = True

        search_margin *= 0.55
        if not improved:
            break

    return np.sort(thresholds), float(best_acc)


def make_scaler(name: str):
    if name == "standard":
        return StandardScaler()
    if name == "robust":
        return RobustScaler()
    raise ValueError(f"Unsupported scaler: {name}")


def dense_block(
    x: tf.Tensor,
    units: int,
    dropout_rate: float,
    l2_reg: float,
    activation: str = "swish",
) -> tf.Tensor:
    x = layers.Dense(
        units,
        kernel_regularizer=regularizers.l2(l2_reg),
        use_bias=False,
    )(x)
    x = layers.BatchNormalization()(x)
    x = layers.Activation(activation)(x)
    x = layers.Dropout(dropout_rate)(x)
    return x


def build_ordinal_model(input_dim: int, n_outputs: int, spec: FamilySpec) -> keras.Model:
    inputs = keras.Input(shape=(input_dim,))
    x = layers.GaussianNoise(spec.noise)(inputs)
    shortcut = None
    for units, drop in zip(spec.hidden_units, spec.dropout):
        block = dense_block(x, units, drop, spec.l2_reg)
        if shortcut is not None and shortcut.shape[-1] == block.shape[-1]:
            x = layers.Add()([shortcut, block])
        else:
            x = block
        shortcut = x

    outputs = layers.Dense(n_outputs, activation="sigmoid")(x)
    model = keras.Model(inputs, outputs, name=spec.name)
    model.compile(
        optimizer=keras.optimizers.AdamW(
            learning_rate=spec.learning_rate,
            weight_decay=spec.l2_reg,
        ),
        loss=keras.losses.BinaryCrossentropy(),
    )
    return model


def build_softmax_model(input_dim: int, n_classes: int, spec: FamilySpec) -> keras.Model:
    inputs = keras.Input(shape=(input_dim,))
    x = layers.GaussianNoise(spec.noise)(inputs)
    for units, drop in zip(spec.hidden_units, spec.dropout):
        x = dense_block(x, units, drop, spec.l2_reg, activation="gelu")
    outputs = layers.Dense(n_classes, activation="softmax")(x)
    model = keras.Model(inputs, outputs, name=spec.name)
    model.compile(
        optimizer=keras.optimizers.AdamW(
            learning_rate=spec.learning_rate,
            weight_decay=spec.l2_reg,
        ),
        loss=keras.losses.CategoricalCrossentropy(label_smoothing=0.03),
    )
    return model


def build_regression_model(input_dim: int, spec: FamilySpec) -> keras.Model:
    inputs = keras.Input(shape=(input_dim,))
    x = layers.GaussianNoise(spec.noise)(inputs)
    shortcut = None
    for units, drop in zip(spec.hidden_units, spec.dropout):
        block = dense_block(x, units, drop, spec.l2_reg)
        if shortcut is not None and shortcut.shape[-1] == block.shape[-1]:
            x = layers.Add()([shortcut, block])
        else:
            x = block
        shortcut = x

    outputs = layers.Dense(1, activation="linear")(x)
    model = keras.Model(inputs, outputs, name=spec.name)
    model.compile(
        optimizer=keras.optimizers.AdamW(
            learning_rate=spec.learning_rate,
            weight_decay=spec.l2_reg,
        ),
        loss=keras.losses.Huber(delta=0.8),
        metrics=[keras.metrics.MeanAbsoluteError(name="mae")],
    )
    return model


def build_model(spec: FamilySpec, input_dim: int, classes: np.ndarray) -> keras.Model:
    if spec.mode == "ordinal":
        return build_ordinal_model(input_dim, len(classes) - 1, spec)
    if spec.mode == "softmax":
        return build_softmax_model(input_dim, len(classes), spec)
    if spec.mode == "regression":
        return build_regression_model(input_dim, spec)
    raise ValueError(f"Unsupported mode: {spec.mode}")


def save_model_summaries(
    specs: list[FamilySpec],
    input_dim: int,
    classes: np.ndarray,
    summary_dir: str,
) -> None:
    output_dir = Path(summary_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    for spec in specs:
        tf.keras.backend.clear_session()
        model = build_model(spec, input_dim, classes)

        summary_lines = []
        model.summary(print_fn=summary_lines.append)
        summary_text = "\n".join(summary_lines)

        print(f"\n=== Model Summary: {spec.name} ===")
        print(summary_text)

        summary_path = output_dir / f"{spec.name}_summary.txt"
        summary_path.write_text(summary_text + "\n", encoding="utf-8")


def prepare_targets(spec: FamilySpec, y_train: np.ndarray, y_val: np.ndarray, classes: np.ndarray):
    if spec.mode == "ordinal":
        return to_ordinal_targets(y_train, classes), to_ordinal_targets(y_val, classes)
    if spec.mode == "softmax":
        train_idx = np.searchsorted(classes, y_train)
        val_idx = np.searchsorted(classes, y_val)
        return keras.utils.to_categorical(train_idx, len(classes)), keras.utils.to_categorical(
            val_idx, len(classes)
        )
    if spec.mode == "regression":
        return y_train.astype(np.float32), y_val.astype(np.float32)
    raise ValueError(f"Unsupported mode: {spec.mode}")


def prediction_to_score(pred: np.ndarray, spec: FamilySpec, classes: np.ndarray) -> np.ndarray:
    if spec.mode == "ordinal":
        return ordinal_probs_to_score(pred, classes)
    if spec.mode == "softmax":
        return softmax_probs_to_score(pred, classes)
    if spec.mode == "regression":
        return pred.reshape(-1)
    raise ValueError(f"Unsupported mode: {spec.mode}")


def class_sample_weights(y: np.ndarray) -> dict[int, float]:
    weights = compute_class_weight(
        class_weight="balanced",
        classes=np.unique(y),
        y=y,
    )
    return dict(zip(np.unique(y), weights))


def fit_family(
    spec: FamilySpec,
    X_train: pd.DataFrame,
    X_test: pd.DataFrame,
    y_train: np.ndarray,
    classes: np.ndarray,
    folds: int,
    epochs: int,
    base_seed: int,
) -> tuple[np.ndarray, np.ndarray]:
    scaler = make_scaler(spec.scaler)
    X_train_scaled = scaler.fit_transform(X_train).astype(np.float32)
    X_test_scaled = scaler.transform(X_test).astype(np.float32)

    oof_seed_scores = []
    test_seed_scores = []
    sample_weight_map = class_sample_weights(y_train)

    for seed_offset, local_seed in enumerate(spec.seeds):
        skf = StratifiedKFold(
            n_splits=folds,
            shuffle=True,
            random_state=base_seed + local_seed * 101,
        )

        oof_scores = np.zeros(len(X_train_scaled), dtype=np.float32)
        fold_test_scores = []

        for fold_idx, (tr_idx, val_idx) in enumerate(skf.split(X_train_scaled, y_train), start=1):
            seed = base_seed + local_seed * 1000 + fold_idx
            set_seed(seed)
            tf.keras.backend.clear_session()

            x_tr = X_train_scaled[tr_idx]
            x_val = X_train_scaled[val_idx]
            y_tr = y_train[tr_idx]
            y_val = y_train[val_idx]

            train_target, val_target = prepare_targets(spec, y_tr, y_val, classes)
            model = build_model(spec, X_train_scaled.shape[1], classes)

            callbacks = [
                keras.callbacks.EarlyStopping(
                    monitor="val_loss",
                    patience=12,
                    min_delta=0.0007,
                    restore_best_weights=True,
                    verbose=0,
                ),
                keras.callbacks.ReduceLROnPlateau(
                    monitor="val_loss",
                    factor=0.5,
                    patience=4,
                    min_lr=1e-6,
                    verbose=0,
                ),
            ]

            sample_weights = np.array([sample_weight_map[v] for v in y_tr], dtype=np.float32)

            model.fit(
                x_tr,
                train_target,
                validation_data=(x_val, val_target),
                sample_weight=sample_weights,
                epochs=epochs,
                batch_size=spec.batch_size,
                callbacks=callbacks,
                verbose=0,
            )

            val_pred = model.predict(x_val, verbose=0)
            test_pred = model.predict(X_test_scaled, verbose=0)

            oof_scores[val_idx] = prediction_to_score(val_pred, spec, classes)
            fold_test_scores.append(prediction_to_score(test_pred, spec, classes))

        oof_seed_scores.append(oof_scores)
        test_seed_scores.append(np.mean(fold_test_scores, axis=0))

    return (
        np.mean(oof_seed_scores, axis=0).astype(np.float32),
        np.mean(test_seed_scores, axis=0).astype(np.float32),
    )


def optimize_blend_weights(
    train_scores: dict[str, np.ndarray],
    y_true: np.ndarray,
    classes: np.ndarray,
) -> tuple[dict[str, float], np.ndarray, float]:
    names = list(train_scores.keys())
    grids = np.linspace(0.0, 1.0, 11)
    best_weights = None
    best_thresholds = None
    best_acc = -1.0

    for w0 in grids:
        for w1 in grids:
            w2 = 1.0 - w0 - w1
            if w2 < 0.0 or w2 > 1.0:
                continue

            weights = np.array([w0, w1, w2], dtype=np.float32)
            if np.isclose(weights.sum(), 0.0):
                continue

            blended = np.zeros_like(next(iter(train_scores.values())))
            for idx, name in enumerate(names):
                blended += weights[idx] * train_scores[name]

            thresholds, acc = optimize_score_thresholds(blended, y_true, classes)
            if acc > best_acc:
                best_acc = acc
                best_thresholds = thresholds
                best_weights = {name: float(weights[idx]) for idx, name in enumerate(names)}

    return best_weights, best_thresholds, best_acc


def evaluate_split(
    name: str,
    scores: np.ndarray,
    thresholds: np.ndarray,
    y_true: np.ndarray,
    classes: np.ndarray,
) -> dict:
    pred = scores_to_classes(scores, thresholds, classes)
    return {
        "name": name,
        "accuracy": float(accuracy_score(y_true, pred)),
        "within_1": float(np.mean(np.abs(pred - y_true) <= 1)),
        "confusion_matrix": confusion_matrix(y_true, pred).tolist(),
        "classification_report": classification_report(y_true, pred, digits=4),
    }


def main() -> None:
    args = parse_args()
    set_seed(args.base_seed)

    df = add_features(load_data(args.data_path))
    X = df.drop(columns=["quality"]).copy()
    y = df["quality"].astype(int).values
    classes = np.sort(np.unique(y))

    X_train, X_test, y_train, y_test = train_test_split(
        X,
        y,
        test_size=args.test_size,
        random_state=args.base_seed,
        stratify=y,
    )
    X_train = X_train.reset_index(drop=True)
    X_test = X_test.reset_index(drop=True)

    family_specs = [
        FamilySpec(
            name="ordinal_std",
            mode="ordinal",
            scaler="standard",
            seeds=(0, 1, 2),
            hidden_units=(256, 192, 128, 64),
            dropout=(0.18, 0.14, 0.10, 0.06),
            l2_reg=3e-4,
            learning_rate=7e-4,
            batch_size=32,
            noise=0.03,
        ),
        FamilySpec(
            name="softmax_robust",
            mode="softmax",
            scaler="robust",
            seeds=(0, 1, 2),
            hidden_units=(192, 128, 96),
            dropout=(0.16, 0.10, 0.06),
            l2_reg=4e-4,
            learning_rate=8e-4,
            batch_size=32,
            noise=0.02,
        ),
        FamilySpec(
            name="regression_std",
            mode="regression",
            scaler="standard",
            seeds=(0, 1, 2),
            hidden_units=(256, 160, 96, 48),
            dropout=(0.15, 0.10, 0.08, 0.04),
            l2_reg=3e-4,
            learning_rate=6e-4,
            batch_size=32,
            noise=0.025,
        ),
    ]

    save_model_summaries(
        specs=family_specs,
        input_dim=X_train.shape[1],
        classes=classes,
        summary_dir=args.summary_dir,
    )

    train_scores = {}
    test_scores = {}
    family_metrics = []

    for spec in family_specs:
        print(f"\n=== Training family: {spec.name} ({spec.mode}) ===")
        oof_scores, holdout_scores = fit_family(
            spec=spec,
            X_train=X_train,
            X_test=X_test,
            y_train=y_train,
            classes=classes,
            folds=args.folds,
            epochs=args.epochs,
            base_seed=args.base_seed,
        )
        thresholds, train_acc = optimize_score_thresholds(oof_scores, y_train, classes)
        metric = evaluate_split(spec.name, holdout_scores, thresholds, y_test, classes)
        metric["train_oof_accuracy"] = float(train_acc)
        metric["thresholds"] = [float(x) for x in thresholds]

        train_scores[spec.name] = oof_scores
        test_scores[spec.name] = holdout_scores
        family_metrics.append(metric)

        print(
            f"{spec.name}: OOF={train_acc:.4f} | "
            f"TEST={metric['accuracy']:.4f} | "
            f"within_1={metric['within_1']:.4f}"
        )

    blend_weights, blend_thresholds, blend_oof_acc = optimize_blend_weights(
        train_scores, y_train, classes
    )
    blended_test_scores = np.zeros_like(next(iter(test_scores.values())))
    for name, weight in blend_weights.items():
        blended_test_scores += weight * test_scores[name]

    blend_metric = evaluate_split(
        "deep_blend",
        blended_test_scores,
        blend_thresholds,
        y_test,
        classes,
    )
    blend_metric["train_oof_accuracy"] = float(blend_oof_acc)
    blend_metric["thresholds"] = [float(x) for x in blend_thresholds]
    blend_metric["weights"] = blend_weights

    results = {
        "data_shape": list(df.shape),
        "train_size": int(len(X_train)),
        "test_size": int(len(X_test)),
        "classes": classes.tolist(),
        "family_results": family_metrics,
        "blend_result": blend_metric,
    }

    print("\n=== Blend Summary ===")
    print(json.dumps(blend_metric, ensure_ascii=False, indent=2))

    with open(args.output_json, "w", encoding="utf-8") as fp:
        json.dump(results, fp, ensure_ascii=False, indent=2)

    print(f"\nSaved results to {args.output_json}")


if __name__ == "__main__":
    main()
