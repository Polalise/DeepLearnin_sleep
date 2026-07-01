# Samsung Stage-Based Proxy Label Summary

## Purpose

Create a Samsung sleep-stage-based proxy label for exploratory external evaluation.

## Inputs

```text
data\processed\samsung_health\pre_sleep_stage1\samsung_sleep_episodes.csv
data\processed\samsung_health\pre_sleep_stage1\samsung_sleep_stage_episode_stage_summary.csv
```

## Outputs

```text
data\processed\samsung_health\pre_sleep_stage1\samsung_sleep_episodes_with_stage_proxy_labels.csv
data\processed\samsung_health\pre_sleep_stage1\samsung_stage_proxy_label_quality_summary.csv
```

## Label Definition

- Duration: `6.0` to `9.0` hours
- Stage-based sleep efficiency: `>= 0.85`
- Awake ratio: `<= 0.2`

## Stage Code Mapping

- `40001`: awake
- `40002`: light
- `40003`: deep
- `40004`: rem

## Quality Summary

- episode_rows: `1493`
- stage_summary_rows: `6338`
- unknown_stage_rows: `0`
- label_coverage_count: `1493`
- label_coverage_rate: `1.0`
- positive_count: `39`
- positive_rate_among_labeled: `0.026121902210314803`
- mean_duration_hours: `6.788186565825706`
- median_duration_hours: `6.246388888888889`
- mean_stage_efficiency: `0.677295024358441`
- median_stage_efficiency: `0.655767562501403`
- mean_awake_ratio: `0.3227049756415589`
- median_awake_ratio: `0.344232437498597`
- duration_ok_rate: `0.3054253181513731`
- efficiency_ok_rate: `0.07635632953784327`
- awake_ok_rate: `0.11654387139986604`

## Caveat

This is a Samsung stage-derived proxy label, not the original project good_sleep_label. It is intended to improve interpretability and diagnostic evaluation, not to claim formal clinical ground truth.
