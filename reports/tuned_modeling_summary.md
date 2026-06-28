# Traditional ML Baseline Tuning Reference

- Generated at: `2026-06-28T22:59:07`
- Train input: `C:\workSpace\DeepLearnin_sleep\data\processed\splits\train_participant_split.csv`
- Test input: `C:\workSpace\DeepLearnin_sleep\data\processed\splits\test_participant_split.csv`
- Metrics output: `C:\workSpace\DeepLearnin_sleep\data\processed\tuned_model_metrics.csv`
- CV results output: `C:\workSpace\DeepLearnin_sleep\data\processed\tuned_model_cv_results.csv`
- Predictions output: `C:\workSpace\DeepLearnin_sleep\data\processed\tuned_model_predictions.csv`

## Scope

- This step tunes compact Logistic Regression and Random Forest grids as traditional ML references.
- Hyperparameter search uses `StratifiedGroupKFold` on the train split, grouped by participant.
- The held-out participant test split is used once for final comparison.
- This is not deep learning modeling and not final model selection for the project.

## Split Used

| split | rows | participants | good_sleep_label mean |
| --- | ---: | ---: | ---: |
| train | 2,944 | 55 | 0.3988 |
| test | 607 | 14 | 0.3690 |

## Tuned Test Metrics

| candidate | feature set | features | CV balanced accuracy | test balanced accuracy | roc auc | f1 | precision | recall |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| `logistic_regression` | `wearable_only` | 103 | 0.8359 | 0.8076 | 0.9046 | 0.7556 | 0.6996 | 0.8214 |
| `logistic_regression` | `all_features` | 197 | 0.8260 | 0.7986 | 0.8801 | 0.7447 | 0.6532 | 0.8661 |
| `random_forest` | `wearable_only` | 103 | 0.7794 | 0.7613 | 0.8301 | 0.7006 | 0.6680 | 0.7366 |
| `random_forest` | `all_features` | 197 | 0.7628 | 0.7545 | 0.8199 | 0.6940 | 0.6426 | 0.7545 |

## Best Traditional ML Baseline Candidate

- Candidate: `logistic_regression`
- Feature set: `wearable_only`
- Test balanced accuracy: `0.8076`
- Test ROC AUC: `0.9046`
- Test F1: `0.7556`
- Best params: `{'model__C': 1.0, 'model__class_weight': 'balanced'}`

## Validation Notes

- Compare CV balanced accuracy with held-out test balanced accuracy before treating this as final.
- Because the test split has only 14 participants, participant composition can still move metrics materially.
- Final reporting should include confidence intervals or repeated participant-aware resampling.

## Figures

- test_metrics: `C:\workSpace\DeepLearnin_sleep\reports\figures\tuned_modeling\tuned_test_metrics.png`
- cv_vs_test: `C:\workSpace\DeepLearnin_sleep\reports\figures\tuned_modeling\cv_vs_test_balanced_accuracy.png`

## Next Step

```text
traditional ML baseline validation reference; main project path continues with MLP / SimpleRNN / LSTM / GRU / BiLSTM / 1D CNN experiments
```
