from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Any

import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns


# This script performs a light validation and visualization pass after the
# date-level aggregation step.
#
# Scope:
# - Check generated daily aggregate tables for duplicate keys, date ranges,
#   row/column counts, and missing values.
# - Visualize the sleep target table and several key aggregated features.
# - Do not merge all tables, impute missing values, encode categories, scale,
#   or run PCA. Those are later pipeline steps.
PROJECT_ROOT = Path(__file__).resolve().parents[1]
DAILY_DIR = PROJECT_ROOT / "data" / "processed" / "daily_aggregates"
REPORT_PATH = PROJECT_ROOT / "reports" / "daily_aggregation_validation.md"
FIGURE_DIR = PROJECT_ROOT / "reports" / "figures"


DAILY_KEY = ["participant_object_id", "calendar_date"]


def read_daily_table(file_name: str) -> pd.DataFrame:
    """Read a daily aggregate table and normalize the calendar_date column."""

    df = pd.read_csv(DAILY_DIR / file_name)
    if "calendar_date" in df.columns:
        df["calendar_date"] = pd.to_datetime(df["calendar_date"], errors="coerce")
    return df


def table_validation(file_name: str, key_columns: list[str]) -> dict[str, Any]:
    """Return a compact validation summary for one generated table."""

    df = read_daily_table(file_name)
    duplicate_count = 0
    if all(column in df.columns for column in key_columns):
        duplicate_count = int(df.duplicated(key_columns).sum())

    date_min = None
    date_max = None
    if "calendar_date" in df.columns:
        valid_dates = df["calendar_date"].dropna()
        if not valid_dates.empty:
            date_min = valid_dates.min().date().isoformat()
            date_max = valid_dates.max().date().isoformat()

    missing_cells = int(df.isna().sum().sum())
    total_cells = int(df.shape[0] * df.shape[1])
    missing_rate = missing_cells / total_cells if total_cells else 0

    return {
        "file_name": file_name,
        "rows": len(df),
        "columns": len(df.columns),
        "duplicate_key_rows": duplicate_count,
        "date_min": date_min,
        "date_max": date_max,
        "missing_cells": missing_cells,
        "missing_rate": missing_rate,
    }


def save_sleep_target_plot(sleep: pd.DataFrame) -> Path:
    """Plot the good/bad sleep label distribution."""

    path = FIGURE_DIR / "sleep_target_distribution.png"
    plt.figure(figsize=(6, 4))
    ax = sns.countplot(data=sleep, x="good_sleep_label", hue="good_sleep_label", palette="Set2", legend=False)
    ax.set_title("Good Sleep Label Distribution")
    ax.set_xlabel("good_sleep_label")
    ax.set_ylabel("Days")
    for container in ax.containers:
        ax.bar_label(container)
    plt.tight_layout()
    plt.savefig(path, dpi=160)
    plt.close()
    return path


def save_sleep_metric_histograms(sleep: pd.DataFrame) -> Path:
    """Plot basic sleep target metric distributions."""

    path = FIGURE_DIR / "sleep_metric_histograms.png"
    columns = ["minutesAsleep", "efficiency", "timeInBed", "awake_ratio"]
    fig, axes = plt.subplots(2, 2, figsize=(10, 7))
    for axis, column in zip(axes.ravel(), columns):
        sns.histplot(sleep[column].dropna(), bins=30, kde=True, ax=axis, color="#4C78A8")
        axis.set_title(column)
        axis.set_xlabel(column)
        axis.set_ylabel("Count")
    plt.tight_layout()
    plt.savefig(path, dpi=160)
    plt.close()
    return path


def save_daily_coverage_plot(tables: dict[str, pd.DataFrame]) -> Path:
    """Plot how many participant-day rows each daily source contributes."""

    path = FIGURE_DIR / "daily_table_row_coverage.png"
    coverage = pd.DataFrame(
        {
            "table": [name.replace(".csv", "") for name in tables],
            "rows": [len(df) for df in tables.values()],
        }
    ).sort_values("rows", ascending=True)

    plt.figure(figsize=(9, 6))
    ax = sns.barplot(data=coverage, x="rows", y="table", color="#59A14F")
    ax.set_title("Daily Aggregate Row Coverage")
    ax.set_xlabel("Rows")
    ax.set_ylabel("")
    plt.tight_layout()
    plt.savefig(path, dpi=160)
    plt.close()
    return path


def save_key_feature_boxplots(tables: dict[str, pd.DataFrame]) -> Path:
    """Plot distributions for several important aggregated feature families."""

    path = FIGURE_DIR / "key_feature_boxplots.png"
    feature_sources = [
        ("fitbit_stress_daily.csv", "stress_score_mean"),
        ("fitbit_daily_hrv_summary_daily.csv", "hrv_summary_rmssd_mean"),
        ("fitbit_resting_heart_rate_daily.csv", "resting_hr_resting_heart_rate_mean"),
        ("fitbit_steps_daily.csv", "steps_sum"),
        ("fitbit_calories_daily.csv", "calories_sum"),
        ("fitbit_wrist_temperature_daily.csv", "wrist_temperature_mean"),
    ]

    records = []
    for file_name, column in feature_sources:
        df = tables[file_name]
        if column not in df.columns:
            continue
        values = pd.to_numeric(df[column], errors="coerce").dropna()
        for value in values:
            records.append({"feature": column, "value": value})

    plot_df = pd.DataFrame(records)
    plt.figure(figsize=(11, 5))
    ax = sns.boxplot(data=plot_df, x="feature", y="value", color="#F28E2B")
    ax.set_title("Key Daily Feature Distributions")
    ax.set_xlabel("")
    ax.set_ylabel("Value")
    ax.tick_params(axis="x", rotation=30)
    plt.tight_layout()
    plt.savefig(path, dpi=160)
    plt.close()
    return path


def save_sleep_time_series(sleep: pd.DataFrame) -> Path:
    """Plot daily average sleep duration and daily observation count."""

    path = FIGURE_DIR / "sleep_daily_time_series.png"
    daily = (
        sleep.groupby("calendar_date")
        .agg(
            avg_minutes_asleep=("minutesAsleep", "mean"),
            sleep_records=("minutesAsleep", "size"),
        )
        .reset_index()
        .sort_values("calendar_date")
    )

    fig, axis1 = plt.subplots(figsize=(11, 4.5))
    sns.lineplot(data=daily, x="calendar_date", y="avg_minutes_asleep", ax=axis1, color="#4C78A8")
    axis1.set_title("Daily Average Sleep Duration and Record Count")
    axis1.set_xlabel("Date")
    axis1.set_ylabel("Average minutes asleep")

    axis2 = axis1.twinx()
    axis2.fill_between(daily["calendar_date"], daily["sleep_records"], color="#BAB0AC", alpha=0.35)
    axis2.set_ylabel("Sleep records")

    fig.autofmt_xdate()
    plt.tight_layout()
    plt.savefig(path, dpi=160)
    plt.close()
    return path


def write_report(
    validations: list[dict[str, Any]],
    sleep_summary: dict[str, Any],
    feature_summary: pd.DataFrame,
    figure_paths: list[Path],
) -> None:
    """Write the validation and visualization report."""

    lines = [
        "# Daily Aggregation Validation",
        "",
        f"- Generated at: `{datetime.now().isoformat(timespec='seconds')}`",
        f"- Input directory: `{DAILY_DIR}`",
        "",
        "## Scope",
        "",
        "- This is a light validation and visualization pass for the date-level aggregate outputs.",
        "- It checks duplicate keys, date ranges, missing cells, target distribution, and selected feature ranges.",
        "- It does not merge the final modeling dataset or perform imputation/encoding/scaling/PCA.",
        "",
        "## Table Validation",
        "",
        "| table | rows | columns | duplicate key rows | date min | date max | missing rate |",
        "| --- | ---: | ---: | ---: | --- | --- | ---: |",
    ]

    for item in validations:
        lines.append(
            f"| `{item['file_name']}` | {item['rows']:,} | {item['columns']} | "
            f"{item['duplicate_key_rows']:,} | `{item['date_min']}` | `{item['date_max']}` | "
            f"{item['missing_rate']:.2%} |"
        )

    lines.extend(
        [
            "",
            "## Sleep Target Summary",
            "",
            f"- Sleep target rows: `{sleep_summary['rows']:,}`",
            f"- Participants: `{sleep_summary['participants']:,}`",
            f"- Date range: `{sleep_summary['date_min']}` to `{sleep_summary['date_max']}`",
            f"- Good sleep days: `{sleep_summary['good_sleep_days']:,}`",
            f"- Bad sleep days: `{sleep_summary['bad_sleep_days']:,}`",
            f"- Good sleep rate: `{sleep_summary['good_sleep_rate']:.2%}`",
            "",
            "## Selected Feature Summary",
            "",
            "| feature | count | mean | std | min | p25 | median | p75 | max |",
            "| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |",
        ]
    )

    for _, row in feature_summary.iterrows():
        lines.append(
            f"| `{row['feature']}` | {int(row['count']):,} | {row['mean']:.3f} | "
            f"{row['std']:.3f} | {row['min']:.3f} | {row['p25']:.3f} | "
            f"{row['median']:.3f} | {row['p75']:.3f} | {row['max']:.3f} |"
        )

    lines.extend(["", "## Figures", ""])
    for path in figure_paths:
        lines.append(f"- `{path}`")

    lines.extend(
        [
            "",
            "## Notes",
            "",
            "- `surveys_participant_summary.csv` is participant-level, so duplicate checks use only `participant_object_id`.",
            "- Missing rates here describe each standalone aggregate table before cross-source merging.",
            "- High missingness in sleep-stage columns can be expected because Fitbit has both stages and classic sleep formats.",
            "",
            "## Next Step",
            "",
            "```text",
            "merge daily fitbit + daily sema + participant surveys -> final dataset EDA",
            "```",
            "",
        ]
    )

    REPORT_PATH.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    FIGURE_DIR.mkdir(parents=True, exist_ok=True)

    file_names = sorted(path.name for path in DAILY_DIR.glob("*.csv"))
    tables = {file_name: read_daily_table(file_name) for file_name in file_names}

    validations = []
    for file_name in file_names:
        key_columns = ["participant_object_id"]
        if file_name != "surveys_participant_summary.csv":
            key_columns = DAILY_KEY
        validations.append(table_validation(file_name, key_columns))

    sleep = tables["sleep_daily_target.csv"]
    sleep_summary = {
        "rows": len(sleep),
        "participants": sleep["participant_object_id"].nunique(),
        "date_min": sleep["calendar_date"].min().date().isoformat(),
        "date_max": sleep["calendar_date"].max().date().isoformat(),
        "good_sleep_days": int((sleep["good_sleep_label"] == 1).sum()),
        "bad_sleep_days": int((sleep["good_sleep_label"] == 0).sum()),
        "good_sleep_rate": float((sleep["good_sleep_label"] == 1).mean()),
    }

    feature_sources = [
        ("sleep_daily_target.csv", "minutesAsleep"),
        ("sleep_daily_target.csv", "efficiency"),
        ("fitbit_stress_daily.csv", "stress_score_mean"),
        ("fitbit_daily_hrv_summary_daily.csv", "hrv_summary_rmssd_mean"),
        ("fitbit_resting_heart_rate_daily.csv", "resting_hr_resting_heart_rate_mean"),
        ("fitbit_steps_daily.csv", "steps_sum"),
        ("fitbit_calories_daily.csv", "calories_sum"),
        ("fitbit_wrist_temperature_daily.csv", "wrist_temperature_mean"),
    ]

    feature_rows = []
    for file_name, column in feature_sources:
        values = pd.to_numeric(tables[file_name][column], errors="coerce").dropna()
        desc = values.describe(percentiles=[0.25, 0.5, 0.75])
        feature_rows.append(
            {
                "feature": column,
                "count": desc["count"],
                "mean": desc["mean"],
                "std": desc["std"],
                "min": desc["min"],
                "p25": desc["25%"],
                "median": desc["50%"],
                "p75": desc["75%"],
                "max": desc["max"],
            }
        )
    feature_summary = pd.DataFrame(feature_rows)

    figure_paths = [
        save_sleep_target_plot(sleep),
        save_sleep_metric_histograms(sleep),
        save_daily_coverage_plot(tables),
        save_key_feature_boxplots(tables),
        save_sleep_time_series(sleep),
    ]

    write_report(validations, sleep_summary, feature_summary, figure_paths)

    print("Validation complete.")
    print(f"Wrote report: {REPORT_PATH}")
    print("Figures:")
    for path in figure_paths:
        print(f"- {path}")


if __name__ == "__main__":
    main()
