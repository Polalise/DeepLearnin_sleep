# Pre-Sleep Forecasting Final Artifact Inventory

## Scope

This inventory lists the final artifacts for the strict pre-sleep forecasting package.

Objective:

```text
Predict the upcoming sleep episode good_sleep_label using only wearable-derived data available before sleep_start_datetime.
```

Final selected model:

- Experiment family: `presleep_stage1_hp_tiny_dropout40_wd1e3`
- Representative checkpoint: `presleep_stage1_hp_tiny_dropout40_wd1e3_seed2027`
- Feature set: Design C Stage 1 strict pre-sleep features
- Model: PyTorch MLP
- Hidden dimensions: `(24, 12)`
- Dropout: `0.40`
- Weight decay: `0.001`
- Official threshold: `0.54`

## Final Model Artifact

Selected checkpoint:

```text
data/processed/pre_sleep_forecasting/design_c_stage1/experiments/stage1_hyperparameter_stability_outputs/models/presleep_stage1_hp_tiny_dropout40_wd1e3_seed2027_best.pt
```

Selection summary:

```text
data/processed/pre_sleep_forecasting/design_c_stage1/experiments/stage1_hyperparameter_stability_outputs/stage1_best_config_seed_selection_summary.csv
data/processed/pre_sleep_forecasting/design_c_stage1/experiments/stage1_hyperparameter_stability_outputs/stage1_best_config_seed_selection_summary.md
```

Threshold policy:

```text
data/processed/pre_sleep_forecasting/design_c_stage1/experiments/stage1_hyperparameter_stability_outputs/stage1_selected_model_threshold_policy_comparison.csv
data/processed/pre_sleep_forecasting/design_c_stage1/experiments/stage1_hyperparameter_stability_outputs/stage1_selected_model_threshold_sensitivity.csv
```

## Inference Package

Inference manifest:

```text
data/processed/pre_sleep_forecasting/design_c_stage1/inference_package/pre_sleep_inference_manifest.json
```

Feature contract:

```text
data/processed/pre_sleep_forecasting/design_c_stage1/inference_package/pre_sleep_inference_feature_contract.csv
```

Preprocessing contract:

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

## Feature And Preprocessing Artifacts

Raw Stage 1 feature columns:

```text
data/processed/pre_sleep_forecasting/design_c_stage1/pre_sleep_design_c_stage1_feature_columns.csv
```

Zero-variance removed features:

```text
data/processed/pre_sleep_forecasting/design_c_stage1/pre_sleep_design_c_stage1_zero_variance_removed_features.csv
```

Final model feature columns:

```text
data/processed/pre_sleep_forecasting/design_c_stage1/pre_sleep_design_c_stage1_final_feature_columns.csv
```

Median imputer:

```text
data/processed/pre_sleep_forecasting/design_c_stage1/pre_sleep_design_c_stage1_median_imputer.joblib
```

StandardScaler:

```text
data/processed/pre_sleep_forecasting/design_c_stage1/pre_sleep_design_c_stage1_standard_scaler.joblib
```

Final MLP tensor directory:

```text
data/processed/pre_sleep_forecasting/design_c_stage1/mlp_current_day_final
```

Final tensor summary:

```text
data/processed/pre_sleep_forecasting/design_c_stage1/pre_sleep_design_c_stage1_final_tensor_summary.csv
```

## Inference Scripts

Feature builder:

```text
src/pre_sleep_forecasting/feature_builder.py
```

Inference runner:

```text
src/pre_sleep_forecasting/inference.py
```

Preset feature builder for partial-input prototype mode:

```text
src/pre_sleep_forecasting/preset_feature_builder.py
```

Package init:

```text
src/pre_sleep_forecasting/__init__.py
```

Reusable QA script:

```text
scripts/24_check_pre_sleep_inference_package.py
```

Raw feature inference debug tool:

```text
prototype/pre_sleep_inference_app.py
docs/pre_sleep_prototype_usage.md
requirements-prototype.txt
```

Samsung live forecasting prototype:

```text
prototype/samsung_sleep_forecasting_app.py
docs/samsung_sleep_live_prototype_usage.md
data/processed/samsung_health/pre_sleep_stage1/prototype_snapshots/
data/processed/pre_sleep_forecasting/prototype_outputs/quick_preset_raw_stage1_features.csv
data/processed/pre_sleep_forecasting/prototype_outputs/quick_preset_prediction.csv
data/processed/pre_sleep_forecasting/prototype_outputs/quick_preset_feature_source_summary.csv
data/processed/pre_sleep_forecasting/prototype_outputs/quick_preset_scenario_comparison.csv
data/processed/pre_sleep_forecasting/prototype_outputs/quick_preset_scenario_raw_features.csv
```

Samsung live prototype UI surfaces:

```text
dashboard with latest prediction target, prediction state, and snapshot delta
today forecast update with current history/baseline feature inputs
Samsung sync prediction table and recent probability trend
partial-input preset prediction with feature-completeness status
preset scenario comparison with probability spread
advanced retraining experiment plan surface
model flow explanation and cross-device caveat
```

Tonight forecast outputs:

```text
data/processed/samsung_health/pre_sleep_stage1/live_forecast/today_sleep_target_episode.csv
data/processed/samsung_health/pre_sleep_stage1/live_forecast/today_raw_stage1_features.csv
data/processed/samsung_health/pre_sleep_stage1/live_forecast/today_sleep_forecast_prediction.csv
data/processed/samsung_health/pre_sleep_stage1/live_forecast/today_samsung_only_raw_stage1_features.csv
data/processed/samsung_health/pre_sleep_stage1/live_forecast/today_samsung_only_prediction.csv
data/processed/samsung_health/pre_sleep_stage1/live_forecast/today_forecast_comparison.csv
data/processed/samsung_health/pre_sleep_stage1/live_forecast/today_numeric_sensitivity.csv
data/processed/samsung_health/pre_sleep_stage1/live_forecast/today_manual_wearable_supplement_report.csv
data/processed/samsung_health/pre_sleep_stage1/live_forecast/snapshots/
data/processed/samsung_health/pre_sleep_stage1/live_forecast/today_stage1_feature_mapping_report.csv
data/processed/samsung_health/pre_sleep_stage1/live_forecast/today_stage1_feature_summary.csv
data/processed/samsung_health/pre_sleep_stage1/live_forecast/today_sleep_forecast_prediction_summary.csv
reports/samsung_today_sleep_forecast_feature_build_summary.md
reports/samsung_today_sleep_forecast_prediction_summary.md
reports/samsung_model_retraining_experiment_plan.md
```

## Samsung Health Cross-Device Diagnostic Artifacts

Samsung Health workflow scripts:

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

Samsung Health processed data:

```text
data/processed/samsung_health/core_table_profile/samsung_health_core_table_summary.csv
data/processed/samsung_health/core_table_profile/samsung_health_core_date_summary.csv
data/processed/samsung_health/core_table_profile/samsung_health_core_numeric_summary.csv
data/processed/samsung_health/core_table_profile/samsung_health_core_missing_summary.csv
data/processed/samsung_health/pre_sleep_stage1/samsung_sleep_episodes.csv
data/processed/samsung_health/pre_sleep_stage1/samsung_sleep_episode_summary.csv
data/processed/samsung_health/pre_sleep_stage1/samsung_sleep_stage_episode_stage_summary.csv
data/processed/samsung_health/pre_sleep_stage1/samsung_raw_stage1_features.csv
data/processed/samsung_health/pre_sleep_stage1/samsung_stage1_feature_mapping_report.csv
data/processed/samsung_health/pre_sleep_stage1/samsung_stage1_feature_summary.csv
data/processed/samsung_health/pre_sleep_stage1/samsung_pre_sleep_predictions.csv
data/processed/samsung_health/pre_sleep_stage1/samsung_pre_sleep_prediction_summary.csv
data/processed/samsung_health/pre_sleep_stage1/samsung_sleep_episodes_with_proxy_labels.csv
data/processed/samsung_health/pre_sleep_stage1/samsung_pre_sleep_predictions_with_proxy_labels.csv
data/processed/samsung_health/pre_sleep_stage1/samsung_pre_sleep_proxy_label_evaluation.csv
data/processed/samsung_health/pre_sleep_stage1/samsung_sleep_score_proxy_label_match_report.csv
data/processed/samsung_health/pre_sleep_stage1/samsung_sleep_episodes_with_stage_proxy_labels.csv
data/processed/samsung_health/pre_sleep_stage1/samsung_stage_proxy_label_quality_summary.csv
data/processed/samsung_health/pre_sleep_stage1/samsung_predictions_with_stage_proxy_labels.csv
data/processed/samsung_health/pre_sleep_stage1/samsung_stage_proxy_prediction_evaluation.csv
data/processed/samsung_health/pre_sleep_stage1/samsung_stage_proxy_threshold_sensitivity.csv
data/processed/samsung_health/pre_sleep_stage1/diagnostics/samsung_presleep_activity_window_coverage_summary.csv
data/processed/samsung_health/pre_sleep_stage1/diagnostics/samsung_presleep_activity_episode_window_diagnostics.csv
data/processed/samsung_health/pre_sleep_stage1/diagnostics/samsung_presleep_activity_source_profile.csv
```

Samsung Health reports:

```text
reports/samsung_health_core_table_profile.md
reports/samsung_health_presleep_mapping_plan.md
reports/samsung_sleep_episode_table_summary.md
reports/samsung_pre_sleep_stage1_feature_build_summary.md
reports/samsung_pre_sleep_external_prediction_summary.md
reports/samsung_pre_sleep_external_prediction_interpretation.md
reports/samsung_sleep_score_proxy_label_join_summary.md
reports/samsung_sleep_score_proxy_evaluation_interpretation.md
reports/samsung_stage_based_proxy_label_summary.md
reports/samsung_stage_proxy_external_evaluation_report.md
reports/samsung_to_fitbit_feature_mapping_confidence.md
reports/samsung_to_fitbit_adapter_high_priority_improvements.md
reports/samsung_presleep_activity_coverage_diagnostic.md
```

Samsung diagnostic conclusion:

```text
Samsung Health data were transformed into a Fitbit-compatible feature schema for cross-device transfer diagnostics.
The workflow is not formal external validation.
The selected Fitbit-trained MLP did not transfer reliably to Samsung stage-proxy labels.
```

## Smoke Test Artifacts

Episode input:

```text
data/processed/pre_sleep_forecasting/new_data/episodes_to_predict.csv
```

Raw Stage 1 features:

```text
data/processed/pre_sleep_forecasting/new_data/raw_stage1_features.csv
```

Predictions:

```text
data/processed/pre_sleep_forecasting/new_data/predictions.csv
```

Recorded smoke status:

```text
rows: 3
threshold: 0.54
```

## Final Reports

Final pre-sleep forecasting report:

```text
reports/pre_sleep_forecasting_stage1_final_report.md
```

Updated final report with uncertainty and calibration:

```text
reports/pre_sleep_forecasting_stage1_final_report_updated.md
```

Inference package QA report:

```text
reports/pre_sleep_inference_package_qa.md
```

Follow-up plans:

```text
reports/pre_sleep_sequence_model_followup_plan.md
reports/pre_sleep_calibration_followup_plan.md
reports/pre_sleep_external_future_validation_plan.md
```

This artifact inventory:

```text
reports/pre_sleep_final_artifact_inventory.md
```

One-page final summary:

```text
reports/pre_sleep_forecasting_final_one_page_summary.md
```

## Documentation

Inference usage guide:

```text
docs/pre_sleep_inference_usage.md
```

Project rules:

```text
Codex.Rule.md
```

Daily work log:

```text
log/2026-06-29.md
```

Inference dependency list:

```text
requirements-inference.txt
```

Main pipeline summary notebook:

```text
notebooks/02_pipeline_from_scripts_summary.ipynb
```

Note: update the main pipeline summary notebook only when final workflow or reporting changes are formalized.

## Performance Reference

Representative held-out test performance:

- Balanced accuracy: `0.6492`
- ROC AUC: `0.6937`
- Average precision: `0.6187`
- Precision: `0.6553`
- Recall: `0.4245`
- Official threshold: `0.54`

Uncertainty and calibration:

- Participant bootstrap balanced accuracy 95% CI: `[0.5436, 0.7259]`
- Brier score: `0.2126`
- Expected calibration error: `0.1256`

## Use Constraints

Appropriate use:

- Research-grade strict pre-sleep forecasting.
- Threshold-based good sleep / not good sleep prediction.
- Relative nightly ranking or exploratory personal feedback.

Not appropriate use:

- Clinical or medical decision-making.
- High-stakes health decisions.
- Communicating `good_sleep_probability` as a well-calibrated real-world probability without calibration caveats.

## Canonical Inference Commands

PowerShell:

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

Optional recall-priority threshold:

```powershell
python src\pre_sleep_forecasting\inference.py `
  --input data\processed\pre_sleep_forecasting\new_data\raw_stage1_features.csv `
  --output data\processed\pre_sleep_forecasting\new_data\predictions_recall_priority.csv `
  --threshold 0.47
```
