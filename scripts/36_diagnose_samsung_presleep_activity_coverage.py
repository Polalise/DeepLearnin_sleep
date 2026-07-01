from __future__ import annotations

from pathlib import Path
import csv
import os

import numpy as np
import pandas as pd


PROJECT_ROOT = Path(os.environ.get("PROJECT_ROOT", Path(__file__).resolve().parents[1]))

SAMSUNG_DIR_CANDIDATES = [
    PROJECT_ROOT / "docs" / "samsung",
    PROJECT_ROOT / "docs" / "samsunghealth",
    PROJECT_ROOT / "docs",
    PROJECT_ROOT / "data" / "raw" / "samsung_health",
]

STAGE1_DIR = PROJECT_ROOT / "data" / "processed" / "samsung_health" / "pre_sleep_stage1"
EPISODE_PATH = STAGE1_DIR / "samsung_sleep_episodes.csv"

PEDOMETER_STEP_COUNT_DATASET = "com.samsung.shealth.tracker.pedometer_step_count"
CALORIES_BURNED_DETAILS_DATASET = "com.samsung.shealth.calories_burned.details"

OUTPUT_DIR = STAGE1_DIR / "diagnostics"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

WINDOW_SUMMARY_PATH = OUTPUT_DIR / "samsung_presleep_activity_window_coverage_summary.csv"
EPISODE_WINDOW_PATH = OUTPUT_DIR / "samsung_presleep_activity_episode_window_diagnostics.csv"
SOURCE_PROFILE_PATH = OUTPUT_DIR / "samsung_presleep_activity_source_profile.csv"
REPORT_PATH = PROJECT_ROOT / "reports" / "samsung_presleep_activity_coverage_diagnostic.md"


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


def read_samsung_csv(path: Path) -> pd.DataFrame:
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
    return df.replace("", np.nan).infer_objects(copy=False)


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


def first_existing_column(df: pd.DataFrame, candidates: list[str]) -> str | None:
    for candidate in candidates:
        if candidate in df.columns:
            return candidate
    return None


def load_pedometer_step_count() -> tuple[pd.DataFrame, dict]:
    path = find_dataset_file(PEDOMETER_STEP_COUNT_DATASET)
    info = {"dataset": PEDOMETER_STEP_COUNT_DATASET, "path": str(path) if path else "", "available": path is not None}
    if path is None:
        return pd.DataFrame(), info

    df = read_samsung_csv(path)
    start_col = first_existing_column(
        df,
        [
            "com.samsung.health.step_count.start_time",
            "step_count.start_time",
            "start_time",
        ],
    )
    end_col = first_existing_column(
        df,
        [
            "com.samsung.health.step_count.end_time",
            "step_count.end_time",
            "end_time",
        ],
    )
    offset_col = first_existing_column(
        df,
        [
            "com.samsung.health.step_count.time_offset",
            "step_count.time_offset",
            "time_offset",
        ],
    )
    steps_col = first_existing_column(
        df,
        [
            "com.samsung.health.step_count.count",
            "step_count.count",
            "count",
        ],
    )
    calorie_col = first_existing_column(
        df,
        [
            "com.samsung.health.step_count.calorie",
            "step_count.calorie",
            "calorie",
        ],
    )

    start_time = parse_datetime(df[start_col]) if start_col else pd.Series(pd.NaT, index=df.index)
    end_time = parse_datetime(df[end_col]) if end_col else pd.Series(pd.NaT, index=df.index)
    offset_series = df[offset_col] if offset_col else None

    out = pd.DataFrame(
        {
            "source": "pedometer_step_count",
            "start_time": apply_utc_offset(start_time, offset_series),
            "end_time": apply_utc_offset(end_time, offset_series),
            "steps": pd.to_numeric(df[steps_col], errors="coerce") if steps_col else np.nan,
            "calories": pd.to_numeric(df[calorie_col], errors="coerce") if calorie_col else np.nan,
        }
    )
    out = out.dropna(subset=["start_time"]).copy()
    info.update(
        {
            "rows": len(out),
            "start_col": start_col or "",
            "end_col": end_col or "",
            "offset_col": offset_col or "",
            "steps_col": steps_col or "",
            "calorie_col": calorie_col or "",
            "min_start_time": str(out["start_time"].min()) if len(out) else "",
            "max_start_time": str(out["start_time"].max()) if len(out) else "",
        }
    )
    return out, info


def load_calories_burned_details_profile() -> dict:
    path = find_dataset_file(CALORIES_BURNED_DETAILS_DATASET)
    info = {
        "dataset": CALORIES_BURNED_DETAILS_DATASET,
        "path": str(path) if path else "",
        "available": path is not None,
    }
    if path is None:
        return info

    df = read_samsung_csv(path)
    day_col = first_existing_column(
        df,
        [
            "com.samsung.shealth.calories_burned.day_time",
            "calories_burned.day_time",
            "day_time",
        ],
    )
    active_calorie_col = first_existing_column(
        df,
        [
            "com.samsung.shealth.calories_burned.active_calorie",
            "calories_burned.active_calorie",
            "active_calorie",
        ],
    )
    info.update(
        {
            "rows": len(df),
            "day_col": day_col or "",
            "active_calorie_col": active_calorie_col or "",
            "day_non_missing": int(df[day_col].notna().sum()) if day_col else 0,
            "active_calorie_non_missing": int(pd.to_numeric(df[active_calorie_col], errors="coerce").notna().sum()) if active_calorie_col else 0,
            "note": "Daily/detail calorie source; use only when timestamp granularity is confirmed to avoid leakage.",
        }
    )
    return info


def aggregate_window(activity_df: pd.DataFrame, window_start: pd.Timestamp, sleep_start: pd.Timestamp) -> dict:
    mask = (activity_df["start_time"] >= window_start) & (activity_df["start_time"] < sleep_start)
    window = activity_df.loc[mask]
    steps = window["steps"].dropna()
    calories = window["calories"].dropna()
    return {
        "record_count": int(len(window)),
        "steps_record_count": int(len(steps)),
        "calorie_record_count": int(len(calories)),
        "steps_sum": float(steps.sum()) if len(steps) else np.nan,
        "calories_sum": float(calories.sum()) if len(calories) else np.nan,
    }


def main() -> None:
    episodes = pd.read_csv(EPISODE_PATH, encoding="utf-8-sig")
    episodes["sleep_start_datetime"] = pd.to_datetime(episodes["sleep_start_datetime"])

    activity_df, step_info = load_pedometer_step_count()
    calories_info = load_calories_burned_details_profile()

    source_profile = pd.DataFrame([step_info, calories_info])
    source_profile.to_csv(SOURCE_PROFILE_PATH, index=False, encoding="utf-8-sig")

    rows = []
    for _, episode in episodes.iterrows():
        sleep_start = episode["sleep_start_datetime"]
        midnight_start = sleep_start.normalize()
        fixed_6h_start = sleep_start - pd.Timedelta(hours=6)
        fixed_3h_start = sleep_start - pd.Timedelta(hours=3)
        fixed_1h_start = sleep_start - pd.Timedelta(hours=1)

        for window_name, window_start in [
            ("midnight_to_sleep_start", midnight_start),
            ("last_6h", fixed_6h_start),
            ("last_3h", fixed_3h_start),
            ("last_1h", fixed_1h_start),
        ]:
            stats = aggregate_window(activity_df, window_start, sleep_start) if not activity_df.empty else {
                "record_count": 0,
                "steps_record_count": 0,
                "calorie_record_count": 0,
                "steps_sum": np.nan,
                "calories_sum": np.nan,
            }
            rows.append(
                {
                    "sleep_episode_id": episode["sleep_episode_id"],
                    "sleep_start_datetime": sleep_start,
                    "window": window_name,
                    "window_start": window_start,
                    **stats,
                }
            )

    episode_window_df = pd.DataFrame(rows)
    episode_window_df.to_csv(EPISODE_WINDOW_PATH, index=False, encoding="utf-8-sig")

    summary_rows = []
    for window_name, group in episode_window_df.groupby("window"):
        summary_rows.append(
            {
                "window": window_name,
                "episodes": int(group["sleep_episode_id"].nunique()),
                "episodes_with_any_record": int((group["record_count"] > 0).sum()),
                "episodes_with_steps": int(group["steps_record_count"].gt(0).sum()),
                "episodes_with_calories": int(group["calorie_record_count"].gt(0).sum()),
                "steps_coverage_rate": float(group["steps_record_count"].gt(0).mean()),
                "calorie_coverage_rate": float(group["calorie_record_count"].gt(0).mean()),
                "median_record_count": float(group["record_count"].median()),
                "median_steps_sum_non_missing": float(group.loc[group["steps_record_count"].gt(0), "steps_sum"].median()) if group["steps_record_count"].gt(0).any() else np.nan,
                "median_calories_sum_non_missing": float(group.loc[group["calorie_record_count"].gt(0), "calories_sum"].median()) if group["calorie_record_count"].gt(0).any() else np.nan,
            }
        )

    window_summary = pd.DataFrame(summary_rows).sort_values("window")
    window_summary.to_csv(WINDOW_SUMMARY_PATH, index=False, encoding="utf-8-sig")

    report_lines = [
        "# Samsung Pre-Sleep Activity Coverage Diagnostic",
        "",
        "## Purpose",
        "",
        "Diagnose whether Samsung interval activity sources can improve pre-sleep step/calorie coverage for the Fitbit-compatible adapter.",
        "",
        "## Inputs",
        "",
        "```text",
        str(EPISODE_PATH.relative_to(PROJECT_ROOT)),
        step_info.get("path", ""),
        calories_info.get("path", ""),
        "```",
        "",
        "## Outputs",
        "",
        "```text",
        str(WINDOW_SUMMARY_PATH.relative_to(PROJECT_ROOT)),
        str(EPISODE_WINDOW_PATH.relative_to(PROJECT_ROOT)),
        str(SOURCE_PROFILE_PATH.relative_to(PROJECT_ROOT)),
        "```",
        "",
        "## Windows Compared",
        "",
        "- midnight-to-sleep-start",
        "- last 6h before sleep start",
        "- last 3h before sleep start",
        "- last 1h before sleep start",
        "",
        "## Source Caveat",
        "",
        "Use interval timestamped sources for same-day pre-sleep aggregation. Daily totals should remain previous-day only unless timestamp granularity is confirmed.",
        "",
    ]
    REPORT_PATH.write_text("\n".join(report_lines), encoding="utf-8")

    print("window summary:", WINDOW_SUMMARY_PATH)
    print("episode window diagnostics:", EPISODE_WINDOW_PATH)
    print("source profile:", SOURCE_PROFILE_PATH)
    print("report:", REPORT_PATH)
    print(window_summary)
    print(source_profile)


if __name__ == "__main__":
    main()
