# Phase 3A Previous-Day Rolling/Trend Feature Engineering Report

## Summary

Phase 3A tested whether rolling and trend features improve strict previous-day sleep forecasting.

The experiment used the previous-day dataset and started from the conservative `daytime_only` feature subset. Rolling and trend features were created within participant-level contiguous date blocks so that feature histories did not cross date gaps.

The main result is that rolling/trend features made the GRU window-7 candidate close to the previous-day reference candidate, but did not clearly exceed it under validation-selected thresholding.

## Inputs

- Previous-day encoded dataset:
  - `data/processed/deep_learning_previous_day/modeling_dataset_previous_day_encoded.csv`
- Base feature subset:
  - `data/processed/deep_learning_feature_subsets/daytime_only_features.csv`
- Phase 3A experiment grid:
  - `data/processed/deep_learning_previous_day/experiments/phase_3a_rolling_trend_daytime_only/phase_3a_rolling_trend_experiment_grid.csv`

## Feature Engineering

The source rows were strict previous-day rows where `feature_date = target calendar_date - 1 day`.

Feature engineering used the 19 `daytime_only` features and created:

- 3-day and 7-day rolling mean
- 3-day and 7-day rolling standard deviation
- 3-day and 7-day rolling minimum
- 3-day and 7-day rolling maximum
- within-block 1-row difference
- deviation from 3-day rolling mean
- deviation from 7-day rolling mean

Rolling history was computed within participant-level contiguous date blocks. A new block was started whenever the `feature_date` gap was not exactly 1 day.

Calendar features were prepared as optional candidates but were not included in this saved Phase 3A tensor set.

## Saved Feature Set

- Base daytime-only features: 19
- Engineered candidate features before filtering: 228
- Train zero-variance features removed: 106
- Final saved feature count: 122

Saved feature-engineering outputs:

- `data/processed/deep_learning_previous_day/rolling_trend_daytime_only/modeling_dataset_previous_day_daytime_only_rolling_trend.csv`
- `data/processed/deep_learning_previous_day/rolling_trend_daytime_only/rolling_trend_daytime_only_feature_columns.csv`
- `data/processed/deep_learning_previous_day/rolling_trend_daytime_only/zero_variance_removed_features.csv`
- `data/processed/deep_learning_previous_day/rolling_trend_daytime_only/rolling_trend_daytime_only_standard_scaler.joblib`
- `data/processed/deep_learning_previous_day/rolling_trend_daytime_only/metadata.json`
- `data/processed/deep_learning_previous_day/rolling_trend_daytime_only/tensor_summary.csv`

## Tensor Summary

| tensor_type | window | split | samples | participants | features | target_mean |
| --- | ---: | --- | ---: | ---: | ---: | ---: |
| `gru_sequence` | 7 | `test` | 296 | 9 | 122 | 0.4155 |
| `gru_sequence` | 7 | `train` | 1303 | 33 | 122 | 0.4021 |
| `gru_sequence` | 7 | `validation` | 245 | 9 | 122 | 0.3755 |
| `gru_sequence` | 14 | `test` | 206 | 5 | 122 | 0.4709 |
| `gru_sequence` | 14 | `train` | 887 | 27 | 122 | 0.3766 |
| `gru_sequence` | 14 | `validation` | 136 | 7 | 122 | 0.3529 |
| `mlp_current_day` | 1 | `test` | 524 | 12 | 122 | 0.3798 |
| `mlp_current_day` | 1 | `train` | 2135 | 41 | 122 | 0.4056 |
| `mlp_current_day` | 1 | `validation` | 457 | 10 | 122 | 0.3939 |


## Phase 3A Experiments

| experiment_id | feature_timing | subset_name | model_family | window |
| --- | --- | --- | --- | ---: |
| `phase3a_000` | previous_day | `daytime_only_rolling_trend` | `mlp_current_day` | 1 |
| `phase3a_001` | previous_day | `daytime_only_rolling_trend` | `gru` | 7 |
| `phase3a_002` | previous_day | `daytime_only_rolling_trend` | `gru` | 14 |

Training used validation balanced accuracy for early stopping and threshold selection. Test metrics were then computed using the validation-selected threshold.

## Validation Ranking And Paired Test Metrics

| experiment_id | model | window | best_epoch | threshold | validation balanced accuracy | validation ROC AUC | test balanced accuracy | test ROC AUC | test F1 | test precision | test recall | delta vs phase2a_006 |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| `phase3a_002` | `gru` | 14 | 4 | 0.36 | 0.7576 | 0.7398 | 0.5793 | 0.5898 | 0.6276 | 0.5282 | 0.7732 | -0.0305 |
| `phase3a_001` | `gru` | 7 | 3 | 0.35 | 0.6941 | 0.6923 | 0.6054 | 0.6385 | 0.6145 | 0.4880 | 0.8293 | -0.0044 |
| `phase3a_000` | `mlp_current_day` | 1 | 1 | 0.51 | 0.6041 | 0.5895 | 0.5678 | 0.6130 | 0.4531 | 0.4703 | 0.4372 | -0.0420 |


## Comparison To Previous-Day Reference

The previous best conservative previous-day candidate was:

| experiment_id | feature_timing | subset_name | model_family | window | test balanced accuracy |
| --- | --- | --- | --- | ---: | ---: |
| `phase2a_006` | previous_day | `daytime_only` | `BiLSTM` | 14 | 0.6098 |

The best Phase 3A test candidate under validation-selected thresholding was:

| experiment_id | model | window | test balanced accuracy | test ROC AUC | test F1 | test precision | test recall |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |
| `phase3a_001` | `gru` | 7 | 0.6054 | 0.6385 | 0.6145 | 0.4880 | 0.8293 |


This result was close to `phase2a_006`, but did not clearly exceed it.

## Threshold Sensitivity

Threshold sensitivity analysis used saved prediction probabilities only. Training was not rerun.

For `phase3a_001` and `phase3a_002`, the validation balanced-accuracy threshold and validation F1 threshold were identical. This means switching from balanced accuracy to F1 as the validation threshold policy did not materially change the official test metrics for the GRU candidates.

| experiment_id | threshold policy | threshold | split | balanced accuracy | F1 | precision | recall |
| --- | --- | ---: | --- | ---: | ---: | ---: | ---: |
| `phase3a_000` | `validation_balanced_accuracy` | 0.51 | `test` | 0.5678 | 0.4531 | 0.4703 | 0.4372 |
| `phase3a_000` | `validation_balanced_accuracy` | 0.51 | `validation` | 0.6041 | 0.5431 | 0.5000 | 0.5944 |
| `phase3a_000` | `validation_f1` | 0.38 | `test` | 0.5688 | 0.5714 | 0.4198 | 0.8945 |
| `phase3a_000` | `validation_f1` | 0.38 | `validation` | 0.5348 | 0.5664 | 0.4133 | 0.9000 |
| `phase3a_001` | `validation_balanced_accuracy` | 0.35 | `test` | 0.6054 | 0.6145 | 0.4880 | 0.8293 |
| `phase3a_001` | `validation_balanced_accuracy` | 0.35 | `validation` | 0.6941 | 0.6502 | 0.5232 | 0.8587 |
| `phase3a_001` | `validation_f1` | 0.35 | `test` | 0.6054 | 0.6145 | 0.4880 | 0.8293 |
| `phase3a_001` | `validation_f1` | 0.35 | `validation` | 0.6941 | 0.6502 | 0.5232 | 0.8587 |
| `phase3a_002` | `validation_balanced_accuracy` | 0.36 | `test` | 0.5793 | 0.6276 | 0.5282 | 0.7732 |
| `phase3a_002` | `validation_balanced_accuracy` | 0.36 | `validation` | 0.7576 | 0.6897 | 0.5882 | 0.8333 |
| `phase3a_002` | `validation_f1` | 0.36 | `test` | 0.5793 | 0.6276 | 0.5282 | 0.7732 |
| `phase3a_002` | `validation_f1` | 0.36 | `validation` | 0.7576 | 0.6897 | 0.5882 | 0.8333 |


A diagnostic test-threshold sweep suggested that `phase3a_001` could reach test balanced accuracy around 0.6189 and F1 around 0.6361 at threshold 0.33. However, this threshold was selected using held-out test labels, so it must not be used for final model selection.

For `phase3a_002`, the highest diagnostic test F1 was achieved by an almost all-positive threshold, which produced very poor specificity. This supports keeping validation-selected thresholding as the official comparison rule.

## Interpretation

Phase 3A shows that rolling/trend feature engineering can improve validation performance for sequence models, especially GRU window 14. However, the validation-selected candidate did not transfer as strongly to the held-out test split.

The most useful Phase 3A comparison candidate is:

`previous_day / daytime_only_rolling_trend / GRU / window 7`

It reached test balanced accuracy close to the previous-day reference candidate, but did not clearly exceed it.

Precision remained limited across Phase 3A GRU candidates. The models achieved relatively high recall but produced many false positives.

## Conclusion

Phase 3A does not justify replacing the current previous-day reference candidate.

Current previous-day reference candidate:

`phase2a_006 / previous_day / daytime_only / window 14 / BiLSTM`

Close rolling/trend comparison candidate:

`phase3a_001 / previous_day / daytime_only_rolling_trend / window 7 / GRU`

The current best overall model remains the same-date classifier:

`phase1a_003 / same_date / daytime_only / window 7 / mlp_current_day`

That same-date model should not be described as strict previous-day forecasting.
