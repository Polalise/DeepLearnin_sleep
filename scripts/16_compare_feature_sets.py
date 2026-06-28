from __future__ import annotations

from datetime import datetime
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd
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
)
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler


# This script reviews the first baseline by comparing feature-set variants.
#
# Validation idea:
# - Baseline performance can look good when the model uses data-availability
#   signals, such as missing indicators or per-day record counts.
# - Those signals may still be valid operational features, but they should be
#   checked separately before claiming that physiology/context values alone
#   predict sleep quality.
#
# Boundary:
# - This script reuses the fixed participant-aware train/test split.
# - It does not tune hyperparameters.
# - It compares a small, interpretable set of feature families.
PROJECT_ROOT = Path(__file__).resolve().parents[1]
TRAIN_PATH = PROJECT_ROOT / "data" / "processed" / "splits" / "train_participant_split.csv"
TEST_PATH = PROJECT_ROOT / "data" / "processed" / "splits" / "test_participant_split.csv"
FEATURE_COLUMNS_PATH = PROJECT_ROOT / "data" / "processed" / "encoded_feature_columns.csv"
METRICS_PATH = PROJECT_ROOT / "data" / "processed" / "feature_set_comparison_metrics.csv"
DEFINITIONS_PATH = PROJECT_ROOT / "data" / "processed" / "feature_set_definitions.csv"
REPORT_PATH = PROJECT_ROOT / "reports" / "feature_set_comparison_summary.md"
FIGURE_DIR = PROJECT_ROOT / "reports" / "figures" / "feature_set_comparison"

KEY_COLUMNS = ["participant_object_id", "calendar_date"]
TARGET_COLUMN = "good_sleep_label"
RANDOM_STATE = 42


def load_feature_columns() -> list[str]:
    """Load the finalized encoded feature columns."""

    feature_metadata = pd.read_csv(FEATURE_COLUMNS_PATH)
    if "feature" not in feature_metadata.columns:
        raise ValueError(f"`feature` column is missing from {FEATURE_COLUMNS_PATH}")
    return feature_metadata["feature"].tolist()


def validate_inputs(
    train: pd.DataFrame,
    test: pd.DataFrame,
    feature_columns: list[str],
) -> None:
    """Validate split isolation and modeling readiness."""

    overlap = set(train["participant_object_id"].astype(str)) & set(
        test["participant_object_id"].astype(str)
    )
    if overlap:
        raise ValueError(f"Participant overlap between train and test: {sorted(overlap)[:5]}")

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


def is_missing_indicator(feature: str) -> bool:
    """Return True for columns added to mark originally missing values."""

    return feature.endswith("_missing_ind")


def is_availability_feature(feature: str) -> bool:
    """Return True for missingness or collection-volume style features."""

    return (
        is_missing_indicator(feature)
        or feature.endswith("_record_count")
        or feature.endswith("_response_count")
        or feature.endswith("_count")
    )


def is_context_or_survey_feature(feature: str) -> bool:
    """Return True for SEMA context/mood and participant-level survey features."""

    prefixes = ("mood_", "place_", "survey_")
    return feature.startswith(prefixes)


def build_feature_sets(feature_columns: list[str]) -> dict[str, list[str]]:
    """Create feature-set variants for robustness checks."""

    feature_sets = {
        "all_features": feature_columns,
        "no_missing_indicators": [
            feature for feature in feature_columns if not is_missing_indicator(feature)
        ],
        "no_availability_features": [
            feature for feature in feature_columns if not is_availability_feature(feature)
        ],
        "wearable_only": [
            feature for feature in feature_columns if not is_context_or_survey_feature(feature)
        ],
        "wearable_values_only": [
            feature
            for feature in feature_columns
            if not is_context_or_survey_feature(feature) and not is_availability_feature(feature)
        ],
        "context_survey_only": [
            feature for feature in feature_columns if is_context_or_survey_feature(feature)
        ],
    }

    empty_sets = [name for name, columns in feature_sets.items() if not columns]
    if empty_sets:
        raise ValueError(f"Feature sets cannot be empty: {empty_sets}")
    return feature_sets


def build_models() -> dict[str, object]:
    """Use the two strongest baseline families for feature-set comparison."""

    return {
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
        "random_forest": RandomForestClassifier(
            n_estimators=400,
            min_samples_leaf=5,
            class_weight="balanced_subsample",
            random_state=RANDOM_STATE,
            n_jobs=-1,
        ),
    }


def evaluate_predictions(
    feature_set: str,
    model_name: str,
    feature_count: int,
    y_true: pd.Series,
    y_pred: pd.Series,
    y_score: pd.Series,
) -> dict[str, float | int | str]:
    """Compute comparable binary-classification metrics."""

    tn, fp, fn, tp = confusion_matrix(y_true, y_pred, labels=[0, 1]).ravel()
    return {
        "feature_set": feature_set,
        "model": model_name,
        "feature_count": feature_count,
        "accuracy": accuracy_score(y_true, y_pred),
        "balanced_accuracy": balanced_accuracy_score(y_true, y_pred),
        "precision": precision_score(y_true, y_pred, zero_division=0),
        "recall": recall_score(y_true, y_pred, zero_division=0),
        "f1": f1_score(y_true, y_pred, zero_division=0),
        "roc_auc": roc_auc_score(y_true, y_score),
        "average_precision": average_precision_score(y_true, y_score),
        "true_negative": int(tn),
        "false_positive": int(fp),
        "false_negative": int(fn),
        "true_positive": int(tp),
    }


def run_feature_set_comparison(
    train: pd.DataFrame,
    test: pd.DataFrame,
    feature_sets: dict[str, list[str]],
) -> pd.DataFrame:
    """Train the same model families on each feature-set variant."""

    y_train = train[TARGET_COLUMN].astype(int)
    y_test = test[TARGET_COLUMN].astype(int)
    rows: list[dict[str, float | int | str]] = []

    for feature_set_name, columns in feature_sets.items():
        x_train = train[columns]
        x_test = test[columns]
        for model_name, model in build_models().items():
            model.fit(x_train, y_train)
            y_pred = model.predict(x_test)
            y_score = model.predict_proba(x_test)[:, 1]
            rows.append(
                evaluate_predictions(
                    feature_set=feature_set_name,
                    model_name=model_name,
                    feature_count=len(columns),
                    y_true=y_test,
                    y_pred=y_pred,
                    y_score=y_score,
                )
            )

    return pd.DataFrame(rows).sort_values(
        ["balanced_accuracy", "roc_auc"],
        ascending=False,
    )


def build_feature_set_definitions(feature_sets: dict[str, list[str]]) -> pd.DataFrame:
    """Store every feature included in each variant for auditability."""

    rows = []
    for feature_set_name, columns in feature_sets.items():
        for feature in columns:
            rows.append({"feature_set": feature_set_name, "feature": feature})
    return pd.DataFrame(rows)


def save_figures(metrics: pd.DataFrame) -> dict[str, Path]:
    """Save compact plots for comparing feature-set robustness."""

    FIGURE_DIR.mkdir(parents=True, exist_ok=True)
    figure_paths = {
        "balanced_accuracy": FIGURE_DIR / "balanced_accuracy_by_feature_set.png",
        "roc_auc": FIGURE_DIR / "roc_auc_by_feature_set.png",
    }

    for metric_name, path in [
        ("balanced_accuracy", figure_paths["balanced_accuracy"]),
        ("roc_auc", figure_paths["roc_auc"]),
    ]:
        pivot = metrics.pivot(index="feature_set", columns="model", values=metric_name)
        pivot = pivot.sort_values("logistic_regression", ascending=False)
        ax = pivot.plot(kind="bar", figsize=(11, 5), ylim=(0, 1))
        ax.set_title(f"{metric_name.replace('_', ' ').title()} by Feature Set")
        ax.set_xlabel("Feature set")
        ax.set_ylabel(metric_name.replace("_", " ").title())
        ax.legend(loc="lower right")
        plt.xticks(rotation=25, ha="right")
        plt.tight_layout()
        plt.savefig(path, dpi=160)
        plt.close()

    return figure_paths


def write_report(
    train: pd.DataFrame,
    test: pd.DataFrame,
    feature_sets: dict[str, list[str]],
    metrics: pd.DataFrame,
    figure_paths: dict[str, Path],
) -> None:
    """Write a model-validation and feature-set comparison report."""

    all_lr = metrics[
        (metrics["feature_set"] == "all_features")
        & (metrics["model"] == "logistic_regression")
    ].iloc[0]
    no_availability_lr = metrics[
        (metrics["feature_set"] == "no_availability_features")
        & (metrics["model"] == "logistic_regression")
    ].iloc[0]
    availability_gap = float(
        all_lr["balanced_accuracy"] - no_availability_lr["balanced_accuracy"]
    )

    lines = [
        "# Feature Set Comparison Summary",
        "",
        f"- Generated at: `{datetime.now().isoformat(timespec='seconds')}`",
        f"- Train input: `{TRAIN_PATH}`",
        f"- Test input: `{TEST_PATH}`",
        f"- Metrics output: `{METRICS_PATH}`",
        f"- Feature-set definitions: `{DEFINITIONS_PATH}`",
        "",
        "## Scope",
        "",
        "- This step compares baseline model performance across feature-set variants.",
        "- The goal is to check whether baseline performance depends heavily on missingness or collection-volume features.",
        "- The participant-aware split is reused unchanged.",
        "",
        "## Split Reused",
        "",
        "| split | rows | participants | good_sleep_label mean |",
        "| --- | ---: | ---: | ---: |",
        f"| train | {len(train):,} | {train['participant_object_id'].nunique():,} | {train[TARGET_COLUMN].mean():.4f} |",
        f"| test | {len(test):,} | {test['participant_object_id'].nunique():,} | {test[TARGET_COLUMN].mean():.4f} |",
        "",
        "## Feature Set Definitions",
        "",
        "| feature set | feature count | intent |",
        "| --- | ---: | --- |",
        f"| `all_features` | {len(feature_sets['all_features']):,} | all encoded baseline features |",
        f"| `no_missing_indicators` | {len(feature_sets['no_missing_indicators']):,} | remove only imputation missing indicators |",
        f"| `no_availability_features` | {len(feature_sets['no_availability_features']):,} | remove missing indicators and count/record-count features |",
        f"| `wearable_only` | {len(feature_sets['wearable_only']):,} | remove SEMA context/mood and survey features |",
        f"| `wearable_values_only` | {len(feature_sets['wearable_values_only']):,} | wearable-only after removing availability features |",
        f"| `context_survey_only` | {len(feature_sets['context_survey_only']):,} | SEMA context/mood plus survey features only |",
        "",
        "## Test Metrics",
        "",
        "| feature set | model | features | balanced accuracy | roc auc | f1 | precision | recall |",
        "| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]

    for _, row in metrics.iterrows():
        lines.append(
            f"| `{row['feature_set']}` | `{row['model']}` | {int(row['feature_count']):,} | "
            f"{row['balanced_accuracy']:.4f} | {row['roc_auc']:.4f} | {row['f1']:.4f} | "
            f"{row['precision']:.4f} | {row['recall']:.4f} |"
        )

    lines.extend(
        [
            "",
            "## Validation Reading",
            "",
            f"- Logistic Regression balanced accuracy with all features: `{all_lr['balanced_accuracy']:.4f}`",
            f"- Logistic Regression balanced accuracy without availability features: `{no_availability_lr['balanced_accuracy']:.4f}`",
            f"- Availability-feature gap: `{availability_gap:.4f}`",
        ]
    )

    if availability_gap > 0.05:
        lines.append(
            "- Interpretation: a meaningful share of performance may come from missingness/count signals, so future reports should separate value-only and availability-aware models."
        )
    else:
        lines.append(
            "- Interpretation: removing missingness/count signals does not strongly reduce Logistic Regression performance on this split."
        )

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
            "tuned modeling with participant-aware cross-validation",
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

    validate_inputs(train, test, feature_columns)
    feature_sets = build_feature_sets(feature_columns)
    metrics = run_feature_set_comparison(train, test, feature_sets)
    definitions = build_feature_set_definitions(feature_sets)
    figure_paths = save_figures(metrics)

    METRICS_PATH.parent.mkdir(parents=True, exist_ok=True)
    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    metrics.to_csv(METRICS_PATH, index=False, encoding="utf-8-sig")
    definitions.to_csv(DEFINITIONS_PATH, index=False, encoding="utf-8-sig")
    write_report(train, test, feature_sets, metrics, figure_paths)

    print(f"Train shape: {train.shape}")
    print(f"Test shape: {test.shape}")
    print(f"Feature sets: {len(feature_sets)}")
    print("Metrics:")
    print(metrics.to_string(index=False))
    print(f"Wrote metrics: {METRICS_PATH}")
    print(f"Wrote definitions: {DEFINITIONS_PATH}")
    print(f"Wrote report: {REPORT_PATH}")


if __name__ == "__main__":
    main()
