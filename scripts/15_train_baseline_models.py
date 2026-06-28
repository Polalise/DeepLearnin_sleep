from __future__ import annotations

from datetime import datetime
from pathlib import Path

import joblib
import matplotlib.pyplot as plt
import pandas as pd
from sklearn.decomposition import PCA
from sklearn.dummy import DummyClassifier
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    accuracy_score,
    average_precision_score,
    balanced_accuracy_score,
    confusion_matrix,
    f1_score,
    precision_score,
    recall_score,
    roc_auc_score,
    roc_curve,
)
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler


# This script trains first baseline classification models.
#
# Modeling unit:
# - Use the participant-aware split created by 14_create_participant_split.py.
# - Predict good_sleep_label from encoded feature columns.
# - Fit preprocessing steps only on the train split inside sklearn pipelines.
#
# Boundary:
# - This is a baseline, not final model selection.
# - Hyperparameter tuning and cross-validation are intentionally left for later.
PROJECT_ROOT = Path(__file__).resolve().parents[1]
TRAIN_PATH = PROJECT_ROOT / "data" / "processed" / "splits" / "train_participant_split.csv"
TEST_PATH = PROJECT_ROOT / "data" / "processed" / "splits" / "test_participant_split.csv"
FEATURE_COLUMNS_PATH = PROJECT_ROOT / "data" / "processed" / "encoded_feature_columns.csv"
PREDICTIONS_PATH = PROJECT_ROOT / "data" / "processed" / "baseline_model_predictions.csv"
METRICS_PATH = PROJECT_ROOT / "data" / "processed" / "baseline_model_metrics.csv"
RF_IMPORTANCE_PATH = PROJECT_ROOT / "data" / "processed" / "baseline_random_forest_feature_importance.csv"
MODELS_PATH = PROJECT_ROOT / "data" / "processed" / "baseline_models.joblib"
REPORT_PATH = PROJECT_ROOT / "reports" / "baseline_modeling_summary.md"
FIGURE_DIR = PROJECT_ROOT / "reports" / "figures" / "baseline"

KEY_COLUMNS = ["participant_object_id", "calendar_date"]
TARGET_COLUMN = "good_sleep_label"
RANDOM_STATE = 42


def load_feature_columns() -> list[str]:
    """Load feature columns finalized by the categorical-encoding step."""

    feature_metadata = pd.read_csv(FEATURE_COLUMNS_PATH)
    if "feature" not in feature_metadata.columns:
        raise ValueError(f"`feature` column is missing from {FEATURE_COLUMNS_PATH}")
    return feature_metadata["feature"].tolist()


def validate_modeling_inputs(
    train: pd.DataFrame,
    test: pd.DataFrame,
    feature_columns: list[str],
) -> None:
    """Check split integrity and feature readiness before fitting baseline models."""

    for split_name, split_df in [("train", train), ("test", test)]:
        missing_features = [column for column in feature_columns if column not in split_df.columns]
        if missing_features:
            raise ValueError(f"{split_name} missing features: {missing_features[:10]}")

        missing_cells = int(split_df[feature_columns + [TARGET_COLUMN]].isna().sum().sum())
        if missing_cells:
            raise ValueError(f"{split_name} contains {missing_cells} missing modeling cells.")

        target_values = sorted(split_df[TARGET_COLUMN].unique().tolist())
        if target_values != [0, 1]:
            raise ValueError(f"{split_name} target should contain both classes, got {target_values}")

    overlap = set(train["participant_object_id"].astype(str)) & set(
        test["participant_object_id"].astype(str)
    )
    if overlap:
        raise ValueError(f"Participant overlap between train and test: {sorted(overlap)[:5]}")


def build_models() -> dict[str, object]:
    """Define a small set of interpretable first baseline classifiers."""

    return {
        "dummy_most_frequent": DummyClassifier(strategy="most_frequent"),
        "logistic_regression": Pipeline(
            steps=[
                ("scaler", StandardScaler()),
                (
                    "model",
                    LogisticRegression(
                        max_iter=5000,
                        class_weight="balanced",
                        random_state=RANDOM_STATE,
                    ),
                ),
            ]
        ),
        "logistic_regression_pca_95": Pipeline(
            steps=[
                ("scaler", StandardScaler()),
                ("pca", PCA(n_components=0.95, random_state=RANDOM_STATE)),
                (
                    "model",
                    LogisticRegression(
                        max_iter=5000,
                        class_weight="balanced",
                        random_state=RANDOM_STATE,
                    ),
                ),
            ]
        ),
        "random_forest": RandomForestClassifier(
            n_estimators=400,
            min_samples_leaf=5,
            class_weight="balanced_subsample",
            random_state=RANDOM_STATE,
            n_jobs=-1,
        ),
    }


def evaluate_model(
    model_name: str,
    model: object,
    x_test: pd.DataFrame,
    y_test: pd.Series,
) -> tuple[dict[str, float | int | str], pd.DataFrame]:
    """Create test-set metrics and row-level prediction output for one model."""

    y_pred = model.predict(x_test)
    if hasattr(model, "predict_proba"):
        y_score = model.predict_proba(x_test)[:, 1]
    else:
        y_score = y_pred

    tn, fp, fn, tp = confusion_matrix(y_test, y_pred, labels=[0, 1]).ravel()
    metrics = {
        "model": model_name,
        "accuracy": accuracy_score(y_test, y_pred),
        "balanced_accuracy": balanced_accuracy_score(y_test, y_pred),
        "precision": precision_score(y_test, y_pred, zero_division=0),
        "recall": recall_score(y_test, y_pred, zero_division=0),
        "f1": f1_score(y_test, y_pred, zero_division=0),
        "roc_auc": roc_auc_score(y_test, y_score),
        "average_precision": average_precision_score(y_test, y_score),
        "true_negative": int(tn),
        "false_positive": int(fp),
        "false_negative": int(fn),
        "true_positive": int(tp),
    }

    if model_name == "logistic_regression_pca_95":
        metrics["pca_components"] = int(model.named_steps["pca"].n_components_)
    else:
        metrics["pca_components"] = 0

    predictions = pd.DataFrame(
        {
            "model": model_name,
            "y_true": y_test.to_numpy(),
            "y_pred": y_pred,
            "y_score": y_score,
        },
        index=x_test.index,
    )
    return metrics, predictions


def extract_random_forest_importance(
    model: RandomForestClassifier,
    feature_columns: list[str],
) -> pd.DataFrame:
    """Save Random Forest impurity-based importance as a rough baseline diagnostic."""

    importance = pd.DataFrame(
        {
            "feature": feature_columns,
            "importance": model.feature_importances_,
        }
    )
    return importance.sort_values("importance", ascending=False).reset_index(drop=True)


def save_figures(
    metrics: pd.DataFrame,
    predictions: pd.DataFrame,
) -> dict[str, Path]:
    """Save metric comparison, ROC curves, and confusion-matrix summaries."""

    FIGURE_DIR.mkdir(parents=True, exist_ok=True)
    figure_paths = {
        "metric_comparison": FIGURE_DIR / "metric_comparison.png",
        "roc_curves": FIGURE_DIR / "roc_curves.png",
        "confusion_matrices": FIGURE_DIR / "confusion_matrices.png",
    }

    metric_columns = ["balanced_accuracy", "f1", "roc_auc", "average_precision"]
    plot_metrics = metrics.set_index("model")[metric_columns]
    ax = plot_metrics.plot(kind="bar", figsize=(10, 5), ylim=(0, 1))
    ax.set_title("Baseline Model Metrics")
    ax.set_xlabel("Model")
    ax.set_ylabel("Score")
    ax.legend(loc="lower right")
    plt.xticks(rotation=25, ha="right")
    plt.tight_layout()
    plt.savefig(figure_paths["metric_comparison"], dpi=160)
    plt.close()

    plt.figure(figsize=(7, 6))
    for model_name, group in predictions.groupby("model"):
        fpr, tpr, _ = roc_curve(group["y_true"], group["y_score"])
        auc = metrics.loc[metrics["model"] == model_name, "roc_auc"].iloc[0]
        plt.plot(fpr, tpr, linewidth=1.8, label=f"{model_name} (AUC={auc:.3f})")
    plt.plot([0, 1], [0, 1], color="gray", linestyle="--", linewidth=1)
    plt.title("Baseline ROC Curves")
    plt.xlabel("False positive rate")
    plt.ylabel("True positive rate")
    plt.legend(fontsize=8)
    plt.tight_layout()
    plt.savefig(figure_paths["roc_curves"], dpi=160)
    plt.close()

    fig, axes = plt.subplots(2, 2, figsize=(9, 8))
    axes = axes.flatten()
    for axis, (_, row) in zip(axes, metrics.iterrows()):
        matrix = [
            [row["true_negative"], row["false_positive"]],
            [row["false_negative"], row["true_positive"]],
        ]
        axis.imshow(matrix, cmap="Blues")
        axis.set_title(row["model"])
        axis.set_xticks([0, 1], labels=["Pred 0", "Pred 1"])
        axis.set_yticks([0, 1], labels=["True 0", "True 1"])
        for i in range(2):
            for j in range(2):
                axis.text(j, i, int(matrix[i][j]), ha="center", va="center")
    for axis in axes[len(metrics) :]:
        axis.axis("off")
    plt.tight_layout()
    plt.savefig(figure_paths["confusion_matrices"], dpi=160)
    plt.close()

    return figure_paths


def write_report(
    train: pd.DataFrame,
    test: pd.DataFrame,
    feature_columns: list[str],
    metrics: pd.DataFrame,
    rf_importance: pd.DataFrame,
    figure_paths: dict[str, Path],
) -> None:
    """Write a concise baseline-modeling report."""

    best_by_balanced_accuracy = metrics.sort_values(
        ["balanced_accuracy", "roc_auc"],
        ascending=False,
    ).iloc[0]

    lines = [
        "# Baseline Modeling Summary",
        "",
        f"- Generated at: `{datetime.now().isoformat(timespec='seconds')}`",
        f"- Train input: `{TRAIN_PATH}`",
        f"- Test input: `{TEST_PATH}`",
        f"- Feature columns: `{FEATURE_COLUMNS_PATH}`",
        f"- Metrics output: `{METRICS_PATH}`",
        f"- Predictions output: `{PREDICTIONS_PATH}`",
        "",
        "## Scope",
        "",
        "- This step trains first baseline classifiers on the participant-aware split.",
        "- Scaling and PCA, when used, are fit inside sklearn pipelines using train data only.",
        "- This is not final tuned modeling.",
        "",
        "## Split Used",
        "",
        "| split | rows | participants | good_sleep_label mean |",
        "| --- | ---: | ---: | ---: |",
    ]

    for split_name, split_df in [("train", train), ("test", test)]:
        lines.append(
            f"| {split_name} | {len(split_df):,} | {split_df['participant_object_id'].nunique():,} | "
            f"{split_df[TARGET_COLUMN].mean():.4f} |"
        )

    lines.extend(
        [
            "",
            "## Feature Set",
            "",
            f"- Feature count: `{len(feature_columns):,}`",
            "- Keys and target were excluded from predictors.",
            "",
            "## Test Metrics",
            "",
            "| model | accuracy | balanced accuracy | precision | recall | f1 | roc auc | average precision | PCA components |",
            "| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |",
        ]
    )

    for _, row in metrics.iterrows():
        lines.append(
            f"| `{row['model']}` | {row['accuracy']:.4f} | {row['balanced_accuracy']:.4f} | "
            f"{row['precision']:.4f} | {row['recall']:.4f} | {row['f1']:.4f} | "
            f"{row['roc_auc']:.4f} | {row['average_precision']:.4f} | "
            f"{int(row['pca_components'])} |"
        )

    lines.extend(
        [
            "",
            "## Best Baseline By Balanced Accuracy",
            "",
            f"- Model: `{best_by_balanced_accuracy['model']}`",
            f"- Balanced accuracy: `{best_by_balanced_accuracy['balanced_accuracy']:.4f}`",
            f"- ROC AUC: `{best_by_balanced_accuracy['roc_auc']:.4f}`",
            f"- F1: `{best_by_balanced_accuracy['f1']:.4f}`",
            "",
            "## Random Forest Top Feature Importance",
            "",
            "| rank | feature | importance |",
            "| ---: | --- | ---: |",
        ]
    )

    for rank, row in enumerate(rf_importance.head(25).itertuples(index=False), start=1):
        lines.append(f"| {rank} | `{row.feature}` | {row.importance:.5f} |")

    lines.extend(
        [
            "",
            "## Figures",
            "",
        ]
    )
    for name, path in figure_paths.items():
        lines.append(f"- {name}: `{path}`")

    lines.extend(
        [
            "",
            "## Next Step",
            "",
            "```text",
            "model validation review, feature-set comparison, and tuned modeling",
            "```",
            "",
        ]
    )

    REPORT_PATH.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    train = pd.read_csv(TRAIN_PATH)
    test = pd.read_csv(TEST_PATH)
    feature_columns = load_feature_columns()

    train["participant_object_id"] = train["participant_object_id"].astype(str)
    test["participant_object_id"] = test["participant_object_id"].astype(str)
    train["calendar_date"] = pd.to_datetime(train["calendar_date"], errors="coerce").dt.date.astype(str)
    test["calendar_date"] = pd.to_datetime(test["calendar_date"], errors="coerce").dt.date.astype(str)

    validate_modeling_inputs(train, test, feature_columns)

    x_train = train[feature_columns]
    y_train = train[TARGET_COLUMN].astype(int)
    x_test = test[feature_columns]
    y_test = test[TARGET_COLUMN].astype(int)

    models = build_models()
    metric_rows: list[dict[str, float | int | str]] = []
    prediction_tables: list[pd.DataFrame] = []

    for model_name, model in models.items():
        model.fit(x_train, y_train)
        metric_row, prediction_table = evaluate_model(model_name, model, x_test, y_test)
        metric_rows.append(metric_row)
        prediction_tables.append(
            pd.concat(
                [
                    test[KEY_COLUMNS].reset_index(drop=True),
                    prediction_table.reset_index(drop=True),
                ],
                axis=1,
            )
        )

    metrics = pd.DataFrame(metric_rows).sort_values("balanced_accuracy", ascending=False)
    predictions = pd.concat(prediction_tables, ignore_index=True)
    rf_importance = extract_random_forest_importance(models["random_forest"], feature_columns)
    figure_paths = save_figures(metrics, predictions)

    PREDICTIONS_PATH.parent.mkdir(parents=True, exist_ok=True)
    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    predictions.to_csv(PREDICTIONS_PATH, index=False, encoding="utf-8-sig")
    metrics.to_csv(METRICS_PATH, index=False, encoding="utf-8-sig")
    rf_importance.to_csv(RF_IMPORTANCE_PATH, index=False, encoding="utf-8-sig")
    joblib.dump(models, MODELS_PATH)
    write_report(train, test, feature_columns, metrics, rf_importance, figure_paths)

    print(f"Train shape: {train.shape}")
    print(f"Test shape: {test.shape}")
    print(f"Feature count: {len(feature_columns)}")
    print("Metrics:")
    print(metrics.to_string(index=False))
    print(f"Wrote metrics: {METRICS_PATH}")
    print(f"Wrote predictions: {PREDICTIONS_PATH}")
    print(f"Wrote report: {REPORT_PATH}")


if __name__ == "__main__":
    main()
