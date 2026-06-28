from __future__ import annotations

import csv
from collections import defaultdict
from datetime import datetime
from pathlib import Path
from typing import Any

import pandas as pd
from pymongo import MongoClient


# This script performs the "date-level aggregation" step.
#
# Selected aggregation unit:
#   participant_object_id + calendar_date
#
# Reason:
# - The sleep target is naturally defined per participant per sleep date.
# - Fitbit stress, HRV, activity, SpO2, respiration, and temperature can be
#   aligned to that same daily axis.
# - SEMA mood/context responses occur several times per day, so daily counts
#   and proportions are more appropriate than row-level joins.
# - Surveys are not day-level repeated measurements; they are kept as
#   participant-level features for the later merge step.
MONGO_URI = "mongodb://localhost:27017"
DB_NAME = "rais_anonymized"

PROJECT_ROOT = Path(__file__).resolve().parents[1]
RAW_DIR = PROJECT_ROOT / "data" / "raw"
EXTRACTED_DIR = RAW_DIR / "extracted_variables"
OUTPUT_DIR = PROJECT_ROOT / "data" / "processed" / "daily_aggregates"
REPORT_PATH = PROJECT_ROOT / "reports" / "daily_aggregation_summary.md"


def parse_calendar_date(value: Any) -> str | None:
    """Normalize mixed Fitbit/SEMA date strings to YYYY-MM-DD."""

    if value is None or pd.isna(value):
        return None

    text = str(value).strip()
    if not text or text.lower() in {"nan", "none", "<no-response>", "<not-shown>"}:
        return None

    # ISO-like strings are common and can be normalized cheaply without pandas.
    if len(text) >= 10 and text[4:5] == "-" and text[7:8] == "-":
        return text[:10]

    # Some Fitbit minute-level records use strings like "05/24/21 00:00:00".
    # Large MongoDB aggregation keeps only the first 10 characters, which can
    # become "05/24/21 0". Split at whitespace to recover the date portion.
    if "/" in text:
        text = text.split()[0]

    parsed = pd.to_datetime(text, errors="coerce")
    if pd.isna(parsed):
        return None
    return parsed.date().isoformat()


def to_numeric(series: pd.Series) -> pd.Series:
    """Convert a pandas Series to numeric values with invalid entries as NaN."""

    return pd.to_numeric(series, errors="coerce")


def clean_category(value: Any) -> str | None:
    """Normalize categorical survey values and drop placeholder responses."""

    if value is None or pd.isna(value):
        return None
    text = str(value).strip()
    if not text or text in {"<no-response>", "<not-shown>", "nan", "None"}:
        return None
    return text


def get_nested(document: dict[str, Any], dotted_path: str) -> Any:
    """Read a dotted field path from a nested MongoDB document."""

    current: Any = document
    for part in dotted_path.split("."):
        if not isinstance(current, dict) or part not in current:
            return None
        current = current[part]
    return current


def safe_name(value: str) -> str:
    """Convert category labels to stable lowercase column-name fragments."""

    cleaned = []
    for char in value.lower():
        cleaned.append(char if char.isalnum() else "_")
    return "_".join("".join(cleaned).split("_")).strip("_")


def summarize_output(path: Path) -> dict[str, Any]:
    """Return row/column counts for a generated CSV file."""

    df = pd.read_csv(path, nrows=5)
    with path.open("r", encoding="utf-8-sig") as file:
        row_count = max(sum(1 for _ in file) - 1, 0)
    return {"path": path, "rows": row_count, "columns": len(df.columns)}


def aggregate_sleep() -> dict[str, Any]:
    """Aggregate sleep logs to one row per participant and sleep date."""

    path = RAW_DIR / "sleep_from_mongodb.csv"
    df = pd.read_csv(path)
    df["calendar_date"] = df["dateOfSleep"].map(parse_calendar_date)

    # The modeling target should use the main sleep period for the date.
    # Non-main naps or extra sleep logs are left out of the daily target table.
    df["mainSleep"] = df["mainSleep"].astype(str).str.lower().eq("true")
    df = df[df["mainSleep"]].copy()

    numeric_columns = [
        "duration",
        "minutesToFallAsleep",
        "minutesAsleep",
        "minutesAwake",
        "minutesAfterWakeup",
        "timeInBed",
        "efficiency",
        "deep_minutes",
        "light_minutes",
        "rem_minutes",
        "wake_minutes",
        "asleep_minutes",
        "restless_minutes",
        "awake_minutes",
    ]
    for column in numeric_columns:
        if column in df.columns:
            df[column] = to_numeric(df[column])

    # If more than one mainSleep record exists for the same participant/date,
    # keep the longest timeInBed record as the representative sleep episode.
    df = df.sort_values(
        ["participant_object_id", "calendar_date", "timeInBed"],
        ascending=[True, True, False],
    )
    daily = df.drop_duplicates(["participant_object_id", "calendar_date"], keep="first").copy()

    daily["sleep_duration_hours"] = daily["minutesAsleep"] / 60
    daily["time_in_bed_hours"] = daily["timeInBed"] / 60
    daily["awake_ratio"] = daily["minutesAwake"] / daily["timeInBed"]
    daily["good_sleep_label"] = (
        (daily["efficiency"] >= 85) & (daily["minutesAsleep"] >= 420)
    ).astype(int)

    for stage in ["deep", "light", "rem", "wake", "asleep", "restless", "awake"]:
        minutes_col = f"{stage}_minutes"
        if minutes_col in daily.columns:
            # Fitbit has two sleep-stage systems:
            # - stages: deep/light/rem/wake
            # - classic: asleep/restless/awake
            # Prefix classic ratios to avoid colliding with the general
            # awake_ratio = minutesAwake / timeInBed feature.
            ratio_name = (
                f"classic_{stage}_ratio"
                if stage in {"asleep", "restless", "awake"}
                else f"{stage}_ratio"
            )
            daily[ratio_name] = daily[minutes_col] / daily["timeInBed"]

    keep_columns = [
        "participant_object_id",
        "calendar_date",
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
        "good_sleep_label",
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
    ]
    keep_columns = [column for column in keep_columns if column in daily.columns]
    output = daily[keep_columns]

    output_path = OUTPUT_DIR / "sleep_daily_target.csv"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output.to_csv(output_path, index=False, encoding="utf-8-sig")
    return summarize_output(output_path)


def aggregate_mean_table(
    input_name: str,
    output_name: str,
    date_column: str,
    numeric_columns: list[str],
    prefix: str,
) -> dict[str, Any]:
    """Aggregate a small extracted CSV by participant/date using mean and count."""

    df = pd.read_csv(EXTRACTED_DIR / input_name)
    df["calendar_date"] = df[date_column].map(parse_calendar_date)
    df = df.dropna(subset=["participant_object_id", "calendar_date"]).copy()

    for column in numeric_columns:
        df[column] = to_numeric(df[column])

    grouped = df.groupby(["participant_object_id", "calendar_date"], as_index=False)
    daily = grouped[numeric_columns].mean()
    daily = daily.rename(columns={column: f"{prefix}_{column}_mean" for column in numeric_columns})
    daily[f"{prefix}_record_count"] = grouped.size()["size"]

    output_path = OUTPUT_DIR / f"{output_name}.csv"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    daily.to_csv(output_path, index=False, encoding="utf-8-sig")
    return summarize_output(output_path)


def aggregate_stress() -> dict[str, Any]:
    """Aggregate Fitbit Stress Score records to participant-day."""

    df = pd.read_csv(EXTRACTED_DIR / "fitbit_stress_score.csv")
    df["calendar_date"] = df["date_time"].map(parse_calendar_date)
    df = df.dropna(subset=["participant_object_id", "calendar_date"]).copy()

    numeric_columns = [
        "stress_score",
        "sleep_points",
        "responsiveness_points",
        "exertion_points",
    ]
    for column in numeric_columns:
        df[column] = to_numeric(df[column])

    df["stress_ready"] = df["status"].astype(str).str.upper().eq("READY").astype(int)
    df["stress_calculation_failed"] = (
        df["calculation_failed"].astype(str).str.lower().eq("true").astype(int)
    )

    grouped = df.groupby(["participant_object_id", "calendar_date"], as_index=False)
    daily = grouped[numeric_columns + ["stress_ready", "stress_calculation_failed"]].mean()
    daily = daily.rename(
        columns={
            "stress_score": "stress_score_mean",
            "sleep_points": "stress_sleep_points_mean",
            "responsiveness_points": "stress_responsiveness_points_mean",
            "exertion_points": "stress_exertion_points_mean",
            "stress_ready": "stress_ready_rate",
            "stress_calculation_failed": "stress_calculation_failed_rate",
        }
    )
    daily["stress_record_count"] = grouped.size()["size"]

    output_path = OUTPUT_DIR / "fitbit_stress_daily.csv"
    daily.to_csv(output_path, index=False, encoding="utf-8-sig")
    return summarize_output(output_path)


def aggregate_activity_minutes() -> dict[str, Any]:
    """Pivot daily activity-minute types to one row per participant/date."""

    df = pd.read_csv(EXTRACTED_DIR / "fitbit_activity_minutes.csv")
    df["calendar_date"] = df["date_time"].map(parse_calendar_date)
    df["value"] = to_numeric(df["value"])
    df = df.dropna(subset=["participant_object_id", "calendar_date", "fitbit_type"]).copy()

    grouped = (
        df.groupby(["participant_object_id", "calendar_date", "fitbit_type"])["value"]
        .sum()
        .reset_index()
    )
    daily = grouped.pivot_table(
        index=["participant_object_id", "calendar_date"],
        columns="fitbit_type",
        values="value",
        fill_value=0,
        aggfunc="sum",
    ).reset_index()
    daily.columns.name = None
    daily = daily.rename(
        columns={
            "sedentary_minutes": "sedentary_minutes_sum",
            "lightly_active_minutes": "lightly_active_minutes_sum",
            "moderately_active_minutes": "moderately_active_minutes_sum",
            "very_active_minutes": "very_active_minutes_sum",
        }
    )

    output_path = OUTPUT_DIR / "fitbit_activity_minutes_daily.csv"
    daily.to_csv(output_path, index=False, encoding="utf-8-sig")
    return summarize_output(output_path)


def aggregate_hrv_details() -> dict[str, Any]:
    """Aggregate detailed HRV samples to daily mean/std/count features."""

    df = pd.read_csv(EXTRACTED_DIR / "fitbit_hrv_details.csv")
    df["calendar_date"] = df["timestamp"].map(parse_calendar_date)
    df = df.dropna(subset=["participant_object_id", "calendar_date"]).copy()

    numeric_columns = ["rmssd", "coverage", "low_frequency", "high_frequency"]
    for column in numeric_columns:
        df[column] = to_numeric(df[column])

    grouped = df.groupby(["participant_object_id", "calendar_date"])
    daily = grouped[numeric_columns].agg(["mean", "std", "min", "max"])
    daily.columns = [f"hrv_detail_{column}_{stat}" for column, stat in daily.columns]
    daily = daily.reset_index()
    daily["hrv_detail_record_count"] = grouped.size().to_numpy()

    output_path = OUTPUT_DIR / "fitbit_hrv_details_daily.csv"
    daily.to_csv(output_path, index=False, encoding="utf-8-sig")
    return summarize_output(output_path)


def aggregate_sema() -> dict[str, Any]:
    """Aggregate SEMA mood/context responses to participant-day."""

    df = pd.read_csv(EXTRACTED_DIR / "sema_responses.csv")
    df["calendar_date"] = df["CREATED_TS"].map(parse_calendar_date)
    df = df.dropna(subset=["participant_object_id", "calendar_date"]).copy()

    df["mood_clean"] = df["MOOD"].map(clean_category)
    df["place_clean"] = df["PLACE"].map(clean_category)

    base = (
        df.groupby(["participant_object_id", "calendar_date"])
        .size()
        .reset_index(name="sema_response_count")
    )

    for source_column, output_prefix in [("mood_clean", "mood"), ("place_clean", "place")]:
        valid = df.dropna(subset=[source_column]).copy()
        if valid.empty:
            continue
        valid["category_col"] = valid[source_column].map(lambda value: f"{output_prefix}_{safe_name(value)}_count")
        counts = (
            valid.groupby(["participant_object_id", "calendar_date", "category_col"])
            .size()
            .reset_index(name="count")
        )
        pivot = counts.pivot_table(
            index=["participant_object_id", "calendar_date"],
            columns="category_col",
            values="count",
            fill_value=0,
            aggfunc="sum",
        ).reset_index()
        pivot.columns.name = None
        base = base.merge(pivot, on=["participant_object_id", "calendar_date"], how="left")

    count_columns = [
        column
        for column in base.columns
        if column not in {"participant_object_id", "calendar_date", "sema_response_count"}
    ]
    base[count_columns] = base[count_columns].fillna(0)
    for column in count_columns:
        if column.endswith("_count"):
            base[column.replace("_count", "_rate")] = base[column] / base["sema_response_count"]

    output_path = OUTPUT_DIR / "sema_daily_context_mood.csv"
    base.to_csv(output_path, index=False, encoding="utf-8-sig")
    return summarize_output(output_path)


def aggregate_surveys_participant() -> dict[str, Any]:
    """Summarize surveys at participant level because surveys are not daily logs."""

    df = pd.read_csv(EXTRACTED_DIR / "surveys_responses.csv")
    base = (
        df.groupby("participant_object_id")
        .size()
        .reset_index(name="survey_response_count")
    )
    type_counts = (
        df.groupby(["participant_object_id", "survey_type"])
        .size()
        .reset_index(name="count")
    )
    type_counts["survey_type_col"] = type_counts["survey_type"].map(
        lambda value: f"survey_{safe_name(str(value))}_count"
    )
    pivot = type_counts.pivot_table(
        index="participant_object_id",
        columns="survey_type_col",
        values="count",
        fill_value=0,
        aggfunc="sum",
    ).reset_index()
    pivot.columns.name = None
    output = base.merge(pivot, on="participant_object_id", how="left")

    output_path = OUTPUT_DIR / "surveys_participant_summary.csv"
    output.to_csv(output_path, index=False, encoding="utf-8-sig")
    return summarize_output(output_path)


def stream_mongo_daily_sum(
    collection: Any,
    type_name: str,
    date_path: str,
    value_path: str,
    output_name: str,
    output_prefix: str,
    date_prefix_bytes: int = 10,
    batch_size: int = 5000,
) -> dict[str, Any]:
    """Aggregate a large Fitbit type by participant/date inside MongoDB.

    The first implementation streamed every raw document through Python, which
    was correct but too slow for calories. This version lets MongoDB reduce
    millions of minute-level rows to participant/date groups first.
    """

    pipeline = [
        {"$match": {"type": type_name}},
        {
            "$project": {
                "participant_object_id": "$id",
                # The raw date formats are mixed:
                # - ISO: 2021-05-24T00:15:00, date prefix length 10
                # - US short: 05/24/21 00:00:00, date prefix length 8
                # The caller chooses the right prefix length so MongoDB groups
                # by date, not by date plus the first hour digit.
                "raw_date": {"$substrBytes": [f"${date_path}", 0, date_prefix_bytes]},
                "numeric_value": {
                    "$convert": {
                        "input": f"${value_path}",
                        "to": "double",
                        "onError": None,
                        "onNull": None,
                    }
                },
            }
        },
        {
            "$match": {
                "participant_object_id": {"$ne": None},
                "raw_date": {"$ne": None},
                "numeric_value": {"$ne": None},
            }
        },
        {
            "$group": {
                "_id": {
                    "participant_object_id": "$participant_object_id",
                    "raw_date": "$raw_date",
                },
                "value_sum": {"$sum": "$numeric_value"},
                "record_count": {"$sum": 1},
            }
        },
    ]

    rows = []
    for document in collection.aggregate(pipeline, allowDiskUse=True, batchSize=batch_size):
        key = document["_id"]
        calendar_date = parse_calendar_date(key.get("raw_date"))
        if calendar_date is None:
            continue
        rows.append(
            {
                "participant_object_id": str(key.get("participant_object_id")),
                "calendar_date": calendar_date,
                f"{output_prefix}_sum": document["value_sum"],
                f"{output_prefix}_record_count": document["record_count"],
            }
        )

    output_path = OUTPUT_DIR / output_name
    pd.DataFrame(rows).sort_values(["participant_object_id", "calendar_date"]).to_csv(
        output_path, index=False, encoding="utf-8-sig"
    )
    return summarize_output(output_path)


def stream_mongo_daily_stats(
    collection: Any,
    type_name: str,
    date_path: str,
    value_path: str,
    output_name: str,
    output_prefix: str,
    date_prefix_bytes: int = 10,
    batch_size: int = 5000,
) -> dict[str, Any]:
    """Aggregate mean/min/max for a large Fitbit type inside MongoDB."""

    pipeline = [
        {"$match": {"type": type_name}},
        {
            "$project": {
                "participant_object_id": "$id",
                "raw_date": {"$substrBytes": [f"${date_path}", 0, date_prefix_bytes]},
                "numeric_value": {
                    "$convert": {
                        "input": f"${value_path}",
                        "to": "double",
                        "onError": None,
                        "onNull": None,
                    }
                },
            }
        },
        {
            "$match": {
                "participant_object_id": {"$ne": None},
                "raw_date": {"$ne": None},
                "numeric_value": {"$ne": None},
            }
        },
        {
            "$group": {
                "_id": {
                    "participant_object_id": "$participant_object_id",
                    "raw_date": "$raw_date",
                },
                "value_mean": {"$avg": "$numeric_value"},
                "value_min": {"$min": "$numeric_value"},
                "value_max": {"$max": "$numeric_value"},
                "record_count": {"$sum": 1},
            }
        },
    ]

    rows = []
    for document in collection.aggregate(pipeline, allowDiskUse=True, batchSize=batch_size):
        key = document["_id"]
        calendar_date = parse_calendar_date(key.get("raw_date"))
        if calendar_date is None:
            continue
        rows.append(
            {
                "participant_object_id": str(key.get("participant_object_id")),
                "calendar_date": calendar_date,
                f"{output_prefix}_mean": document["value_mean"],
                f"{output_prefix}_min": document["value_min"],
                f"{output_prefix}_max": document["value_max"],
                f"{output_prefix}_record_count": document["record_count"],
            }
        )

    output_path = OUTPUT_DIR / output_name
    pd.DataFrame(rows).sort_values(["participant_object_id", "calendar_date"]).to_csv(
        output_path, index=False, encoding="utf-8-sig"
    )
    return summarize_output(output_path)


def write_report(outputs: list[dict[str, Any]]) -> None:
    """Write a report for the date-level aggregation step."""

    lines = [
        "# Daily Aggregation Summary",
        "",
        f"- Generated at: `{datetime.now().isoformat(timespec='seconds')}`",
        f"- Mongo URI: `{MONGO_URI}`",
        f"- Database: `{DB_NAME}`",
        "",
        "## Selected Unit",
        "",
        "- Aggregation unit: `participant_object_id + calendar_date`",
        "- This is the most appropriate unit because the prediction target is one sleep outcome per participant-day.",
        "- SEMA responses are summarized to daily counts/rates.",
        "- Surveys are summarized at participant level because they are not repeated daily measurements.",
        "",
        "## Generated Tables",
        "",
        "| table | rows | columns | path |",
        "| --- | ---: | ---: | --- |",
    ]

    for output in outputs:
        lines.append(
            f"| `{output['path'].name}` | {output['rows']:,} | {output['columns']} | `{output['path']}` |"
        )

    lines.extend(
        [
            "",
            "## Boundary",
            "",
            "- This step aggregates sources to the chosen unit.",
            "- It does not yet merge all sources into one final modeling dataset.",
            "- It does not impute missing values, encode categories beyond daily SEMA count/rate columns, scale, or run PCA.",
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
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=5000)
    client.admin.command("ping")
    fitbit = client[DB_NAME].fitbit

    outputs: list[dict[str, Any]] = []

    print("Aggregating sleep target...")
    outputs.append(aggregate_sleep())

    print("Aggregating stress score...")
    outputs.append(aggregate_stress())

    print("Aggregating daily HRV summary...")
    outputs.append(
        aggregate_mean_table(
            "fitbit_daily_hrv_summary.csv",
            "fitbit_daily_hrv_summary_daily",
            "timestamp",
            ["rmssd", "nremhr", "entropy"],
            "hrv_summary",
        )
    )

    print("Aggregating detailed HRV...")
    outputs.append(aggregate_hrv_details())

    print("Aggregating resting heart rate...")
    outputs.append(
        aggregate_mean_table(
            "fitbit_resting_heart_rate.csv",
            "fitbit_resting_heart_rate_daily",
            "date_time",
            ["resting_heart_rate", "error"],
            "resting_hr",
        )
    )

    print("Aggregating activity minutes...")
    outputs.append(aggregate_activity_minutes())

    print("Aggregating Daily SpO2...")
    outputs.append(
        aggregate_mean_table(
            "fitbit_daily_spo2.csv",
            "fitbit_daily_spo2_daily",
            "timestamp",
            ["average_value", "lower_bound", "upper_bound"],
            "spo2",
        )
    )

    print("Aggregating respiratory rate...")
    outputs.append(
        aggregate_mean_table(
            "fitbit_respiratory_rate_summary.csv",
            "fitbit_respiratory_rate_summary_daily",
            "timestamp",
            [
                "full_sleep_breathing_rate",
                "full_sleep_signal_to_noise",
                "full_sleep_standard_deviation",
                "deep_sleep_breathing_rate",
                "light_sleep_breathing_rate",
                "rem_sleep_breathing_rate",
            ],
            "respiratory",
        )
    )

    print("Aggregating SEMA mood/context...")
    outputs.append(aggregate_sema())

    print("Summarizing participant-level surveys...")
    outputs.append(aggregate_surveys_participant())

    print("Streaming steps from MongoDB...")
    outputs.append(
        stream_mongo_daily_sum(
            fitbit,
            "steps",
            "data.dateTime",
            "data.value",
            "fitbit_steps_daily.csv",
            "steps",
        )
    )

    print("Streaming calories from MongoDB...")
    outputs.append(
        stream_mongo_daily_sum(
            fitbit,
            "calories",
            "data.dateTime",
            "data.value",
            "fitbit_calories_daily.csv",
            "calories",
            date_prefix_bytes=8,
        )
    )

    print("Streaming wrist temperature from MongoDB...")
    outputs.append(
        stream_mongo_daily_stats(
            fitbit,
            "Wrist Temperature",
            "data.recorded_time",
            "data.temperature",
            "fitbit_wrist_temperature_daily.csv",
            "wrist_temperature",
        )
    )

    write_report(outputs)

    print("\nDaily aggregation outputs:")
    for output in outputs:
        print(f"- {output['path'].name}: {output['rows']} rows, {output['columns']} cols")
    print(f"\nWrote report: {REPORT_PATH}")


if __name__ == "__main__":
    main()
