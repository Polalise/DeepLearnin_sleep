# Traditional ML Baseline Reference Summary

- Generated at: `2026-06-28T21:02:34`
- Train input: `C:\workSpace\DeepLearnin_sleep\data\processed\splits\train_participant_split.csv`
- Test input: `C:\workSpace\DeepLearnin_sleep\data\processed\splits\test_participant_split.csv`
- Feature columns: `C:\workSpace\DeepLearnin_sleep\data\processed\encoded_feature_columns.csv`
- Metrics output: `C:\workSpace\DeepLearnin_sleep\data\processed\baseline_model_metrics.csv`
- Predictions output: `C:\workSpace\DeepLearnin_sleep\data\processed\baseline_model_predictions.csv`

## Scope

- This step trains first traditional ML baseline classifiers on the participant-aware split.
- Scaling and PCA, when used, are fit inside sklearn pipelines using train data only.
- This is not deep learning modeling.
- These results are retained as baseline/reference only for later MLP, SimpleRNN, LSTM, GRU, BiLSTM, and 1D CNN experiments.

## Split Used

| split | rows | participants | good_sleep_label mean |
| --- | ---: | ---: | ---: |
| train | 2,944 | 55 | 0.3988 |
| test | 607 | 14 | 0.3690 |

## Feature Set

- Feature count: `197`
- Keys and target were excluded from predictors.

## Test Metrics

| model | accuracy | balanced accuracy | precision | recall | f1 | roc auc | average precision | PCA components |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| `logistic_regression` | 0.7809 | 0.7986 | 0.6532 | 0.8661 | 0.7447 | 0.8801 | 0.8055 | 0 |
| `random_forest` | 0.7512 | 0.7491 | 0.6409 | 0.7411 | 0.6874 | 0.8304 | 0.7066 | 0 |
| `logistic_regression_pca_95` | 0.4975 | 0.5073 | 0.3754 | 0.5446 | 0.4444 | 0.5483 | 0.4448 | 38 |
| `dummy_most_frequent` | 0.6310 | 0.5000 | 0.0000 | 0.0000 | 0.0000 | 0.5000 | 0.3690 | 0 |

## Best Traditional ML Baseline By Balanced Accuracy

- Model: `logistic_regression`
- Balanced accuracy: `0.7986`
- ROC AUC: `0.8801`
- F1: `0.7447`

## Random Forest Top Feature Importance

| rank | feature | importance |
| ---: | --- | ---: |
| 1 | `hrv_detail_record_count` | 0.16845 |
| 2 | `sedentary_minutes_sum` | 0.13487 |
| 3 | `steps_record_count` | 0.05092 |
| 4 | `lightly_active_minutes_sum` | 0.04068 |
| 5 | `calories_sum` | 0.02846 |
| 6 | `steps_sum` | 0.02526 |
| 7 | `resting_hr_resting_heart_rate_mean` | 0.02062 |
| 8 | `wrist_temperature_record_count` | 0.01955 |
| 9 | `resting_hr_error_mean` | 0.01621 |
| 10 | `wrist_temperature_mean` | 0.01543 |
| 11 | `wrist_temperature_min` | 0.01497 |
| 12 | `wrist_temperature_max` | 0.01393 |
| 13 | `moderately_active_minutes_sum` | 0.01258 |
| 14 | `hrv_summary_nremhr_mean` | 0.01235 |
| 15 | `survey_bfpt_count` | 0.01215 |
| 16 | `respiratory_full_sleep_breathing_rate_mean` | 0.01193 |
| 17 | `survey_response_count` | 0.01179 |
| 18 | `very_active_minutes_sum` | 0.01142 |
| 19 | `hrv_detail_low_frequency_mean` | 0.01133 |
| 20 | `hrv_detail_rmssd_mean` | 0.01127 |
| 21 | `respiratory_full_sleep_signal_to_noise_mean` | 0.01112 |
| 22 | `survey_breq_count` | 0.01107 |
| 23 | `hrv_summary_rmssd_mean` | 0.01063 |
| 24 | `hrv_detail_high_frequency_min` | 0.01042 |
| 25 | `hrv_detail_high_frequency_mean` | 0.01033 |

## Figures

- metric_comparison: `C:\workSpace\DeepLearnin_sleep\reports\figures\baseline\metric_comparison.png`
- roc_curves: `C:\workSpace\DeepLearnin_sleep\reports\figures\baseline\roc_curves.png`
- confusion_matrices: `C:\workSpace\DeepLearnin_sleep\reports\figures\baseline\confusion_matrices.png`

## Next Step

```text
traditional ML baseline review only; main project path continues with deep learning sequence modeling
```
