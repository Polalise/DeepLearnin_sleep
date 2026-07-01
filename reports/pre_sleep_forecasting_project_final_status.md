# Pre-Sleep Forecasting Project Final Status

## 1. Project Objective

The final project objective is strict pre-sleep forecasting:

```text
Predict the upcoming sleep episode good_sleep_label using only wearable-derived data available before sleep_start_datetime.
```

This is different from earlier same-date sleep classification. The final workflow avoids using data that would only be known after the sleep episode starts or ends.

## 2. What Was Completed

The project progressed from broad sleep modeling into a strict pre-sleep forecasting package.

Completed work:

- Reframed Logistic Regression and Random Forest as traditional ML baseline/reference only.
- Reframed PCA as exploratory feature-structure analysis only.
- Built Design C Stage 1 strict pre-sleep features from:
  - pre-sleep intraday steps
  - pre-sleep intraday calories
  - pre-sleep intraday heart rate
  - sleep start timing/calendar features
  - previous-day daily activity/resting-HR features
  - missing indicators
- Created participant-level train/validation/test splits.
- Trained PyTorch MLP candidates for strict pre-sleep forecasting.
- Tested Stage 1, Stage 2 rolling/history, and Stage 2B compact rolling variants.
- Selected the Stage 1 tiny regularized MLP as the final current model.
- Added participant-level bootstrap uncertainty and calibration diagnostics.
- Packaged reusable inference scripts and inference artifacts.
- Created usage documentation, QA report, final artifact inventory, and a lightweight raw-feature inference debug tool.
- Ran sequence-model and calibration follow-ups.
- Built and evaluated a Samsung Health to Fitbit-compatible feature adapter as a cross-device transfer diagnostic.

## 3. Final Model

Final selected model:

- Experiment family: `presleep_stage1_hp_tiny_dropout40_wd1e3`
- Representative checkpoint: `presleep_stage1_hp_tiny_dropout40_wd1e3_seed2027`
- Feature set: Design C Stage 1 strict pre-sleep features
- Model: PyTorch MLP
- Hidden dimensions: `(24, 12)`
- Dropout: `0.40`
- Weight decay: `0.001`
- Official threshold: `0.54`

Representative checkpoint:

```text
data/processed/pre_sleep_forecasting/design_c_stage1/experiments/stage1_hyperparameter_stability_outputs/models/presleep_stage1_hp_tiny_dropout40_wd1e3_seed2027_best.pt
```

## 4. Inference Contract

The final inference contract is:

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

Core inference artifacts:

```text
data/processed/pre_sleep_forecasting/design_c_stage1/inference_package/pre_sleep_inference_manifest.json
data/processed/pre_sleep_forecasting/design_c_stage1/inference_package/pre_sleep_inference_feature_contract.csv
data/processed/pre_sleep_forecasting/design_c_stage1/pre_sleep_design_c_stage1_median_imputer.joblib
data/processed/pre_sleep_forecasting/design_c_stage1/pre_sleep_design_c_stage1_standard_scaler.joblib
```

Inference scripts:

```text
src/pre_sleep_forecasting/feature_builder.py
src/pre_sleep_forecasting/inference.py
```

## 5. Performance Summary

Held-out participant test performance for the representative model:

- Balanced accuracy: `0.6492`
- ROC AUC: `0.6937`
- Average precision: `0.6187`
- F1: `0.5153`
- Precision: `0.6553`
- Recall: `0.4245`
- Official threshold: `0.54`

Uncertainty and calibration:

- Participant bootstrap balanced accuracy 95% CI: `[0.5436, 0.7259]`
- Brier score: `0.2126`
- Expected calibration error: `0.1256`

Interpretation:

- The model shows useful predictive signal under a strict pre-sleep timing definition.
- Performance is moderate, not high.
- Recall is limited under the official threshold.
- Probability scores should be treated as model scores, not perfectly calibrated real-world probabilities.

## 6. Main Limitations

Important limitations:

- Held-out test set contains only 14 participants.
- Bootstrap confidence intervals are still wide.
- Generalization to new participants remains uncertain.
- Probability calibration is imperfect.
- Samsung Health application was completed as a cross-device transfer diagnostic, but it did not provide formal external validation.
- The model is not appropriate for clinical, medical, or high-stakes decision-making.

Recommended use:

- Research-grade strict pre-sleep forecasting.
- Threshold-based good sleep / not good sleep prediction.
- Relative nightly ranking or exploratory personal feedback.

Not recommended use:

- Clinical decisions.
- High-risk health decisions.
- Communicating model probability as a calibrated real-world probability without caveats.

## 7. How To Predict New Data

Input episode CSV must contain:

```text
participant_object_id
sleep_start_datetime
```

Optional:

```text
sleep_episode_id
```

Canonical PowerShell workflow:

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

Output columns:

```text
sleep_episode_id
participant_object_id
sleep_start_datetime
prediction_cutoff_datetime
good_sleep_probability
good_sleep_pred
threshold
```

Usage guide:

```text
docs/pre_sleep_inference_usage.md
```

Debug tool usage guide:

```text
docs/pre_sleep_prototype_usage.md
```

Artifact inventory:

```text
reports/pre_sleep_final_artifact_inventory.md
```

## 8. Current Project State

The project now has:

- a final strict pre-sleep forecasting model candidate,
- a documented inference preprocessing contract,
- reusable feature-building and inference scripts,
- a smoke-tested inference package,
- uncertainty and calibration reporting,
- usage documentation,
- artifact inventory,
- QA report.

The current package is suitable as a research-grade inference package. The existing Streamlit UI is a raw-feature debug tool, not the final Samsung live forecasting prototype.

Updated prototype status:

- The raw-feature Streamlit debug tool remains available for inference-package checks.
- The Samsung live forecasting prototype now provides the main demo surface:
  - dashboard-first prediction state
  - tonight forecast update using current Samsung history/baseline feature inputs
  - Samsung Health sync prediction
  - partial-input preset prediction
  - preset scenario sensitivity comparison
  - advanced retraining experiment planning surface
  - model-flow and domain-shift caveat sections

Prototype distinction:

- `오늘 밤 예측 갱신` updates current feature inputs and runs the existing final MLP.
- `고급 재학습` is separated as a research workflow and should require labeled data rebuild, validation, thresholding, calibration review, and artifact versioning before any candidate model is promoted.

## 9. Samsung Health Transfer Diagnostic

Samsung Health data were processed into a Fitbit-compatible Design C Stage 1 feature table and passed through the existing final inference package.

Workflow:

```text
Samsung Health export
-> sleep_stage-derived sleep episodes
-> Samsung raw Stage 1 features
-> existing Design C imputer/scaler/model
-> Samsung prediction output
-> sleep_score and stage-based proxy diagnostics
```

Main findings:

- Samsung sleep episodes were built successfully after UTC offset correction.
- Samsung Stage 1 raw features matched the 70-feature inference contract.
- Pre-sleep heart-rate and previous-day daily activity coverage were usable.
- Pre-sleep step/calorie interval coverage remained sparse because `pedometer_step_count` only covered a short recent date range.
- Samsung `sleep_score` proxy labels matched only `64 / 1493` episodes.
- Samsung stage-based proxy label v1 covered all `1493` episodes, but positive rate was only `0.0261`.
- Against stage proxy label v1, the final MLP showed weak transfer:
  - ROC AUC rank approximation: `0.3224`
  - average precision: `0.0180`
  - official threshold balanced accuracy: `0.4972`
  - official threshold sensitivity: `0.0000`
  - official threshold confusion matrix: TN `1446`, FP `8`, FN `39`, TP `0`

Interpretation:

- Samsung Health data can be transformed into a Fitbit-compatible feature schema for diagnostic inference.
- The current Samsung run is not formal external validation.
- The existing Fitbit-trained MLP should not be used as a reliable Samsung good-sleep classifier without Samsung-specific label design, calibration, and likely retraining/fine-tuning.

Samsung summary reports:

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

## 10. Follow-Up Work Completed

Sequence-model follow-up:

- GRU/LSTM/BiLSTM/CNN sequence variants were evaluated.
- Best sequence result did not materially improve over the selected Stage 1 MLP.
- Sequence models are not selected as final.

Calibration follow-up:

- Platt scaling improved Brier/ECE diagnostics in the selected-model follow-up.
- Calibration remains optional post-processing.
- Official final model and threshold remain unchanged.

Samsung external/future follow-up:

- Completed as a cross-device transfer diagnostic.
- Result supports a strong domain-shift caveat.

## 11. Remaining Optional Work

Optional next steps now have planning documents:

- Strict pre-sleep sequence models:
  - `reports/pre_sleep_sequence_model_followup_plan.md`
- Calibration correction:
  - `reports/pre_sleep_calibration_followup_plan.md`
- External or future-period validation:
  - `reports/pre_sleep_external_future_validation_plan.md`

The inference dependency reference is:

```text
requirements-inference.txt
```

Future work after this project state:

- Samsung-first or canonical wearable feature schema.
- Richer Samsung interval export or bin-level activity parsing.
- Samsung-specific label design and calibration.
- Samsung-specific model training only if time and labels are available.
