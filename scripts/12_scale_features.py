from __future__ import annotations

from datetime import datetime
from pathlib import Path

import joblib
import pandas as pd
from sklearn.preprocessing import StandardScaler


# This script performs the scaling step after categorical encoding.
#
# Scaling unit:
# - Scale only model feature columns.
# - Preserve participant_object_id and calendar_date for split/diagnostics.
# - Preserve good_sleep_label as the prediction target.
#
# Boundary:
# - This script does not run PCA.
# - This script does not train models.
# - It uses all rows to fit the scaler because no train/test split has been
#   created yet. For final modeling, the scaler should be fit inside a training
#   pipeline after participant-aware split to avoid train/test leakage.
PROJECT_ROOT = Path(__file__).resolve().parents[1]
INPUT_PATH = PROJECT_ROOT / "data" / "processed" / "modeling_dataset_encoded.csv"
FEATURE_COLUMNS_PATH = PROJECT_ROOT / "data" / "processed" / "encoded_feature_columns.csv"
OUTPUT_PATH = PROJECT_ROOT / "data" / "processed" / "modeling_dataset_scaled.csv"
SCALER_PATH = PROJECT_ROOT / "data" / "processed" / "standard_scaler.joblib"
SCALED_FEATURE_COLUMNS_PATH = PROJECT_ROOT / "data" / "processed" / "scaled_feature_columns.csv"
SCALING_DROPPED_FEATURES_PATH = PROJECT_ROOT / "data" / "processed" / "scaling_dropped_features.csv"
REPORT_PATH = PROJECT_ROOT / "reports" / "scaling_summary.md"

KEY_COLUMNS = ["participant_object_id", "calendar_date"]
TARGET_COLUMN = "good_sleep_label"


def validate_feature_columns(df: pd.DataFrame, feature_columns: list[str]) -> None:
    """Ensure all feature columns exist, are numeric, and contain no missing values."""

    missing = [column for column in feature_columns if column not in df.columns]
    if missing:
        raise ValueError(f"Feature columns missing from input: {missing[:10]}")

    non_numeric = [
        column for column in feature_columns if not pd.api.types.is_numeric_dtype(df[column])
    ]
    if non_numeric:
        raise ValueError(f"Non-numeric feature columns cannot be scaled: {non_numeric[:10]}")

    missing_cells = int(df[feature_columns].isna().sum().sum())
    if missing_cells:
        raise ValueError(f"Feature matrix contains {missing_cells} missing cells.")


def drop_zero_variance_features(
    df: pd.DataFrame, feature_columns: list[str]
) -> tuple[list[str], pd.DataFrame]:
    """Remove feature columns with no variance before scaling/PCA."""

    std = df[feature_columns].std(ddof=0)
    dropped = std[std == 0].index.tolist()
    kept = [column for column in feature_columns if column not in set(dropped)]
    dropped_metadata = pd.DataFrame(
        {
            "feature": dropped,
            "reason": "zero_variance",
        }
    )
    return kept, dropped_metadata


def scale_features(df: pd.DataFrame, feature_columns: list[str]) -> tuple[pd.DataFrame, StandardScaler]:
    """Fit StandardScaler and return a scaled feature table with preserved keys/target."""

    scaler = StandardScaler()
    scaled_values = scaler.fit_transform(df[feature_columns])

    scaled_features = pd.DataFrame(
        scaled_values,
        columns=feature_columns,
        index=df.index,
    )
    output = pd.concat([df[KEY_COLUMNS + [TARGET_COLUMN]].copy(), scaled_features], axis=1)
    return output, scaler


def feature_scale_summary(scaled: pd.DataFrame, feature_columns: list[str]) -> pd.DataFrame:
    """Summarize scaled feature means and standard deviations."""

    summary = pd.DataFrame(
        {
            "feature": feature_columns,
            "scaled_mean": scaled[feature_columns].mean().to_numpy(),
            "scaled_std": scaled[feature_columns].std(ddof=0).to_numpy(),
            "scaled_min": scaled[feature_columns].min().to_numpy(),
            "scaled_max": scaled[feature_columns].max().to_numpy(),
        }
    )
    return summary


def write_report(
    original: pd.DataFrame,
    scaled: pd.DataFrame,
    feature_columns: list[str],
    scale_summary: pd.DataFrame,
    dropped_features: pd.DataFrame,
) -> None:
    """Write a report describing scaling outputs and validation."""

    max_abs_mean = float(scale_summary["scaled_mean"].abs().max())
    max_std_deviation = float((scale_summary["scaled_std"] - 1).abs().max())
    duplicate_rows = int(scaled.duplicated(KEY_COLUMNS).sum())
    missing_cells = int(scaled.isna().sum().sum())

    largest_ranges = scale_summary.assign(
        scaled_abs_max=scale_summary[["scaled_min", "scaled_max"]].abs().max(axis=1)
    ).sort_values("scaled_abs_max", ascending=False)

    lines = [
        "# Scaling Summary",
        "",
        f"- Generated at: `{datetime.now().isoformat(timespec='seconds')}`",
        f"- Input file: `{INPUT_PATH}`",
        f"- Output file: `{OUTPUT_PATH}`",
        f"- Scaler file: `{SCALER_PATH}`",
        "",
        "## Scope",
        "",
        "- This step applies `StandardScaler` to numeric model feature columns.",
        "- It preserves `participant_object_id`, `calendar_date`, and `good_sleep_label`.",
        "- It does not run PCA or train models.",
        "",
        "## Important Leakage Note",
        "",
        "- This scaler is fit on the full current dataset for preprocessing exploration.",
        "- For final model evaluation, scaling should be fit only on training folds inside a participant-aware pipeline.",
        "",
        "## Output Shape",
        "",
        f"- Input rows: `{len(original):,}`",
        f"- Input columns: `{len(original.columns):,}`",
        f"- Output rows: `{len(scaled):,}`",
        f"- Output columns: `{len(scaled.columns):,}`",
        f"- Scaled feature columns: `{len(feature_columns):,}`",
        f"- Dropped zero-variance features: `{len(dropped_features):,}`",
        f"- Output missing cells: `{missing_cells:,}`",
        f"- Duplicate participant-date rows: `{duplicate_rows:,}`",
        "",
        "## Scaling Validation",
        "",
        f"- Max absolute scaled feature mean: `{max_abs_mean:.10f}`",
        f"- Max absolute deviation of scaled std from 1: `{max_std_deviation:.10f}`",
        "",
        "## Largest Absolute Scaled Ranges",
        "",
        "| feature | mean | std | min | max |",
        "| --- | ---: | ---: | ---: | ---: |",
    ]

    for _, row in largest_ranges.head(25).iterrows():
        lines.append(
            f"| `{row['feature']}` | {row['scaled_mean']:.4f} | {row['scaled_std']:.4f} | "
            f"{row['scaled_min']:.4f} | {row['scaled_max']:.4f} |"
        )

    lines.extend(
        [
            "",
            "## Dropped Zero-Variance Features",
            "",
            "| feature | reason |",
            "| --- | --- |",
        ]
    )
    if dropped_features.empty:
        lines.append("| None | - |")
    else:
        for _, row in dropped_features.iterrows():
            lines.append(f"| `{row['feature']}` | `{row['reason']}` |")

    lines.extend(
        [
            "",
            "## Next Step",
            "",
            "```text",
            "PCA",
            "```",
            "",
        ]
    )

    REPORT_PATH.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    df = pd.read_csv(INPUT_PATH)
    feature_metadata = pd.read_csv(FEATURE_COLUMNS_PATH)
    feature_columns = feature_metadata["feature"].tolist()

    df["participant_object_id"] = df["participant_object_id"].astype(str)
    df["calendar_date"] = pd.to_datetime(df["calendar_date"], errors="coerce").dt.date.astype(str)

    validate_feature_columns(df, feature_columns)
    feature_columns, dropped_features = drop_zero_variance_features(df, feature_columns)
    scaled, scaler = scale_features(df, feature_columns)
    scale_summary = feature_scale_summary(scaled, feature_columns)

    if len(scaled) != len(df):
        raise RuntimeError("Scaling changed row count.")
    if scaled[KEY_COLUMNS].duplicated().sum() != 0:
        raise RuntimeError("Scaled output has duplicate participant-date rows.")
    if scaled.isna().sum().sum() != 0:
        raise RuntimeError("Scaled output contains missing values.")

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    scaled.to_csv(OUTPUT_PATH, index=False, encoding="utf-8-sig")
    scale_summary.to_csv(SCALED_FEATURE_COLUMNS_PATH, index=False, encoding="utf-8-sig")
    dropped_features.to_csv(SCALING_DROPPED_FEATURES_PATH, index=False, encoding="utf-8-sig")
    joblib.dump(scaler, SCALER_PATH)
    write_report(df, scaled, feature_columns, scale_summary, dropped_features)

    print(f"Input shape: {df.shape}")
    print(f"Output shape: {scaled.shape}")
    print(f"Scaled features: {len(feature_columns)}")
    print(f"Dropped zero-variance features: {len(dropped_features)}")
    print(f"Output missing cells: {int(scaled.isna().sum().sum())}")
    print(f"Wrote dataset: {OUTPUT_PATH}")
    print(f"Wrote scaler: {SCALER_PATH}")
    print(f"Wrote report: {REPORT_PATH}")


if __name__ == "__main__":
    main()
