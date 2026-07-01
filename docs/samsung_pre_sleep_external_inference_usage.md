# Samsung Health External Pre-Sleep Inference Usage

## Purpose

Use Samsung Health export-derived Stage 1 raw features with the selected strict pre-sleep forecasting MLP.

This is an external/future-style application step. It does not retrain the model and does not compute label-based performance unless a reliable Samsung proxy label is added later.

## Current Input

```text
data/processed/samsung_health/pre_sleep_stage1/samsung_raw_stage1_features.csv
```

Expected shape from the latest build:

- rows: `1493`
- passthrough columns: `4`
- raw Stage 1 features: `70`
- total columns: `74`

## Model Contract

- raw Stage 1 features: `70`
- median imputer and StandardScaler fitted on the original Design C Stage 1 training data
- zero-variance removed features: `12`
- final model input features: `58`
- model: PyTorch MLP
- official threshold: `0.54`

## Run Prediction

Before prediction, rebuild the Samsung sleep episode table and Stage 1 features after timezone correction:

```powershell
cd C:\workSpace\DeepLearnin_sleep
.\.venv\Scripts\python.exe scripts\30_build_samsung_sleep_episode_table.py
.\.venv\Scripts\python.exe scripts\31_build_samsung_pre_sleep_stage1_features.py
```

PowerShell:

```powershell
cd C:\workSpace\DeepLearnin_sleep
.\.venv\Scripts\python.exe scripts\32_run_samsung_pre_sleep_inference.py
```

Default outputs:

```text
data/processed/samsung_health/pre_sleep_stage1/samsung_pre_sleep_predictions.csv
data/processed/samsung_health/pre_sleep_stage1/samsung_pre_sleep_prediction_summary.csv
reports/samsung_pre_sleep_external_prediction_summary.md
```

## Optional Proxy Label Join

Samsung `sleep_score` can be joined as a vendor proxy label after prediction:

```powershell
.\.venv\Scripts\python.exe scripts\33_join_samsung_sleep_score_proxy_labels.py
```

Default outputs:

```text
data/processed/samsung_health/pre_sleep_stage1/samsung_sleep_episodes_with_proxy_labels.csv
data/processed/samsung_health/pre_sleep_stage1/samsung_pre_sleep_predictions_with_proxy_labels.csv
data/processed/samsung_health/pre_sleep_stage1/samsung_sleep_score_proxy_label_match_report.csv
data/processed/samsung_health/pre_sleep_stage1/samsung_pre_sleep_proxy_label_evaluation.csv
reports/samsung_sleep_score_proxy_label_join_summary.md
```

Proxy label caveat:

- Samsung `sleep_score >= 80` is treated as a diagnostic proxy only.
- It is not the original project `good_sleep_label`.
- Any metrics from this join are proxy-label diagnostics, not official external validation.

## Optional Threshold Override

Official threshold:

```powershell
.\.venv\Scripts\python.exe scripts\32_run_samsung_pre_sleep_inference.py --threshold 0.54
```

Recall-priority reference threshold:

```powershell
.\.venv\Scripts\python.exe scripts\32_run_samsung_pre_sleep_inference.py --threshold 0.47 --output data\processed\samsung_health\pre_sleep_stage1\samsung_pre_sleep_predictions_threshold047.csv
```

## Output Columns

```text
sleep_episode_id
participant_object_id
sleep_start_datetime
prediction_cutoff_datetime
good_sleep_probability
good_sleep_pred
threshold
```

## Interpretation Caveats

- This applies the selected Fitbit-trained/Design C Stage 1 MLP to Samsung Health-adapted features.
- Samsung source timestamps are adjusted by their exported `UTC+0900` offset before feature generation.
- Samsung pre-sleep heart-rate coverage is strong in the current adapter.
- Previous-day daily steps/calories/activity coverage is strong.
- Samsung pre-sleep intraday step/calorie coverage is sparse in the current export.
- `good_sleep_probability` should be read as a model score, not a clinical or fully calibrated probability.
- No training is performed by this script.
