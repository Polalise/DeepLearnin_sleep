# Pre-Sleep Calibration Follow-Up Report

## 1. Purpose

This follow-up experiment tested optional probability calibration correction for the selected final strict pre-sleep forecasting model.

Selected model:

```text
presleep_stage1_hp_tiny_dropout40_wd1e3_seed2027
```

This calibration experiment is probability post-processing. It does not replace the final model checkpoint or the official original threshold policy.

## 2. Setup

Calibration fitting split:

```text
validation
```

Evaluation split:

```text
test
```

Methods compared:

- Original uncalibrated model probability
- Platt scaling
- Isotonic regression

Original official threshold:

```text
0.54
```

For calibrated methods, thresholds were selected on the validation split by balanced accuracy.

## 3. Test Results

| Method | Threshold | Balanced accuracy | ROC AUC | Average precision | Brier | ECE | Precision | Recall |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| Original | 0.54 | 0.6492 | 0.6937 | 0.6187 | 0.2126 | 0.1256 | 0.6553 | 0.4245 |
| Platt | 0.40 | 0.6565 | 0.6937 | 0.6187 | 0.2083 | 0.0745 | 0.6500 | 0.4497 |
| Isotonic | 0.34 | 0.6492 | 0.6902 | 0.5584 | 0.2081 | 0.0486 | 0.6553 | 0.4245 |

## 4. Interpretation

Platt scaling gave the most balanced calibration result:

- improved Brier score,
- improved expected calibration error,
- preserved ROC AUC,
- preserved average precision,
- slightly improved balanced accuracy and recall under validation-selected calibrated thresholding.

Isotonic regression achieved the lowest ECE, but it reduced average precision and fit the validation split nearly perfectly. Given the small validation participant count, this is a warning sign for overfitting.

Therefore:

```text
Platt scaling is the preferred optional calibration post-processing candidate.
```

However:

```text
The official final model remains the original selected MLP with threshold 0.54.
```

## 5. Artifacts

Method comparison:

```text
data/processed/pre_sleep_forecasting/design_c_stage1/experiments/calibration_followup_outputs/selected_model_calibration_method_comparison.csv
```

Calibrated test predictions:

```text
data/processed/pre_sleep_forecasting/design_c_stage1/experiments/calibration_followup_outputs/selected_model_calibrated_predictions.csv
```

Calibration table:

```text
data/processed/pre_sleep_forecasting/design_c_stage1/experiments/calibration_followup_outputs/selected_model_calibrated_calibration_table.csv
```

Generated calibration summary:

```text
data/processed/pre_sleep_forecasting/design_c_stage1/experiments/calibration_followup_outputs/selected_model_calibration_followup_summary.md
```

This report:

```text
reports/pre_sleep_calibration_followup_report.md
```

## 6. Recommendation

Use the original final model and official threshold as the primary reported model:

```text
presleep_stage1_hp_tiny_dropout40_wd1e3_seed2027
threshold = 0.54
```

If probability communication is needed, report Platt scaling as an optional post-processing candidate with caveats:

- fitted on only 9 validation participants,
- not externally validated,
- still research-grade,
- not suitable for clinical or high-stakes health decisions.

Recommended wording:

```text
Platt scaling improved calibration diagnostics and may be used as optional probability post-processing, but the primary final model and official threshold remain unchanged.
```
