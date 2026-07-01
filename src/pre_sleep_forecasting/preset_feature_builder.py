from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from math import cos, pi, sin
from pathlib import Path
import json

import numpy as np
import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_MANIFEST_PATH = (
    PROJECT_ROOT
    / "data"
    / "processed"
    / "pre_sleep_forecasting"
    / "design_c_stage1"
    / "inference_package"
    / "pre_sleep_inference_manifest.json"
)

PASSTHROUGH_COLUMNS = [
    "sleep_episode_id",
    "participant_object_id",
    "sleep_start_datetime",
    "prediction_cutoff_datetime",
]

ACTIVITY_MULTIPLIERS = {
    "전날보다 증가": 1.20,
    "전날과 비슷": 1.00,
    "전날보다 감소": 0.80,
    "모름": np.nan,
}

CALORIE_MULTIPLIERS = {
    "평소보다 높음": 1.15,
    "평소와 비슷": 1.00,
    "평소보다 낮음": 0.85,
    "모름": np.nan,
}

HEART_RATE_DELTAS = {
    "평소보다 높음": 7.0,
    "평소와 비슷": 0.0,
    "평소보다 낮음": -5.0,
    "모름": np.nan,
}


@dataclass(frozen=True)
class QuickPresetInput:
    sleep_start_datetime: datetime
    previous_day_steps_sum: float | None
    pre_sleep_steps_sum: float | None
    pre_sleep_last_3h_steps_sum: float | None
    pre_sleep_last_1h_steps_sum: float | None
    baseline_daily_calories: float | None
    baseline_resting_heart_rate: float | None
    baseline_active_minutes: float | None
    activity_preset: str
    calorie_preset: str
    heart_rate_preset: str
    previous_sleep_preset: str


def load_raw_feature_order(manifest_path: Path | None = None) -> list[str]:
    path = manifest_path or DEFAULT_MANIFEST_PATH
    manifest = json.loads(Path(path).read_text(encoding="utf-8"))
    return list(manifest["raw_feature_order"])


def build_quick_preset_features(
    preset_input: QuickPresetInput,
    manifest_path: Path | None = None,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    raw_features = load_raw_feature_order(manifest_path)
    row = {feature: np.nan for feature in raw_features}
    sources: dict[str, str] = {}

    sleep_start = pd.Timestamp(preset_input.sleep_start_datetime).to_pydatetime()
    episode_id = f"quick_preset__{sleep_start.strftime('%Y%m%d%H%M%S')}"

    passthrough = {
        "sleep_episode_id": episode_id,
        "participant_object_id": "quick_preset_user",
        "sleep_start_datetime": sleep_start.strftime("%Y-%m-%d %H:%M:%S"),
        "prediction_cutoff_datetime": sleep_start.strftime("%Y-%m-%d %H:%M:%S"),
    }

    def set_feature(feature: str, value: float | int | None, source: str) -> None:
        if feature not in row:
            return
        row[feature] = np.nan if value is None else value
        sources[feature] = source

    def finite(value: float | int | None) -> bool:
        return value is not None and pd.notna(value)

    sleep_hour = sleep_start.hour + sleep_start.minute / 60 + sleep_start.second / 3600
    dayofweek = sleep_start.weekday()
    month = sleep_start.month
    pre_sleep_window_hours = sleep_hour

    set_feature("pre_sleep_window_hours", pre_sleep_window_hours, "time_input")
    set_feature("sleep_start_hour", sleep_hour, "time_input")
    set_feature("sleep_start_dayofweek", dayofweek, "time_input")
    set_feature("sleep_start_month", month, "time_input")
    set_feature("sleep_start_dayofweek_sin", sin(2 * pi * dayofweek / 7), "time_input")
    set_feature("sleep_start_dayofweek_cos", cos(2 * pi * dayofweek / 7), "time_input")
    set_feature("sleep_start_month_sin", sin(2 * pi * month / 12), "time_input")
    set_feature("sleep_start_month_cos", cos(2 * pi * month / 12), "time_input")

    previous_day_steps = preset_input.previous_day_steps_sum
    pre_sleep_steps = preset_input.pre_sleep_steps_sum
    last_3h_steps = preset_input.pre_sleep_last_3h_steps_sum
    last_1h_steps = preset_input.pre_sleep_last_1h_steps_sum

    set_feature("previous_day_steps_sum", previous_day_steps, "user_numeric_input")
    set_feature("previous_day_steps_record_count", 1 if finite(previous_day_steps) else None, "derived_count")
    set_feature("steps_pre_sleep_sum", pre_sleep_steps, "user_numeric_input")
    set_feature("steps_pre_sleep_record_count", 1 if finite(pre_sleep_steps) else None, "derived_count")
    set_feature(
        "steps_pre_sleep_active_record_count",
        1 if finite(pre_sleep_steps) and float(pre_sleep_steps) > 0 else None,
        "derived_count",
    )
    set_feature("steps_pre_sleep_last_3h_sum", last_3h_steps, "user_numeric_input")
    set_feature("steps_pre_sleep_last_1h_sum", last_1h_steps, "user_numeric_input")

    calorie_multiplier = CALORIE_MULTIPLIERS.get(preset_input.calorie_preset, np.nan)
    if finite(preset_input.baseline_daily_calories) and pd.notna(calorie_multiplier):
        previous_calories = float(preset_input.baseline_daily_calories) * float(calorie_multiplier)
    else:
        previous_calories = None

    estimated_pre_sleep_calories = None
    estimated_last_3h_calories = None
    estimated_last_1h_calories = None
    if finite(pre_sleep_steps):
        estimated_pre_sleep_calories = float(pre_sleep_steps) * 0.04
    if finite(last_3h_steps):
        estimated_last_3h_calories = float(last_3h_steps) * 0.04
    if finite(last_1h_steps):
        estimated_last_1h_calories = float(last_1h_steps) * 0.04

    set_feature("previous_day_calories_sum", previous_calories, "preset_estimate")
    set_feature("previous_day_calories_record_count", 1 if finite(previous_calories) else None, "derived_count")
    set_feature("calories_pre_sleep_sum", estimated_pre_sleep_calories, "step_based_estimate")
    set_feature(
        "calories_pre_sleep_record_count",
        1 if finite(estimated_pre_sleep_calories) else None,
        "derived_count",
    )
    set_feature("calories_pre_sleep_last_3h_sum", estimated_last_3h_calories, "step_based_estimate")
    set_feature("calories_pre_sleep_last_1h_sum", estimated_last_1h_calories, "step_based_estimate")

    activity_multiplier = ACTIVITY_MULTIPLIERS.get(preset_input.activity_preset, np.nan)
    if finite(preset_input.baseline_active_minutes) and pd.notna(activity_multiplier):
        active_minutes = float(preset_input.baseline_active_minutes) * float(activity_multiplier)
    else:
        active_minutes = None

    set_feature("previous_day_lightly_active_minutes_sum", active_minutes, "preset_estimate")
    set_feature("previous_day_moderately_active_minutes_sum", None, "missing_imputed")
    set_feature("previous_day_very_active_minutes_sum", None, "missing_imputed")
    set_feature("previous_day_sedentary_minutes_sum", None, "missing_imputed")

    heart_rate_delta = HEART_RATE_DELTAS.get(preset_input.heart_rate_preset, np.nan)
    if finite(preset_input.baseline_resting_heart_rate) and pd.notna(heart_rate_delta):
        hr_mean = float(preset_input.baseline_resting_heart_rate) + float(heart_rate_delta)
    else:
        hr_mean = None

    set_feature("previous_day_resting_hr_resting_heart_rate_mean", preset_input.baseline_resting_heart_rate, "user_numeric_input")
    set_feature("previous_day_resting_hr_error_mean", None, "missing_imputed")
    set_feature("previous_day_resting_hr_record_count", 1 if finite(preset_input.baseline_resting_heart_rate) else None, "derived_count")
    set_feature("heart_rate_pre_sleep_mean", hr_mean, "preset_estimate")
    set_feature("heart_rate_pre_sleep_median", hr_mean, "preset_estimate")
    set_feature("heart_rate_pre_sleep_std", 4.0 if finite(hr_mean) else None, "preset_estimate")
    set_feature("heart_rate_pre_sleep_min", float(hr_mean) - 5.0 if finite(hr_mean) else None, "preset_estimate")
    set_feature("heart_rate_pre_sleep_max", float(hr_mean) + 5.0 if finite(hr_mean) else None, "preset_estimate")
    set_feature("heart_rate_pre_sleep_record_count", 1 if finite(hr_mean) else None, "derived_count")
    set_feature("heart_rate_pre_sleep_mean_confidence", None, "missing_imputed")
    set_feature("heart_rate_pre_sleep_last_3h_mean", hr_mean, "preset_estimate")
    set_feature("heart_rate_pre_sleep_last_1h_mean", hr_mean, "preset_estimate")

    for feature in raw_features:
        if not feature.endswith("_missing_ind"):
            continue
        base_feature = feature[: -len("_missing_ind")]
        missing_value = 1 if pd.isna(row.get(base_feature, np.nan)) else 0
        row[feature] = missing_value
        sources[feature] = "derived_missing_indicator"

    feature_df = pd.DataFrame([{**passthrough, **row}], columns=PASSTHROUGH_COLUMNS + raw_features)
    source_rows = []
    for feature in raw_features:
        value = row[feature]
        source = sources.get(feature, "missing_imputed" if pd.isna(value) else "derived")
        source_rows.append(
            {
                "feature": feature,
                "source": source,
                "value": value,
                "is_missing_before_imputer": bool(pd.isna(value)),
            }
        )

    source_rows.append(
        {
            "feature": "previous_sleep_preset",
            "source": "not_used_by_design_c_stage1_contract",
            "value": preset_input.previous_sleep_preset,
            "is_missing_before_imputer": False,
        }
    )
    source_df = pd.DataFrame(source_rows)
    return feature_df, source_df
