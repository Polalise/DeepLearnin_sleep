from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Any

import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns


# This script performs final EDA on the merged modeling dataset.
#
# Boundary:
# - It does not impute missing values.
# - It does not encode categorical variables.
# - It does not scale features.
# - It does not run PCA.
#
# Purpose:
# - Understand final dataset shape, target balance, missingness, feature coverage,
#   basic distributions, and target-feature relationships before preprocessing.
PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATA_PATH = PROJECT_ROOT / "data" / "processed" / "modeling_dataset_daily.csv"
REPORT_PATH = PROJECT_ROOT / "reports" / "final_dataset_eda.md"
FIGURE_DIR = PROJECT_ROOT / "reports" / "figures" / "final_dataset_eda"

KEY_COLUMNS = [
    "participant_object_id",
    "calendar_date",
    "mongo_doc_id",
    "logId",
    "startTime",
    "endTime",
]
TARGET_COLUMNS = [
    "good_sleep_label",
    "minutesAsleep",
    "minutesAwake",
    "timeInBed",
    "efficiency",
    "sleep_duration_hours",
    "time_in_bed_hours",
    "awake_ratio",
]


def numeric_feature_columns(df: pd.DataFrame) -> list[str]:
    """Return numeric modeling feature candidates, excluding identifiers and targets."""

    excluded = set(KEY_COLUMNS + TARGET_COLUMNS)
    numeric_columns = df.select_dtypes(include=["number"]).columns
    return [column for column in numeric_columns if column not in excluded]


def missing_summary(df: pd.DataFrame) -> pd.DataFrame:
    """Summarize missingness for every column."""

    return (
        pd.DataFrame(
            {
                "column": df.columns,
                "missing_count": df.isna().sum().to_numpy(),
                "missing_rate": df.isna().mean().to_numpy(),
                "dtype": [str(dtype) for dtype in df.dtypes],
            }
        )
        .sort_values(["missing_rate", "missing_count"], ascending=False)
        .reset_index(drop=True)
    )


def feature_family(column: str) -> str:
    """Group columns into human-readable source/feature families."""

    if column in KEY_COLUMNS:
        return "key"
    if column in TARGET_COLUMNS:
        return "target"
    if column.startswith("stress_"):
        return "stress"
    if column.startswith("hrv_summary_") or column.startswith("hrv_detail_"):
        return "hrv"
    if column.startswith("resting_hr_"):
        return "resting_hr"
    if column.endswith("_minutes_sum") or column.startswith("steps_") or column.startswith("calories_"):
        return "activity"
    if column.startswith("spo2_"):
        return "spo2"
    if column.startswith("respiratory_"):
        return "respiratory"
    if column.startswith("wrist_temperature_"):
        return "temperature"
    if column.startswith("mood_") or column.startswith("place_") or column.startswith("sema_"):
        return "sema"
    if column.startswith("survey_"):
        return "survey"
    if column.endswith("_ratio") or column.endswith("_minutes"):
        return "sleep_stage"
    return "other"


def family_missing_summary(df: pd.DataFrame) -> pd.DataFrame:
    """Summarize missingness by feature family."""

    missing = missing_summary(df)
    missing["family"] = missing["column"].map(feature_family)
    return (
        missing.groupby("family", as_index=False)
        .agg(
            columns=("column", "count"),
            avg_missing_rate=("missing_rate", "mean"),
            max_missing_rate=("missing_rate", "max"),
        )
        .sort_values("avg_missing_rate", ascending=False)
    )


def target_feature_difference(df: pd.DataFrame, features: list[str]) -> pd.DataFrame:
    """Compare selected numeric features between good and bad sleep days."""

    rows: list[dict[str, Any]] = []
    for column in features:
        if column not in df.columns:
            continue
        values = pd.to_numeric(df[column], errors="coerce")
        grouped = df.assign(_value=values).groupby("good_sleep_label")["_value"]
        means = grouped.mean()
        counts = grouped.count()
        bad_mean = means.get(0, pd.NA)
        good_mean = means.get(1, pd.NA)
        rows.append(
            {
                "feature": column,
                "bad_sleep_mean": bad_mean,
                "good_sleep_mean": good_mean,
                "difference_good_minus_bad": good_mean - bad_mean,
                "non_null_bad": counts.get(0, 0),
                "non_null_good": counts.get(1, 0),
            }
        )
    return pd.DataFrame(rows).sort_values("difference_good_minus_bad", key=lambda s: s.abs(), ascending=False)


def correlation_with_target(df: pd.DataFrame, features: list[str]) -> pd.DataFrame:
    """Compute Pearson correlation between numeric features and good_sleep_label."""

    rows = []
    target = pd.to_numeric(df["good_sleep_label"], errors="coerce")
    for column in features:
        values = pd.to_numeric(df[column], errors="coerce")
        valid = pd.concat([target, values], axis=1).dropna()
        if len(valid) < 30 or valid[column].nunique() <= 1:
            continue
        rows.append(
            {
                "feature": column,
                "non_null_count": len(valid),
                "corr_with_good_sleep_label": valid["good_sleep_label"].corr(valid[column]),
            }
        )
    return pd.DataFrame(rows).sort_values(
        "corr_with_good_sleep_label", key=lambda s: s.abs(), ascending=False
    )


def outlier_summary(df: pd.DataFrame, features: list[str]) -> pd.DataFrame:
    """Flag simple IQR-based outlier counts for numeric feature candidates."""

    rows = []
    for column in features:
        values = pd.to_numeric(df[column], errors="coerce").dropna()
        if len(values) < 30:
            continue
        q1 = values.quantile(0.25)
        q3 = values.quantile(0.75)
        iqr = q3 - q1
        if iqr == 0:
            continue
        lower = q1 - 1.5 * iqr
        upper = q3 + 1.5 * iqr
        outliers = int(((values < lower) | (values > upper)).sum())
        rows.append(
            {
                "feature": column,
                "non_null_count": len(values),
                "outlier_count": outliers,
                "outlier_rate": outliers / len(values),
                "lower_bound": lower,
                "upper_bound": upper,
            }
        )
    return pd.DataFrame(rows).sort_values("outlier_rate", ascending=False)


def save_target_plot(df: pd.DataFrame) -> Path:
    """Save target distribution plot."""

    path = FIGURE_DIR / "target_distribution.png"
    plt.figure(figsize=(6, 4))
    ax = sns.countplot(data=df, x="good_sleep_label", hue="good_sleep_label", palette="Set2", legend=False)
    ax.set_title("Final Dataset Target Distribution")
    ax.set_xlabel("good_sleep_label")
    ax.set_ylabel("Rows")
    for container in ax.containers:
        ax.bar_label(container)
    plt.tight_layout()
    plt.savefig(path, dpi=160)
    plt.close()
    return path


def save_missing_family_plot(family_missing: pd.DataFrame) -> Path:
    """Save feature-family missingness plot."""

    path = FIGURE_DIR / "missing_rate_by_feature_family.png"
    plot_df = family_missing.sort_values("avg_missing_rate", ascending=True)
    plt.figure(figsize=(9, 5))
    ax = sns.barplot(data=plot_df, x="avg_missing_rate", y="family", color="#4C78A8")
    ax.set_title("Average Missing Rate by Feature Family")
    ax.set_xlabel("Average missing rate")
    ax.set_ylabel("")
    ax.xaxis.set_major_formatter(lambda x, _: f"{x:.0%}")
    plt.tight_layout()
    plt.savefig(path, dpi=160)
    plt.close()
    return path


def save_key_feature_by_target_plot(df: pd.DataFrame) -> Path:
    """Save boxplots for selected key features by sleep label."""

    path = FIGURE_DIR / "key_features_by_target.png"
    selected = [
        "minutesAsleep",
        "efficiency",
        "stress_score_mean",
        "hrv_summary_rmssd_mean",
        "steps_sum",
        "calories_sum",
        "wrist_temperature_mean",
        "sema_response_count",
    ]
    available = [column for column in selected if column in df.columns]
    plot_df = df[["good_sleep_label", *available]].melt(
        id_vars="good_sleep_label", var_name="feature", value_name="value"
    )
    plot_df["value"] = pd.to_numeric(plot_df["value"], errors="coerce")
    plot_df = plot_df.dropna()

    fig, axes = plt.subplots(2, 4, figsize=(14, 7))
    for axis, feature in zip(axes.ravel(), available):
        subset = plot_df[plot_df["feature"] == feature]
        sns.boxplot(data=subset, x="good_sleep_label", y="value", ax=axis, color="#F28E2B")
        axis.set_title(feature)
        axis.set_xlabel("good_sleep_label")
        axis.set_ylabel("")
    for axis in axes.ravel()[len(available):]:
        axis.axis("off")
    plt.tight_layout()
    plt.savefig(path, dpi=160)
    plt.close()
    return path


def save_correlation_plot(correlations: pd.DataFrame) -> Path:
    """Save top absolute correlations with target."""

    path = FIGURE_DIR / "top_target_correlations.png"
    plot_df = correlations.head(20).copy()
    plot_df = plot_df.sort_values("corr_with_good_sleep_label", ascending=True)
    plt.figure(figsize=(9, 7))
    ax = sns.barplot(
        data=plot_df,
        x="corr_with_good_sleep_label",
        y="feature",
        hue=plot_df["corr_with_good_sleep_label"] > 0,
        palette={True: "#59A14F", False: "#E15759"},
        legend=False,
    )
    ax.set_title("Top Correlations With Good Sleep Label")
    ax.set_xlabel("Pearson correlation")
    ax.set_ylabel("")
    plt.tight_layout()
    plt.savefig(path, dpi=160)
    plt.close()
    return path


def write_report(
    df: pd.DataFrame,
    missing: pd.DataFrame,
    family_missing: pd.DataFrame,
    target_diffs: pd.DataFrame,
    correlations: pd.DataFrame,
    outliers: pd.DataFrame,
    figure_paths: list[Path],
) -> None:
    """Write final dataset EDA report."""

    duplicate_rows = int(df.duplicated(["participant_object_id", "calendar_date"]).sum())
    target_counts = df["good_sleep_label"].value_counts(dropna=False).sort_index()
    numeric_features = numeric_feature_columns(df)

    lines = [
        "# Final Dataset EDA",
        "",
        f"- Generated at: `{datetime.now().isoformat(timespec='seconds')}`",
        f"- Input file: `{DATA_PATH}`",
        "",
        "## Scope",
        "",
        "- This report explores the merged daily modeling dataset.",
        "- It does not perform missing-value imputation, categorical encoding, scaling, PCA, or modeling.",
        "",
        "## Dataset Shape",
        "",
        f"- Rows: `{len(df):,}`",
        f"- Columns: `{len(df.columns):,}`",
        f"- Participants: `{df['participant_object_id'].nunique():,}`",
        f"- Date range: `{df['calendar_date'].min()}` to `{df['calendar_date'].max()}`",
        f"- Duplicate participant-date rows: `{duplicate_rows:,}`",
        f"- Numeric feature candidates, excluding keys and targets: `{len(numeric_features):,}`",
        "",
        "## Target Distribution",
        "",
        "| good_sleep_label | rows | rate |",
        "| ---: | ---: | ---: |",
    ]

    for label, count in target_counts.items():
        lines.append(f"| `{label}` | {int(count):,} | {count / len(df):.2%} |")

    lines.extend(
        [
            "",
            "## Missingness By Feature Family",
            "",
            "| family | columns | avg missing rate | max missing rate |",
            "| --- | ---: | ---: | ---: |",
        ]
    )
    for _, row in family_missing.iterrows():
        lines.append(
            f"| `{row['family']}` | {int(row['columns']):,} | "
            f"{row['avg_missing_rate']:.2%} | {row['max_missing_rate']:.2%} |"
        )

    lines.extend(
        [
            "",
            "## Highest Missing Columns",
            "",
            "| column | dtype | missing count | missing rate |",
            "| --- | --- | ---: | ---: |",
        ]
    )
    for _, row in missing.head(30).iterrows():
        lines.append(
            f"| `{row['column']}` | `{row['dtype']}` | "
            f"{int(row['missing_count']):,} | {row['missing_rate']:.2%} |"
        )

    lines.extend(
        [
            "",
            "## Largest Mean Differences By Target",
            "",
            "| feature | bad sleep mean | good sleep mean | good - bad | non-null bad | non-null good |",
            "| --- | ---: | ---: | ---: | ---: | ---: |",
        ]
    )
    for _, row in target_diffs.head(25).iterrows():
        lines.append(
            f"| `{row['feature']}` | {row['bad_sleep_mean']:.3f} | "
            f"{row['good_sleep_mean']:.3f} | {row['difference_good_minus_bad']:.3f} | "
            f"{int(row['non_null_bad']):,} | {int(row['non_null_good']):,} |"
        )

    lines.extend(
        [
            "",
            "## Top Absolute Correlations With Target",
            "",
            "| feature | non-null count | corr with good_sleep_label |",
            "| --- | ---: | ---: |",
        ]
    )
    for _, row in correlations.head(25).iterrows():
        lines.append(
            f"| `{row['feature']}` | {int(row['non_null_count']):,} | "
            f"{row['corr_with_good_sleep_label']:.3f} |"
        )

    lines.extend(
        [
            "",
            "## Highest IQR Outlier Rates",
            "",
            "| feature | non-null count | outlier count | outlier rate |",
            "| --- | ---: | ---: | ---: |",
        ]
    )
    for _, row in outliers.head(20).iterrows():
        lines.append(
            f"| `{row['feature']}` | {int(row['non_null_count']):,} | "
            f"{int(row['outlier_count']):,} | {row['outlier_rate']:.2%} |"
        )

    lines.extend(["", "## Figures", ""])
    for path in figure_paths:
        lines.append(f"- `{path}`")

    lines.extend(
        [
            "",
            "## EDA Notes For Next Step",
            "",
            "- Classic sleep-stage columns have very high missingness because Fitbit mixes classic and stages sleep formats.",
            "- SpO2, stress, and SEMA features have partial day coverage and need explicit missing-value strategy.",
            "- Stress-related features may leak sleep/recovery information and should be reported as a limitation if used.",
            "- Several record-count columns may be useful both as coverage indicators and missingness flags.",
            "",
            "## Recommended Next Step",
            "",
            "```text",
            "missing-value handling plan -> apply imputation/drop rules -> categorical encoding",
            "```",
            "",
        ]
    )

    REPORT_PATH.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    FIGURE_DIR.mkdir(parents=True, exist_ok=True)
    df = pd.read_csv(DATA_PATH)
    df["calendar_date"] = pd.to_datetime(df["calendar_date"], errors="coerce").dt.date.astype(str)

    features = numeric_feature_columns(df)
    missing = missing_summary(df)
    family_missing = family_missing_summary(df)
    target_diffs = target_feature_difference(df, features)
    correlations = correlation_with_target(df, features)
    outliers = outlier_summary(df, features)

    figure_paths = [
        save_target_plot(df),
        save_missing_family_plot(family_missing),
        save_key_feature_by_target_plot(df),
        save_correlation_plot(correlations),
    ]

    write_report(df, missing, family_missing, target_diffs, correlations, outliers, figure_paths)

    print(f"Rows: {len(df)}")
    print(f"Columns: {len(df.columns)}")
    print(f"Numeric feature candidates: {len(features)}")
    print(f"Wrote report: {REPORT_PATH}")
    print("Figures:")
    for path in figure_paths:
        print(f"- {path}")


if __name__ == "__main__":
    main()
