# Samsung Health Pre-Sleep Mapping Plan

## 1. Purpose

This plan describes how to map exported Samsung Health data into the existing strict pre-sleep forecasting workflow.

Target workflow:

```text
Samsung Health export
-> sleep episode table
-> raw Design C Stage 1 pre-sleep features
-> existing median imputer
-> existing StandardScaler
-> remove 12 zero-variance features
-> final 58-feature MLP input
-> selected pre-sleep model inference
```

The current selected model remains:

```text
presleep_stage1_hp_tiny_dropout40_wd1e3_seed2027
```

## 2. Samsung Health Export Structure

The export summary files are:

```text
docs/samsunghealth_structure_summary.txt
docs/samsunghealth_file_catalog.csv
docs/samsunghealth_column_dictionary.csv
```

Important CSV parsing rule:

```text
1st row = dataset/schema metadata
2nd row = actual column names
3rd row onward = data rows
```

Therefore Samsung Health CSV files should be read with:

```python
pd.read_csv(path, skiprows=1, encoding="utf-8-sig")
```

Export summary:

- CSV files: 80
- Total CSV rows: 256,910
- Major categories:
  - sleep
  - cardiovascular/vitals
  - activity/exercise
  - nutrition
  - body/profile
  - device/settings

## 3. Core Tables For Pre-Sleep Forecasting

### Sleep Episode Tables

Primary candidates:

```text
com.samsung.shealth.sleep.20260629163038.csv
com.samsung.shealth.sleep_combined.20260629163038.csv
com.samsung.health.sleep_stage.20260629163038.csv
```

Useful columns from `com.samsung.shealth.sleep`:

```text
start_time
end_time
sleep_score
sleep_duration
efficiency
sleep_type
quality
physical_recovery
mental_recovery
factor_01 ... factor_10
```

Role:

- construct sleep episode rows,
- define `sleep_start_datetime`,
- define `sleep_end_datetime`,
- optionally define Samsung-specific `good_sleep_label` from `sleep_score`.

### Heart Rate

Primary table:

```text
com.samsung.shealth.tracker.heart_rate.20260629163038.csv
```

Useful columns:

```text
start_time
end_time
heart_rate
```

Role:

- pre-sleep heart-rate mean/std/min/max,
- record count,
- last-3h and last-1h mean,
- median heart rate.

### Steps And Activity

Primary tables:

```text
com.samsung.shealth.tracker.pedometer_day_summary.20260629163038.csv
com.samsung.shealth.tracker.pedometer_step_count.20260629163038.csv
com.samsung.shealth.activity.day_summary.20260629163038.csv
com.samsung.shealth.step_daily_trend.20260629163038.csv
```

Useful columns include:

```text
day_time
start_time
end_time
step_count
active_time
calorie
distance
```

Role:

- pre-sleep step sum,
- pre-sleep step record count,
- active step record count,
- last-3h and last-1h step sums,
- previous-day daily steps,
- previous-day activity summaries.

### Calories

Primary candidates:

```text
com.samsung.shealth.calories_burned.details.20260629163038.csv
com.samsung.shealth.activity.day_summary.20260629163038.csv
com.samsung.shealth.step_daily_trend.20260629163038.csv
com.samsung.shealth.tracker.pedometer_day_summary.20260629163038.csv
```

Role:

- pre-sleep calories sum,
- calorie record count,
- last-3h and last-1h calories,
- previous-day daily calories.

## 4. Mapping To Stage 1 Feature Contract

The existing inference contract expects 70 raw features:

```text
pre-sleep intraday features
previous-day daily features
sleep-start timing/calendar features
missing indicators
```

Expected pipeline:

```text
Samsung raw tables
-> Samsung sleep episodes
-> raw Stage 1 70 features
-> existing inference pipeline
```

### Directly Mappable

Likely direct or near-direct mappings:

```text
sleep_start_datetime
pre_sleep_window_hours
sleep_start_hour
sleep_start_dayofweek_sin
sleep_start_dayofweek_cos
sleep_start_month_sin
sleep_start_month_cos
steps_pre_sleep_sum
steps_pre_sleep_record_count
steps_pre_sleep_active_record_count
steps_pre_sleep_last_3h_sum
steps_pre_sleep_last_1h_sum
calories_pre_sleep_sum
calories_pre_sleep_record_count
calories_pre_sleep_last_3h_sum
calories_pre_sleep_last_1h_sum
heart_rate_pre_sleep_mean
heart_rate_pre_sleep_std
heart_rate_pre_sleep_min
heart_rate_pre_sleep_max
heart_rate_pre_sleep_record_count
heart_rate_pre_sleep_last_3h_mean
heart_rate_pre_sleep_last_1h_mean
heart_rate_pre_sleep_median
previous_day_steps_sum
previous_day_calories_sum
```

### Possibly Mappable With Different Semantics

These Stage 1 fields may need Samsung-specific approximations:

```text
previous_day_lightly_active_minutes_sum
previous_day_moderately_active_minutes_sum
previous_day_sedentary_minutes_sum
previous_day_very_active_minutes_sum
previous_day_resting_hr_resting_heart_rate_mean
previous_day_resting_hr_error_mean
previous_day_resting_hr_record_count
heart_rate_pre_sleep_mean_confidence
```

Recommended handling for first adapter version:

- use available Samsung daily activity summaries when possible,
- otherwise leave unmapped values as missing,
- rely on the existing train-fitted median imputer and missing indicators,
- document every approximation.

### Missing Indicators

Missing indicator features should be generated after raw numeric features are created:

```text
feature_missing_ind = 1 if feature is missing else 0
```

This must follow the existing raw Stage 1 feature order from:

```text
data/processed/pre_sleep_forecasting/design_c_stage1/inference_package/pre_sleep_inference_manifest.json
```

## 5. Samsung-Specific Label For Evaluation

The existing final model predicts LifeSnaps-derived `good_sleep_label`.

Samsung Health has `sleep_score`, but it is not the same target definition. If evaluation is desired, define a Samsung-specific label clearly, for example:

```text
samsung_good_sleep_label = 1 if sleep_score >= 80 else 0
```

This should be reported as compatibility or exploratory external validation, not a perfect label-equivalent validation.

Recommended wording:

```text
Samsung Health evaluation uses a Samsung sleep-score-derived proxy label, which is not identical to the original LifeSnaps good_sleep_label.
```

## 6. Recommended First Script

Create a core-table profiler before building the full adapter:

```text
scripts/29_profile_samsung_health_core_tables.py
```

Purpose:

- read only core Samsung Health CSVs,
- use `skiprows=1`,
- report row counts,
- report columns,
- report date ranges,
- report missingness,
- summarize sleep_score,
- summarize heart_rate,
- summarize step/calorie/activity fields.

Recommended outputs:

```text
data/processed/samsung_health/core_table_profile/
samsung_health_core_table_summary.csv
samsung_health_core_column_summary.csv
reports/samsung_health_core_table_profile.md
```

## 7. Recommended Adapter Script

After profiling confirms column semantics, create:

```text
scripts/30_build_samsung_pre_sleep_stage1_features.py
```

Recommended outputs:

```text
data/processed/samsung_health/pre_sleep_stage1/samsung_sleep_episodes.csv
data/processed/samsung_health/pre_sleep_stage1/samsung_raw_stage1_features.csv
data/processed/samsung_health/pre_sleep_stage1/samsung_predictions.csv
data/processed/samsung_health/pre_sleep_stage1/samsung_feature_mapping_report.csv
```

## 8. Validation Levels

### Level 1: Inference Compatibility

Goal:

```text
Can Samsung Health data be transformed into the 70 raw Stage 1 features and passed through the final model?
```

This does not require a label.

### Level 2: Proxy-Label Evaluation

Goal:

```text
Evaluate predictions against a Samsung sleep_score-derived label.
```

This requires explicit caveats because the label differs from LifeSnaps.

### Level 3: Stronger External Validation

Goal:

```text
Evaluate against a label definition that closely matches the original good_sleep_label.
```

This may require manual or externally defined labels and is not guaranteed from Samsung Health alone.

## 9. Main Risks

Important risks:

- Samsung sleep_score is not the original `good_sleep_label`.
- Samsung activity minutes may not map cleanly to Fitbit activity minute categories.
- Samsung heart-rate sampling frequency may differ from LifeSnaps/Fitbit.
- Missing or approximated features may cause the model to lean heavily on imputer behavior.
- This is personal single-user data, so it cannot establish broad external generalization.

## 10. Recommended Next Step

Next step:

```text
Create scripts/29_profile_samsung_health_core_tables.py
```

Do not build the full adapter until the core-table profile confirms:

- sleep episode start/end columns,
- sleep_score coverage,
- heart_rate coverage,
- step/calorie timestamp granularity,
- daily activity summary availability.
