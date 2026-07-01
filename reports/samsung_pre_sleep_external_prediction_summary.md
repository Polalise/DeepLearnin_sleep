# Samsung Health External Pre-Sleep Prediction Summary

## Purpose

Apply the selected strict pre-sleep forecasting MLP to Samsung Health Stage 1 raw features.

## Inputs

```text
data\processed\samsung_health\pre_sleep_stage1\samsung_raw_stage1_features.csv
```

## Outputs

```text
data\processed\samsung_health\pre_sleep_stage1\samsung_pre_sleep_predictions.csv
data\processed\samsung_health\pre_sleep_stage1\samsung_pre_sleep_prediction_summary.csv
```

## Model

- Experiment family: `presleep_stage1_hp_tiny_dropout40_wd1e3`
- Representative checkpoint: `presleep_stage1_hp_tiny_dropout40_wd1e3_seed2027`
- Official threshold: `0.54` unless overridden at runtime
- Raw feature contract: 70 Samsung-adapted Stage 1 features

## Prediction Distribution

- Rows: `1493`
- Threshold: `0.5400`
- Predicted positive rate: `0.0054`
- Mean probability: `0.3848`
- Median probability: `0.3846`
- P10/P90 probability: `0.3503` / `0.4175`

## Highest Probability Episodes

- `2026-05-31 03:17:00` | pred=1 | probability=0.5886 | `samsung_user__20260531031700__20260531123016__3aea63324e79`
- `2026-06-02 01:19:00` | pred=1 | probability=0.5819 | `samsung_user__20260602011900__20260602071646__63ffa017e128`
- `2026-06-24 01:45:00` | pred=1 | probability=0.5717 | `samsung_user__20260624014500__20260624070758__037f9c13f267`
- `2026-06-25 01:20:00` | pred=1 | probability=0.5529 | `samsung_user__20260625012000__20260625070729__90df3e9aa7f7`
- `2023-09-03 05:33:00` | pred=1 | probability=0.5512 | `samsung_user__20230903053300__20230903143230__93fe012a37b6`
- `2026-05-28 02:17:00` | pred=1 | probability=0.5444 | `samsung_user__20260528021700__20260528062839__f382b05bf267`
- `2026-06-26 01:50:00` | pred=1 | probability=0.5438 | `samsung_user__20260626015000__20260626064900__86ddf343c752`
- `2026-06-17 00:59:00` | pred=1 | probability=0.5413 | `samsung_user__20260617005900__20260617072131__8a02f74d0571`
- `2023-09-27 01:01:00` | pred=0 | probability=0.5350 | `samsung_user__20230927010100__20230927065052__b68b7d62a6e7`
- `2023-04-19 00:47:00` | pred=0 | probability=0.5290 | `samsung_user__20230419004700__20230419061030__827dc5d13c61`

## Lowest Probability Episodes

- `2024-07-31 06:02:00` | pred=0 | probability=0.2268 | `samsung_user__20240731060200__20240731084230__e77587d6a58d`
- `2024-07-31 02:16:00` | pred=0 | probability=0.2547 | `samsung_user__20240731021600__20240731053758__c30185c60f10`
- `2024-07-26 03:30:00` | pred=0 | probability=0.2677 | `samsung_user__20240726033000__20240726082756__3e27d2dde6db`
- `2021-08-27 08:40:44` | pred=0 | probability=0.2681 | `samsung_user__20210827084044__20210827135724__000055c7b386`
- `2025-05-24 02:30:00` | pred=0 | probability=0.2688 | `samsung_user__20250524023000__20250524063623__cc590d897ae5`
- `2024-07-29 06:06:00` | pred=0 | probability=0.2752 | `samsung_user__20240729060600__20240729184232__60d309fdfddf`
- `2024-08-01 02:36:00` | pred=0 | probability=0.2770 | `samsung_user__20240801023600__20240801084203__5d25a0e8bb6d`
- `2025-05-22 04:00:00` | pred=0 | probability=0.2787 | `samsung_user__20250522040000__20250522063153__12833851c4d9`
- `2025-05-26 01:13:00` | pred=0 | probability=0.2792 | `samsung_user__20250526011300__20250526110713__207c307fa6ad`
- `2025-05-21 03:06:00` | pred=0 | probability=0.2843 | `samsung_user__20250521030600__20250521072310__5c466cffbb31`

## Interpretation Caveats

- This is external/future-style application to Samsung Health export data, not a retrained Samsung model.
- Samsung adapter coverage is strong for pre-sleep heart rate and previous-day daily activity.
- Samsung pre-sleep intraday step/calorie coverage is sparse in the current export.
- Probabilities should be interpreted as model scores, not calibrated clinical probabilities.
- No label-based external performance metric is computed by this script.
