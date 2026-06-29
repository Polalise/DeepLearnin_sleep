from __future__ import annotations

from pathlib import Path
import csv
import re

import numpy as np
import pandas as pd


PROJECT_ROOT = Path(r"C:\workSpace\DeepLearnin_sleep")

SAMSUNG_DIR_CANDIDATES = [
    PROJECT_ROOT / "docs" / "samsung",
    PROJECT_ROOT / "docs" / "samsunghealth",
    PROJECT_ROOT / "docs",
    PROJECT_ROOT / "data" / "raw" / "samsung_health",
]

OUTPUT_DIR = PROJECT_ROOT / "data" / "processed" / "samsung_health" / "pre_sleep_stage1"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

SLEEP_DATASET = "com.samsung.shealth.sleep"

OUTPUT_PATH = OUTPUT_DIR / "samsung_sleep_episodes.csv"
SUMMARY_PATH = OUTPUT_DIR / "samsung_sleep_episode_summary.csv"
REPORT_PATH = PROJECT_ROOT / "reports" / "samsung_sleep_episode_table_summary.md"

PARTICIPANT_ID = "samsung_user"
GOOD_SLEEP_SCORE_THRESHOLD = 80

MIN_SLEEP_DURATION_HOURS = 2.0
MAX_SLEEP_DURATION_HOURS = 16.0


def find_dataset_file(dataset_name: str) -> Path:
    for root in SAMSUNG_DIR_CANDIDATES:
        if not root.exists():
            continue

        matches = sorted(root.glob(f"{dataset_name}.*.csv"))
        if matches:
            return matches[0]

        recursive_matches = sorted(root.rglob(f"{dataset_name}.*.csv"))
        if recursive_matches:
            return recursive_matches[0]

    raise FileNotFoundError(f"Could not find Samsung Health CSV for dataset: {dataset_name}")


def read_samsung_csv(path: Path) -> pd.DataFrame:
    """
    Samsung Health CSV export:
    - line 1: dataset/schema metadata
    - line 2: header
    - line 3+: data

    Some Samsung Health files have one more data field than header fields.
    This reader pads the header with leading extra columns so rows can be loaded
    without pandas silently shifting fields.
    """
    with open(path, "r", encoding="utf-8-sig", newline="") as f:
        reader = csv.reader(f)
        _metadata = next(reader)
        header = next(reader)

        rows = []
        max_fields = len(header)

        for row in reader:
            rows.append(row)
            if len(row) > max_fields:
                max_fields = len(row)

    if max_fields > len(header):
        extra_count = max_fields - len(header)
        header = [f"_extra_field_{i}" for i in range(extra_count)] + header

    normalized_rows = []
    for row in rows:
        if len(row) < len(header):
            row = row + [""] * (len(header) - len(row))
        elif len(row) > len(header):
            row = row[: len(header)]
        normalized_rows.append(row)

    df = pd.DataFrame(normalized_rows, columns=header)
    df = df.replace("", np.nan).infer_objects(copy=False)

    return df


def find_column(df: pd.DataFrame, candidates: list[str]) -> str | None:
    exact_map = {str(col).lower(): col for col in df.columns}

    for candidate in candidates:
        if candidate.lower() in exact_map:
            return exact_map[candidate.lower()]

    for candidate in candidates:
        candidate_l = candidate.lower()
        for col in df.columns:
            col_l = str(col).lower()
            if col_l.endswith("." + candidate_l) or col_l.endswith(candidate_l):
                return col

    return None


def parse_datetime(series: pd.Series) -> pd.Series:
    return pd.to_datetime(series, errors="coerce")


def parsed_non_missing_count(df: pd.DataFrame, col: str | None) -> int:
    if col is None or col not in df.columns:
        return 0
    return int(pd.to_datetime(df[col], errors="coerce").notna().sum())


def looks_like_uuid_value(value) -> bool:
    if pd.isna(value):
        return False
    text = str(value)
    return bool(re.match(r"^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}$", text))


def looks_like_uuid_series(series: pd.Series) -> bool:
    sample = series.dropna().astype(str).head(50)
    if len(sample) == 0:
        return False
    return float(sample.map(looks_like_uuid_value).mean()) > 0.5


def choose_sleep_columns(sleep_df: pd.DataFrame) -> tuple[str, str, str | None]:
    start_col = find_column(
        sleep_df,
        ["start_time", "com.samsung.health.sleep.start_time"],
    )
    end_col = find_column(
        sleep_df,
        ["end_time", "com.samsung.health.sleep.end_time"],
    )
    datauuid_col = find_column(
        sleep_df,
        ["datauuid", "com.samsung.health.sleep.datauuid"],
    )

    print("INITIAL START_COL:", start_col)
    print("INITIAL END_COL:", end_col)
    print("INITIAL DATAUUID_COL:", datauuid_col)

    # This Samsung sleep export has a shifted tail:
    # actual sleep start appears under pkg_name,
    # actual sleep end appears under update_time,
    # actual datauuid appears under end_time.
    fallback_start = "com.samsung.health.sleep.pkg_name"
    fallback_end = "com.samsung.health.sleep.update_time"
    fallback_uuid = "com.samsung.health.sleep.end_time"

    if parsed_non_missing_count(sleep_df, start_col) == 0:
        if fallback_start in sleep_df.columns and parsed_non_missing_count(sleep_df, fallback_start) > 0:
            print("Using fallback START_COL:", fallback_start)
            start_col = fallback_start

    if end_col is not None and end_col in sleep_df.columns and looks_like_uuid_series(sleep_df[end_col]):
        if fallback_end in sleep_df.columns and parsed_non_missing_count(sleep_df, fallback_end) > 0:
            print("Using fallback END_COL:", fallback_end)
            end_col = fallback_end

    if fallback_uuid in sleep_df.columns and looks_like_uuid_series(sleep_df[fallback_uuid]):
        print("Using fallback DATAUUID_COL:", fallback_uuid)
        datauuid_col = fallback_uuid

    if start_col is None or end_col is None:
        raise ValueError(
            f"Could not identify sleep start/end columns. Columns: {sleep_df.columns.tolist()}"
        )

    print("FINAL START_COL:", start_col)
    print("FINAL END_COL:", end_col)
    print("FINAL DATAUUID_COL:", datauuid_col)

    preview_cols = [col for col in [start_col, end_col, datauuid_col] if col is not None]
    print("Column preview:")
    print(sleep_df[preview_cols].head())

    return start_col, end_col, datauuid_col


def first_existing_column(df: pd.DataFrame, candidates: list[str]) -> str | None:
    return find_column(df, candidates)


def numeric_column_or_nan(df: pd.DataFrame, column: str | None) -> pd.Series:
    if column is None:
        return pd.Series(np.nan, index=df.index)
    return pd.to_numeric(df[column], errors="coerce")


def make_sleep_episode_id(row: pd.Series) -> str:
    start_token = row["sleep_start_datetime"].strftime("%Y%m%d%H%M%S")
    end_token = row["sleep_end_datetime"].strftime("%Y%m%d%H%M%S")
    datauuid = str(row.get("source_datauuid", ""))
    datauuid_short = datauuid[:12] if datauuid and datauuid != "nan" else "no_uuid"
    return f"{PARTICIPANT_ID}__{start_token}__{end_token}__{datauuid_short}"


def main() -> None:
    sleep_path = find_dataset_file(SLEEP_DATASET)
    sleep_df = read_samsung_csv(sleep_path)

    print("sleep source:", sleep_path)
    print("raw sleep shape:", sleep_df.shape)

    start_col, end_col, datauuid_col = choose_sleep_columns(sleep_df)

    output_df = pd.DataFrame(index=sleep_df.index)

    output_df["participant_object_id"] = PARTICIPANT_ID
    output_df["sleep_start_datetime"] = parse_datetime(sleep_df[start_col])
    output_df["sleep_end_datetime"] = parse_datetime(sleep_df[end_col])

    if datauuid_col is not None:
        output_df["source_datauuid"] = sleep_df[datauuid_col].astype(str)
    else:
        output_df["source_datauuid"] = ""

    sleep_score_col = first_existing_column(sleep_df, ["sleep_score"])
    efficiency_col = first_existing_column(sleep_df, ["efficiency"])
    sleep_duration_col = first_existing_column(sleep_df, ["sleep_duration"])
    sleep_type_col = first_existing_column(sleep_df, ["sleep_type"])
    quality_col = first_existing_column(sleep_df, ["quality"])

    output_df["samsung_sleep_score"] = numeric_column_or_nan(sleep_df, sleep_score_col)
    output_df["samsung_sleep_efficiency"] = numeric_column_or_nan(sleep_df, efficiency_col)
    output_df["samsung_sleep_duration_ms"] = numeric_column_or_nan(sleep_df, sleep_duration_col)
    output_df["samsung_sleep_type"] = numeric_column_or_nan(sleep_df, sleep_type_col)
    output_df["samsung_quality_code"] = numeric_column_or_nan(sleep_df, quality_col)

    optional_numeric_cols = [
        "physical_recovery",
        "mental_recovery",
        "sleep_latency",
        "movement_awakening",
        "sleep_cycle",
        "total_rem_duration",
        "total_light_duration",
        "factor_01",
        "factor_02",
        "factor_03",
        "factor_04",
        "factor_05",
        "factor_06",
        "factor_07",
        "factor_08",
        "factor_09",
        "factor_10",
    ]

    for col in optional_numeric_cols:
        actual_col = first_existing_column(sleep_df, [col])
        output_df[f"samsung_{col}"] = numeric_column_or_nan(sleep_df, actual_col)

    output_df["sleep_duration_hours_from_time"] = (
        output_df["sleep_end_datetime"] - output_df["sleep_start_datetime"]
    ).dt.total_seconds() / 3600

    output_df["sleep_duration_hours_from_samsung"] = (
        output_df["samsung_sleep_duration_ms"] / (1000 * 60 * 60)
    )

    output_df["calendar_date"] = output_df["sleep_end_datetime"].dt.normalize()
    output_df["sleep_start_date"] = output_df["sleep_start_datetime"].dt.normalize()
    output_df["sleep_end_date"] = output_df["sleep_end_datetime"].dt.normalize()

    output_df["cross_midnight"] = (
        output_df["sleep_start_date"] != output_df["sleep_end_date"]
    ).astype(int)

    output_df["has_samsung_sleep_score"] = output_df["samsung_sleep_score"].notna().astype(int)

    output_df["samsung_good_sleep_label"] = np.where(
        output_df["samsung_sleep_score"].notna(),
        (output_df["samsung_sleep_score"] >= GOOD_SLEEP_SCORE_THRESHOLD).astype(int),
        np.nan,
    )

    valid_mask = (
        output_df["sleep_start_datetime"].notna()
        & output_df["sleep_end_datetime"].notna()
        & output_df["sleep_duration_hours_from_time"].between(
            MIN_SLEEP_DURATION_HOURS,
            MAX_SLEEP_DURATION_HOURS,
            inclusive="both",
        )
    )

    invalid_df = output_df[~valid_mask].copy()
    output_df = output_df[valid_mask].copy()

    if len(output_df) == 0:
        raise ValueError(
            "No valid Samsung sleep episodes after filtering. "
            "Check sleep start/end column mapping and duration filters."
        )

    output_df = output_df.sort_values("sleep_start_datetime").reset_index(drop=True)

    output_df["sleep_episode_id"] = output_df.apply(make_sleep_episode_id, axis=1)
    output_df["prediction_cutoff_datetime"] = output_df["sleep_start_datetime"]

    column_order = [
        "sleep_episode_id",
        "participant_object_id",
        "sleep_start_datetime",
        "sleep_end_datetime",
        "prediction_cutoff_datetime",
        "calendar_date",
        "sleep_start_date",
        "sleep_end_date",
        "cross_midnight",
        "source_datauuid",
        "samsung_sleep_score",
        "samsung_good_sleep_label",
        "has_samsung_sleep_score",
        "samsung_sleep_efficiency",
        "samsung_sleep_duration_ms",
        "sleep_duration_hours_from_time",
        "sleep_duration_hours_from_samsung",
        "samsung_sleep_type",
        "samsung_quality_code",
    ]

    remaining_columns = [col for col in output_df.columns if col not in column_order]
    output_df = output_df[column_order + remaining_columns]

    output_df.to_csv(OUTPUT_PATH, index=False, encoding="utf-8-sig")

    summary_rows = [
        {"metric": "source_file", "value": str(sleep_path.relative_to(PROJECT_ROOT))},
        {"metric": "source_rows", "value": len(sleep_df)},
        {"metric": "valid_episode_rows", "value": len(output_df)},
        {"metric": "invalid_or_filtered_rows", "value": len(invalid_df)},
        {"metric": "start_column", "value": start_col},
        {"metric": "end_column", "value": end_col},
        {"metric": "datauuid_column", "value": datauuid_col or ""},
        {"metric": "sleep_score_non_missing", "value": int(output_df["samsung_sleep_score"].notna().sum())},
        {"metric": "sleep_score_missing", "value": int(output_df["samsung_sleep_score"].isna().sum())},
        {"metric": "good_sleep_score_threshold", "value": GOOD_SLEEP_SCORE_THRESHOLD},
        {
            "metric": "proxy_label_positive_rate",
            "value": float(output_df["samsung_good_sleep_label"].dropna().mean())
            if output_df["samsung_good_sleep_label"].notna().any()
            else np.nan,
        },
        {
            "metric": "min_sleep_start_datetime",
            "value": str(output_df["sleep_start_datetime"].min()) if len(output_df) else "",
        },
        {
            "metric": "max_sleep_start_datetime",
            "value": str(output_df["sleep_start_datetime"].max()) if len(output_df) else "",
        },
        {
            "metric": "median_duration_hours_from_time",
            "value": float(output_df["sleep_duration_hours_from_time"].median()) if len(output_df) else np.nan,
        },
    ]

    summary_df = pd.DataFrame(summary_rows)
    summary_df.to_csv(SUMMARY_PATH, index=False, encoding="utf-8-sig")

    report_lines = [
        "# Samsung Health Sleep Episode Table Summary",
        "",
        "## Purpose",
        "",
        "Create a sleep episode table from Samsung Health sleep export for strict pre-sleep inference preparation.",
        "",
        "## Source",
        "",
        "```text",
        str(sleep_path.relative_to(PROJECT_ROOT)),
        "```",
        "",
        "## Output",
        "",
        "```text",
        str(OUTPUT_PATH.relative_to(PROJECT_ROOT)),
        "```",
        "",
        "## Summary",
        "",
        "| Metric | Value |",
        "|---|---:|",
    ]

    for _, row in summary_df.iterrows():
        report_lines.append(f"| {row['metric']} | {row['value']} |")

    report_lines.extend(
        [
            "",
            "## Label Caveat",
            "",
            "`samsung_good_sleep_label` is a proxy label derived from Samsung `sleep_score`.",
            "It is not identical to the original LifeSnaps `good_sleep_label`.",
            "",
            "## Column Mapping Note",
            "",
            "This export required fallback column mapping for sleep start/end/datauuid because the Samsung sleep CSV data rows contain one more field than the header row and the tail fields are shifted.",
            "",
        ]
    )

    REPORT_PATH.write_text("\n".join(report_lines), encoding="utf-8")

    print("output:", OUTPUT_PATH)
    print("summary:", SUMMARY_PATH)
    print("report:", REPORT_PATH)
    print()
    print(summary_df)


if __name__ == "__main__":
    main()