# Samsung Sleep Score Proxy Label Join Summary

## Purpose

Join Samsung sleep-score proxy labels to sleep_stage-derived episodes and external prediction outputs.

## Inputs

```text
data\processed\samsung_health\pre_sleep_stage1\samsung_sleep_episodes.csv
data\processed\samsung_health\pre_sleep_stage1\samsung_pre_sleep_predictions.csv
docs\samsunghealth\com.samsung.shealth.sleep.20260629163038.csv
```

## Outputs

```text
data\processed\samsung_health\pre_sleep_stage1\samsung_sleep_episodes_with_proxy_labels.csv
data\processed\samsung_health\pre_sleep_stage1\samsung_pre_sleep_predictions_with_proxy_labels.csv
data\processed\samsung_health\pre_sleep_stage1\samsung_sleep_score_proxy_label_match_report.csv
data\processed\samsung_health\pre_sleep_stage1\samsung_pre_sleep_proxy_label_evaluation.csv
```

## Matching Rule

- Proxy label source: Samsung `sleep_score`
- Good-sleep proxy threshold: `sleep_score >= 80`
- Episode matching: nearest sleep start within `30` minutes
- Samsung shifted sleep-table mapping is used for this export.
- Sleep start/end times are adjusted by the exported UTC offset before matching.

## Match Summary

- sleep_score_source_file: `docs\samsunghealth\com.samsung.shealth.sleep.20260629163038.csv`
- sleep_score_source_rows_with_score: `1640`
- episode_rows: `1493`
- matched_episode_rows: `64`
- matched_episode_rate: `0.042866711319490956`
- good_sleep_score_threshold: `80`
- max_match_time_diff_minutes: `30`
- proxy_positive_rate: `0.078125`
- mean_sleep_score: `57.203125`
- median_sleep_score: `59.5`
- median_match_time_diff_minutes: `18.733333333333334`

## Caveat

Samsung `sleep_score` is a device/vendor proxy label, not the original project `good_sleep_label`. Any metrics computed here are proxy-label diagnostics only.
