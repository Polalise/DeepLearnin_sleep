# Final Dataset EDA

- Generated at: `2026-06-28T20:42:20`
- Input file: `C:\workSpace\DeepLearnin_sleep\data\processed\modeling_dataset_daily.csv`

## Scope

- This report explores the merged daily modeling dataset.
- It does not perform missing-value imputation, categorical encoding, scaling, PCA, or modeling.

## Dataset Shape

- Rows: `3,551`
- Columns: `130`
- Participants: `69`
- Date range: `2021-05-24` to `2022-01-22`
- Duplicate participant-date rows: `0`
- Numeric feature candidates, excluding keys and targets: `116`

## Target Distribution

| good_sleep_label | rows | rate |
| ---: | ---: | ---: |
| `0` | 2,153 | 60.63% |
| `1` | 1,398 | 39.37% |

## Missingness By Feature Family

| family | columns | avg missing rate | max missing rate |
| --- | ---: | ---: | ---: |
| `spo2` | 4 | 65.36% | 65.36% |
| `stress` | 7 | 47.48% | 47.48% |
| `sleep_stage` | 14 | 43.63% | 94.56% |
| `respiratory` | 7 | 37.65% | 83.78% |
| `sema` | 41 | 32.55% | 32.55% |
| `hrv` | 21 | 30.11% | 30.64% |
| `temperature` | 4 | 7.49% | 7.49% |
| `survey` | 7 | 2.25% | 2.25% |
| `activity` | 8 | 0.11% | 0.28% |
| `key` | 6 | 0.00% | 0.00% |
| `resting_hr` | 3 | 0.00% | 0.00% |
| `target` | 8 | 0.00% | 0.00% |

## Highest Missing Columns

| column | dtype | missing count | missing rate |
| --- | --- | ---: | ---: |
| `asleep_minutes` | `float64` | 3,358 | 94.56% |
| `restless_minutes` | `float64` | 3,358 | 94.56% |
| `awake_minutes` | `float64` | 3,358 | 94.56% |
| `classic_asleep_ratio` | `float64` | 3,358 | 94.56% |
| `classic_restless_ratio` | `float64` | 3,358 | 94.56% |
| `classic_awake_ratio` | `float64` | 3,358 | 94.56% |
| `respiratory_light_sleep_breathing_rate_mean` | `float64` | 2,975 | 83.78% |
| `spo2_average_value_mean` | `float64` | 2,321 | 65.36% |
| `spo2_lower_bound_mean` | `float64` | 2,321 | 65.36% |
| `spo2_upper_bound_mean` | `float64` | 2,321 | 65.36% |
| `spo2_record_count` | `float64` | 2,321 | 65.36% |
| `stress_score_mean` | `float64` | 1,686 | 47.48% |
| `stress_sleep_points_mean` | `float64` | 1,686 | 47.48% |
| `stress_responsiveness_points_mean` | `float64` | 1,686 | 47.48% |
| `stress_exertion_points_mean` | `float64` | 1,686 | 47.48% |
| `stress_ready_rate` | `float64` | 1,686 | 47.48% |
| `stress_calculation_failed_rate` | `float64` | 1,686 | 47.48% |
| `stress_record_count` | `float64` | 1,686 | 47.48% |
| `sema_response_count` | `float64` | 1,156 | 32.55% |
| `mood_alert_count` | `float64` | 1,156 | 32.55% |
| `mood_anger_count` | `float64` | 1,156 | 32.55% |
| `mood_fear_count` | `float64` | 1,156 | 32.55% |
| `mood_happy_count` | `float64` | 1,156 | 32.55% |
| `mood_joy_count` | `float64` | 1,156 | 32.55% |
| `mood_neutral_count` | `float64` | 1,156 | 32.55% |
| `mood_rested_relaxed_count` | `float64` | 1,156 | 32.55% |
| `mood_sad_count` | `float64` | 1,156 | 32.55% |
| `mood_sadness_count` | `float64` | 1,156 | 32.55% |
| `mood_surprise_count` | `float64` | 1,156 | 32.55% |
| `mood_tense_anxious_count` | `float64` | 1,156 | 32.55% |

## Largest Mean Differences By Target

| feature | bad sleep mean | good sleep mean | good - bad | non-null bad | non-null good |
| --- | ---: | ---: | ---: | ---: | ---: |
| `steps_sum` | 9222.734 | 8007.195 | -1215.539 | 2,148 | 1,393 |
| `asleep_minutes` | 164.609 | 534.883 | 370.274 | 133 | 60 |
| `calories_sum` | 2506.335 | 2271.648 | -234.688 | 2,151 | 1,398 |
| `hrv_detail_high_frequency_max` | 1962.579 | 2191.287 | 228.708 | 1,466 | 1,021 |
| `hrv_detail_low_frequency_max` | 6818.479 | 6670.008 | -148.471 | 1,466 | 1,021 |
| `hrv_detail_low_frequency_mean` | 1564.730 | 1438.242 | -126.488 | 1,466 | 1,021 |
| `hrv_detail_low_frequency_std` | 1288.550 | 1171.638 | -116.912 | 1,464 | 1,020 |
| `sedentary_minutes_sum` | 766.119 | 661.607 | -104.512 | 2,151 | 1,398 |
| `steps_record_count` | 710.122 | 626.989 | -83.133 | 2,148 | 1,393 |
| `light_minutes` | 208.514 | 282.510 | 73.995 | 2,020 | 1,338 |
| `wrist_temperature_record_count` | 1310.343 | 1345.991 | 35.648 | 1,973 | 1,312 |
| `rem_minutes` | 74.147 | 105.936 | 31.789 | 2,020 | 1,338 |
| `lightly_active_minutes_sum` | 223.856 | 193.099 | -30.758 | 2,151 | 1,398 |
| `hrv_detail_low_frequency_min` | 219.073 | 189.399 | -29.674 | 1,466 | 1,021 |
| `hrv_detail_high_frequency_mean` | 516.903 | 545.913 | 29.010 | 1,466 | 1,021 |
| `hrv_detail_record_count` | 78.981 | 100.691 | 21.711 | 1,466 | 1,021 |
| `deep_minutes` | 67.194 | 86.220 | 19.027 | 2,020 | 1,338 |
| `wake_minutes` | 52.080 | 69.472 | 17.392 | 2,020 | 1,338 |
| `calories_record_count` | 1447.690 | 1453.961 | 6.270 | 2,151 | 1,398 |
| `moderately_active_minutes_sum` | 24.685 | 20.225 | -4.460 | 2,151 | 1,398 |
| `restless_minutes` | 12.797 | 17.117 | 4.320 | 133 | 60 |
| `very_active_minutes_sum` | 23.589 | 20.792 | -2.798 | 2,151 | 1,398 |
| `hrv_detail_high_frequency_min` | 96.456 | 93.669 | -2.788 | 1,466 | 1,021 |
| `stress_sleep_points_mean` | 18.853 | 20.854 | 2.001 | 1,126 | 739 |
| `hrv_detail_high_frequency_std` | 356.770 | 358.658 | 1.888 | 1,464 | 1,020 |

## Top Absolute Correlations With Target

| feature | non-null count | corr with good_sleep_label |
| --- | ---: | ---: |
| `asleep_minutes` | 193 | 0.830 |
| `light_minutes` | 3,358 | 0.607 |
| `hrv_detail_record_count` | 2,487 | 0.535 |
| `rem_minutes` | 3,358 | 0.506 |
| `wake_minutes` | 3,358 | 0.434 |
| `deep_minutes` | 3,358 | 0.373 |
| `sedentary_minutes_sum` | 3,549 | -0.292 |
| `steps_record_count` | 3,541 | -0.197 |
| `classic_asleep_ratio` | 193 | 0.191 |
| `classic_restless_ratio` | 193 | -0.178 |
| `calories_sum` | 3,549 | -0.168 |
| `lightly_active_minutes_sum` | 3,549 | -0.162 |
| `survey_bfpt_count` | 3,471 | 0.139 |
| `spo2_lower_bound_mean` | 1,230 | -0.124 |
| `classic_awake_ratio` | 193 | -0.123 |
| `awake_minutes` | 193 | 0.112 |
| `steps_sum` | 3,541 | -0.109 |
| `stress_sleep_points_mean` | 1,865 | 0.108 |
| `rem_ratio` | 3,358 | 0.103 |
| `respiratory_full_sleep_signal_to_noise_mean` | 2,487 | 0.094 |
| `deep_ratio` | 3,358 | -0.091 |
| `spo2_upper_bound_mean` | 1,230 | 0.080 |
| `respiratory_full_sleep_standard_deviation_mean` | 2,487 | 0.080 |
| `moderately_active_minutes_sum` | 3,549 | -0.078 |
| `mood_alert_rate` | 2,395 | -0.076 |

## Highest IQR Outlier Rates

| feature | non-null count | outlier count | outlier rate |
| --- | ---: | ---: | ---: |
| `stress_responsiveness_points_mean` | 1,865 | 292 | 15.66% |
| `stress_exertion_points_mean` | 1,865 | 292 | 15.66% |
| `stress_score_mean` | 1,865 | 292 | 15.66% |
| `stress_sleep_points_mean` | 1,865 | 292 | 15.66% |
| `resting_hr_error_mean` | 3,551 | 506 | 14.25% |
| `wrist_temperature_record_count` | 3,285 | 342 | 10.41% |
| `classic_awake_ratio` | 193 | 19 | 9.84% |
| `hrv_detail_high_frequency_std` | 2,484 | 234 | 9.42% |
| `hrv_detail_high_frequency_min` | 2,487 | 224 | 9.01% |
| `awake_minutes` | 193 | 17 | 8.81% |
| `hrv_detail_high_frequency_max` | 2,487 | 213 | 8.56% |
| `respiratory_deep_sleep_breathing_rate_mean` | 2,487 | 209 | 8.40% |
| `restless_minutes` | 193 | 16 | 8.29% |
| `hrv_detail_high_frequency_mean` | 2,487 | 206 | 8.28% |
| `hrv_detail_coverage_max` | 2,487 | 179 | 7.20% |
| `hrv_detail_rmssd_std` | 2,484 | 168 | 6.76% |
| `wrist_temperature_max` | 3,285 | 206 | 6.27% |
| `respiratory_light_sleep_breathing_rate_mean` | 576 | 36 | 6.25% |
| `hrv_detail_rmssd_min` | 2,487 | 146 | 5.87% |
| `hrv_detail_rmssd_max` | 2,487 | 142 | 5.71% |

## Figures

- `C:\workSpace\DeepLearnin_sleep\reports\figures\final_dataset_eda\target_distribution.png`
- `C:\workSpace\DeepLearnin_sleep\reports\figures\final_dataset_eda\missing_rate_by_feature_family.png`
- `C:\workSpace\DeepLearnin_sleep\reports\figures\final_dataset_eda\key_features_by_target.png`
- `C:\workSpace\DeepLearnin_sleep\reports\figures\final_dataset_eda\top_target_correlations.png`

## EDA Notes For Next Step

- Classic sleep-stage columns have very high missingness because Fitbit mixes classic and stages sleep formats.
- SpO2, stress, and SEMA features have partial day coverage and need explicit missing-value strategy.
- Stress-related features may leak sleep/recovery information and should be reported as a limitation if used.
- Several record-count columns may be useful both as coverage indicators and missingness flags.

## Recommended Next Step

```text
missing-value handling plan -> apply imputation/drop rules -> feature finalization -> deep learning sequence preparation
```
