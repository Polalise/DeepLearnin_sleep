# Samsung Pre-Sleep Activity Coverage Diagnostic

## Purpose

Diagnose whether Samsung interval activity sources can improve pre-sleep step/calorie coverage for the Fitbit-compatible adapter.

## Inputs

```text
data\processed\samsung_health\pre_sleep_stage1\samsung_sleep_episodes.csv
C:\workSpace\DeepLearnin_sleep\docs\samsunghealth\com.samsung.shealth.tracker.pedometer_step_count.20260629163038.csv
C:\workSpace\DeepLearnin_sleep\docs\samsunghealth\com.samsung.shealth.calories_burned.details.20260629163038.csv
```

## Outputs

```text
data\processed\samsung_health\pre_sleep_stage1\diagnostics\samsung_presleep_activity_window_coverage_summary.csv
data\processed\samsung_health\pre_sleep_stage1\diagnostics\samsung_presleep_activity_episode_window_diagnostics.csv
data\processed\samsung_health\pre_sleep_stage1\diagnostics\samsung_presleep_activity_source_profile.csv
```

## Windows Compared

- midnight-to-sleep-start
- last 6h before sleep start
- last 3h before sleep start
- last 1h before sleep start

## Source Caveat

Use interval timestamped sources for same-day pre-sleep aggregation. Daily totals should remain previous-day only unless timestamp granularity is confirmed.

## Result Summary

| window | episodes | episodes with records | steps coverage | calorie coverage |
|---|---:|---:|---:|---:|
| last 1h | 1493 | 10 | 0.0067 | 0.0067 |
| last 3h | 1493 | 14 | 0.0094 | 0.0094 |
| last 6h | 1493 | 14 | 0.0094 | 0.0094 |
| midnight-to-sleep-start | 1493 | 14 | 0.0094 | 0.0094 |

## Source Availability

- `pedometer_step_count` is available but only covers `2026-05-25 00:00:00` to `2026-06-29 15:39:00`.
- Samsung sleep episodes span `2021-07-30` to `2026-06-27`.
- Therefore most sleep episodes have no overlapping interval step/calorie source rows.
- `calories_burned.details` has daily/detail calorie rows, but it should not be used for same-day pre-sleep aggregation unless its timestamp granularity is confirmed, because daily totals may include post-sleep-start information.

## Interpretation

The sparse pre-sleep step/calorie coverage is not primarily a window-definition problem. Coverage remains below 1% for midnight-to-sleep-start and fixed 6h/3h/1h windows.

The limiting factor is source availability: interval step-count data are present only for a short recent date range, while the sleep episode table spans multiple years.

## Recommendation

- Keep previous-day daily activity features.
- Keep pre-sleep heart-rate features.
- Keep pre-sleep step/calorie features as low-confidence and mostly missing for the current Samsung export.
- Do not fill same-day pre-sleep step/calorie from daily totals because of leakage risk.
- Treat fixed-window pre-sleep activity recovery as future work requiring richer interval Samsung export data.
