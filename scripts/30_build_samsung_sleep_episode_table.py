from __future__ import annotations

from pathlib import Path
import csv
import os

import numpy as np
import pandas as pd


PROJECT_ROOT = Path(os.environ.get("PROJECT_ROOT", Path(__file__).resolve().parents[1]))

SAMSUNG_DIR_CANDIDATES = [
    Path(os.environ["SAMSUNG_HEALTH_DIR"]) if os.environ.get("SAMSUNG_HEALTH_DIR") else None,
    PROJECT_ROOT / "docs" / "samsung",
    PROJECT_ROOT / "docs" / "samsunghealth",
    PROJECT_ROOT / "docs",
    PROJECT_ROOT / "data" / "raw" / "samsung_health",
]

OUTPUT_DIR = PROJECT_ROOT / "data" / "processed" / "samsung_health" / "pre_sleep_stage1"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

SLEEP_STAGE_DATASET = "com.samsung.health.sleep_stage"

OUTPUT_PATH = OUTPUT_DIR / "samsung_sleep_episodes.csv"
SUMMARY_PATH = OUTPUT_DIR / "samsung_sleep_episode_summary.csv"
STAGE_SUMMARY_PATH = OUTPUT_DIR / "samsung_sleep_stage_episode_stage_summary.csv"
REPORT_PATH = PROJECT_ROOT / "reports" / "samsung_sleep_episode_table_summary.md"

PARTICIPANT_ID = "samsung_user"

MIN_SLEEP_DURATION_HOURS = 2.0
MAX_SLEEP_DURATION_HOURS = 16.0


def display_path(path: Path) -> str:
    try:
        return str(path.relative_to(PROJECT_ROOT))
    except ValueError:
        return str(path)


def find_dataset_file(dataset_name: str) -> Path:
    for root in SAMSUNG_DIR_CANDIDATES:
        if root is None or not root.exists():
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
    This reader pads the header with leading extra columns so rows can be loaded.
    """
    with open(path, "r", encoding="utf-8-sig", newline="") as f:
        reader = csv.reader(f)
        _metadata = next(reader)
        header = next(reader)
        rows = list(reader)

    max_fields = max([len(header)] + [len(row) for row in rows])

    if max_fields > len(header):
        extra_count = max_fields - len(header)
        header = [f"_extra_field_{i}" for i in range(extra_count)] + header

    fixed_rows = []
    for row in rows:
        if len(row) < len(header):
            row = row + [""] * (len(header) - len(row))
        elif len(row) > len(header):
            row = row[: len(header)]
        fixed_rows.append(row)

    df = pd.DataFrame(fixed_rows, columns=header)
    df = df.replace("", np.nan).infer_objects(copy=False)

    return df


def parse_datetime(series: pd.Series) -> pd.Series:
    return pd.to_datetime(series, errors="coerce")


def parse_utc_offset_minutes(value) -> float:
    if pd.isna(value):
        return np.nan
    text = str(value).strip()
    if not text.startswith("UTC") or len(text) < 8:
        return np.nan
    sign = 1 if text[3] == "+" else -1
    hours = pd.to_numeric(text[4:6], errors="coerce")
    minutes = pd.to_numeric(text[6:8], errors="coerce")
    if pd.isna(hours) or pd.isna(minutes):
        return np.nan
    return float(sign * (hours * 60 + minutes))


def apply_utc_offset(datetime_series: pd.Series, offset_series: pd.Series) -> pd.Series:
    offsets = offset_series.map(parse_utc_offset_minutes)
    return datetime_series + pd.to_timedelta(offsets.fillna(0), unit="m")


def make_sleep_episode_id(row: pd.Series) -> str:
    start_token = row["sleep_start_datetime"].strftime("%Y%m%d%H%M%S")
    end_token = row["sleep_end_datetime"].strftime("%Y%m%d%H%M%S")
    sleep_id_short = str(row["source_sleep_id"])[-12:]
    return f"{PARTICIPANT_ID}__{start_token}__{end_token}__{sleep_id_short}"


def main() -> None:
    sleep_stage_path = find_dataset_file(SLEEP_STAGE_DATASET)
    stage_df = read_samsung_csv(sleep_stage_path)

    print("sleep_stage source:", sleep_stage_path)
    print("raw sleep_stage shape:", stage_df.shape)
    print("columns:", stage_df.columns.tolist())

    required_columns = [
        "start_time",
        "create_sh_ver",
        "update_time",
        "create_time",
        "end_time",
    ]

    missing = [col for col in required_columns if col not in stage_df.columns]
    if missing:
        raise ValueError(f"Missing required sleep_stage columns: {missing}")

    # In this Samsung Health export, sleep_stage tail fields are shifted:
    # - start_time contains the sleep episode UUID
    # - create_sh_ver contains segment start time
    # - update_time contains segment end time
    # - create_time contains stage code
    # - stage contains UTC offset, e.g. UTC+0900
    # - end_time contains segment datauuid
    stage_df["source_sleep_id"] = stage_df["start_time"].astype(str)
    stage_df["stage_start_datetime"] = parse_datetime(stage_df["create_sh_ver"])
    stage_df["stage_end_datetime"] = parse_datetime(stage_df["update_time"])
    stage_df["stage_utc_offset"] = stage_df["stage"].astype(str)
    stage_df["stage_start_datetime"] = apply_utc_offset(
        stage_df["stage_start_datetime"],
        stage_df["stage_utc_offset"],
    )
    stage_df["stage_end_datetime"] = apply_utc_offset(
        stage_df["stage_end_datetime"],
        stage_df["stage_utc_offset"],
    )
    stage_df["samsung_stage_code"] = pd.to_numeric(stage_df["create_time"], errors="coerce")
    stage_df["source_stage_datauuid"] = stage_df["end_time"].astype(str)

    valid_stage_df = stage_df.dropna(
        subset=[
            "source_sleep_id",
            "stage_start_datetime",
            "stage_end_datetime",
        ]
    ).copy()

    valid_stage_df["stage_duration_minutes"] = (
        valid_stage_df["stage_end_datetime"] - valid_stage_df["stage_start_datetime"]
    ).dt.total_seconds() / 60

    stage_summary_df = (
        valid_stage_df.groupby(["source_sleep_id", "samsung_stage_code"], dropna=False)
        .agg(
            stage_rows=("samsung_stage_code", "size"),
            stage_total_minutes=("stage_duration_minutes", "sum"),
        )
        .reset_index()
    )

    episode_df = (
        valid_stage_df.groupby("source_sleep_id")
        .agg(
            sleep_start_datetime=("stage_start_datetime", "min"),
            sleep_end_datetime=("stage_end_datetime", "max"),
            stage_rows=("samsung_stage_code", "size"),
            unique_stage_codes=("samsung_stage_code", "nunique"),
            min_stage_code=("samsung_stage_code", "min"),
            max_stage_code=("samsung_stage_code", "max"),
        )
        .reset_index()
    )

    episode_df["participant_object_id"] = PARTICIPANT_ID

    episode_df["sleep_duration_hours"] = (
        episode_df["sleep_end_datetime"] - episode_df["sleep_start_datetime"]
    ).dt.total_seconds() / 3600

    episode_df["calendar_date"] = episode_df["sleep_end_datetime"].dt.normalize()
    episode_df["sleep_start_date"] = episode_df["sleep_start_datetime"].dt.normalize()
    episode_df["sleep_end_date"] = episode_df["sleep_end_datetime"].dt.normalize()

    episode_df["prediction_cutoff_datetime"] = episode_df["sleep_start_datetime"]
    episode_df["cross_midnight"] = (
        episode_df["sleep_start_date"] != episode_df["sleep_end_date"]
    ).astype(int)

    valid_episode_mask = episode_df["sleep_duration_hours"].between(
        MIN_SLEEP_DURATION_HOURS,
        MAX_SLEEP_DURATION_HOURS,
        inclusive="both",
    )

    invalid_episode_df = episode_df[~valid_episode_mask].copy()
    episode_df = episode_df[valid_episode_mask].copy()

    if len(episode_df) == 0:
        raise ValueError("No valid Samsung sleep_stage-derived episodes after duration filtering.")

    episode_df = episode_df.sort_values("sleep_start_datetime").reset_index(drop=True)

    episode_df["sleep_episode_id"] = episode_df.apply(make_sleep_episode_id, axis=1)

    # Keep label columns explicit but empty for now.
    # Samsung sleep_score proxy labels require a separate join to the sleep table.
    episode_df["samsung_sleep_score"] = np.nan
    episode_df["samsung_good_sleep_label"] = np.nan
    episode_df["has_samsung_sleep_score"] = 0

    column_order = [
        "sleep_episode_id",
        "participant_object_id",
        "source_sleep_id",
        "sleep_start_datetime",
        "sleep_end_datetime",
        "prediction_cutoff_datetime",
        "calendar_date",
        "sleep_start_date",
        "sleep_end_date",
        "cross_midnight",
        "sleep_duration_hours",
        "stage_rows",
        "unique_stage_codes",
        "min_stage_code",
        "max_stage_code",
        "samsung_sleep_score",
        "samsung_good_sleep_label",
        "has_samsung_sleep_score",
    ]

    remaining_columns = [col for col in episode_df.columns if col not in column_order]
    episode_df = episode_df[column_order + remaining_columns]

    episode_df.to_csv(OUTPUT_PATH, index=False, encoding="utf-8-sig")
    stage_summary_df.to_csv(STAGE_SUMMARY_PATH, index=False, encoding="utf-8-sig")

    summary_rows = [
        {"metric": "source_file", "value": display_path(sleep_stage_path)},
        {"metric": "source_stage_rows", "value": len(stage_df)},
        {"metric": "valid_stage_rows", "value": len(valid_stage_df)},
        {"metric": "raw_episode_count", "value": int(valid_stage_df["source_sleep_id"].nunique())},
        {"metric": "valid_episode_rows", "value": len(episode_df)},
        {"metric": "invalid_or_filtered_episode_rows", "value": len(invalid_episode_df)},
        {
            "metric": "min_sleep_start_datetime",
            "value": str(episode_df["sleep_start_datetime"].min()),
        },
        {
            "metric": "max_sleep_start_datetime",
            "value": str(episode_df["sleep_start_datetime"].max()),
        },
        {
            "metric": "median_duration_hours",
            "value": float(episode_df["sleep_duration_hours"].median()),
        },
        {
            "metric": "mean_duration_hours",
            "value": float(episode_df["sleep_duration_hours"].mean()),
        },
        {
            "metric": "cross_midnight_rate",
            "value": float(episode_df["cross_midnight"].mean()),
        },
        {
            "metric": "sleep_score_joined",
            "value": False,
        },
    ]

    summary_df = pd.DataFrame(summary_rows)
    summary_df.to_csv(SUMMARY_PATH, index=False, encoding="utf-8-sig")

    report_lines = [
        "# Samsung Health Sleep Episode Table Summary",
        "",
        "## Purpose",
        "",
        "Create a sleep episode table from Samsung Health sleep_stage export for strict pre-sleep inference preparation.",
        "",
        "## Source",
        "",
        "```text",
        display_path(sleep_stage_path),
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
            "## Column Mapping Note",
            "",
            "This Samsung Health export has shifted sleep_stage tail fields.",
            "",
            "Observed mapping:",
            "",
            "```text",
            "source_sleep_id = start_time",
            "stage_start_datetime = create_sh_ver",
            "stage_end_datetime = update_time",
            "samsung_stage_code = create_time",
            "stage_utc_offset = stage",
            "source_stage_datauuid = end_time",
            "```",
            "",
            "Stage start/end datetimes are adjusted by the observed UTC offset before episode aggregation.",
            "",
            "## Label Caveat",
            "",
            "`samsung_sleep_score` and `samsung_good_sleep_label` are not joined in this table yet.",
            "A Samsung sleep-score proxy label can be added later by linking to the Samsung sleep table.",
            "",
        ]
    )

    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    REPORT_PATH.write_text("\n".join(report_lines), encoding="utf-8")

    print("output:", OUTPUT_PATH)
    print("summary:", SUMMARY_PATH)
    print("stage summary:", STAGE_SUMMARY_PATH)
    print("report:", REPORT_PATH)
    print()
    print(summary_df)


if __name__ == "__main__":
    main()
