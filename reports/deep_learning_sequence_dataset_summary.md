# Deep Learning Sequence Dataset Summary

- Generated at: `2026-06-29T00:12:41`
- Input file: `C:\workSpace\DeepLearnin_sleep\data\processed\modeling_dataset_encoded.csv`
- Feature column file: `C:\workSpace\DeepLearnin_sleep\data\processed\encoded_feature_columns.csv`
- Base participant split file: `C:\workSpace\DeepLearnin_sleep\data\processed\splits\participant_split_assignments.csv`
- Output directory: `C:\workSpace\DeepLearnin_sleep\data\processed\deep_learning_sequences`

## Scope

- This step creates deep-learning tensors from participant-date daily data before PCA.
- Rows are sorted by `participant_object_id` and `calendar_date` before windowing.
- PCA outputs are not used as model inputs in this step.
- Logistic Regression and Random Forest remain traditional ML baseline/reference only.
- Validation participants are split from the original training participants.
- Feature scaling is fit on deep-learning train rows only, then applied to validation/test rows.

## Windowing

- Windows: `[7, 14, 30]` days
- Require contiguous calendar dates: `True`
- Feature count: `197`

Each `.npz` file contains:

- `X_sequence`: samples x time_steps x features for SimpleRNN, LSTM, GRU, BiLSTM, and 1D CNN.
- `X_mlp_flattened`: samples x (time_steps * features) for a window-flattened MLP.
- `X_mlp_current_day`: samples x features for a daily tabular MLP baseline at the window endpoint.
- `y`, `participant_object_id`, `window_start_date`, `window_end_date`, and `feature_names`.

## Daily Row Split Summary

| split | rows | participants | good_sleep_label mean |
| --- | ---: | ---: | ---: |
| test | 607 | 14 | 0.3690 |
| train | 2,425 | 44 | 0.4000 |
| validation | 519 | 11 | 0.3931 |

## Tensor Summary

| window | split | samples | participants | sequence shape | MLP flattened shape | MLP current-day shape | class 0 | class 1 | target mean |
| ---: | --- | ---: | ---: | --- | --- | --- | ---: | ---: | ---: |
| 7 | test | 314 | 9 | `314 x 7 x 197` | `314 x 1379` | `314 x 197` | 182 | 132 | 0.4204 |
| 7 | train | 1,393 | 35 | `1393 x 7 x 197` | `1393 x 1379` | `1393 x 197` | 831 | 562 | 0.4034 |
| 7 | validation | 269 | 9 | `269 x 7 x 197` | `269 x 1379` | `269 x 197` | 163 | 106 | 0.3941 |
| 14 | test | 214 | 5 | `214 x 14 x 197` | `214 x 2758` | `214 x 197` | 116 | 98 | 0.4579 |
| 14 | train | 933 | 27 | `933 x 14 x 197` | `933 x 2758` | `933 x 197` | 576 | 357 | 0.3826 |
| 14 | validation | 146 | 7 | `146 x 14 x 197` | `146 x 2758` | `146 x 197` | 95 | 51 | 0.3493 |
| 30 | test | 106 | 4 | `106 x 30 x 197` | `106 x 5910` | `106 x 197` | 43 | 63 | 0.5943 |
| 30 | train | 435 | 19 | `435 x 30 x 197` | `435 x 5910` | `435 x 197` | 287 | 148 | 0.3402 |
| 30 | validation | 55 | 3 | `55 x 30 x 197` | `55 x 5910` | `55 x 197` | 42 | 13 | 0.2364 |

## Output Files

- Feature columns: `C:\workSpace\DeepLearnin_sleep\data\processed\deep_learning_sequences\feature_columns.csv`
- Deep-learning participant split assignments: `C:\workSpace\DeepLearnin_sleep\data\processed\deep_learning_sequences\deep_learning_participant_split_assignments.csv`
- Train-only scaler: `C:\workSpace\DeepLearnin_sleep\data\processed\deep_learning_sequences\deep_learning_standard_scaler.joblib`
- Tensor summary: `C:\workSpace\DeepLearnin_sleep\data\processed\deep_learning_sequences\sequence_tensor_summary.csv`

### Window 7

- Train tensors: `C:\workSpace\DeepLearnin_sleep\data\processed\deep_learning_sequences\window_7\train.npz`
- Validation tensors: `C:\workSpace\DeepLearnin_sleep\data\processed\deep_learning_sequences\window_7\validation.npz`
- Test tensors: `C:\workSpace\DeepLearnin_sleep\data\processed\deep_learning_sequences\window_7\test.npz`
- Sample index: `C:\workSpace\DeepLearnin_sleep\data\processed\deep_learning_sequences\window_7\sample_index.csv`

### Window 14

- Train tensors: `C:\workSpace\DeepLearnin_sleep\data\processed\deep_learning_sequences\window_14\train.npz`
- Validation tensors: `C:\workSpace\DeepLearnin_sleep\data\processed\deep_learning_sequences\window_14\validation.npz`
- Test tensors: `C:\workSpace\DeepLearnin_sleep\data\processed\deep_learning_sequences\window_14\test.npz`
- Sample index: `C:\workSpace\DeepLearnin_sleep\data\processed\deep_learning_sequences\window_14\sample_index.csv`

### Window 30

- Train tensors: `C:\workSpace\DeepLearnin_sleep\data\processed\deep_learning_sequences\window_30\train.npz`
- Validation tensors: `C:\workSpace\DeepLearnin_sleep\data\processed\deep_learning_sequences\window_30\validation.npz`
- Test tensors: `C:\workSpace\DeepLearnin_sleep\data\processed\deep_learning_sequences\window_30\test.npz`
- Sample index: `C:\workSpace\DeepLearnin_sleep\data\processed\deep_learning_sequences\window_30\sample_index.csv`

## Next Step

```text
Train MLP / SimpleRNN / LSTM / GRU / BiLSTM / 1D CNN deep learning experiments using these tensors.
```
