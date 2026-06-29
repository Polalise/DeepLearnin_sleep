# Samsung Health Sleep Episode Table Summary

## Purpose

Create a sleep episode table from Samsung Health sleep export for strict pre-sleep inference preparation.

## Source

```text
docs\samsunghealth\com.samsung.shealth.sleep.20260629163038.csv
```

## Output

```text
data\processed\samsung_health\pre_sleep_stage1\samsung_sleep_episodes.csv
```

## Summary

| Metric | Value |
|---|---:|
| source_file | docs\samsunghealth\com.samsung.shealth.sleep.20260629163038.csv |
| source_rows | 1698 |
| valid_episode_rows | 28 |
| invalid_or_filtered_rows | 1670 |
| start_column | com.samsung.health.sleep.pkg_name |
| end_column | com.samsung.health.sleep.update_time |
| datauuid_column | com.samsung.health.sleep.end_time |
| sleep_score_non_missing | 6 |
| sleep_score_missing | 22 |
| good_sleep_score_threshold | 80 |
| proxy_label_positive_rate | 1.0 |
| min_sleep_start_datetime | 2018-11-08 23:10:00 |
| max_sleep_start_datetime | 2025-07-05 00:43:00 |
| median_duration_hours_from_time | 3.8422252777777777 |

## Label Caveat

`samsung_good_sleep_label` is a proxy label derived from Samsung `sleep_score`.
It is not identical to the original LifeSnaps `good_sleep_label`.

## Column Mapping Note

This export required fallback column mapping for sleep start/end/datauuid because the Samsung sleep CSV data rows contain one more field than the header row and the tail fields are shifted.
