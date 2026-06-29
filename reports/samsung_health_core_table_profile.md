# Samsung Health Core Table Profile

## Purpose

Profile the Samsung Health core tables needed for strict pre-sleep inference mapping.

This profiling step does not run model inference, validation evaluation, or training.

## Core Table Summary

| dataset_key | exists | rows | columns | file_path |
|---|---:|---:|---:|---|
| sleep | True | 1698 | 62 | docs\samsunghealth\com.samsung.shealth.sleep.20260629163038.csv |
| sleep_combined | True | 48 | 55 | docs\samsunghealth\com.samsung.shealth.sleep_combined.20260629163038.csv |
| sleep_stage | True | 92744 | 13 | docs\samsunghealth\com.samsung.health.sleep_stage.20260629163038.csv |
| heart_rate | True | 86140 | 21 | docs\samsunghealth\com.samsung.shealth.tracker.heart_rate.20260629163038.csv |
| pedometer_day_summary | True | 6658 | 21 | docs\samsunghealth\com.samsung.shealth.tracker.pedometer_day_summary.20260629163038.csv |
| pedometer_step_count | True | 7237 | 18 | docs\samsunghealth\com.samsung.shealth.tracker.pedometer_step_count.20260629163038.csv |
| activity_day_summary | True | 3087 | 33 | docs\samsunghealth\com.samsung.shealth.activity.day_summary.20260629163038.csv |
| step_daily_trend | True | 6658 | 13 | docs\samsunghealth\com.samsung.shealth.step_daily_trend.20260629163038.csv |
| calories_burned_details | True | 3088 | 17 | docs\samsunghealth\com.samsung.shealth.calories_burned.details.20260629163038.csv |

## Date Ranges

| dataset_key | column | parsed_count | min | max |
|---|---|---:|---|---|
| sleep | original_bed_time | 354 | 1970-01-01 00:00:00.082800 | 1970-01-01 00:00:00.082800 |
| sleep | original_wake_up_time | 1640 | 1970-01-01 00:00:00 | 1970-01-01 00:00:00.000000100 |
| sleep_combined | start_time | 48 | 1970-01-01 00:00:00 | 1970-01-01 00:00:00.000000099 |
| sleep_combined | end_time | 0 |  |  |
| sleep_combined | create_time | 0 |  |  |
| sleep_combined | update_time | 7 | 1970-01-01 00:00:00 | 1970-01-01 00:00:00 |
| sleep_combined | original_bed_time | 23 | 1970-01-01 00:00:00.001800 | 1970-01-01 00:00:00.082800 |
| sleep_combined | original_wake_up_time | 0 |  |  |
| sleep_stage | start_time | 0 |  |  |
| sleep_stage | end_time | 0 |  |  |
| sleep_stage | create_time | 92744 | 1970-01-01 00:00:00.000040001 | 1970-01-01 00:00:00.000040004 |
| sleep_stage | update_time | 92744 | 2021-07-29 18:44:14 | 2026-06-27 02:11:11.563000 |
| pedometer_day_summary | day_time | 0 |  |  |
| pedometer_day_summary | create_time | 0 |  |  |
| pedometer_day_summary | update_time | 0 |  |  |
| activity_day_summary | day_time | 0 |  |  |
| activity_day_summary | create_time | 943 | 1970-01-01 00:00:00 | 1970-01-01 00:00:00.000000070 |
| activity_day_summary | update_time | 943 | 1970-01-01 00:00:00.000000010 | 1970-01-01 00:00:00.000000010 |
| step_daily_trend | day_time | 0 |  |  |
| step_daily_trend | create_time | 0 |  |  |
| step_daily_trend | update_time | 6658 | 2025-08-01 11:26:10.094000 | 2026-06-28 15:33:51.907000 |

## Key Numeric Summaries

| dataset_key | column | count | mean | min | median | max |
|---|---|---:|---:|---:|---:|---:|
| sleep | efficiency | 1640 | 64.5957 | 9.0000 | 65.0000 | 99.0000 |
| sleep | sleep_score | 1640 | 370.4415 | 15.0000 | 346.5000 | 1065.0000 |
| sleep | sleep_duration | 532 | 1.7274 | 1.0000 | 2.0000 | 2.0000 |
| sleep_combined | efficiency | 48 | 62.5208 | 16.0000 | 62.5000 | 88.0000 |
| sleep_combined | sleep_duration | 23 | 1.8261 | 1.0000 | 2.0000 | 2.0000 |
| pedometer_day_summary | active_time | 6658 | 9999.3992 | 6000.0000 | 10000.0000 | 10000.0000 |
| pedometer_day_summary | calorie | 6658 | 5744.5153 | 6.0000 | 5364.5000 | 34974.0000 |
| pedometer_step_count | duration | 7237 | 4.0000 | 4.0000 | 4.0000 | 4.0000 |
| activity_day_summary | step_count | 943 | 300.0000 | 300.0000 | 300.0000 | 300.0000 |
| activity_day_summary | active_time | 1823 | 90.0000 | 90.0000 | 90.0000 | 90.0000 |

## Mapping Readiness

- Sleep episodes: check `sleep` start/end and sleep_score coverage.
- Heart rate: check `heart_rate` start/end and heart_rate coverage.
- Steps/calories: check step/activity day summary and step count coverage.
- Next adapter should create Samsung sleep episodes first, then raw Stage 1 features.

## Output Files

```text
data/processed/samsung_health/core_table_profile/samsung_health_core_table_summary.csv
data/processed/samsung_health/core_table_profile/samsung_health_core_date_summary.csv
data/processed/samsung_health/core_table_profile/samsung_health_core_numeric_summary.csv
data/processed/samsung_health/core_table_profile/samsung_health_core_missing_summary.csv
```
