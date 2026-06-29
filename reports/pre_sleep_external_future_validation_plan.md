# Pre-Sleep External Or Future-Period Validation Plan

## Purpose

This plan defines how to validate the final strict pre-sleep forecasting model on external or future-period data.

Current final model:

```text
presleep_stage1_hp_tiny_dropout40_wd1e3_seed2027
```

External or future-period validation is the most important next step before making stronger generalization claims.

## Validation Goal

Measure whether the final model generalizes beyond the current held-out participant test split.

Target question:

```text
Does the selected strict pre-sleep MLP retain useful performance on data not used in any design, tuning, threshold selection, or final reporting step?
```

## Preferred Validation Data

Best option:

```text
new participants from the same data schema
```

Second-best option:

```text
future-period episodes from existing participants, with no overlap in model selection or threshold tuning
```

Less ideal option:

```text
additional episodes mixed with previously seen participants and similar dates
```

## Data Requirements

Minimum raw inputs:

- participant identifier compatible with `participant_object_id`
- sleep episode start time
- sleep episode label `good_sleep_label`
- Fitbit intraday steps before sleep onset
- Fitbit intraday calories before sleep onset
- Fitbit intraday heart rate before sleep onset
- previous-day daily activity/resting-HR fields required by the Stage 1 feature contract

Inference input columns:

```text
participant_object_id
sleep_start_datetime
```

Optional:

```text
sleep_episode_id
```

Evaluation labels:

```text
good_sleep_label
```

## Fixed Inference Contract

Do not refit preprocessing artifacts during validation.

Use the existing final package:

```text
data/processed/pre_sleep_forecasting/design_c_stage1/inference_package/pre_sleep_inference_manifest.json
data/processed/pre_sleep_forecasting/design_c_stage1/inference_package/pre_sleep_inference_feature_contract.csv
data/processed/pre_sleep_forecasting/design_c_stage1/pre_sleep_design_c_stage1_median_imputer.joblib
data/processed/pre_sleep_forecasting/design_c_stage1/pre_sleep_design_c_stage1_standard_scaler.joblib
data/processed/pre_sleep_forecasting/design_c_stage1/experiments/stage1_hyperparameter_stability_outputs/models/presleep_stage1_hp_tiny_dropout40_wd1e3_seed2027_best.pt
```

Fixed threshold:

```text
0.54
```

No threshold tuning should be performed on the external/future validation labels before reporting the primary result.

## Recommended Validation Outputs

Suggested input/output directory:

```text
data/processed/pre_sleep_forecasting/external_validation/
```

Suggested files:

```text
episodes_to_predict.csv
raw_stage1_features.csv
predictions.csv
predictions_with_labels.csv
external_validation_metrics.csv
external_validation_participant_metrics.csv
external_validation_calibration_table.csv
```

Recommended report:

```text
reports/pre_sleep_external_future_validation_report.md
```

Optional validation script:

```text
scripts/28_evaluate_pre_sleep_external_validation.py
```

## Metrics

Primary metric:

```text
balanced accuracy at fixed threshold 0.54
```

Secondary metrics:

- ROC AUC
- average precision
- F1
- precision
- recall
- confusion matrix
- Brier score
- expected calibration error
- participant-level metric distribution

Uncertainty:

- participant-level bootstrap confidence intervals when enough participants are available
- otherwise, report that participant-level uncertainty cannot be estimated reliably

## Recommended Procedure

1. Prepare new episode CSV.
2. Generate raw Stage 1 features with `feature_builder.py`.
3. Generate predictions with `inference.py` using threshold `0.54`.
4. Join predictions to held-out labels.
5. Compute metrics without changing model, imputer, scaler, feature order, or threshold.
6. Report participant-level results and calibration.
7. Compare to the original held-out test result:
   - balanced accuracy `0.6492`
   - bootstrap 95% CI `[0.5436, 0.7259]`

## Interpretation Guide

Strong external validation signal:

- balanced accuracy remains near or above the original test result,
- ROC AUC remains meaningfully above 0.5,
- participant-level results are not driven by one or two participants,
- calibration does not materially worsen.

Weak external validation signal:

- balanced accuracy falls near 0.5,
- recall or specificity collapses,
- performance is strong only for a small participant subset,
- calibration becomes substantially worse.

## Decision Rule

If external/future validation is strong:

- keep the selected Stage 1 MLP as final,
- update the final report with the new validation evidence,
- consider cautious generalization claims.

If external/future validation is weak:

- keep the model as research-grade only,
- do not make stronger generalization claims,
- investigate domain shift, participant differences, missingness, and device/data schema changes.

## Reporting Guardrails

Do not describe the model as clinically validated.

Acceptable wording:

```text
The model showed external/future-period validation evidence under the same strict pre-sleep inference contract.
```

Avoid:

```text
The model is ready for medical decision-making.
```
