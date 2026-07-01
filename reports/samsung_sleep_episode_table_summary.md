# Samsung Health Sleep Episode Table Summary

## Purpose

Create a sleep episode table from Samsung Health sleep_stage export for strict pre-sleep inference preparation.

## Source

```text
docs\samsunghealth\com.samsung.health.sleep_stage.20260629163038.csv
```

## Output

```text
data\processed\samsung_health\pre_sleep_stage1\samsung_sleep_episodes.csv
```

## Summary

| Metric | Value |
|---|---:|
| source_file | docs\samsunghealth\com.samsung.health.sleep_stage.20260629163038.csv |
| source_stage_rows | 92744 |
| valid_stage_rows | 92744 |
| raw_episode_count | 1642 |
| valid_episode_rows | 1493 |
| invalid_or_filtered_episode_rows | 149 |
| min_sleep_start_datetime | 2021-07-30 03:40:14 |
| max_sleep_start_datetime | 2026-06-27 03:39:00 |
| median_duration_hours | 6.246388888888889 |
| mean_duration_hours | 6.788186565825706 |
| cross_midnight_rate | 0.08908238446081715 |
| sleep_score_joined | False |

## Column Mapping Note

This Samsung Health export has shifted sleep_stage tail fields.

Observed mapping:

```text
source_sleep_id = start_time
stage_start_datetime = create_sh_ver
stage_end_datetime = update_time
samsung_stage_code = create_time
stage_utc_offset = stage
source_stage_datauuid = end_time
```

Stage start/end datetimes are adjusted by the observed UTC offset before episode aggregation.

## Label Caveat

`samsung_sleep_score` and `samsung_good_sleep_label` are not joined in this table yet.
A Samsung sleep-score proxy label can be added later by linking to the Samsung sleep table.
