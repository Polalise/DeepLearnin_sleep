# Traditional ML Baseline Validation Reference

## Technical Summary

- The current selected baseline is `wearable_only + Logistic Regression`; it is a baseline candidate, not the final model across all model families.
- This report is a traditional ML reference report, not a deep learning result.
- On the held-out participant test split, it achieved balanced accuracy `0.8076`, ROC AUC `0.9046`, and F1 `0.7556`.
- Participant bootstrap suggests balanced accuracy is directionally positive but still uncertain: median `0.8040`, 95% interval `0.7630` to `0.8333`.
- Coefficients should be interpreted as associations in a predictive model, not causal effects on sleep quality.

## The Baseline Signal Is Mainly Wearable-Driven

The tuned comparison selected `wearable_only` with `103` features. This means SEMA context/mood and participant survey features were not needed for the strongest current baseline. The model used standardized wearable-derived features and retained the fixed participant-aware split.

| metric | value |
| --- | ---: |
| accuracy | 0.8040 |
| balanced accuracy | 0.8076 |
| precision | 0.6996 |
| recall | 0.8214 |
| F1 | 0.7556 |
| ROC AUC | 0.9046 |
| average precision | 0.8462 |

The recall is higher than precision, so this baseline is better at catching good-sleep days than avoiding false positives. That tradeoff is acceptable for exploratory modeling, but a final application would need a threshold chosen for the intended use case.

Figure: `C:\workSpace\DeepLearnin_sleep\reports\figures\final_baseline_validation\top_logistic_coefficients.png`

## Coefficients Identify Predictive Associations, Not Causes

Because the model is Logistic Regression after standardization, larger absolute coefficients indicate stronger model influence on the log-odds of `good_sleep_label=1`. Positive coefficients push predictions toward good sleep; negative coefficients push predictions away from good sleep.

### Strongest Positive Coefficients

| feature | coefficient |
| --- | ---: |
| `stress_score_mean` | 3.5155 |
| `calories_record_count` | 3.1799 |
| `hrv_detail_record_count` | 2.1516 |
| `stress_calculation_failed_rate` | 0.9134 |
| `hrv_detail_high_frequency_max` | 0.8507 |
| `hrv_detail_high_frequency_mean` | 0.8395 |
| `spo2_record_count` | 0.8120 |
| `hrv_summary_rmssd_mean` | 0.4890 |
| `hrv_detail_low_frequency_min` | 0.2653 |
| `spo2_lower_bound_mean_missing_ind` | 0.2546 |

### Strongest Negative Coefficients

| feature | coefficient |
| --- | ---: |
| `sedentary_minutes_sum` | -4.3705 |
| `lightly_active_minutes_sum` | -2.3981 |
| `stress_record_count` | -1.6756 |
| `stress_responsiveness_points_mean` | -1.3969 |
| `stress_exertion_points_mean` | -1.3708 |
| `hrv_detail_rmssd_mean` | -1.0410 |
| `hrv_detail_high_frequency_std` | -0.9302 |
| `very_active_minutes_sum` | -0.8017 |
| `moderately_active_minutes_sum` | -0.7487 |
| `hrv_detail_coverage_mean` | -0.4398 |

Some large coefficients are count or missingness-related wearable availability signals. These can be operationally predictive, but they should be reported separately from physiological interpretation.

## Probability Scores Are Useful But Not Fully Calibrated

The calibration table compares predicted probability deciles with observed good-sleep rates on the held-out participant test split. The deciles are directionally informative, but this is not enough to claim calibrated probability estimates.

Figure: `C:\workSpace\DeepLearnin_sleep\reports\figures\final_baseline_validation\probability_calibration.png`

| decile | rows | mean predicted probability | observed good-sleep rate |
| ---: | ---: | ---: | ---: |
| 1 | 61 | 0.0028 | 0.0164 |
| 2 | 61 | 0.0249 | 0.0164 |
| 3 | 60 | 0.0904 | 0.0333 |
| 4 | 61 | 0.2049 | 0.1148 |
| 5 | 61 | 0.3250 | 0.2131 |
| 6 | 60 | 0.4749 | 0.3833 |
| 7 | 61 | 0.6515 | 0.3770 |
| 8 | 60 | 0.8204 | 0.7333 |
| 9 | 61 | 0.9424 | 0.8689 |
| 10 | 61 | 0.9940 | 0.9344 |

## Validation Depends On Only 14 Held-Out Participants

The test set contains `14` participants and `607` participant-day rows. Since rows from the same participant are correlated, participant-level uncertainty matters more than row count alone.

Figure: `C:\workSpace\DeepLearnin_sleep\reports\figures\final_baseline_validation\bootstrap_metric_intervals.png`

| metric | mean | median | 95% interval | valid bootstrap repeats |
| --- | ---: | ---: | --- | ---: |
| `balanced_accuracy` | 0.8024 | 0.8040 | 0.7630 to 0.8333 | 1,000 |
| `roc_auc` | 0.9060 | 0.9066 | 0.8815 to 0.9266 | 1,000 |
| `f1` | 0.7473 | 0.7549 | 0.6335 to 0.8095 | 1,000 |

## Scope, Data, And Metric Definitions

- Train split: `2,944` rows, `55` participants.
- Test split: `607` rows, `14` participants.
- Target: `good_sleep_label`, binary label where `1` represents a good-sleep day.
- Model feature set: `wearable_only`, excluding SEMA context/mood and participant survey features.
- Evaluation grain: participant-day rows, with split isolation at participant level.
- Main comparison metric: balanced accuracy, because class balance is not perfectly even.

## Methodology

1. Reused the fixed participant-aware train/test split.
2. Selected the tuned `logistic_regression__wearable_only` model from `tuned_models.joblib`.
3. Recomputed held-out test predictions and metrics from the saved model.
4. Extracted standardized Logistic Regression coefficients for interpretability.
5. Built decile-level probability calibration checks.
6. Resampled held-out participants with replacement to estimate uncertainty intervals.

## Limitations And Robustness Checks

- The selected model is a baseline candidate only; it has not been compared against boosted trees, SVM, MLP, or sequence models.
- The held-out test split has only 14 participants, so participant composition can materially affect metrics.
- Coefficients are predictive associations and should not be described as causal sleep drivers.
- Same-day wearable features may still include data-availability patterns related to user/device behavior.
- Probability calibration is directional but not established enough for clinical or high-stakes use.

## Recommended Next Steps

1. Train initial deep learning models using the saved rolling-window tensors: MLP, SimpleRNN, LSTM, GRU, BiLSTM, and 1D CNN.
2. Compare deep learning results against `wearable_only + Logistic Regression` as a reference baseline only.
3. Add participant-level uncertainty checks for the selected deep learning model family.
4. Decide whether same-day or prior-day-only features should be used before final deployment-style interpretation.

## Further Questions

- Should the final model optimize recall, precision, balanced accuracy, or calibrated probability?
- Should same-day features be used, or should the model predict tomorrow's sleep from prior-day signals?
- Should participant-specific baselines be modeled explicitly?
