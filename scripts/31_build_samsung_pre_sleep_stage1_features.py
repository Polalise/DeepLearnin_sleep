from __future__ import annotations

from pathlib import Path
import argparse
import csv
import json
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

STAGE1_DIR = PROJECT_ROOT / "data" / "processed" / "pre_sleep_forecasting" / "design_c_stage1"
MANIFEST_PATH = (
    STAGE1_DIR
    / "inference_package"
    / "pre_sleep_inference_manifest.json"
)

SAMSUNG_OUTPUT_DIR = PROJECT_ROOT / "data" / "processed" / "samsung_health" / "pre_sleep_stage1"
SLEEP_EPISODE_PATH = SAMSUNG_OUTPUT_DIR / "samsung_sleep_episodes.csv"
OUTPUT_PATH = SAMSUNG_OUTPUT_DIR / "samsung_raw_stage1_features.csv"
MAPPING_REPORT_PATH = SAMSUNG_OUTPUT_DIR / "samsung_stage1_feature_mapping_report.csv"
SUMMARY_PATH = SAMSUNG_OUTPUT_DIR / "samsung_stage1_feature_summary.csv"
REPORT_PATH = PROJECT_ROOT / "reports" / "samsung_pre_sleep_stage1_feature_build_summary.md"

HEART_RATE_DATASET = "com.samsung.shealth.tracker.heart_rate"
PEDOMETER_DAY_DATASET = "com.samsung.shealth.tracker.pedometer_day_summary"
PEDOMETER_STEP_COUNT_DATASET = "com.samsung.shealth.tracker.pedometer_step_count"
ACTIVITY_DAY_DATASET = "com.samsung.shealth.activity.day_summary"
STEP_DAILY_TREND_DATASET = "com.samsung.shealth.step_daily_trend"

ID_COL = "participant_object_id"


def find_dataset_file(dataset_name: str) -> Path | None:
    for root in SAMSUNG_DIR_CANDIDATES:
        if root is None or not root.exists():
            continue

        matches = sorted(root.glob(f"{dataset_name}.*.csv"))
        if matches:
            return matches[0]

        recursive_matches = sorted(root.rglob(f"{dataset_name}.*.csv"))
        if recursive_matches:
            return recursive_matches[0]

    return None


def read_samsung_csv(path: Path) -> pd.DataFrame:
    """
    Samsung Health CSV export:
    - line 1: dataset/schema metadata
    - line 2: header
    - line 3+: data

    The core feature tables used here commonly have one extra trailing blank
    field in data rows. Drop that field so values stay aligned with headers.
    """
    with open(path, "r", encoding="utf-8-sig", newline="") as f:
        reader = csv.reader(f)
        _metadata = next(reader)
        header = next(reader)
        rows = list(reader)

    fixed_rows = []
    for row in rows:
        if len(row) == len(header) + 1 and row[-1] == "":
            row = row[:-1]
        if len(row) < len(header):
            row = row + [""] * (len(header) - len(row))
        elif len(row) > len(header):
            row = row[: len(header)]
        fixed_rows.append(row)

    df = pd.DataFrame(fixed_rows, columns=header)
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


def apply_utc_offset(datetime_series: pd.Series, offset_series: pd.Series | None) -> pd.Series:
    if offset_series is None:
        return datetime_series
    offsets = offset_series.map(parse_utc_offset_minutes)
    return datetime_series + pd.to_timedelta(offsets.fillna(0), unit="m")


def find_time_offset_column(df: pd.DataFrame, candidates: list[str]) -> str | None:
    return find_column(df, candidates + ["time_offset"])


def numeric_or_nan(df: pd.DataFrame, column: str | None) -> pd.Series:
    if column is None:
        return pd.Series(np.nan, index=df.index)
    return pd.to_numeric(df[column], errors="coerce")


def load_manifest() -> dict:
    return json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))


def load_optional_samsung_table(dataset_name: str) -> tuple[pd.DataFrame | None, Path | None]:
    path = find_dataset_file(dataset_name)
    if path is None:
        return None, None
    return read_samsung_csv(path), path


def prepare_heart_rate_table() -> tuple[pd.DataFrame, dict]:
    df, path = load_optional_samsung_table(HEART_RATE_DATASET)
    info = {"dataset": HEART_RATE_DATASET, "path": str(path) if path else "", "available": df is not None}

    if df is None:
        return pd.DataFrame(), info

    # In this export family, tail fields may be shifted. Prefer columns that
    # actually parse as timestamps or numeric heart-rate values.
    start_candidates = [
        "start_time",
        "com.samsung.health.heart_rate.start_time",
        "com.samsung.shealth.tracker.heart_rate.start_time",
        "create_sh_ver",
    ]
    end_candidates = [
        "end_time",
        "com.samsung.health.heart_rate.end_time",
        "com.samsung.shealth.tracker.heart_rate.end_time",
        "update_time",
    ]
    hr_candidates = [
        "heart_rate",
        "com.samsung.health.heart_rate.heart_rate",
        "com.samsung.shealth.tracker.heart_rate.heart_rate",
    ]

    start_col = find_column(df, start_candidates)
    end_col = find_column(df, end_candidates)
    heart_rate_col = find_column(df, hr_candidates)
    offset_col = find_time_offset_column(
        df,
        [
            "com.samsung.health.heart_rate.time_offset",
            "com.samsung.shealth.tracker.heart_rate.time_offset",
        ],
    )

    parsed_start = parse_datetime(df[start_col]) if start_col else pd.Series(pd.NaT, index=df.index)
    if parsed_start.notna().sum() == 0 and "create_sh_ver" in df.columns:
        start_col = "create_sh_ver"
        parsed_start = parse_datetime(df[start_col])

    parsed_end = parse_datetime(df[end_col]) if end_col else pd.Series(pd.NaT, index=df.index)
    if parsed_end.notna().sum() == 0 and "update_time" in df.columns:
        end_col = "update_time"
        parsed_end = parse_datetime(df[end_col])

    offset_series = df[offset_col] if offset_col else None
    parsed_start = apply_utc_offset(parsed_start, offset_series)
    parsed_end = apply_utc_offset(parsed_end, offset_series)

    if heart_rate_col is None:
        numeric_candidates = []
        for col in df.columns:
            col_l = str(col).lower()
            if "heart" in col_l or "rate" in col_l:
                numeric_candidates.append(col)
        for col in numeric_candidates:
            values = pd.to_numeric(df[col], errors="coerce")
            if values.notna().sum() > 0:
                heart_rate_col = col
                break

    out = pd.DataFrame(
        {
            "start_time": parsed_start,
            "end_time": parsed_end,
            "heart_rate": numeric_or_nan(df, heart_rate_col),
        }
    )
    out = out.dropna(subset=["start_time", "heart_rate"]).copy()

    info.update(
        {
            "start_col": start_col or "",
            "end_col": end_col or "",
            "time_offset_col": offset_col or "",
            "heart_rate_col": heart_rate_col or "",
            "rows": len(out),
        }
    )
    return out, info


def prepare_daily_activity_table() -> tuple[pd.DataFrame, list[dict]]:
    reports: list[dict] = []

    pedometer_df, pedometer_path = load_optional_samsung_table(PEDOMETER_DAY_DATASET)
    activity_df, activity_path = load_optional_samsung_table(ACTIVITY_DAY_DATASET)
    trend_df, trend_path = load_optional_samsung_table(STEP_DAILY_TREND_DATASET)

    daily_parts = []

    if pedometer_df is not None:
        day_col = find_column(pedometer_df, ["day_time", "start_time", "create_time"])
        offset_col = find_time_offset_column(
            pedometer_df,
            [
                "com.samsung.shealth.tracker.pedometer_day_summary.time_offset",
                "pedometer_day_summary.time_offset",
            ],
        )
        steps_col = find_column(pedometer_df, ["step_count", "steps"])
        calorie_col = find_column(pedometer_df, ["calorie", "calories"])
        active_time_col = find_column(pedometer_df, ["active_time", "total_active_time"])
        day_datetime = parse_datetime(pedometer_df[day_col]) if day_col else pd.Series(pd.NaT, index=pedometer_df.index)
        day_datetime = apply_utc_offset(day_datetime, pedometer_df[offset_col] if offset_col else None)

        part = pd.DataFrame(
            {
                "calendar_date": day_datetime.dt.normalize() if day_col else pd.NaT,
                "previous_day_steps_sum": numeric_or_nan(pedometer_df, steps_col),
                "previous_day_calories_sum": numeric_or_nan(pedometer_df, calorie_col),
                "active_time_minutes": numeric_or_nan(pedometer_df, active_time_col) / 60000,
                "source": "pedometer_day_summary",
            }
        )
        daily_parts.append(part)
        reports.append(
            {
                "dataset": PEDOMETER_DAY_DATASET,
                "path": str(pedometer_path) if pedometer_path else "",
                "day_col": day_col or "",
                "time_offset_col": offset_col or "",
                "steps_col": steps_col or "",
                "calorie_col": calorie_col or "",
                "active_time_col": active_time_col or "",
                "rows": len(part),
            }
        )

    if activity_df is not None:
        day_col = find_column(activity_df, ["day_time", "start_time", "create_time"])
        offset_col = find_time_offset_column(
            activity_df,
            [
                "com.samsung.shealth.activity.day_summary.time_offset",
                "activity.day_summary.time_offset",
            ],
        )
        steps_col = find_column(activity_df, ["step_count", "steps"])
        calorie_col = find_column(activity_df, ["calorie", "calories"])
        active_time_col = find_column(activity_df, ["active_time", "total_active_time"])
        day_datetime = parse_datetime(activity_df[day_col]) if day_col else pd.Series(pd.NaT, index=activity_df.index)
        day_datetime = apply_utc_offset(day_datetime, activity_df[offset_col] if offset_col else None)

        part = pd.DataFrame(
            {
                "calendar_date": day_datetime.dt.normalize() if day_col else pd.NaT,
                "previous_day_steps_sum": numeric_or_nan(activity_df, steps_col),
                "previous_day_calories_sum": numeric_or_nan(activity_df, calorie_col),
                "active_time_minutes": numeric_or_nan(activity_df, active_time_col) / 60000,
                "source": "activity_day_summary",
            }
        )
        daily_parts.append(part)
        reports.append(
            {
                "dataset": ACTIVITY_DAY_DATASET,
                "path": str(activity_path) if activity_path else "",
                "day_col": day_col or "",
                "time_offset_col": offset_col or "",
                "steps_col": steps_col or "",
                "calorie_col": calorie_col or "",
                "active_time_col": active_time_col or "",
                "rows": len(part),
            }
        )

    if trend_df is not None:
        day_col = find_column(trend_df, ["day_time", "start_time", "create_time"])
        offset_col = find_time_offset_column(
            trend_df,
            [
                "com.samsung.shealth.step_daily_trend.time_offset",
                "step_daily_trend.time_offset",
            ],
        )
        calorie_col = find_column(trend_df, ["calorie", "calories"])
        day_datetime = parse_datetime(trend_df[day_col]) if day_col else pd.Series(pd.NaT, index=trend_df.index)
        day_datetime = apply_utc_offset(day_datetime, trend_df[offset_col] if offset_col else None)

        part = pd.DataFrame(
            {
                "calendar_date": day_datetime.dt.normalize() if day_col else pd.NaT,
                "previous_day_steps_sum": np.nan,
                "previous_day_calories_sum": numeric_or_nan(trend_df, calorie_col),
                "active_time_minutes": np.nan,
                "source": "step_daily_trend",
            }
        )
        daily_parts.append(part)
        reports.append(
            {
                "dataset": STEP_DAILY_TREND_DATASET,
                "path": str(trend_path) if trend_path else "",
                "day_col": day_col or "",
                "time_offset_col": offset_col or "",
                "steps_col": "",
                "calorie_col": calorie_col or "",
                "active_time_col": "",
                "rows": len(part),
            }
        )

    if not daily_parts:
        return pd.DataFrame(), reports

    combined = pd.concat(daily_parts, ignore_index=True)
    combined = combined.dropna(subset=["calendar_date"]).copy()

    daily = (
        combined.groupby("calendar_date")
        .agg(
            previous_day_steps_sum=("previous_day_steps_sum", "max"),
            previous_day_calories_sum=("previous_day_calories_sum", "max"),
            active_time_minutes=("active_time_minutes", "max"),
        )
        .reset_index()
    )

    daily["previous_day_steps_record_count"] = daily["previous_day_steps_sum"].notna().astype(float)
    daily["previous_day_calories_record_count"] = daily["previous_day_calories_sum"].notna().astype(float)

    # Samsung export does not provide Fitbit-style activity intensity buckets in
    # this first adapter. Approximate lightly active minutes with total active
    # time and leave other intensity buckets missing.
    daily["previous_day_lightly_active_minutes_sum"] = daily["active_time_minutes"]
    daily["previous_day_moderately_active_minutes_sum"] = np.nan
    daily["previous_day_sedentary_minutes_sum"] = np.nan
    daily["previous_day_very_active_minutes_sum"] = np.nan

    return daily, reports


def prepare_intraday_activity_table() -> tuple[pd.DataFrame, dict]:
    df, path = load_optional_samsung_table(PEDOMETER_STEP_COUNT_DATASET)
    info = {
        "dataset": PEDOMETER_STEP_COUNT_DATASET,
        "path": str(path) if path else "",
        "available": df is not None,
    }

    if df is None:
        return pd.DataFrame(), info

    start_col = find_column(
        df,
        [
            "com.samsung.health.step_count.start_time",
            "step_count.start_time",
            "start_time",
        ],
    )
    end_col = find_column(
        df,
        [
            "com.samsung.health.step_count.end_time",
            "step_count.end_time",
            "end_time",
        ],
    )
    count_col = find_column(
        df,
        [
            "com.samsung.health.step_count.count",
            "step_count.count",
            "count",
        ],
    )
    calorie_col = find_column(
        df,
        [
            "com.samsung.health.step_count.calorie",
            "step_count.calorie",
            "calorie",
        ],
    )
    offset_col = find_time_offset_column(
        df,
        [
            "com.samsung.health.step_count.time_offset",
            "step_count.time_offset",
        ],
    )
    start_time = parse_datetime(df[start_col]) if start_col else pd.Series(pd.NaT, index=df.index)
    end_time = parse_datetime(df[end_col]) if end_col else pd.Series(pd.NaT, index=df.index)
    offset_series = df[offset_col] if offset_col else None

    out = pd.DataFrame(
        {
            "start_time": apply_utc_offset(start_time, offset_series),
            "end_time": apply_utc_offset(end_time, offset_series),
            "step_count": numeric_or_nan(df, count_col),
            "calorie": numeric_or_nan(df, calorie_col),
        }
    )
    out = out.dropna(subset=["start_time"]).copy()
    if "end_time" not in out.columns or out["end_time"].isna().all():
        out["end_time"] = out["start_time"]

    info.update(
        {
            "start_col": start_col or "",
            "end_col": end_col or "",
            "time_offset_col": offset_col or "",
            "steps_col": count_col or "",
            "calorie_col": calorie_col or "",
            "rows": len(out),
        }
    )
    return out, info


def build_timing_features(sleep_start_datetime: pd.Timestamp) -> dict:
    sleep_start_date = sleep_start_datetime.normalize()
    pre_sleep_window_hours = (sleep_start_datetime - sleep_start_date).total_seconds() / 3600

    sleep_start_hour = (
        sleep_start_datetime.hour
        + sleep_start_datetime.minute / 60
        + sleep_start_datetime.second / 3600
    )

    dayofweek = sleep_start_datetime.dayofweek
    month = sleep_start_datetime.month

    return {
        "pre_sleep_window_hours": pre_sleep_window_hours,
        "sleep_start_hour": sleep_start_hour,
        "sleep_start_dayofweek_sin": np.sin(2 * np.pi * dayofweek / 7),
        "sleep_start_dayofweek_cos": np.cos(2 * np.pi * dayofweek / 7),
        "sleep_start_month_sin": np.sin(2 * np.pi * month / 12),
        "sleep_start_month_cos": np.cos(2 * np.pi * month / 12),
    }


def aggregate_pre_sleep_activity(
    activity_df: pd.DataFrame,
    sleep_start_datetime: pd.Timestamp,
    observation_end_datetime: pd.Timestamp | None = None,
) -> dict:
    empty = {
        "steps_pre_sleep_sum": np.nan,
        "steps_pre_sleep_record_count": 0,
        "steps_pre_sleep_active_record_count": 0,
        "steps_pre_sleep_last_3h_sum": np.nan,
        "steps_pre_sleep_last_1h_sum": np.nan,
        "calories_pre_sleep_sum": np.nan,
        "calories_pre_sleep_record_count": 0,
        "calories_pre_sleep_last_3h_sum": np.nan,
        "calories_pre_sleep_last_1h_sum": np.nan,
    }
    if activity_df.empty:
        return empty

    start_dt = sleep_start_datetime.normalize()
    end_dt = observation_end_datetime if observation_end_datetime is not None else sleep_start_datetime
    end_dt = min(pd.Timestamp(end_dt), sleep_start_datetime)
    mask = (activity_df["start_time"] >= start_dt) & (activity_df["start_time"] < end_dt)
    window = activity_df.loc[mask].copy()
    if window.empty:
        return empty

    last_3h = window[window["start_time"] >= sleep_start_datetime - pd.Timedelta(hours=3)]
    last_1h = window[window["start_time"] >= sleep_start_datetime - pd.Timedelta(hours=1)]

    step_values = window["step_count"].dropna()
    calorie_values = window["calorie"].dropna()
    last_3h_steps = last_3h["step_count"].dropna()
    last_1h_steps = last_1h["step_count"].dropna()
    last_3h_calories = last_3h["calorie"].dropna()
    last_1h_calories = last_1h["calorie"].dropna()

    return {
        "steps_pre_sleep_sum": float(step_values.sum()) if len(step_values) else np.nan,
        "steps_pre_sleep_record_count": int(len(step_values)),
        "steps_pre_sleep_active_record_count": int((step_values > 0).sum()) if len(step_values) else 0,
        "steps_pre_sleep_last_3h_sum": float(last_3h_steps.sum()) if len(last_3h_steps) else np.nan,
        "steps_pre_sleep_last_1h_sum": float(last_1h_steps.sum()) if len(last_1h_steps) else np.nan,
        "calories_pre_sleep_sum": float(calorie_values.sum()) if len(calorie_values) else np.nan,
        "calories_pre_sleep_record_count": int(len(calorie_values)),
        "calories_pre_sleep_last_3h_sum": float(last_3h_calories.sum()) if len(last_3h_calories) else np.nan,
        "calories_pre_sleep_last_1h_sum": float(last_1h_calories.sum()) if len(last_1h_calories) else np.nan,
    }


def aggregate_heart_rate(
    hr_df: pd.DataFrame,
    sleep_start_datetime: pd.Timestamp,
    observation_end_datetime: pd.Timestamp | None = None,
) -> dict:
    if hr_df.empty:
        return {
            "heart_rate_pre_sleep_mean": np.nan,
            "heart_rate_pre_sleep_std": np.nan,
            "heart_rate_pre_sleep_min": np.nan,
            "heart_rate_pre_sleep_max": np.nan,
            "heart_rate_pre_sleep_record_count": 0,
            "heart_rate_pre_sleep_mean_confidence": np.nan,
            "heart_rate_pre_sleep_last_3h_mean": np.nan,
            "heart_rate_pre_sleep_last_1h_mean": np.nan,
            "heart_rate_pre_sleep_median": np.nan,
        }

    start_dt = sleep_start_datetime.normalize()
    end_dt = observation_end_datetime if observation_end_datetime is not None else sleep_start_datetime
    end_dt = min(pd.Timestamp(end_dt), sleep_start_datetime)
    mask = (hr_df["start_time"] >= start_dt) & (hr_df["start_time"] < end_dt)
    values = hr_df.loc[mask, "heart_rate"].dropna()

    last_3h_mask = mask & (hr_df["start_time"] >= sleep_start_datetime - pd.Timedelta(hours=3))
    last_1h_mask = mask & (hr_df["start_time"] >= sleep_start_datetime - pd.Timedelta(hours=1))
    last_3h_values = hr_df.loc[last_3h_mask, "heart_rate"].dropna()
    last_1h_values = hr_df.loc[last_1h_mask, "heart_rate"].dropna()

    if len(values) == 0:
        return {
            "heart_rate_pre_sleep_mean": np.nan,
            "heart_rate_pre_sleep_std": np.nan,
            "heart_rate_pre_sleep_min": np.nan,
            "heart_rate_pre_sleep_max": np.nan,
            "heart_rate_pre_sleep_record_count": 0,
            "heart_rate_pre_sleep_mean_confidence": np.nan,
            "heart_rate_pre_sleep_last_3h_mean": np.nan,
            "heart_rate_pre_sleep_last_1h_mean": np.nan,
            "heart_rate_pre_sleep_median": np.nan,
        }

    return {
        "heart_rate_pre_sleep_mean": float(values.mean()),
        "heart_rate_pre_sleep_std": float(values.std(ddof=0)),
        "heart_rate_pre_sleep_min": float(values.min()),
        "heart_rate_pre_sleep_max": float(values.max()),
        "heart_rate_pre_sleep_record_count": int(len(values)),
        "heart_rate_pre_sleep_mean_confidence": np.nan,
        "heart_rate_pre_sleep_last_3h_mean": float(last_3h_values.mean()) if len(last_3h_values) else np.nan,
        "heart_rate_pre_sleep_last_1h_mean": float(last_1h_values.mean()) if len(last_1h_values) else np.nan,
        "heart_rate_pre_sleep_median": float(values.median()),
    }


def build_row(
    episode_row: pd.Series,
    raw_features: list[str],
    hr_df: pd.DataFrame,
    activity_df: pd.DataFrame,
    daily_df: pd.DataFrame,
) -> dict:
    sleep_start_datetime = pd.to_datetime(episode_row["sleep_start_datetime"])
    if "prediction_cutoff_datetime" in episode_row and pd.notna(episode_row["prediction_cutoff_datetime"]):
        prediction_cutoff_datetime = pd.to_datetime(episode_row["prediction_cutoff_datetime"])
    else:
        prediction_cutoff_datetime = sleep_start_datetime
    previous_day = sleep_start_datetime.normalize() - pd.Timedelta(days=1)

    output = {
        "sleep_episode_id": episode_row["sleep_episode_id"],
        ID_COL: episode_row[ID_COL],
        "sleep_start_datetime": sleep_start_datetime,
        "prediction_cutoff_datetime": prediction_cutoff_datetime,
    }

    output.update(aggregate_pre_sleep_activity(activity_df, sleep_start_datetime, prediction_cutoff_datetime))
    output.update(aggregate_heart_rate(hr_df, sleep_start_datetime, prediction_cutoff_datetime))
    output.update(build_timing_features(sleep_start_datetime))

    previous_match = daily_df[daily_df["calendar_date"] == previous_day]
    if len(previous_match):
        daily_row = previous_match.iloc[0]
        for feature in [
            "previous_day_lightly_active_minutes_sum",
            "previous_day_moderately_active_minutes_sum",
            "previous_day_sedentary_minutes_sum",
            "previous_day_very_active_minutes_sum",
            "previous_day_steps_sum",
            "previous_day_steps_record_count",
            "previous_day_calories_sum",
            "previous_day_calories_record_count",
        ]:
            output[feature] = daily_row[feature] if feature in daily_row.index else np.nan
    else:
        for feature in [
            "previous_day_lightly_active_minutes_sum",
            "previous_day_moderately_active_minutes_sum",
            "previous_day_sedentary_minutes_sum",
            "previous_day_very_active_minutes_sum",
            "previous_day_steps_sum",
            "previous_day_steps_record_count",
            "previous_day_calories_sum",
            "previous_day_calories_record_count",
        ]:
            output[feature] = np.nan

    # Resting HR fields are not mapped in the first Samsung adapter version.
    output["previous_day_resting_hr_resting_heart_rate_mean"] = np.nan
    output["previous_day_resting_hr_error_mean"] = np.nan
    output["previous_day_resting_hr_record_count"] = np.nan

    for feature in raw_features:
        if feature.endswith("_missing_ind"):
            base_feature = feature.replace("_missing_ind", "")
            output[feature] = int(pd.isna(output.get(base_feature, np.nan)))

    for feature in raw_features:
        if feature not in output:
            output[feature] = np.nan

    return output


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--episodes", default=str(SLEEP_EPISODE_PATH))
    parser.add_argument("--output", default=str(OUTPUT_PATH))
    parser.add_argument("--mapping-report", default=str(MAPPING_REPORT_PATH))
    parser.add_argument("--summary", default=str(SUMMARY_PATH))
    parser.add_argument("--report", default=str(REPORT_PATH))
    args = parser.parse_args()

    sleep_episode_path = Path(args.episodes)
    output_path = Path(args.output)
    mapping_report_path = Path(args.mapping_report)
    summary_path = Path(args.summary)
    report_path = Path(args.report)

    manifest = load_manifest()
    raw_features = manifest["raw_feature_order"]

    episodes_df = pd.read_csv(sleep_episode_path, encoding="utf-8-sig")
    episodes_df["sleep_start_datetime"] = pd.to_datetime(episodes_df["sleep_start_datetime"])

    hr_df, hr_info = prepare_heart_rate_table()
    activity_df, activity_info = prepare_intraday_activity_table()
    daily_df, daily_reports = prepare_daily_activity_table()

    if not daily_df.empty:
        daily_df["calendar_date"] = pd.to_datetime(daily_df["calendar_date"]).dt.normalize()

    rows = []
    total = len(episodes_df)
    for index, (_, episode_row) in enumerate(episodes_df.iterrows(), start=1):
        rows.append(
            build_row(
                episode_row=episode_row,
                raw_features=raw_features,
                hr_df=hr_df,
                activity_df=activity_df,
                daily_df=daily_df,
            )
        )
        if index == 1 or index % 100 == 0 or index == total:
            print(f"{index}/{total} episodes processed")

    output_df = pd.DataFrame(rows)
    passthrough_columns = [
        "sleep_episode_id",
        ID_COL,
        "sleep_start_datetime",
        "prediction_cutoff_datetime",
    ]
    output_df = output_df[passthrough_columns + raw_features]
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_df.to_csv(output_path, index=False, encoding="utf-8-sig")

    mapping_rows = [
        {
            "source": "heart_rate",
            **hr_info,
        },
        {
            "source": "pedometer_step_count",
            **activity_info,
        }
    ]
    mapping_rows.extend(daily_reports)
    mapping_df = pd.DataFrame(mapping_rows)
    mapping_report_path.parent.mkdir(parents=True, exist_ok=True)
    mapping_df.to_csv(mapping_report_path, index=False, encoding="utf-8-sig")

    feature_summary_rows = []
    for feature in raw_features:
        feature_summary_rows.append(
            {
                "feature": feature,
                "non_missing_count": int(output_df[feature].notna().sum()),
                "missing_count": int(output_df[feature].isna().sum()),
                "non_missing_ratio": float(output_df[feature].notna().mean()),
            }
        )
    summary_df = pd.DataFrame(feature_summary_rows)
    summary_path.parent.mkdir(parents=True, exist_ok=True)
    summary_df.to_csv(summary_path, index=False, encoding="utf-8-sig")

    report_lines = [
        "# Samsung Pre-Sleep Stage 1 Feature Build Summary",
        "",
        "## Purpose",
        "",
        "Build Samsung Health raw Stage 1 features compatible with the selected strict pre-sleep inference contract.",
        "",
        "## Inputs",
        "",
        "```text",
        str(sleep_episode_path.relative_to(PROJECT_ROOT)),
        str(MANIFEST_PATH.relative_to(PROJECT_ROOT)),
        "```",
        "",
        "## Outputs",
        "",
        "```text",
        str(output_path.relative_to(PROJECT_ROOT)),
        str(mapping_report_path.relative_to(PROJECT_ROOT)),
        str(summary_path.relative_to(PROJECT_ROOT)),
        "```",
        "",
        "## Contract",
        "",
        f"- Raw Stage 1 features: {len(raw_features)}",
        f"- Output rows: {len(output_df)}",
        f"- Output columns: {len(output_df.columns)}",
        "",
        "## Mapping Caveats",
        "",
        "- This first Samsung adapter prioritizes inference-contract compatibility.",
        "- Samsung sleep episodes come from sleep_stage-derived episodes.",
        "- Pre-sleep heart-rate features are mapped when heart-rate timestamps are available.",
        "- Previous-day steps/calories/activity are mapped from Samsung daily summaries when available.",
        "- Pre-sleep step and calorie features are mapped from Samsung pedometer step-count intervals when available.",
        "- Fitbit-style activity intensity buckets remain incomplete in this adapter.",
        "- Resting-HR fields are left missing and handled by the existing imputer/missing indicators.",
        "",
    ]
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text("\n".join(report_lines), encoding="utf-8")

    print("raw Stage 1 features:", output_path)
    print("mapping report:", mapping_report_path)
    print("feature summary:", summary_path)
    print("report:", report_path)
    print("rows:", len(output_df))
    print("columns:", len(output_df.columns))
    print("raw features:", len(raw_features))


if __name__ == "__main__":
    main()
