from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Any

import pandas as pd


# This script performs the missing-value handling step after final dataset EDA.
#
# Boundary:
# - It does not perform categorical encoding beyond preserving key columns.
# - It does not scale features.
# - It does not run PCA.
# - It does not train models.
#
# Important modeling choice:
# - Same-night sleep outcome columns are excluded from feature columns because
#   they directly define or describe the prediction target.
# - Stress-related columns are kept, but the report flags leakage risk.
PROJECT_ROOT = Path(__file__).resolve().parents[1]
INPUT_PATH = PROJECT_ROOT / "data" / "processed" / "modeling_dataset_daily.csv"
OUTPUT_PATH = PROJECT_ROOT / "data" / "processed" / "modeling_dataset_missing_handled.csv"
METADATA_PATH = PROJECT_ROOT / "data" / "processed" / "missing_value_feature_metadata.csv"
REPORT_PATH = PROJECT_ROOT / "reports" / "missing_value_handling_summary.md"

KEY_COLUMNS = ["participant_object_id", "calendar_date"]
TARGET_COLUMN = "good_sleep_label"

# These columns are identifiers, timestamps, target components, or same-night
# sleep outcomes. They are useful for EDA, but should not be model input
# features for predicting good_sleep_label.
LEAKAGE_OR_NON_FEATURE_COLUMNS = {
    "mongo_doc_id",
    "logId",
    "startTime",
    "endTime",
    "minutesAsleep",
    "minutesAwake",
    "timeInBed",
    "efficiency",
    "sleep_duration_hours",
    "time_in_bed_hours",
    "awake_ratio",
    "deep_minutes",
    "light_minutes",
    "rem_minutes",
    "wake_minutes",
    "deep_ratio",
    "light_ratio",
    "rem_ratio",
    "wake_ratio",
    "asleep_minutes",
    "restless_minutes",
    "awake_minutes",
    "classic_asleep_ratio",
    "classic_restless_ratio",
    "classic_awake_ratio",
    # This subcomponent explicitly reflects sleep contribution inside Fitbit
    # stress score and is more leak-prone than the aggregate stress score.
    "stress_sleep_points_mean",
}

DROP_MISSING_THRESHOLD = 0.70


def is_zero_fill_column(column: str) -> bool:
    """Return True when missing means no observed records/responses for that day."""

    return (
        column.endswith("_record_count")
        or column.endswith("_count")
        or column.endswith("_rate")
        or column.endswith("_sum")
        or column in {"stress_ready_rate", "stress_calculation_failed_rate"}
    )


def feature_family(column: str) -> str:
    """Group feature columns into broad source families for reporting."""

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
    return "other"


def select_candidate_features(df: pd.DataFrame) -> list[str]:
    """Select numeric feature candidates after excluding keys, target, and leakage columns."""

    excluded = set(KEY_COLUMNS + [TARGET_COLUMN]) | LEAKAGE_OR_NON_FEATURE_COLUMNS
    numeric_columns = df.select_dtypes(include=["number"]).columns
    return [column for column in numeric_columns if column not in excluded]


def handle_missing_values(df: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Apply drop/impute/indicator rules and return cleaned data plus metadata."""

    features = select_candidate_features(df)
    output_columns: dict[str, Any] = {
        column: df[column].copy() for column in KEY_COLUMNS + [TARGET_COLUMN]
    }
    metadata_rows: list[dict[str, Any]] = []

    for column in features:
        values = pd.to_numeric(df[column], errors="coerce")
        missing_rate = float(values.isna().mean())
        family = feature_family(column)

        if missing_rate > DROP_MISSING_THRESHOLD:
            metadata_rows.append(
                {
                    "column": column,
                    "family": family,
                    "original_missing_rate": missing_rate,
                    "action": "drop_high_missing",
                    "fill_value": None,
                    "indicator_added": False,
                }
            )
            continue

        indicator_added = missing_rate > 0
        if indicator_added:
            output_columns[f"{column}_missing_ind"] = values.isna().astype(int)

        if missing_rate == 0:
            filled = values
            action = "keep_no_missing"
            fill_value = None
        elif is_zero_fill_column(column):
            filled = values.fillna(0)
            action = "fill_zero_add_indicator"
            fill_value = 0
        else:
            fill_value = float(values.median())
            filled = values.fillna(fill_value)
            action = "median_impute_add_indicator"

        output_columns[column] = filled
        metadata_rows.append(
            {
                "column": column,
                "family": family,
                "original_missing_rate": missing_rate,
                "action": action,
                "fill_value": fill_value,
                "indicator_added": indicator_added,
            }
        )

    output = pd.DataFrame(output_columns)
    metadata = pd.DataFrame(metadata_rows)
    return output, metadata


def write_report(original: pd.DataFrame, cleaned: pd.DataFrame, metadata: pd.DataFrame) -> None:
    """Write a report describing missing-value decisions and output shape."""

    action_counts = metadata["action"].value_counts().rename_axis("action").reset_index(name="columns")
    family_counts = (
        metadata.groupby(["family", "action"], as_index=False)
        .size()
        .rename(columns={"size": "columns"})
        .sort_values(["family", "action"])
    )
    dropped = metadata[metadata["action"] == "drop_high_missing"].sort_values(
        "original_missing_rate", ascending=False
    )
    indicators_added = int(metadata["indicator_added"].sum())

    lines = [
        "# Missing Value Handling Summary",
        "",
        f"- Generated at: `{datetime.now().isoformat(timespec='seconds')}`",
        f"- Input file: `{INPUT_PATH}`",
        f"- Output file: `{OUTPUT_PATH}`",
        f"- Metadata file: `{METADATA_PATH}`",
        "",
        "## Scope",
        "",
        "- This step handles missing values for numeric modeling features.",
        "- It excludes direct same-night sleep outcome columns from model features.",
        "- It does not perform categorical encoding, scaling, PCA, or modeling.",
        "",
        "## Strategy",
        "",
        f"- Drop feature columns with missing rate greater than `{DROP_MISSING_THRESHOLD:.0%}`.",
        "- Add missing indicators for retained columns that originally had missing values.",
        "- Fill count/rate/sum/record-count style columns with `0` when missing.",
        "- Fill other retained numeric columns with the column median.",
        "- Preserve `participant_object_id`, `calendar_date`, and `good_sleep_label`.",
        "",
        "## Output Shape",
        "",
        f"- Input rows: `{len(original):,}`",
        f"- Input columns: `{len(original.columns):,}`",
        f"- Output rows: `{len(cleaned):,}`",
        f"- Output columns: `{len(cleaned.columns):,}`",
        f"- Output missing cells: `{int(cleaned.isna().sum().sum()):,}`",
        f"- Missing indicators added: `{indicators_added:,}`",
        "",
        "## Action Counts",
        "",
        "| action | columns |",
        "| --- | ---: |",
    ]

    for _, row in action_counts.iterrows():
        lines.append(f"| `{row['action']}` | {int(row['columns']):,} |")

    lines.extend(
        [
            "",
            "## Actions By Feature Family",
            "",
            "| family | action | columns |",
            "| --- | --- | ---: |",
        ]
    )
    for _, row in family_counts.iterrows():
        lines.append(f"| `{row['family']}` | `{row['action']}` | {int(row['columns']):,} |")

    lines.extend(
        [
            "",
            "## Dropped High-Missing Columns",
            "",
            "| column | family | missing rate |",
            "| --- | --- | ---: |",
        ]
    )
    if dropped.empty:
        lines.append("| None | - | - |")
    else:
        for _, row in dropped.iterrows():
            lines.append(
                f"| `{row['column']}` | `{row['family']}` | {row['original_missing_rate']:.2%} |"
            )

    leakage_excluded = sorted(
        column for column in LEAKAGE_OR_NON_FEATURE_COLUMNS if column in original.columns
    )
    lines.extend(
        [
            "",
            "## Excluded Non-Feature Or Leakage-Prone Columns",
            "",
            "These columns are retained in earlier EDA outputs but excluded from the missing-handled modeling feature table.",
            "",
            "```text",
            "\n".join(leakage_excluded),
            "```",
            "",
            "## Notes",
            "",
            "- Stress score is retained as a candidate explanatory feature, but it may still carry sleep/recovery leakage risk.",
            "- `stress_sleep_points_mean` is excluded because it is explicitly sleep-related.",
            "- Missing indicators should help downstream models distinguish true low values from absent measurements.",
            "",
            "## Next Step",
            "",
            "```text",
            "categorical encoding / feature table finalization -> scaling -> PCA",
            "```",
            "",
        ]
    )

    REPORT_PATH.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    df = pd.read_csv(INPUT_PATH)
    df["participant_object_id"] = df["participant_object_id"].astype(str)
    df["calendar_date"] = pd.to_datetime(df["calendar_date"], errors="coerce").dt.date.astype(str)

    cleaned, metadata = handle_missing_values(df)

    if len(cleaned) != len(df):
        raise RuntimeError("Missing-value handling changed row count.")
    if cleaned[KEY_COLUMNS].duplicated().sum() != 0:
        raise RuntimeError("Output has duplicate participant-date rows.")
    if cleaned.isna().sum().sum() != 0:
        raise RuntimeError("Output still contains missing values.")

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    cleaned.to_csv(OUTPUT_PATH, index=False, encoding="utf-8-sig")
    metadata.to_csv(METADATA_PATH, index=False, encoding="utf-8-sig")
    write_report(df, cleaned, metadata)

    print(f"Input shape: {df.shape}")
    print(f"Output shape: {cleaned.shape}")
    print(f"Output missing cells: {int(cleaned.isna().sum().sum())}")
    print(f"Wrote dataset: {OUTPUT_PATH}")
    print(f"Wrote metadata: {METADATA_PATH}")
    print(f"Wrote report: {REPORT_PATH}")


if __name__ == "__main__":
    main()
