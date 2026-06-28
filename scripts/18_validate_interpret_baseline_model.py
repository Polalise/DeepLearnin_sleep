from __future__ import annotations

from datetime import datetime
from pathlib import Path

import joblib
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
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


# This script validates and interprets the selected baseline model.
#
# Selected baseline:
# - Logistic Regression
# - wearable_only feature set
# - participant-aware train/test split
#
# Interpretation scope:
# - Coefficients are from the standardized Logistic Regression pipeline.
# - Positive coefficients increase the probability of good_sleep_label=1.
# - This is the final baseline candidate, not the final model across all
#   possible model families.
PROJECT_ROOT = Path(__file__).resolve().parents[1]
TRAIN_PATH = PROJECT_ROOT / "data" / "processed" / "splits" / "train_participant_split.csv"
TEST_PATH = PROJECT_ROOT / "data" / "processed" / "splits" / "test_participant_split.csv"
FEATURE_COLUMNS_PATH = PROJECT_ROOT / "data" / "processed" / "encoded_feature_columns.csv"
TUNED_MODELS_PATH = PROJECT_ROOT / "data" / "processed" / "tuned_models.joblib"
TUNED_METRICS_PATH = PROJECT_ROOT / "data" / "processed" / "tuned_model_metrics.csv"
COEFFICIENTS_PATH = PROJECT_ROOT / "data" / "processed" / "baseline_logistic_coefficients.csv"
CALIBRATION_PATH = PROJECT_ROOT / "data" / "processed" / "baseline_probability_calibration.csv"
BOOTSTRAP_PATH = PROJECT_ROOT / "data" / "processed" / "baseline_participant_bootstrap_metrics.csv"
REPORT_PATH = PROJECT_ROOT / "reports" / "final_baseline_validation_report.md"
FIGURE_DIR = PROJECT_ROOT / "reports" / "figures" / "final_baseline_validation"

TARGET_COLUMN = "good_sleep_label"
KEY_COLUMNS = ["participant_object_id", "calendar_date"]
BEST_MODEL_KEY = "logistic_regression__wearable_only"
RANDOM_STATE = 42
BOOTSTRAP_REPEATS = 1000

FONT_FAMILY = ["Aptos", "Inter", "Segoe UI", "DejaVu Sans", "Arial", "sans-serif"]
TOKENS = {
    "surface": "#FCFCFD",
    "panel": "#FFFFFF",
    "ink": "#1F2430",
    "muted": "#6F768A",
    "grid": "#E6E8F0",
    "axis": "#D7DBE7",
}
COLOR_FAMILIES = {
    "blue": {"base": "#A3BEFA", "dark": "#2E4780", "light": "#CEDFFE"},
    "gold": {"base": "#FFE15B", "dark": "#736422", "light": "#FFEA8F"},
    "orange": {"base": "#F0986E", "dark": "#804126", "light": "#FFBDA1"},
    "olive": {"base": "#A3D576", "dark": "#386411", "light": "#BEEB96"},
}


def use_chart_theme() -> None:
    """Apply a consistent static report chart style."""

    plt.rcParams.update(
        {
            "figure.facecolor": TOKENS["surface"],
            "savefig.facecolor": TOKENS["surface"],
            "axes.facecolor": TOKENS["panel"],
            "axes.edgecolor": TOKENS["axis"],
            "axes.labelcolor": TOKENS["ink"],
            "axes.grid": True,
            "grid.color": TOKENS["grid"],
            "grid.linewidth": 0.8,
            "font.family": "sans-serif",
            "font.sans-serif": FONT_FAMILY,
            "xtick.color": TOKENS["muted"],
            "ytick.color": TOKENS["muted"],
        }
    )


def add_chart_header(fig: plt.Figure, ax: plt.Axes, title: str, subtitle: str) -> None:
    """Add a visible title/subtitle above a report chart."""

    ax.set_title("")
    fig.subplots_adjust(top=0.82)
    left = ax.get_position().x0
    fig.text(left, 0.98, title, ha="left", va="top", fontsize=13, fontweight="semibold", color=TOKENS["ink"])
    fig.text(left, 0.925, subtitle, ha="left", va="top", fontsize=9, color=TOKENS["muted"])
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)


def load_feature_columns() -> list[str]:
    """Load encoded feature columns and keep the wearable-only subset."""

    feature_metadata = pd.read_csv(FEATURE_COLUMNS_PATH)
    feature_columns = feature_metadata["feature"].tolist()
    return [
        feature
        for feature in feature_columns
        if not feature.startswith(("mood_", "place_", "survey_"))
    ]


def validate_inputs(train: pd.DataFrame, test: pd.DataFrame, feature_columns: list[str]) -> None:
    """Ensure the fixed split and selected feature set are ready for interpretation."""

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


def score_best_model(
    model: object,
    test: pd.DataFrame,
    feature_columns: list[str],
) -> pd.DataFrame:
    """Create row-level predictions for the selected baseline model."""

    x_test = test[feature_columns]
    output = test[KEY_COLUMNS + [TARGET_COLUMN]].copy()
    output["y_score"] = model.predict_proba(x_test)[:, 1]
    output["y_pred"] = model.predict(x_test)
    return output


def compute_metrics(predictions: pd.DataFrame) -> dict[str, float | int]:
    """Compute standard binary-classification metrics from row-level predictions."""

    y_true = predictions[TARGET_COLUMN].astype(int)
    y_pred = predictions["y_pred"].astype(int)
    y_score = predictions["y_score"].astype(float)
    tn, fp, fn, tp = confusion_matrix(y_true, y_pred, labels=[0, 1]).ravel()
    return {
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


def extract_coefficients(model: object, feature_columns: list[str]) -> pd.DataFrame:
    """Extract standardized Logistic Regression coefficients."""

    coefficients = model.named_steps["model"].coef_[0]
    table = pd.DataFrame(
        {
            "feature": feature_columns,
            "coefficient": coefficients,
            "abs_coefficient": np.abs(coefficients),
            "direction_for_good_sleep": np.where(coefficients >= 0, "positive", "negative"),
        }
    )
    return table.sort_values("abs_coefficient", ascending=False).reset_index(drop=True)


def build_calibration_table(predictions: pd.DataFrame) -> pd.DataFrame:
    """Compare predicted probability bins with observed good-sleep rates."""

    calibration = predictions.copy()
    calibration["probability_bin"] = pd.qcut(
        calibration["y_score"],
        q=10,
        duplicates="drop",
    )
    table = (
        calibration.groupby("probability_bin", observed=True)
        .agg(
            rows=(TARGET_COLUMN, "size"),
            mean_predicted_probability=("y_score", "mean"),
            observed_good_sleep_rate=(TARGET_COLUMN, "mean"),
        )
        .reset_index()
    )
    table["probability_bin"] = table["probability_bin"].astype(str)
    return table


def bootstrap_participant_metrics(predictions: pd.DataFrame) -> pd.DataFrame:
    """Estimate uncertainty by resampling held-out participants with replacement."""

    rng = np.random.default_rng(RANDOM_STATE)
    participants = predictions["participant_object_id"].astype(str).unique()
    rows: list[dict[str, float | int]] = []

    for repeat in range(BOOTSTRAP_REPEATS):
        sampled_participants = rng.choice(participants, size=len(participants), replace=True)
        sampled = pd.concat(
            [
                predictions[predictions["participant_object_id"].astype(str) == participant]
                for participant in sampled_participants
            ],
            ignore_index=True,
        )

        # Some bootstrap samples can contain only one target class. ROC AUC is
        # undefined there, but threshold metrics remain useful.
        metric_row = {
            "repeat": repeat + 1,
            "rows": len(sampled),
            "participants_sampled": len(sampled_participants),
            "balanced_accuracy": balanced_accuracy_score(
                sampled[TARGET_COLUMN],
                sampled["y_pred"],
            ),
            "f1": f1_score(sampled[TARGET_COLUMN], sampled["y_pred"], zero_division=0),
        }
        if sampled[TARGET_COLUMN].nunique() == 2:
            metric_row["roc_auc"] = roc_auc_score(sampled[TARGET_COLUMN], sampled["y_score"])
        else:
            metric_row["roc_auc"] = np.nan
        rows.append(metric_row)

    return pd.DataFrame(rows)


def summarize_bootstrap(bootstrap: pd.DataFrame) -> pd.DataFrame:
    """Summarize participant bootstrap intervals for report metrics."""

    rows = []
    for metric in ["balanced_accuracy", "roc_auc", "f1"]:
        values = bootstrap[metric].dropna()
        rows.append(
            {
                "metric": metric,
                "mean": values.mean(),
                "p025": values.quantile(0.025),
                "p500": values.quantile(0.5),
                "p975": values.quantile(0.975),
                "valid_repeats": len(values),
            }
        )
    return pd.DataFrame(rows)


def save_figures(
    coefficients: pd.DataFrame,
    calibration: pd.DataFrame,
    bootstrap_summary: pd.DataFrame,
) -> dict[str, Path]:
    """Save report figures for model interpretation and validation."""

    use_chart_theme()
    FIGURE_DIR.mkdir(parents=True, exist_ok=True)
    figure_paths = {
        "coefficients": FIGURE_DIR / "top_logistic_coefficients.png",
        "calibration": FIGURE_DIR / "probability_calibration.png",
        "bootstrap": FIGURE_DIR / "bootstrap_metric_intervals.png",
    }

    top_positive = coefficients[coefficients["coefficient"] > 0].nlargest(10, "coefficient")
    top_negative = coefficients[coefficients["coefficient"] < 0].nsmallest(10, "coefficient")
    plot_coefficients = pd.concat([top_negative, top_positive]).sort_values("coefficient")

    fig, ax = plt.subplots(figsize=(10, 8))
    colors = [
        COLOR_FAMILIES["orange"]["base"] if value < 0 else COLOR_FAMILIES["olive"]["base"]
        for value in plot_coefficients["coefficient"]
    ]
    edge_colors = [
        COLOR_FAMILIES["orange"]["dark"] if value < 0 else COLOR_FAMILIES["olive"]["dark"]
        for value in plot_coefficients["coefficient"]
    ]
    bars = ax.barh(plot_coefficients["feature"], plot_coefficients["coefficient"], color=colors)
    for bar, edge_color in zip(bars, edge_colors):
        bar.set_edgecolor(edge_color)
        bar.set_linewidth(1.0)
    ax.axvline(0, color=TOKENS["ink"], linewidth=1.0)
    ax.set_xlabel("Standardized logistic coefficient")
    ax.set_ylabel("")
    add_chart_header(
        fig,
        ax,
        "Largest baseline model coefficients",
        "Positive coefficients increase predicted probability of good sleep; wearable-only Logistic Regression.",
    )
    plt.tight_layout(rect=[0, 0, 1, 0.88])
    plt.savefig(figure_paths["coefficients"], dpi=160)
    plt.close()

    fig, ax = plt.subplots(figsize=(8, 6))
    x = np.arange(len(calibration))
    ax.plot(
        x,
        calibration["mean_predicted_probability"],
        marker="o",
        color=COLOR_FAMILIES["blue"]["base"],
        label="Mean predicted probability",
    )
    ax.plot(
        x,
        calibration["observed_good_sleep_rate"],
        marker="o",
        color=COLOR_FAMILIES["gold"]["dark"],
        label="Observed good-sleep rate",
    )
    ax.set_ylim(0, 1)
    ax.set_xticks(x, [str(i + 1) for i in x])
    ax.set_xlabel("Predicted probability decile")
    ax.set_ylabel("Rate")
    ax.legend(loc="lower right", frameon=False)
    add_chart_header(
        fig,
        ax,
        "Predicted probability deciles are directionally ordered",
        "Each decile contains held-out participant-day rows sorted by predicted good-sleep probability.",
    )
    plt.tight_layout(rect=[0, 0, 1, 0.88])
    plt.savefig(figure_paths["calibration"], dpi=160)
    plt.close()

    fig, ax = plt.subplots(figsize=(8, 4.8))
    metrics = bootstrap_summary.copy()
    y = np.arange(len(metrics))
    lower = metrics["p500"] - metrics["p025"]
    upper = metrics["p975"] - metrics["p500"]
    ax.errorbar(
        metrics["p500"],
        y,
        xerr=[lower, upper],
        fmt="o",
        color=COLOR_FAMILIES["blue"]["base"],
        ecolor=COLOR_FAMILIES["blue"]["dark"],
        capsize=4,
    )
    ax.set_yticks(y, metrics["metric"].str.replace("_", " ").str.title())
    ax.set_xlim(0, 1)
    ax.set_xlabel("Metric value")
    add_chart_header(
        fig,
        ax,
        "Held-out participant bootstrap intervals",
        "Intervals resample the 14 held-out participants with replacement, 1,000 repeats.",
    )
    plt.tight_layout(rect=[0, 0, 1, 0.88])
    plt.savefig(figure_paths["bootstrap"], dpi=160)
    plt.close()

    return figure_paths


def write_report(
    train: pd.DataFrame,
    test: pd.DataFrame,
    feature_columns: list[str],
    metrics: dict[str, float | int],
    tuned_metrics: pd.DataFrame,
    coefficients: pd.DataFrame,
    calibration: pd.DataFrame,
    bootstrap_summary: pd.DataFrame,
    figure_paths: dict[str, Path],
) -> None:
    """Write the technical final-baseline validation and interpretation report."""

    best_tuned = tuned_metrics.sort_values(["balanced_accuracy", "roc_auc"], ascending=False).iloc[0]
    positive = coefficients[coefficients["coefficient"] > 0].head(10)
    negative = coefficients[coefficients["coefficient"] < 0].head(10)
    ba_interval = bootstrap_summary[bootstrap_summary["metric"] == "balanced_accuracy"].iloc[0]
    roc_interval = bootstrap_summary[bootstrap_summary["metric"] == "roc_auc"].iloc[0]

    lines = [
        "# Final Baseline Validation and Interpretation",
        "",
        "## Technical Summary",
        "",
        "- The current selected baseline is `wearable_only + Logistic Regression`; it is a baseline candidate, not the final model across all model families.",
        f"- On the held-out participant test split, it achieved balanced accuracy `{metrics['balanced_accuracy']:.4f}`, ROC AUC `{metrics['roc_auc']:.4f}`, and F1 `{metrics['f1']:.4f}`.",
        f"- Participant bootstrap suggests balanced accuracy is directionally positive but still uncertain: median `{ba_interval['p500']:.4f}`, 95% interval `{ba_interval['p025']:.4f}` to `{ba_interval['p975']:.4f}`.",
        "- Coefficients should be interpreted as associations in a predictive model, not causal effects on sleep quality.",
        "",
        "## The Baseline Signal Is Mainly Wearable-Driven",
        "",
        f"The tuned comparison selected `{best_tuned['feature_set']}` with `{int(best_tuned['feature_count'])}` features. This means SEMA context/mood and participant survey features were not needed for the strongest current baseline. The model used standardized wearable-derived features and retained the fixed participant-aware split.",
        "",
        "| metric | value |",
        "| --- | ---: |",
        f"| accuracy | {metrics['accuracy']:.4f} |",
        f"| balanced accuracy | {metrics['balanced_accuracy']:.4f} |",
        f"| precision | {metrics['precision']:.4f} |",
        f"| recall | {metrics['recall']:.4f} |",
        f"| F1 | {metrics['f1']:.4f} |",
        f"| ROC AUC | {metrics['roc_auc']:.4f} |",
        f"| average precision | {metrics['average_precision']:.4f} |",
        "",
        "The recall is higher than precision, so this baseline is better at catching good-sleep days than avoiding false positives. That tradeoff is acceptable for exploratory modeling, but a final application would need a threshold chosen for the intended use case.",
        "",
        f"Figure: `{figure_paths['coefficients']}`",
        "",
        "## Coefficients Identify Predictive Associations, Not Causes",
        "",
        "Because the model is Logistic Regression after standardization, larger absolute coefficients indicate stronger model influence on the log-odds of `good_sleep_label=1`. Positive coefficients push predictions toward good sleep; negative coefficients push predictions away from good sleep.",
        "",
        "### Strongest Positive Coefficients",
        "",
        "| feature | coefficient |",
        "| --- | ---: |",
    ]
    for _, row in positive.iterrows():
        lines.append(f"| `{row['feature']}` | {row['coefficient']:.4f} |")

    lines.extend(
        [
            "",
            "### Strongest Negative Coefficients",
            "",
            "| feature | coefficient |",
            "| --- | ---: |",
        ]
    )
    for _, row in negative.iterrows():
        lines.append(f"| `{row['feature']}` | {row['coefficient']:.4f} |")

    lines.extend(
        [
            "",
            "Some large coefficients are count or missingness-related wearable availability signals. These can be operationally predictive, but they should be reported separately from physiological interpretation.",
            "",
            "## Probability Scores Are Useful But Not Fully Calibrated",
            "",
            "The calibration table compares predicted probability deciles with observed good-sleep rates on the held-out participant test split. The deciles are directionally informative, but this is not enough to claim calibrated probability estimates.",
            "",
            f"Figure: `{figure_paths['calibration']}`",
            "",
            "| decile | rows | mean predicted probability | observed good-sleep rate |",
            "| ---: | ---: | ---: | ---: |",
        ]
    )
    for i, row in enumerate(calibration.itertuples(index=False), start=1):
        lines.append(
            f"| {i} | {int(row.rows):,} | {row.mean_predicted_probability:.4f} | "
            f"{row.observed_good_sleep_rate:.4f} |"
        )

    lines.extend(
        [
            "",
            "## Validation Depends On Only 14 Held-Out Participants",
            "",
            f"The test set contains `{test['participant_object_id'].nunique()}` participants and `{len(test):,}` participant-day rows. Since rows from the same participant are correlated, participant-level uncertainty matters more than row count alone.",
            "",
            f"Figure: `{figure_paths['bootstrap']}`",
            "",
            "| metric | mean | median | 95% interval | valid bootstrap repeats |",
            "| --- | ---: | ---: | --- | ---: |",
        ]
    )
    for _, row in bootstrap_summary.iterrows():
        lines.append(
            f"| `{row['metric']}` | {row['mean']:.4f} | {row['p500']:.4f} | "
            f"{row['p025']:.4f} to {row['p975']:.4f} | {int(row['valid_repeats']):,} |"
        )

    lines.extend(
        [
            "",
            "## Scope, Data, And Metric Definitions",
            "",
            f"- Train split: `{len(train):,}` rows, `{train['participant_object_id'].nunique():,}` participants.",
            f"- Test split: `{len(test):,}` rows, `{test['participant_object_id'].nunique():,}` participants.",
            "- Target: `good_sleep_label`, binary label where `1` represents a good-sleep day.",
            "- Model feature set: `wearable_only`, excluding SEMA context/mood and participant survey features.",
            "- Evaluation grain: participant-day rows, with split isolation at participant level.",
            "- Main comparison metric: balanced accuracy, because class balance is not perfectly even.",
            "",
            "## Methodology",
            "",
            "1. Reused the fixed participant-aware train/test split.",
            "2. Selected the tuned `logistic_regression__wearable_only` model from `tuned_models.joblib`.",
            "3. Recomputed held-out test predictions and metrics from the saved model.",
            "4. Extracted standardized Logistic Regression coefficients for interpretability.",
            "5. Built decile-level probability calibration checks.",
            "6. Resampled held-out participants with replacement to estimate uncertainty intervals.",
            "",
            "## Limitations And Robustness Checks",
            "",
            "- The selected model is a baseline candidate only; it has not been compared against boosted trees, SVM, MLP, or sequence models.",
            "- The held-out test split has only 14 participants, so participant composition can materially affect metrics.",
            "- Coefficients are predictive associations and should not be described as causal sleep drivers.",
            "- Same-day wearable features may still include data-availability patterns related to user/device behavior.",
            "- Probability calibration is directional but not established enough for clinical or high-stakes use.",
            "",
            "## Recommended Next Steps",
            "",
            "1. Compare stronger tabular models such as XGBoost, LightGBM, and CatBoost using the same participant-aware split and CV design.",
            "2. Add repeated participant-aware resampling or confidence intervals to final model selection.",
            "3. Compare tabular daily models against sequence-aware models that use participant day order.",
            "4. Decide whether availability/count features are allowed for the target use case before final interpretation.",
            "",
            "## Further Questions",
            "",
            "- Should the final model optimize recall, precision, balanced accuracy, or calibrated probability?",
            "- Should same-day features be used, or should the model predict tomorrow's sleep from prior-day signals?",
            "- Should participant-specific baselines be modeled explicitly?",
            "",
        ]
    )

    REPORT_PATH.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    train = pd.read_csv(TRAIN_PATH)
    test = pd.read_csv(TEST_PATH)
    tuned_metrics = pd.read_csv(TUNED_METRICS_PATH)
    models = joblib.load(TUNED_MODELS_PATH)
    feature_columns = load_feature_columns()

    train["participant_object_id"] = train["participant_object_id"].astype(str)
    test["participant_object_id"] = test["participant_object_id"].astype(str)
    train["calendar_date"] = pd.to_datetime(train["calendar_date"], errors="coerce").dt.date.astype(str)
    test["calendar_date"] = pd.to_datetime(test["calendar_date"], errors="coerce").dt.date.astype(str)

    validate_inputs(train, test, feature_columns)
    model = models[BEST_MODEL_KEY]
    predictions = score_best_model(model, test, feature_columns)
    metrics = compute_metrics(predictions)
    coefficients = extract_coefficients(model, feature_columns)
    calibration = build_calibration_table(predictions)
    bootstrap = bootstrap_participant_metrics(predictions)
    bootstrap_summary = summarize_bootstrap(bootstrap)
    figure_paths = save_figures(coefficients, calibration, bootstrap_summary)

    COEFFICIENTS_PATH.parent.mkdir(parents=True, exist_ok=True)
    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    coefficients.to_csv(COEFFICIENTS_PATH, index=False, encoding="utf-8-sig")
    calibration.to_csv(CALIBRATION_PATH, index=False, encoding="utf-8-sig")
    bootstrap.to_csv(BOOTSTRAP_PATH, index=False, encoding="utf-8-sig")
    write_report(
        train=train,
        test=test,
        feature_columns=feature_columns,
        metrics=metrics,
        tuned_metrics=tuned_metrics,
        coefficients=coefficients,
        calibration=calibration,
        bootstrap_summary=bootstrap_summary,
        figure_paths=figure_paths,
    )

    print(f"Selected model: {BEST_MODEL_KEY}")
    print(f"Feature count: {len(feature_columns)}")
    print(f"Test rows: {len(test)}")
    print(f"Test participants: {test['participant_object_id'].nunique()}")
    print(f"Balanced accuracy: {metrics['balanced_accuracy']:.4f}")
    print(f"ROC AUC: {metrics['roc_auc']:.4f}")
    print(f"F1: {metrics['f1']:.4f}")
    print(f"Wrote coefficients: {COEFFICIENTS_PATH}")
    print(f"Wrote calibration: {CALIBRATION_PATH}")
    print(f"Wrote bootstrap metrics: {BOOTSTRAP_PATH}")
    print(f"Wrote report: {REPORT_PATH}")


if __name__ == "__main__":
    main()
