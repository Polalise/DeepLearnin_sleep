# Deep Learning Subset Ablation And Previous-Day Timing Report

## Summary

This report summarizes the first two deep learning data-improvement rounds.

1. Phase 1A tested same-date feature subsets.
2. Phase 2A tested stricter previous-day features using `target_date - 1 day`.
3. The strongest test performance came from the same-date `daytime_only` feature subset.
4. Previous-day features substantially reduced performance, suggesting that the same-date signal is important and should not be interpreted as strict prior-day forecasting.

## Best Current Candidate

| item | value |
| --- | --- |
| experiment_id | `phase1a_003` |
| feature_timing | `same_date` |
| subset_name | `daytime_only` |
| window | `7` |
| model_family | `mlp_current_day` |
| selected threshold | `0.42` |
| test balanced accuracy | `0.8440` |
| test ROC AUC | `0.9023` |
| test average precision | `0.8402` |
| test F1 | `0.8215` |
| test precision | `0.7394` |
| test recall | `0.9242` |

## Participant-Level Bootstrap Uncertainty

Participant-level bootstrap resampling was used to estimate uncertainty while preserving within-participant row dependence more conservatively than row-level resampling.

| candidate | feature timing | model | participants | test rows | metric | original | bootstrap mean | 95% CI |
| --- | --- | --- | ---: | ---: | --- | ---: | ---: | --- |
| `phase1a_003` | same-date | `daytime_only / window 7 / mlp_current_day` | 9 | 314 | balanced accuracy | 0.8440 | 0.8486 | [0.8042, 0.8924] |
| `phase1a_003` | same-date | `daytime_only / window 7 / mlp_current_day` | 9 | 314 | ROC AUC | 0.9023 | 0.9064 | [0.8483, 0.9463] |
| `phase1a_002` | same-date | `daytime_only / window 7 / GRU` | 9 | 314 | balanced accuracy | 0.8317 | 0.8350 | [0.7886, 0.8859] |
| `phase1a_007` | same-date | `daytime_only / window 14 / mlp_current_day` | 5 | 214 | balanced accuracy | 0.8291 | 0.8305 | [0.7805, 0.8730] |
| `phase2a_006` | previous-day | `daytime_only / window 14 / BiLSTM` | 5 | 206 | balanced accuracy | 0.6098 | 0.5871 | [0.4758, 0.7413] |

The bootstrap results support `phase1a_003` as the strongest current candidate. Its participant-level confidence interval remains well above 0.80 for balanced accuracy, while the best previous-day candidate has a much wider interval and substantially lower central performance.

## Test Comparison By Feature Timing

| feature_timing | subset_name | split | experiments | mean_balanced_accuracy | max_balanced_accuracy | mean_roc_auc | max_roc_auc | mean_f1 | max_f1 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| same_date | daytime_only | test | 12 | 0.7635 | 0.8440 | 0.8450 | 0.9047 | 0.7859 | 0.8529 |
| same_date | no_high_sleep_session | test | 12 | 0.6671 | 0.8146 | 0.7253 | 0.8783 | 0.6817 | 0.8293 |
| same_date | full_current | test | 12 | 0.5941 | 0.7290 | 0.6522 | 0.8114 | 0.5288 | 0.6931 |
| previous_day | daytime_only | test | 8 | 0.5577 | 0.6098 | 0.5889 | 0.6286 | 0.5685 | 0.5984 |
| previous_day | no_high_sleep_session | test | 8 | 0.4772 | 0.5486 | 0.4871 | 0.5661 | 0.4597 | 0.5333 |

## Top Test Candidates

| feature_timing | experiment_id | subset_name | window | model_family | selected_threshold_from_validation | balanced_accuracy | roc_auc | average_precision | f1 | precision | recall |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| same_date | phase1a_003 | daytime_only | 7 | mlp_current_day | 0.4200 | 0.8440 | 0.9023 | 0.8402 | 0.8215 | 0.7394 | 0.9242 |
| same_date | phase1a_002 | daytime_only | 7 | gru | 0.3400 | 0.8317 | 0.9047 | 0.8381 | 0.8103 | 0.7039 | 0.9545 |
| same_date | phase1a_007 | daytime_only | 14 | mlp_current_day | 0.4300 | 0.8291 | 0.8772 | 0.8337 | 0.8241 | 0.7542 | 0.9082 |
| same_date | phase1a_031 | no_high_sleep_session | 14 | mlp_current_day | 0.4400 | 0.8146 | 0.8783 | 0.8388 | 0.8093 | 0.7436 | 0.8878 |
| same_date | phase1a_000 | daytime_only | 7 | bilstm | 0.3200 | 0.8144 | 0.8814 | 0.7927 | 0.7921 | 0.7018 | 0.9091 |
| same_date | phase1a_001 | daytime_only | 7 | cnn_1d | 0.5000 | 0.8043 | 0.8976 | 0.8257 | 0.7749 | 0.7554 | 0.7955 |
| same_date | phase1a_027 | no_high_sleep_session | 7 | mlp_current_day | 0.4400 | 0.8033 | 0.8399 | 0.7316 | 0.7732 | 0.7591 | 0.7879 |
| same_date | phase1a_035 | no_high_sleep_session | 30 | mlp_current_day | 0.5100 | 0.8001 | 0.8387 | 0.8083 | 0.8293 | 0.8500 | 0.8095 |
| same_date | phase1a_006 | daytime_only | 14 | gru | 0.2800 | 0.7915 | 0.8823 | 0.8087 | 0.8000 | 0.6761 | 0.9796 |
| same_date | phase1a_010 | daytime_only | 30 | gru | 0.4900 | 0.7859 | 0.8490 | 0.8828 | 0.8529 | 0.7945 | 0.9206 |

## Interpretation

The best-performing model is:

`same_date / daytime_only / window 7 / mlp_current_day`

This model achieved strong held-out test performance, but it uses features aligned to the sleep target `calendar_date`.

Earlier date-alignment checks showed that the sleep target `calendar_date` matches the sleep `endTime` date. Therefore, same-date features may include information from the day of sleep completion or information close to the target event.

The model should be interpreted as a same-date sleep classification model, not a strict previous-day forecasting model.

## Previous-Day Experiment Result

The previous-day feature experiment was designed to reduce temporal ambiguity by using only features from `target_date - 1 day`.

Performance dropped substantially:

- `same_date + daytime_only`: highest test balanced accuracy around `0.844`
- `previous_day + daytime_only`: highest test balanced accuracy around `0.610`

This suggests that strictly prior-day features alone are weaker predictors in the current dataset.

## Practical Conclusion

For the current project, the most defensible result is to report two tracks:

1. Best same-date classifier:
   - `same_date / daytime_only / window 7 / mlp_current_day`
   - strong performance
   - not a strict prospective model

2. Strict previous-day experiment:
   - lower performance
   - useful as a conservative timing-control analysis
   - substantially wider uncertainty under participant-level bootstrap

## Limitations

- Window 30 experiments have small validation/test participant counts and should be interpreted cautiously.
- Some same-date features may occur after the sleep event depending on source timing.
- Participant-level split shift remains a major factor.
- The previous-day dataset loses rows and participants because a prior-day feature row is required.

## Recommended Next Steps

1. Use `same_date / daytime_only / window 7 / mlp_current_day` as the current best same-date classifier.
2. Keep `same_date / daytime_only / window 7 / GRU` as the best sequence-model comparison candidate.
3. Report previous-day results as a stricter timing sensitivity analysis.
4. Update the main pipeline summary notebook once the final reporting structure is fixed.
5. Keep any final claim carefully scoped as same-date classification unless a future prospective feature design improves previous-day performance.
