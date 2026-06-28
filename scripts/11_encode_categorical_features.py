from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Any

import pandas as pd


# This script performs the categorical-encoding / feature-table finalization step.
#
# Current data reality:
# - After missing-value handling, the only object columns are:
#   participant_object_id and calendar_date.
# - These are keys/grouping variables, not model predictors.
# - Encoding participant ID would leak identity-specific patterns.
# - Encoding exact calendar dates would create brittle date indicators and is not
#   needed before scaling/PCA.
#
# Therefore, this step preserves keys separately and confirms that all model
# feature columns are numeric. If future categorical predictor columns are added,
# this script will one-hot encode them.
PROJECT_ROOT = Path(__file__).resolve().parents[1]
INPUT_PATH = PROJECT_ROOT / "data" / "processed" / "modeling_dataset_missing_handled.csv"
OUTPUT_PATH = PROJECT_ROOT / "data" / "processed" / "modeling_dataset_encoded.csv"
FEATURE_COLUMNS_PATH = PROJECT_ROOT / "data" / "processed" / "encoded_feature_columns.csv"
REPORT_PATH = PROJECT_ROOT / "reports" / "categorical_encoding_summary.md"

KEY_COLUMNS = ["participant_object_id", "calendar_date"]
TARGET_COLUMN = "good_sleep_label"


def split_columns(df: pd.DataFrame) -> tuple[list[str], list[str]]:
    """Return numeric feature columns and categorical predictor columns."""

    protected = set(KEY_COLUMNS + [TARGET_COLUMN])
    candidate_columns = [column for column in df.columns if column not in protected]
    categorical_columns = [
        column
        for column in candidate_columns
        if not pd.api.types.is_numeric_dtype(df[column])
    ]
    numeric_columns = [
        column
        for column in candidate_columns
        if pd.api.types.is_numeric_dtype(df[column])
    ]
    return numeric_columns, categorical_columns


def encode_dataset(df: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame, list[str], list[str]]:
    """Encode categorical predictors if present and return model-ready table."""

    numeric_columns, categorical_columns = split_columns(df)
    output = df[KEY_COLUMNS + [TARGET_COLUMN]].copy()

    feature_blocks = []
    if numeric_columns:
        feature_blocks.append(df[numeric_columns].copy())

    encoded_columns: list[str] = []
    if categorical_columns:
        encoded = pd.get_dummies(
            df[categorical_columns],
            columns=categorical_columns,
            dummy_na=False,
            drop_first=False,
            dtype=int,
        )
        encoded_columns = encoded.columns.tolist()
        feature_blocks.append(encoded)

    if feature_blocks:
        features = pd.concat(feature_blocks, axis=1)
        output = pd.concat([output, features], axis=1)

    feature_columns = [
        column for column in output.columns if column not in set(KEY_COLUMNS + [TARGET_COLUMN])
    ]
    feature_metadata = pd.DataFrame(
        {
            "feature": feature_columns,
            "source_type": [
                "one_hot_categorical" if column in encoded_columns else "numeric"
                for column in feature_columns
            ],
        }
    )

    return output, feature_metadata, numeric_columns, categorical_columns


def write_report(
    original: pd.DataFrame,
    encoded: pd.DataFrame,
    feature_metadata: pd.DataFrame,
    numeric_columns: list[str],
    categorical_columns: list[str],
) -> None:
    """Write a report describing categorical encoding decisions."""

    encoded_feature_count = int((feature_metadata["source_type"] == "one_hot_categorical").sum())
    numeric_feature_count = int((feature_metadata["source_type"] == "numeric").sum())

    lines = [
        "# Categorical Encoding Summary",
        "",
        f"- Generated at: `{datetime.now().isoformat(timespec='seconds')}`",
        f"- Input file: `{INPUT_PATH}`",
        f"- Output file: `{OUTPUT_PATH}`",
        f"- Feature columns file: `{FEATURE_COLUMNS_PATH}`",
        "",
        "## Scope",
        "",
        "- This step finalizes the feature table after missing-value handling.",
        "- It one-hot encodes categorical predictor columns when they exist.",
        "- It preserves `participant_object_id`, `calendar_date`, and `good_sleep_label`.",
        "- It does not scale features, run PCA, or train models.",
        "",
        "## Encoding Decision",
        "",
        f"- Object columns in input: `{', '.join(original.select_dtypes(include='object').columns)}`",
        "- `participant_object_id` and `calendar_date` are treated as keys, not predictors.",
        "- No categorical predictor columns were found in the current missing-handled dataset.",
        "- Therefore no one-hot columns were added in this run.",
        "",
        "## Output Shape",
        "",
        f"- Input rows: `{len(original):,}`",
        f"- Input columns: `{len(original.columns):,}`",
        f"- Output rows: `{len(encoded):,}`",
        f"- Output columns: `{len(encoded.columns):,}`",
        f"- Numeric feature columns: `{numeric_feature_count:,}`",
        f"- One-hot categorical feature columns: `{encoded_feature_count:,}`",
        f"- Output missing cells: `{int(encoded.isna().sum().sum()):,}`",
        f"- Duplicate participant-date rows: `{int(encoded.duplicated(KEY_COLUMNS).sum()):,}`",
        "",
        "## Categorical Predictor Columns",
        "",
        "```text",
        "\n".join(categorical_columns) if categorical_columns else "None",
        "```",
        "",
        "## Notes",
        "",
        "- Participant ID is preserved for participant-aware split, not used as a one-hot model feature.",
        "- Calendar date is preserved for temporal diagnostics and possible time-based split, not one-hot encoded.",
        "- The output is ready for scaling and PCA.",
        "",
        "## Next Step",
        "",
        "```text",
        "scaling -> PCA",
        "```",
        "",
    ]

    REPORT_PATH.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    df = pd.read_csv(INPUT_PATH)
    df["participant_object_id"] = df["participant_object_id"].astype(str)
    df["calendar_date"] = pd.to_datetime(df["calendar_date"], errors="coerce").dt.date.astype(str)

    encoded, feature_metadata, numeric_columns, categorical_columns = encode_dataset(df)

    if len(encoded) != len(df):
        raise RuntimeError("Encoding changed row count.")
    if encoded[KEY_COLUMNS].duplicated().sum() != 0:
        raise RuntimeError("Encoded output has duplicate participant-date rows.")
    if encoded.isna().sum().sum() != 0:
        raise RuntimeError("Encoded output contains missing values.")

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    encoded.to_csv(OUTPUT_PATH, index=False, encoding="utf-8-sig")
    feature_metadata.to_csv(FEATURE_COLUMNS_PATH, index=False, encoding="utf-8-sig")
    write_report(df, encoded, feature_metadata, numeric_columns, categorical_columns)

    print(f"Input shape: {df.shape}")
    print(f"Output shape: {encoded.shape}")
    print(f"Categorical predictor columns: {len(categorical_columns)}")
    print(f"Feature columns: {len(feature_metadata)}")
    print(f"Wrote dataset: {OUTPUT_PATH}")
    print(f"Wrote feature columns: {FEATURE_COLUMNS_PATH}")
    print(f"Wrote report: {REPORT_PATH}")


if __name__ == "__main__":
    main()
