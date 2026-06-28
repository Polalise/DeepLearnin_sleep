from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Any

import pandas as pd


# This script performs the data merge step after date-level aggregation.
#
# Merge unit:
#   participant_object_id + calendar_date
#
# Base table:
#   sleep_daily_target.csv
#
# Reason:
# - The modeling task predicts sleep health, so each output row must have a
#   valid sleep target.
# - A left join keeps all sleep target rows and attaches available Fitbit,
#   SEMA, and survey features.
#
# Boundary:
# - This script does not impute missing values.
# - This script does not encode categorical variables, scale features, or run PCA.
# - Those steps should happen after final dataset EDA.
PROJECT_ROOT = Path(__file__).resolve().parents[1]
DAILY_DIR = PROJECT_ROOT / "data" / "processed" / "daily_aggregates"
OUTPUT_PATH = PROJECT_ROOT / "data" / "processed" / "modeling_dataset_daily.csv"
REPORT_PATH = PROJECT_ROOT / "reports" / "merge_summary.md"

DAILY_KEY = ["participant_object_id", "calendar_date"]


DAILY_FEATURE_TABLES = [
    "fitbit_stress_daily.csv",
    "fitbit_daily_hrv_summary_daily.csv",
    "fitbit_hrv_details_daily.csv",
    "fitbit_resting_heart_rate_daily.csv",
    "fitbit_activity_minutes_daily.csv",
    "fitbit_daily_spo2_daily.csv",
    "fitbit_respiratory_rate_summary_daily.csv",
    "fitbit_steps_daily.csv",
    "fitbit_calories_daily.csv",
    "fitbit_wrist_temperature_daily.csv",
    "sema_daily_context_mood.csv",
]

PARTICIPANT_FEATURE_TABLES = [
    "surveys_participant_summary.csv",
]


def read_table(file_name: str) -> pd.DataFrame:
    """Read a processed aggregate table and normalize key column types."""

    df = pd.read_csv(DAILY_DIR / file_name)
    df["participant_object_id"] = df["participant_object_id"].astype(str)
    if "calendar_date" in df.columns:
        df["calendar_date"] = pd.to_datetime(df["calendar_date"], errors="coerce").dt.date.astype(str)
    return df


def validate_unique_key(df: pd.DataFrame, table_name: str, key: list[str]) -> None:
    """Fail early if a table cannot be safely left-joined on its intended key."""

    missing_key_columns = [column for column in key if column not in df.columns]
    if missing_key_columns:
        raise ValueError(f"{table_name} is missing key columns: {missing_key_columns}")

    duplicate_count = int(df.duplicated(key).sum())
    if duplicate_count:
        raise ValueError(f"{table_name} has {duplicate_count} duplicate rows for key {key}")


def merge_daily_tables(base: pd.DataFrame) -> tuple[pd.DataFrame, list[dict[str, Any]]]:
    """Left-join daily feature tables onto the sleep target base."""

    merged = base.copy()
    summaries: list[dict[str, Any]] = []

    for file_name in DAILY_FEATURE_TABLES:
        feature = read_table(file_name)
        validate_unique_key(feature, file_name, DAILY_KEY)

        before_columns = set(merged.columns)
        before_rows = len(merged)
        merged = merged.merge(feature, on=DAILY_KEY, how="left", validate="one_to_one")

        added_columns = [column for column in merged.columns if column not in before_columns]
        if len(merged) != before_rows:
            raise RuntimeError(f"Row count changed while merging {file_name}.")

        non_null_rows = int(merged[added_columns].notna().any(axis=1).sum()) if added_columns else 0
        summaries.append(
            {
                "table": file_name,
                "join_key": "participant_object_id + calendar_date",
                "source_rows": len(feature),
                "added_columns": len(added_columns),
                "matched_base_rows": non_null_rows,
                "match_rate": non_null_rows / len(merged) if len(merged) else 0,
            }
        )

    return merged, summaries


def merge_participant_tables(base: pd.DataFrame) -> tuple[pd.DataFrame, list[dict[str, Any]]]:
    """Left-join participant-level feature tables onto the modeling dataset."""

    merged = base.copy()
    summaries: list[dict[str, Any]] = []

    for file_name in PARTICIPANT_FEATURE_TABLES:
        feature = read_table(file_name)
        key = ["participant_object_id"]
        validate_unique_key(feature, file_name, key)

        before_columns = set(merged.columns)
        before_rows = len(merged)
        merged = merged.merge(feature, on=key, how="left", validate="many_to_one")

        added_columns = [column for column in merged.columns if column not in before_columns]
        if len(merged) != before_rows:
            raise RuntimeError(f"Row count changed while merging {file_name}.")

        non_null_rows = int(merged[added_columns].notna().any(axis=1).sum()) if added_columns else 0
        summaries.append(
            {
                "table": file_name,
                "join_key": "participant_object_id",
                "source_rows": len(feature),
                "added_columns": len(added_columns),
                "matched_base_rows": non_null_rows,
                "match_rate": non_null_rows / len(merged) if len(merged) else 0,
            }
        )

    return merged, summaries


def missing_summary(df: pd.DataFrame, limit: int = 30) -> pd.DataFrame:
    """Return the highest-missing columns for the merged dataset."""

    summary = pd.DataFrame(
        {
            "column": df.columns,
            "missing_count": df.isna().sum().to_numpy(),
            "missing_rate": df.isna().mean().to_numpy(),
        }
    )
    summary = summary.sort_values(["missing_rate", "missing_count"], ascending=False)
    return summary.head(limit)


def write_report(
    merged: pd.DataFrame,
    merge_summaries: list[dict[str, Any]],
    base_rows: int,
    base_columns: int,
) -> None:
    """Write a merge report with coverage and basic quality checks."""

    duplicate_rows = int(merged.duplicated(DAILY_KEY).sum())
    participants = int(merged["participant_object_id"].nunique())
    date_min = merged["calendar_date"].min()
    date_max = merged["calendar_date"].max()
    target_counts = merged["good_sleep_label"].value_counts(dropna=False).sort_index()
    missing = missing_summary(merged)

    lines = [
        "# Merge Summary",
        "",
        f"- Generated at: `{datetime.now().isoformat(timespec='seconds')}`",
        f"- Base table: `sleep_daily_target.csv`",
        f"- Output file: `{OUTPUT_PATH}`",
        "",
        "## Scope",
        "",
        "- This report covers merging daily Fitbit features, daily SEMA features, and participant-level survey summaries.",
        "- The merge uses sleep target rows as the base.",
        "- No missing-value imputation, categorical encoding, scaling, or PCA was performed.",
        "",
        "## Output Shape",
        "",
        f"- Base rows: `{base_rows:,}`",
        f"- Base columns: `{base_columns:,}`",
        f"- Merged rows: `{len(merged):,}`",
        f"- Merged columns: `{len(merged.columns):,}`",
        f"- Participants: `{participants:,}`",
        f"- Date range: `{date_min}` to `{date_max}`",
        f"- Duplicate `participant_object_id + calendar_date` rows: `{duplicate_rows:,}`",
        "",
        "## Target Distribution",
        "",
        "| good_sleep_label | rows |",
        "| ---: | ---: |",
    ]

    for label, count in target_counts.items():
        lines.append(f"| `{label}` | {int(count):,} |")

    lines.extend(
        [
            "",
            "## Merge Coverage",
            "",
            "| source table | join key | source rows | added columns | matched base rows | match rate |",
            "| --- | --- | ---: | ---: | ---: | ---: |",
        ]
    )
    for item in merge_summaries:
        lines.append(
            f"| `{item['table']}` | `{item['join_key']}` | {item['source_rows']:,} | "
            f"{item['added_columns']:,} | {item['matched_base_rows']:,} | {item['match_rate']:.2%} |"
        )

    lines.extend(
        [
            "",
            "## Highest Missing Columns",
            "",
            "| column | missing count | missing rate |",
            "| --- | ---: | ---: |",
        ]
    )
    for _, row in missing.iterrows():
        lines.append(
            f"| `{row['column']}` | {int(row['missing_count']):,} | {row['missing_rate']:.2%} |"
        )

    lines.extend(
        [
            "",
            "## Notes",
            "",
            "- Missingness is expected because not every participant-day has every Fitbit, SEMA, or survey-derived feature.",
            "- Stress-related features may carry sleep/recovery leakage risk and should be handled carefully in modeling reports.",
            "- The next step should be final dataset EDA before deciding imputation and feature selection rules.",
            "",
            "## Next Step",
            "",
            "```text",
            "final dataset EDA -> missing-value handling -> categorical encoding -> scaling -> PCA",
            "```",
            "",
        ]
    )

    REPORT_PATH.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    base = read_table("sleep_daily_target.csv")
    validate_unique_key(base, "sleep_daily_target.csv", DAILY_KEY)

    base_rows = len(base)
    base_columns = len(base.columns)

    merged, daily_summaries = merge_daily_tables(base)
    merged, participant_summaries = merge_participant_tables(merged)
    merge_summaries = daily_summaries + participant_summaries

    if len(merged) != base_rows:
        raise RuntimeError("Merged dataset row count differs from sleep target base.")
    if int(merged.duplicated(DAILY_KEY).sum()) != 0:
        raise RuntimeError("Merged dataset has duplicate participant-date rows.")

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    merged.to_csv(OUTPUT_PATH, index=False, encoding="utf-8-sig")
    write_report(merged, merge_summaries, base_rows, base_columns)

    print(f"Merged rows: {len(merged)}")
    print(f"Merged columns: {len(merged.columns)}")
    print(f"Participants: {merged['participant_object_id'].nunique()}")
    print(f"Wrote dataset: {OUTPUT_PATH}")
    print(f"Wrote report: {REPORT_PATH}")


if __name__ == "__main__":
    main()
