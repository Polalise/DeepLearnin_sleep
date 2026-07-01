from __future__ import annotations

from pathlib import Path
import json
import os

import numpy as np
import pandas as pd


PROJECT_ROOT = Path(os.environ.get("PROJECT_ROOT", Path(__file__).resolve().parents[1]))

DOCS_DIR = PROJECT_ROOT / "docs"

SAMSUNG_DIR_CANDIDATES = [
    PROJECT_ROOT / "docs" / "samsung",
    PROJECT_ROOT / "docs",
    PROJECT_ROOT / "data" / "raw" / "samsung_health",
]

OUTPUT_DIR = PROJECT_ROOT / "data" / "processed" / "samsung_health" / "core_table_profile"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

REPORT_PATH = PROJECT_ROOT / "reports" / "samsung_health_core_table_profile.md"

FILE_CATALOG_PATH = DOCS_DIR / "samsunghealth_file_catalog.csv"
COLUMN_DICTIONARY_PATH = DOCS_DIR / "samsunghealth_column_dictionary.csv"

CORE_DATASETS = {
    "sleep": "com.samsung.shealth.sleep",
    "sleep_combined": "com.samsung.shealth.sleep_combined",
    "sleep_stage": "com.samsung.health.sleep_stage",
    "heart_rate": "com.samsung.shealth.tracker.heart_rate",
    "pedometer_day_summary": "com.samsung.shealth.tracker.pedometer_day_summary",
    "pedometer_step_count": "com.samsung.shealth.tracker.pedometer_step_count",
    "activity_day_summary": "com.samsung.shealth.activity.day_summary",
    "step_daily_trend": "com.samsung.shealth.step_daily_trend",
    "calories_burned_details": "com.samsung.shealth.calories_burned.details",
}

DATE_CANDIDATES = [
    "start_time",
    "end_time",
    "day_time",
    "create_time",
    "update_time",
    "original_bed_time",
    "original_wake_up_time",
]

VALUE_CANDIDATE_TOKENS = [
    "sleep",
    "score",
    "duration",
    "efficiency",
    "heart",
    "rate",
    "step",
    "calorie",
    "active",
    "distance",
    "time",
    "count",
    "stage",
]


def read_samsung_csv(path: Path) -> pd.DataFrame:
    # Samsung Health CSV export uses row 1 as dataset metadata and row 2 as header.
    return pd.read_csv(path, skiprows=1, encoding="utf-8-sig", low_memory=False)


def find_dataset_file(dataset_name: str) -> Path | None:
    for root in SAMSUNG_DIR_CANDIDATES:
        if not root.exists():
            continue

        matches = sorted(root.glob(f"{dataset_name}.*.csv"))
        if matches:
            return matches[0]

        recursive_matches = sorted(root.rglob(f"{dataset_name}.*.csv"))
        if recursive_matches:
            return recursive_matches[0]

    return None


def normalize_datetime(series: pd.Series) -> pd.Series:
    return pd.to_datetime(series, errors="coerce")


def summarize_missing(df: pd.DataFrame, dataset_key: str, dataset_name: str) -> pd.DataFrame:
    rows = []

    for column in df.columns:
        non_empty = df[column].notna().sum()
        missing = df[column].isna().sum()

        rows.append(
            {
                "dataset_key": dataset_key,
                "dataset_name": dataset_name,
                "column": column,
                "dtype": str(df[column].dtype),
                "non_empty_count": int(non_empty),
                "missing_count": int(missing),
                "non_empty_ratio": float(non_empty / len(df)) if len(df) else np.nan,
                "unique_count": int(df[column].nunique(dropna=True)),
            }
        )

    return pd.DataFrame(rows)


def summarize_dates(df: pd.DataFrame, dataset_key: str, dataset_name: str) -> pd.DataFrame:
    rows = []

    for column in DATE_CANDIDATES:
        if column not in df.columns:
            continue

        parsed = normalize_datetime(df[column])
        non_null = parsed.dropna()

        rows.append(
            {
                "dataset_key": dataset_key,
                "dataset_name": dataset_name,
                "column": column,
                "parsed_count": int(non_null.shape[0]),
                "min": str(non_null.min()) if len(non_null) else "",
                "max": str(non_null.max()) if len(non_null) else "",
            }
        )

    return pd.DataFrame(rows)


def summarize_numeric(df: pd.DataFrame, dataset_key: str, dataset_name: str) -> pd.DataFrame:
    rows = []

    candidate_columns = []
    for column in df.columns:
        column_l = column.lower()
        if any(token in column_l for token in VALUE_CANDIDATE_TOKENS):
            candidate_columns.append(column)

    for column in candidate_columns:
        numeric = pd.to_numeric(df[column], errors="coerce")
        non_null = numeric.dropna()

        if len(non_null) == 0:
            continue

        rows.append(
            {
                "dataset_key": dataset_key,
                "dataset_name": dataset_name,
                "column": column,
                "count": int(len(non_null)),
                "mean": float(non_null.mean()),
                "std": float(non_null.std(ddof=0)),
                "min": float(non_null.min()),
                "p25": float(non_null.quantile(0.25)),
                "median": float(non_null.median()),
                "p75": float(non_null.quantile(0.75)),
                "max": float(non_null.max()),
            }
        )

    return pd.DataFrame(rows)


def make_core_table_summary_row(dataset_key: str, dataset_name: str, path: Path | None, df: pd.DataFrame | None) -> dict:
    if path is None:
        return {
            "dataset_key": dataset_key,
            "dataset_name": dataset_name,
            "file_path": "",
            "exists": False,
            "rows": 0,
            "columns": 0,
            "column_list": "",
        }

    if df is None:
        return {
            "dataset_key": dataset_key,
            "dataset_name": dataset_name,
            "file_path": str(path.relative_to(PROJECT_ROOT)),
            "exists": True,
            "rows": np.nan,
            "columns": np.nan,
            "column_list": "",
        }

    return {
        "dataset_key": dataset_key,
        "dataset_name": dataset_name,
        "file_path": str(path.relative_to(PROJECT_ROOT)),
        "exists": True,
        "rows": int(len(df)),
        "columns": int(len(df.columns)),
        "column_list": "; ".join(df.columns.astype(str).tolist()),
    }


def build_markdown_report(table_summary, date_summary, numeric_summary, missing_summary) -> str:
    lines = []

    lines.append("# Samsung Health Core Table Profile")
    lines.append("")
    lines.append("## Purpose")
    lines.append("")
    lines.append("Profile the Samsung Health core tables needed for strict pre-sleep inference mapping.")
    lines.append("")
    lines.append("This profiling step does not run model inference, validation evaluation, or training.")
    lines.append("")

    lines.append("## Core Table Summary")
    lines.append("")
    lines.append("| dataset_key | exists | rows | columns | file_path |")
    lines.append("|---|---:|---:|---:|---|")

    for _, row in table_summary.iterrows():
        lines.append(
            f"| {row['dataset_key']} | {row['exists']} | {row['rows']} | {row['columns']} | {row['file_path']} |"
        )

    lines.append("")
    lines.append("## Date Ranges")
    lines.append("")

    if len(date_summary):
        lines.append("| dataset_key | column | parsed_count | min | max |")
        lines.append("|---|---|---:|---|---|")
        for _, row in date_summary.iterrows():
            lines.append(
                f"| {row['dataset_key']} | {row['column']} | {row['parsed_count']} | {row['min']} | {row['max']} |"
            )
    else:
        lines.append("No date columns parsed.")

    lines.append("")
    lines.append("## Key Numeric Summaries")
    lines.append("")

    key_columns = [
        "sleep_score",
        "sleep_duration",
        "efficiency",
        "heart_rate",
        "step_count",
        "calorie",
        "active_time",
        "duration",
    ]

    numeric_view = numeric_summary[
        numeric_summary["column"].str.lower().isin(key_columns)
    ].copy() if len(numeric_summary) else pd.DataFrame()

    if len(numeric_view):
        lines.append("| dataset_key | column | count | mean | min | median | max |")
        lines.append("|---|---|---:|---:|---:|---:|---:|")
        for _, row in numeric_view.iterrows():
            lines.append(
                f"| {row['dataset_key']} | {row['column']} | {row['count']} | "
                f"{row['mean']:.4f} | {row['min']:.4f} | {row['median']:.4f} | {row['max']:.4f} |"
            )
    else:
        lines.append("No key numeric summaries matched the selected column list.")

    lines.append("")
    lines.append("## Mapping Readiness")
    lines.append("")
    lines.append("- Sleep episodes: check `sleep` start/end and sleep_score coverage.")
    lines.append("- Heart rate: check `heart_rate` start/end and heart_rate coverage.")
    lines.append("- Steps/calories: check step/activity day summary and step count coverage.")
    lines.append("- Next adapter should create Samsung sleep episodes first, then raw Stage 1 features.")
    lines.append("")
    lines.append("## Output Files")
    lines.append("")
    lines.append("```text")
    lines.append("data/processed/samsung_health/core_table_profile/samsung_health_core_table_summary.csv")
    lines.append("data/processed/samsung_health/core_table_profile/samsung_health_core_date_summary.csv")
    lines.append("data/processed/samsung_health/core_table_profile/samsung_health_core_numeric_summary.csv")
    lines.append("data/processed/samsung_health/core_table_profile/samsung_health_core_missing_summary.csv")
    lines.append("```")
    lines.append("")

    return "\n".join(lines)


def main() -> None:
    table_rows = []
    missing_summaries = []
    date_summaries = []
    numeric_summaries = []

    for dataset_key, dataset_name in CORE_DATASETS.items():
        path = find_dataset_file(dataset_name)

        if path is None:
            table_rows.append(make_core_table_summary_row(dataset_key, dataset_name, path, None))
            continue

        try:
            df = read_samsung_csv(path)
        except Exception as exc:
            table_rows.append(
                {
                    "dataset_key": dataset_key,
                    "dataset_name": dataset_name,
                    "file_path": str(path.relative_to(PROJECT_ROOT)),
                    "exists": True,
                    "rows": np.nan,
                    "columns": np.nan,
                    "column_list": "",
                    "read_error": repr(exc),
                }
            )
            continue

        table_rows.append(make_core_table_summary_row(dataset_key, dataset_name, path, df))
        missing_summaries.append(summarize_missing(df, dataset_key, dataset_name))
        date_summaries.append(summarize_dates(df, dataset_key, dataset_name))
        numeric_summaries.append(summarize_numeric(df, dataset_key, dataset_name))

    table_summary = pd.DataFrame(table_rows)

    missing_summary = (
        pd.concat(missing_summaries, ignore_index=True)
        if missing_summaries
        else pd.DataFrame()
    )
    date_summary = (
        pd.concat(date_summaries, ignore_index=True)
        if date_summaries
        else pd.DataFrame()
    )
    numeric_summary = (
        pd.concat(numeric_summaries, ignore_index=True)
        if numeric_summaries
        else pd.DataFrame()
    )

    table_summary.to_csv(
        OUTPUT_DIR / "samsung_health_core_table_summary.csv",
        index=False,
        encoding="utf-8-sig",
    )
    missing_summary.to_csv(
        OUTPUT_DIR / "samsung_health_core_missing_summary.csv",
        index=False,
        encoding="utf-8-sig",
    )
    date_summary.to_csv(
        OUTPUT_DIR / "samsung_health_core_date_summary.csv",
        index=False,
        encoding="utf-8-sig",
    )
    numeric_summary.to_csv(
        OUTPUT_DIR / "samsung_health_core_numeric_summary.csv",
        index=False,
        encoding="utf-8-sig",
    )

    report = build_markdown_report(
        table_summary=table_summary,
        date_summary=date_summary,
        numeric_summary=numeric_summary,
        missing_summary=missing_summary,
    )
    REPORT_PATH.write_text(report, encoding="utf-8")

    print("table summary:", OUTPUT_DIR / "samsung_health_core_table_summary.csv")
    print("date summary:", OUTPUT_DIR / "samsung_health_core_date_summary.csv")
    print("numeric summary:", OUTPUT_DIR / "samsung_health_core_numeric_summary.csv")
    print("missing summary:", OUTPUT_DIR / "samsung_health_core_missing_summary.csv")
    print("report:", REPORT_PATH)

    print()
    print(table_summary[["dataset_key", "exists", "rows", "columns", "file_path"]])


if __name__ == "__main__":
    main()
