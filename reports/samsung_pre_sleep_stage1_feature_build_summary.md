# Samsung Pre-Sleep Stage 1 Feature Build Summary

## Purpose

Build Samsung Health raw Stage 1 features compatible with the selected strict pre-sleep inference contract.

## Inputs

```text
data\processed\samsung_health\pre_sleep_stage1\samsung_sleep_episodes.csv
data\processed\pre_sleep_forecasting\design_c_stage1\inference_package\pre_sleep_inference_manifest.json
```

## Outputs

```text
data\processed\samsung_health\pre_sleep_stage1\samsung_raw_stage1_features.csv
data\processed\samsung_health\pre_sleep_stage1\samsung_stage1_feature_mapping_report.csv
data\processed\samsung_health\pre_sleep_stage1\samsung_stage1_feature_summary.csv
```

## Contract

- Raw Stage 1 features: 70
- Output rows: 1493
- Output columns: 74

## Mapping Caveats

- This first Samsung adapter prioritizes inference-contract compatibility.
- Samsung sleep episodes come from sleep_stage-derived episodes.
- Pre-sleep heart-rate features are mapped when heart-rate timestamps are available.
- Previous-day steps/calories/activity are mapped from Samsung daily summaries when available.
- Pre-sleep step and calorie features are mapped from Samsung pedometer step-count intervals when available.
- Fitbit-style activity intensity buckets remain incomplete in this adapter.
- Resting-HR fields are left missing and handled by the existing imputer/missing indicators.
