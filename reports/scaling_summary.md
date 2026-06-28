# Scaling Summary

- Generated at: `2026-06-28T20:53:17`
- Input file: `C:\workSpace\DeepLearnin_sleep\data\processed\modeling_dataset_encoded.csv`
- Output file: `C:\workSpace\DeepLearnin_sleep\data\processed\modeling_dataset_scaled.csv`
- Scaler file: `C:\workSpace\DeepLearnin_sleep\data\processed\standard_scaler.joblib`

## Scope

- This step applies `StandardScaler` to numeric model feature columns.
- It preserves `participant_object_id`, `calendar_date`, and `good_sleep_label`.
- It does not run PCA or train models.
- This full-table scaling output is for exploratory PCA and traditional ML reference work.
- The default deep learning tensor workflow fits its own scaler on deep-learning train rows only.

## Important Leakage Note

- This scaler is fit on the full current dataset for preprocessing exploration.
- For final model evaluation, scaling should be fit only on training folds inside a participant-aware pipeline.

## Output Shape

- Input rows: `3,551`
- Input columns: `200`
- Output rows: `3,551`
- Output columns: `190`
- Scaled feature columns: `187`
- Dropped zero-variance features: `10`
- Output missing cells: `0`
- Duplicate participant-date rows: `0`

## Scaling Validation

- Max absolute scaled feature mean: `0.0000000000`
- Max absolute deviation of scaled std from 1: `0.0000000000`

## Largest Absolute Scaled Ranges

| feature | mean | std | min | max |
| --- | ---: | ---: | ---: | ---: |
| `hrv_detail_low_frequency_min` | -0.0000 | 1.0000 | -0.8227 | 44.8571 |
| `hrv_detail_coverage_max` | -0.0000 | 1.0000 | -42.8382 | 13.8965 |
| `lightly_active_minutes_sum_missing_ind` | 0.0000 | 1.0000 | -0.0237 | 42.1248 |
| `calories_sum_missing_ind` | 0.0000 | 1.0000 | -0.0237 | 42.1248 |
| `very_active_minutes_sum_missing_ind` | 0.0000 | 1.0000 | -0.0237 | 42.1248 |
| `sedentary_minutes_sum_missing_ind` | 0.0000 | 1.0000 | -0.0237 | 42.1248 |
| `calories_record_count_missing_ind` | 0.0000 | 1.0000 | -0.0237 | 42.1248 |
| `moderately_active_minutes_sum_missing_ind` | 0.0000 | 1.0000 | -0.0237 | 42.1248 |
| `place_gym_count` | -0.0000 | 1.0000 | -0.0588 | 29.7878 |
| `place_gym_rate` | -0.0000 | 1.0000 | -0.0588 | 29.7878 |
| `hrv_detail_coverage_mean` | 0.0000 | 1.0000 | -22.3108 | 2.7229 |
| `resting_hr_error_mean` | 0.0000 | 1.0000 | -1.8133 | 21.0841 |
| `steps_sum_missing_ind` | -0.0000 | 1.0000 | -0.0531 | 18.8175 |
| `steps_record_count_missing_ind` | -0.0000 | 1.0000 | -0.0531 | 18.8175 |
| `hrv_detail_high_frequency_min` | -0.0000 | 1.0000 | -0.7603 | 17.1998 |
| `place_entertainment_rate` | -0.0000 | 1.0000 | -0.1999 | 16.7789 |
| `hrv_detail_high_frequency_std` | -0.0000 | 1.0000 | -0.7026 | 16.5733 |
| `hrv_detail_high_frequency_max` | 0.0000 | 1.0000 | -0.5897 | 16.4647 |
| `hrv_detail_rmssd_min` | -0.0000 | 1.0000 | -1.9249 | 15.6321 |
| `place_other_rate` | 0.0000 | 1.0000 | -0.1211 | 14.6057 |
| `place_other_count` | 0.0000 | 1.0000 | -0.1219 | 14.5461 |
| `mood_sad_count` | -0.0000 | 1.0000 | -0.1594 | 14.1075 |
| `mood_sad_rate` | -0.0000 | 1.0000 | -0.1587 | 13.9584 |
| `place_entertainment_count` | -0.0000 | 1.0000 | -0.2049 | 13.1042 |
| `hrv_detail_rmssd_std` | -0.0000 | 1.0000 | -1.4964 | 12.4908 |

## Dropped Zero-Variance Features

| feature | reason |
| --- | --- |
| `mood_anger_count` | `zero_variance` |
| `mood_fear_count` | `zero_variance` |
| `mood_joy_count` | `zero_variance` |
| `mood_sadness_count` | `zero_variance` |
| `mood_surprise_count` | `zero_variance` |
| `mood_anger_rate` | `zero_variance` |
| `mood_fear_rate` | `zero_variance` |
| `mood_joy_rate` | `zero_variance` |
| `mood_sadness_rate` | `zero_variance` |
| `mood_surprise_rate` | `zero_variance` |

## Next Step

```text
exploratory PCA, or use encoded daily data directly for deep learning sequence tensors
```
