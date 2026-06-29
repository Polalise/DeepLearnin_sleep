# Pre-Sleep Calibration Follow-Up Plan

## Purpose

This plan defines optional calibration correction experiments for the final strict pre-sleep forecasting model.

Current final model:

```text
presleep_stage1_hp_tiny_dropout40_wd1e3_seed2027
```

Calibration work should be treated as follow-up research. It should not change the final classification model unless calibration improves probability reliability without damaging threshold-based performance.

## Current Calibration Status

Held-out test calibration diagnostics:

- Brier score: `0.2126`
- Expected calibration error: `0.1256`
- Maximum calibration error: `0.8342`
- Mean predicted probability: `0.4396`
- Observed positive rate: `0.3610`

Interpretation:

- The model probability is useful as a score.
- It should not yet be communicated as a well-calibrated real-world probability.
- Calibration varies across participants.

## Key Risk

The validation split is small:

```text
validation participants: 9
validation samples: 347
```

Calibration models may overfit. Any calibration correction should be reported with this limitation.

## Candidate Calibration Methods

Recommended first-pass methods:

1. Platt scaling / logistic calibration
2. Isotonic regression
3. Temperature scaling on logits, if logits are available for all splits

Recommended order:

```text
Platt scaling -> isotonic regression -> temperature scaling
```

Reason:

- Platt scaling is lower capacity and less likely to overfit.
- Isotonic regression is more flexible but riskier with small validation data.
- Temperature scaling is simple, but the current saved prediction tables may store probabilities rather than logits.

## Data Inputs

Use saved predictions from the selected final model:

```text
data/processed/pre_sleep_forecasting/design_c_stage1/experiments/stage1_hyperparameter_stability_outputs/stage1_hyperparameter_stability_predictions.csv
```

Use selection metadata:

```text
data/processed/pre_sleep_forecasting/design_c_stage1/experiments/stage1_hyperparameter_stability_outputs/stage1_best_config_seed_selection_summary.csv
```

Filter to:

```text
experiment_id == presleep_stage1_hp_tiny_dropout40_wd1e3_seed2027
```

Calibration fitting split:

```text
validation only
```

Evaluation split:

```text
held-out test only
```

## Metrics

Primary calibration metrics:

- Brier score
- expected calibration error
- maximum calibration error
- calibration curve by probability bin

Classification metrics to preserve:

- balanced accuracy
- precision
- recall
- F1

Threshold policy:

- The primary final model threshold remains `0.54`.
- If calibrated probabilities are used for classification, any new threshold must be selected on validation only.
- Test-only thresholds are diagnostic only.

## Recommended Output Files

Notebook:

```text
notebooks/20_pre_sleep_calibration_followup.ipynb
```

Optional script after notebook logic stabilizes:

```text
scripts/27_calibrate_pre_sleep_selected_model.py
```

Outputs:

```text
data/processed/pre_sleep_forecasting/design_c_stage1/experiments/calibration_followup_outputs/
```

Suggested output files:

```text
selected_model_calibration_method_comparison.csv
selected_model_calibrated_predictions.csv
selected_model_calibrated_calibration_table.csv
selected_model_calibration_followup_summary.md
```

Report:

```text
reports/pre_sleep_calibration_followup_report.md
```

## Recommended Procedure

1. Load selected model validation/test predictions.
2. Fit Platt scaling on validation probabilities and labels.
3. Fit isotonic regression on validation probabilities and labels.
4. Apply calibration mappings to test probabilities.
5. Compare Brier score, ECE, and calibration tables.
6. Check whether classification metrics at validation-selected thresholds remain acceptable.
7. Report calibration as optional probability post-processing only.

## Decision Rule

Calibration correction can be recommended only if:

- Brier score improves on held-out test,
- ECE improves on held-out test,
- probability bins become more reliable,
- threshold-based classification does not materially degrade,
- the method is not obviously overfit to the small validation split.

If these conditions are not met, keep the current probability as an uncalibrated model score.

## Reporting Language

Preferred wording:

```text
Calibration correction was explored as optional probability post-processing.
```

Avoid:

```text
The calibrated probability is a clinically reliable real-world sleep probability.
```

The model remains research-grade even if calibration improves.
