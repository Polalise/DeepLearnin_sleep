# Traditional ML Feature-Set Reference Summary

- Generated at: `2026-06-28T22:52:00`
- Train input: `C:\workSpace\DeepLearnin_sleep\data\processed\splits\train_participant_split.csv`
- Test input: `C:\workSpace\DeepLearnin_sleep\data\processed\splits\test_participant_split.csv`
- Metrics output: `C:\workSpace\DeepLearnin_sleep\data\processed\feature_set_comparison_metrics.csv`
- Feature-set definitions: `C:\workSpace\DeepLearnin_sleep\data\processed\feature_set_definitions.csv`

## Scope

- This step compares traditional ML baseline performance across feature-set variants.
- The goal is to check whether reference baseline performance depends heavily on missingness or collection-volume features.
- The participant-aware split is reused unchanged.
- These results are not deep learning results and should not be treated as final model selection.

## Split Reused

| split | rows | participants | good_sleep_label mean |
| --- | ---: | ---: | ---: |
| train | 2,944 | 55 | 0.3988 |
| test | 607 | 14 | 0.3690 |

## Feature Set Definitions

| feature set | feature count | intent |
| --- | ---: | --- |
| `all_features` | 197 | all encoded baseline features |
| `no_missing_indicators` | 100 | remove only imputation missing indicators |
| `no_availability_features` | 63 | remove missing indicators and count/record-count features |
| `wearable_only` | 103 | remove SEMA context/mood and survey features |
| `wearable_values_only` | 43 | wearable-only after removing availability features |
| `context_survey_only` | 94 | SEMA context/mood plus survey features only |

## Test Metrics

| feature set | model | features | balanced accuracy | roc auc | f1 | precision | recall |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |
| `wearable_only` | `logistic_regression` | 103 | 0.8076 | 0.9046 | 0.7556 | 0.6996 | 0.8214 |
| `all_features` | `logistic_regression` | 197 | 0.7986 | 0.8801 | 0.7447 | 0.6532 | 0.8661 |
| `no_missing_indicators` | `logistic_regression` | 100 | 0.7963 | 0.8819 | 0.7423 | 0.6520 | 0.8616 |
| `no_availability_features` | `logistic_regression` | 63 | 0.7750 | 0.8602 | 0.7173 | 0.6800 | 0.7589 |
| `wearable_values_only` | `logistic_regression` | 43 | 0.7749 | 0.8705 | 0.7167 | 0.6901 | 0.7455 |
| `wearable_only` | `random_forest` | 103 | 0.7672 | 0.8295 | 0.7083 | 0.6641 | 0.7589 |
| `no_missing_indicators` | `random_forest` | 100 | 0.7534 | 0.8437 | 0.6918 | 0.6522 | 0.7366 |
| `all_features` | `random_forest` | 197 | 0.7491 | 0.8304 | 0.6874 | 0.6409 | 0.7411 |
| `wearable_values_only` | `random_forest` | 43 | 0.7396 | 0.8156 | 0.6751 | 0.6400 | 0.7143 |
| `no_availability_features` | `random_forest` | 63 | 0.7143 | 0.8012 | 0.6439 | 0.6163 | 0.6741 |
| `context_survey_only` | `logistic_regression` | 94 | 0.4842 | 0.4616 | 0.4768 | 0.3589 | 0.7098 |
| `context_survey_only` | `random_forest` | 94 | 0.4749 | 0.4548 | 0.3478 | 0.3390 | 0.3571 |

## Validation Reading

- Logistic Regression balanced accuracy with all features: `0.7986`
- Logistic Regression balanced accuracy without availability features: `0.7750`
- Availability-feature gap: `0.0235`
- Interpretation: removing missingness/count signals does not strongly reduce Logistic Regression performance on this split.

## Figures

- balanced_accuracy: `C:\workSpace\DeepLearnin_sleep\reports\figures\feature_set_comparison\balanced_accuracy_by_feature_set.png`
- roc_auc: `C:\workSpace\DeepLearnin_sleep\reports\figures\feature_set_comparison\roc_auc_by_feature_set.png`

## Next Step

```text
traditional ML baseline tuning as reference; deep learning experiments remain the main project path
```
