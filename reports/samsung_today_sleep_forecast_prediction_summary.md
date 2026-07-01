# Samsung Health External Pre-Sleep Prediction Summary

## Purpose

Apply the selected strict pre-sleep forecasting MLP to Samsung Health Stage 1 raw features.

## Inputs

```text
data\processed\samsung_health\pre_sleep_stage1\live_forecast\today_raw_stage1_features.csv
```

## Outputs

```text
data\processed\samsung_health\pre_sleep_stage1\live_forecast\today_sleep_forecast_prediction.csv
data\processed\samsung_health\pre_sleep_stage1\live_forecast\today_sleep_forecast_prediction_summary.csv
```

## Model

- Experiment family: `presleep_stage1_hp_tiny_dropout40_wd1e3`
- Representative checkpoint: `presleep_stage1_hp_tiny_dropout40_wd1e3_seed2027`
- Official threshold: `0.54` unless overridden at runtime
- Raw feature contract: 70 Samsung-adapted Stage 1 features

## Prediction Distribution

- Rows: `1`
- Threshold: `0.5400`
- Predicted positive rate: `1.0000`
- Mean probability: `0.6079`
- Median probability: `0.6079`
- P10/P90 probability: `0.6079` / `0.6079`

## Highest Probability Episodes

- `2026-06-30 23:30:00` | pred=1 | probability=0.6079 | `today_forecast__20260630233000`

## Lowest Probability Episodes

- `2026-06-30 23:30:00` | pred=1 | probability=0.6079 | `today_forecast__20260630233000`

## Interpretation Caveats

- This is external/future-style application to Samsung Health export data, not a retrained Samsung model.
- Samsung adapter coverage is strong for pre-sleep heart rate and previous-day daily activity.
- Samsung pre-sleep intraday step/calorie coverage is sparse in the current export.
- Probabilities should be interpreted as model scores, not calibrated clinical probabilities.
- No label-based external performance metric is computed by this script.
