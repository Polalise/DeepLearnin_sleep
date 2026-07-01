# DeepLearnin Sleep

Strict pre-sleep forecasting project for predicting the upcoming sleep episode `good_sleep_label` using only data available before `sleep_start_datetime`.

## Final Objective

```text
Predict whether the upcoming sleep episode will be good sleep using prior sleep/wearable history and wearable data observed before sleep start.
```

The final workflow avoids using information from after sleep onset or after sleep completion.

## Final Model

- Experiment family: `presleep_stage1_hp_tiny_dropout40_wd1e3`
- Representative checkpoint: `presleep_stage1_hp_tiny_dropout40_wd1e3_seed2027`
- Feature set: Design C Stage 1 strict pre-sleep features
- Model: PyTorch MLP
- Hidden dimensions: `(24, 12)`
- Dropout: `0.40`
- Weight decay: `0.001`
- Official threshold: `0.54`

Checkpoint:

```text
data/processed/pre_sleep_forecasting/design_c_stage1/experiments/stage1_hyperparameter_stability_outputs/models/presleep_stage1_hp_tiny_dropout40_wd1e3_seed2027_best.pt
```

## Performance Reference

Representative held-out participant test performance:

- Balanced accuracy: `0.6492`
- ROC AUC: `0.6937`
- Average precision: `0.6187`
- Precision: `0.6553`
- Recall: `0.4245`
- Participant bootstrap balanced accuracy 95% CI: `[0.5436, 0.7259]`
- Brier score: `0.2126`
- Expected calibration error: `0.1256`

Interpretation:

- The model shows moderate predictive signal under a strict pre-sleep timing definition.
- Probability output should be treated as a model score, not a perfectly calibrated real-world probability.
- The model is not intended for clinical, medical, or high-stakes decisions.

## Inference Contract

```text
raw Stage 1 features 70
-> train median imputer
-> train StandardScaler
-> remove 12 zero-variance features
-> final model input features 58
-> PyTorch MLP
-> sigmoid probability
-> threshold 0.54
```

Core files:

```text
src/pre_sleep_forecasting/feature_builder.py
src/pre_sleep_forecasting/inference.py
data/processed/pre_sleep_forecasting/design_c_stage1/inference_package/pre_sleep_inference_manifest.json
data/processed/pre_sleep_forecasting/design_c_stage1/inference_package/pre_sleep_inference_feature_contract.csv
```

## Predict New Episodes

Input episode CSV requires:

```text
participant_object_id
sleep_start_datetime
```

Optional:

```text
sleep_episode_id
```

PowerShell workflow:

```powershell
cd C:\workSpace\DeepLearnin_sleep
.\.venv\Scripts\Activate.ps1

python src\pre_sleep_forecasting\feature_builder.py `
  --episodes data\processed\pre_sleep_forecasting\new_data\episodes_to_predict.csv `
  --output data\processed\pre_sleep_forecasting\new_data\raw_stage1_features.csv

python src\pre_sleep_forecasting\inference.py `
  --input data\processed\pre_sleep_forecasting\new_data\raw_stage1_features.csv `
  --output data\processed\pre_sleep_forecasting\new_data\predictions.csv
```

Prediction output columns:

```text
sleep_episode_id
participant_object_id
sleep_start_datetime
prediction_cutoff_datetime
good_sleep_probability
good_sleep_pred
threshold
```

## Samsung Health Diagnostic

Samsung Health data were transformed into a Fitbit-compatible feature schema for cross-device transfer diagnostics.

This does not mean Samsung raw data were converted into Fitbit raw data, and it is not formal external validation.

Samsung workflow:

```text
scripts/29_profile_samsung_health_core_tables.py
scripts/30_build_samsung_sleep_episode_table.py
scripts/31_build_samsung_pre_sleep_stage1_features.py
scripts/32_run_samsung_pre_sleep_inference.py
scripts/33_join_samsung_sleep_score_proxy_labels.py
scripts/34_build_samsung_stage_based_proxy_labels.py
scripts/35_evaluate_samsung_predictions_against_stage_proxy_labels.py
scripts/36_diagnose_samsung_presleep_activity_coverage.py
```

Main Samsung conclusion:

- The adapter can produce a 70-feature Fitbit-compatible Stage 1 table.
- Pre-sleep heart-rate and previous-day daily activity features are usable.
- Pre-sleep step/calorie interval data are sparse in the current export.
- Samsung proxy labels do not provide formal external validation.
- The selected Fitbit-trained MLP does not transfer reliably to Samsung stage-proxy labels.

Key Samsung reports:

```text
reports/samsung_pre_sleep_external_prediction_interpretation.md
reports/samsung_stage_proxy_external_evaluation_report.md
reports/samsung_to_fitbit_feature_mapping_confidence.md
reports/samsung_to_fitbit_adapter_high_priority_improvements.md
reports/samsung_presleep_activity_coverage_diagnostic.md
```

## Raw Feature Inference Debug Tool

A lightweight Streamlit debug tool is available for running the selected inference pipeline on already-built raw Stage 1 feature CSV files.

Debug app:

```text
prototype/pre_sleep_inference_app.py
```

Run:

```powershell
cd C:\workSpace\DeepLearnin_sleep
.\.venv\Scripts\python.exe -m pip install -r requirements-prototype.txt
.\.venv\Scripts\python.exe -m streamlit run prototype\pre_sleep_inference_app.py
```

Debug tool usage guide:

```text
docs/pre_sleep_prototype_usage.md
```

This is not the end-to-end Samsung live forecasting prototype. It does not read Samsung Health export folders or build features from raw wearable files.

## Samsung Live Forecasting Prototype

The Samsung live prototype runs the end-to-end diagnostic workflow from a Samsung Health export folder through the final trained MLP. It also includes a partial-input preset mode for fast prototype interaction.

App:

```text
prototype/samsung_sleep_forecasting_app.py
```

Run:

```powershell
cd C:\workSpace\DeepLearnin_sleep
.\.venv\Scripts\python.exe -m pip install -r requirements-prototype.txt
.\.venv\Scripts\python.exe -m streamlit run prototype\samsung_sleep_forecasting_app.py
```

Default data source:

```text
docs/samsunghealth
```

Usage guide:

```text
docs/samsung_sleep_live_prototype_usage.md
```

Flow:

```text
Samsung Health export
-> sleep episode generation
-> Samsung-to-Fitbit feature adapter
-> final Design C PyTorch MLP
-> prediction trend and latest results
```

The first screen is a live-style dashboard with:

```text
Samsung data availability
latest prediction target sleep-start time
plain-language tonight/upcoming-sleep forecast sentence
latest prediction state
snapshot probability delta
recent probability trend
model/caveat status
```

Main live forecast update:

```text
오늘 밤 예측 갱신
-> completed Samsung sleep history update
-> target sleep episode for the selected expected sleep-start time
-> latest Samsung wearable feature build
-> existing final MLP inference
-> tonight/upcoming-sleep forecast sentence
```

This updates feature history/baseline inputs for inference. It does not retrain the neural network.

Tonight forecast outputs:

```text
data/processed/samsung_health/pre_sleep_stage1/live_forecast/today_sleep_target_episode.csv
data/processed/samsung_health/pre_sleep_stage1/live_forecast/today_raw_stage1_features.csv
data/processed/samsung_health/pre_sleep_stage1/live_forecast/today_sleep_forecast_prediction.csv
data/processed/samsung_health/pre_sleep_stage1/live_forecast/today_stage1_feature_summary.csv
data/processed/samsung_health/pre_sleep_stage1/live_forecast/today_sleep_forecast_prediction_summary.csv
reports/samsung_today_sleep_forecast_feature_build_summary.md
reports/samsung_today_sleep_forecast_prediction_summary.md
```

The prototype reports which key inputs were actually reflected:

```text
history/baseline feature coverage
current-day wearable feature coverage
missing current-day features handled by fitted imputer/missing indicators
```

It also reports Samsung source freshness by table, so missing current-day features can be traced to export coverage:

```text
sleep stage
sleep summary
heart rate
daily steps
interval steps
daily activity
step trend
```

When current-day Samsung intraday values are missing, the today forecast flow can optionally apply manual wearable supplements before inference:

```text
today steps so far
last 3-hour / last 1-hour steps
pre-sleep / last 3-hour / last 1-hour heart rate
```

Supplement values are recorded separately and do not retrain the model:

```text
data/processed/samsung_health/pre_sleep_stage1/live_forecast/today_manual_wearable_supplement_report.csv
```

The app also stores the Samsung-only baseline prediction, final prediction, comparison table, and timestamped snapshots:

```text
data/processed/samsung_health/pre_sleep_stage1/live_forecast/today_samsung_only_prediction.csv
data/processed/samsung_health/pre_sleep_stage1/live_forecast/today_forecast_comparison.csv
data/processed/samsung_health/pre_sleep_stage1/live_forecast/today_numeric_sensitivity.csv
data/processed/samsung_health/pre_sleep_stage1/live_forecast/snapshots/
```

Advanced retraining remains separated from live prediction:

```text
고급 재학습
-> retraining experiment plan
-> no UI-triggered training by default
```

Preset quick prediction flow:

```text
steps and coarse user presets
-> 70 raw Design C Stage 1 features
-> existing imputer/scaler
-> final Design C PyTorch MLP
-> good_sleep probability
```

Preset quick prediction also reports how many raw features came from direct input, derived values, preset estimates, and fitted-imputer completion.

Preset scenario comparison flow:

```text
same direct inputs
-> multiple activity / calorie / heart-rate preset combinations
-> repeated final Design C PyTorch MLP inference
-> ranked probability comparison
```

The scenario screen highlights the highest/lowest probability spread so changes in preset state are visible without reading the raw feature table.

Preset feature builder:

```text
src/pre_sleep_forecasting/preset_feature_builder.py
```

Preset mode outputs:

```text
data/processed/pre_sleep_forecasting/prototype_outputs/quick_preset_raw_stage1_features.csv
data/processed/pre_sleep_forecasting/prototype_outputs/quick_preset_prediction.csv
data/processed/pre_sleep_forecasting/prototype_outputs/quick_preset_feature_source_summary.csv
data/processed/pre_sleep_forecasting/prototype_outputs/quick_preset_scenario_comparison.csv
data/processed/pre_sleep_forecasting/prototype_outputs/quick_preset_scenario_raw_features.csv
```

## Main Reports

Final project status:

```text
reports/pre_sleep_forecasting_project_final_status.md
```

Final artifact inventory:

```text
reports/pre_sleep_final_artifact_inventory.md
```

Inference usage guide:

```text
docs/pre_sleep_inference_usage.md
```

Inference package QA report:

```text
reports/pre_sleep_inference_package_qa.md
```

Final model report:

```text
reports/pre_sleep_forecasting_stage1_final_report_updated.md
```

## Modeling Notes

- Logistic Regression and Random Forest are traditional ML baseline/reference models only.
- PCA is exploratory feature-structure analysis only.
- Sequence models and calibration correction were evaluated as follow-ups; the selected final model remains the Design C Stage 1 MLP.
- Samsung Health transfer was completed as a cross-device diagnostic and should be reported with strong domain-shift caveats.

## Dependencies

Inference dependency reference:

```text
requirements-inference.txt
```

Project rules:

```text
Codex.Rule.md
```
