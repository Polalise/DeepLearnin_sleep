from __future__ import annotations

from datetime import datetime
from pathlib import Path

import joblib
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
from sklearn.model_selection import GridSearchCV, StratifiedGroupKFold
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler


# This script tunes a small set of baseline candidates.
#
# Tuning unit:
# - Use the fixed participant-aware train/test split.
# - Tune only on the train split with participant-aware cross-validation.
# - Evaluate the selected model once on the held-out participant test split.
#
# Boundary:
# - This is still baseline-level tuning with compact grids.
# - It does not perform repeated nested validation or final model selection.
PROJECT_ROOT = Path(__file__).resolve().parents[1]
TRAIN_PATH = PROJECT_ROOT / "data" / "processed" / "splits" / "train_participant_split.csv"
TEST_PATH = PROJECT_ROOT / "data" / "processed" / "splits" / "test_participant_split.csv"
FEATURE_COLUMNS_PATH = PROJECT_ROOT / "data" / "processed" / "encoded_feature_columns.csv"
METRICS_PATH = PROJECT_ROOT / "data" / "processed" / "tuned_model_metrics.csv"
CV_RESULTS_PATH = PROJECT_ROOT / "data" / "processed" / "tuned_model_cv_results.csv"
PREDICTIONS_PATH = PROJECT_ROOT / "data" / "processed" / "tuned_model_predictions.csv"
MODELS_PATH = PROJECT_ROOT / "data" / "processed" / "tuned_models.joblib"
REPORT_PATH = PROJECT_ROOT / "reports" / "tuned_modeling_summary.md"
FIGURE_DIR = PROJECT_ROOT / "reports" / "figures" / "tuned_modeling"

TARGET_COLUMN = "good_sleep_label"
KEY_COLUMNS = ["participant_object_id", "calendar_date"]
RANDOM_STATE = 42


def load_feature_columns() -> list[str]:
    """Load encoded feature columns used by the baseline modeling scripts."""

    feature_metadata = pd.read_csv(FEATURE_COLUMNS_PATH)
    if "feature" not in feature_metadata.columns:
        raise ValueError(f"`feature` column is missing from {FEATURE_COLUMNS_PATH}")
    return feature_metadata["feature"].tolist()


def is_context_or_survey_feature(feature: str) -> bool:
    """Identify SEMA context/mood and participant survey columns."""

    return feature.startswith(("mood_", "place_", "survey_"))


def build_feature_sets(feature_columns: list[str]) -> dict[str, list[str]]:
    """Tune only the most relevant feature-set candidates from comparison."""

    return {
        "all_features": feature_columns,
        "wearable_only": [
            feature for feature in feature_columns if not is_context_or_survey_feature(feature)
        ],
    }


def validate_inputs(
    train: pd.DataFrame,
    test: pd.DataFrame,
    feature_columns: list[str],
) -> None:
    """Validate split isolation and train/test feature readiness."""

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


def build_searches() -> dict[str, tuple[Pipeline | RandomForestClassifier, dict[str, list[object]]]]:
    """Define compact grids for baseline-level model tuning."""

    logistic = Pipeline(
        steps=[
            ("scaler", StandardScaler()),
            (
                "model",
                LogisticRegression(
                    max_iter=5000,
                    random_state=RANDOM_STATE,
                ),
            ),
        ]
    )
    random_forest = RandomForestClassifier(
        n_estimators=200,
        class_weight="balanced_subsample",
        random_state=RANDOM_STATE,
        n_jobs=1,
    )

    return {
        "logistic_regression": (
            logistic,
            {
                "model__C": [0.03, 0.1, 0.3, 1.0],
                "model__class_weight": ["balanced", None],
            },
        ),
        "random_forest": (
            random_forest,
            {
                "max_depth": [None, 8],
                "max_features": ["sqrt"],
                "min_samples_leaf": [5, 10],
            },
        ),
    }


def evaluate_test_predictions(
    candidate: str,
    feature_set: str,
    feature_count: int,
    best_params: dict[str, object],
    cv_score: float,
    y_true: pd.Series,
    y_pred: pd.Series,
    y_score: pd.Series,
) -> dict[str, float | int | str]:
    """Compute held-out participant test metrics for a tuned model."""

    tn, fp, fn, tp = confusion_matrix(y_true, y_pred, labels=[0, 1]).ravel()
    return {
        "candidate": candidate,
        "feature_set": feature_set,
        "feature_count": feature_count,
        "best_cv_balanced_accuracy": cv_score,
        "best_params": str(best_params),
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


def run_tuning(
    train: pd.DataFrame,
    test: pd.DataFrame,
    feature_sets: dict[str, list[str]],
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, dict[str, object]]:
    """Run participant-aware CV searches and evaluate selected models on test."""

    y_train = train[TARGET_COLUMN].astype(int)
    y_test = test[TARGET_COLUMN].astype(int)
    groups = train["participant_object_id"].astype(str)
    cv = StratifiedGroupKFold(n_splits=5, shuffle=True, random_state=RANDOM_STATE)

    metric_rows: list[dict[str, float | int | str]] = []
    cv_result_tables: list[pd.DataFrame] = []
    prediction_tables: list[pd.DataFrame] = []
    fitted_models: dict[str, object] = {}

    for feature_set_name, columns in feature_sets.items():
        x_train = train[columns]
        x_test = test[columns]

        for candidate_name, (estimator, param_grid) in build_searches().items():
            search_name = f"{candidate_name}__{feature_set_name}"
            search = GridSearchCV(
                estimator=estimator,
                param_grid=param_grid,
                scoring="balanced_accuracy",
                cv=cv,
                n_jobs=1,
                refit=True,
                return_train_score=True,
            )
            search.fit(x_train, y_train, groups=groups)

            best_model = search.best_estimator_
            y_pred = best_model.predict(x_test)
            y_score = best_model.predict_proba(x_test)[:, 1]

            metric_rows.append(
                evaluate_test_predictions(
                    candidate=candidate_name,
                    feature_set=feature_set_name,
                    feature_count=len(columns),
                    best_params=search.best_params_,
                    cv_score=float(search.best_score_),
                    y_true=y_test,
                    y_pred=y_pred,
                    y_score=y_score,
                )
            )

            cv_results = pd.DataFrame(search.cv_results_)
            cv_results.insert(0, "candidate", candidate_name)
            cv_results.insert(1, "feature_set", feature_set_name)
            cv_result_tables.append(cv_results)

            prediction_tables.append(
                pd.concat(
                    [
                        test[KEY_COLUMNS].reset_index(drop=True),
                        pd.DataFrame(
                            {
                                "candidate": candidate_name,
                                "feature_set": feature_set_name,
                                "y_true": y_test.to_numpy(),
                                "y_pred": y_pred,
                                "y_score": y_score,
                            }
                        ),
                    ],
                    axis=1,
                )
            )
            fitted_models[search_name] = best_model

    metrics = pd.DataFrame(metric_rows).sort_values(
        ["balanced_accuracy", "roc_auc"],
        ascending=False,
    )
    cv_results = pd.concat(cv_result_tables, ignore_index=True)
    predictions = pd.concat(prediction_tables, ignore_index=True)
    return metrics, cv_results, predictions, fitted_models


def save_figures(metrics: pd.DataFrame) -> dict[str, Path]:
    """Save tuned model comparison charts."""

    FIGURE_DIR.mkdir(parents=True, exist_ok=True)
    figure_paths = {
        "test_metrics": FIGURE_DIR / "tuned_test_metrics.png",
        "cv_vs_test": FIGURE_DIR / "cv_vs_test_balanced_accuracy.png",
    }

    labels = metrics["candidate"] + "__" + metrics["feature_set"]
    plot_metrics = metrics.assign(label=labels).set_index("label")[
        ["balanced_accuracy", "roc_auc", "f1", "average_precision"]
    ]
    ax = plot_metrics.plot(kind="bar", figsize=(11, 5), ylim=(0, 1))
    ax.set_title("Tuned Model Held-Out Test Metrics")
    ax.set_xlabel("Candidate")
    ax.set_ylabel("Score")
    ax.legend(loc="lower right")
    plt.xticks(rotation=25, ha="right")
    plt.tight_layout()
    plt.savefig(figure_paths["test_metrics"], dpi=160)
    plt.close()

    cv_test = metrics.assign(label=labels).set_index("label")[
        ["best_cv_balanced_accuracy", "balanced_accuracy"]
    ]
    ax = cv_test.plot(kind="bar", figsize=(11, 5), ylim=(0, 1))
    ax.set_title("Participant-CV vs Held-Out Test Balanced Accuracy")
    ax.set_xlabel("Candidate")
    ax.set_ylabel("Balanced accuracy")
    ax.legend(["CV", "Test"], loc="lower right")
    plt.xticks(rotation=25, ha="right")
    plt.tight_layout()
    plt.savefig(figure_paths["cv_vs_test"], dpi=160)
    plt.close()

    return figure_paths


def write_report(
    train: pd.DataFrame,
    test: pd.DataFrame,
    metrics: pd.DataFrame,
    figure_paths: dict[str, Path],
) -> None:
    """Write a tuned-modeling report with CV and held-out test results."""

    best = metrics.iloc[0]
    lines = [
        "# Tuned Modeling Summary",
        "",
        f"- Generated at: `{datetime.now().isoformat(timespec='seconds')}`",
        f"- Train input: `{TRAIN_PATH}`",
        f"- Test input: `{TEST_PATH}`",
        f"- Metrics output: `{METRICS_PATH}`",
        f"- CV results output: `{CV_RESULTS_PATH}`",
        f"- Predictions output: `{PREDICTIONS_PATH}`",
        "",
        "## Scope",
        "",
        "- This step tunes compact Logistic Regression and Random Forest grids.",
        "- Hyperparameter search uses `StratifiedGroupKFold` on the train split, grouped by participant.",
        "- The held-out participant test split is used once for final comparison.",
        "",
        "## Split Used",
        "",
        "| split | rows | participants | good_sleep_label mean |",
        "| --- | ---: | ---: | ---: |",
        f"| train | {len(train):,} | {train['participant_object_id'].nunique():,} | {train[TARGET_COLUMN].mean():.4f} |",
        f"| test | {len(test):,} | {test['participant_object_id'].nunique():,} | {test[TARGET_COLUMN].mean():.4f} |",
        "",
        "## Tuned Test Metrics",
        "",
        "| candidate | feature set | features | CV balanced accuracy | test balanced accuracy | roc auc | f1 | precision | recall |",
        "| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]

    for _, row in metrics.iterrows():
        lines.append(
            f"| `{row['candidate']}` | `{row['feature_set']}` | {int(row['feature_count']):,} | "
            f"{row['best_cv_balanced_accuracy']:.4f} | {row['balanced_accuracy']:.4f} | "
            f"{row['roc_auc']:.4f} | {row['f1']:.4f} | {row['precision']:.4f} | {row['recall']:.4f} |"
        )

    lines.extend(
        [
            "",
            "## Best Tuned Candidate",
            "",
            f"- Candidate: `{best['candidate']}`",
            f"- Feature set: `{best['feature_set']}`",
            f"- Test balanced accuracy: `{best['balanced_accuracy']:.4f}`",
            f"- Test ROC AUC: `{best['roc_auc']:.4f}`",
            f"- Test F1: `{best['f1']:.4f}`",
            f"- Best params: `{best['best_params']}`",
            "",
            "## Validation Notes",
            "",
            "- Compare CV balanced accuracy with held-out test balanced accuracy before treating this as final.",
            "- Because the test split has only 14 participants, participant composition can still move metrics materially.",
            "- Final reporting should include confidence intervals or repeated participant-aware resampling.",
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
            "final validation report and model interpretation",
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
    metrics, cv_results, predictions, fitted_models = run_tuning(train, test, feature_sets)
    figure_paths = save_figures(metrics)

    METRICS_PATH.parent.mkdir(parents=True, exist_ok=True)
    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    metrics.to_csv(METRICS_PATH, index=False, encoding="utf-8-sig")
    cv_results.to_csv(CV_RESULTS_PATH, index=False, encoding="utf-8-sig")
    predictions.to_csv(PREDICTIONS_PATH, index=False, encoding="utf-8-sig")
    joblib.dump(fitted_models, MODELS_PATH)
    write_report(train, test, metrics, figure_paths)

    print(f"Train shape: {train.shape}")
    print(f"Test shape: {test.shape}")
    print("Tuned metrics:")
    print(metrics.to_string(index=False))
    print(f"Wrote metrics: {METRICS_PATH}")
    print(f"Wrote CV results: {CV_RESULTS_PATH}")
    print(f"Wrote report: {REPORT_PATH}")


if __name__ == "__main__":
    main()
