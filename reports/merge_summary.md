# Merge Summary

- Generated at: `2026-06-27T02:37:44`
- Base table: `sleep_daily_target.csv`
- Output file: `C:\workSpace\DeepLearnin_sleep\data\processed\modeling_dataset_daily.csv`

## Scope

- This report covers merging daily Fitbit features, daily SEMA features, and participant-level survey summaries.
- The merge uses sleep target rows as the base.
- No missing-value imputation, categorical encoding, scaling, or PCA was performed.

## Output Shape

- Base rows: `3,551`
- Base columns: `28`
- Merged rows: `3,551`
- Merged columns: `130`
- Participants: `69`
- Date range: `2021-05-24` to `2022-01-22`
- Duplicate `participant_object_id + calendar_date` rows: `0`

## Target Distribution

| good_sleep_label | rows |
| ---: | ---: |
| `0` | 2,153 |
| `1` | 1,398 |

## Merge Coverage

| source table | join key | source rows | added columns | matched base rows | match rate |
| --- | --- | ---: | ---: | ---: | ---: |
| `fitbit_stress_daily.csv` | `participant_object_id + calendar_date` | 1,876 | 7 | 1,865 | 52.52% |
| `fitbit_daily_hrv_summary_daily.csv` | `participant_object_id + calendar_date` | 2,475 | 4 | 2,463 | 69.36% |
| `fitbit_hrv_details_daily.csv` | `participant_object_id + calendar_date` | 2,583 | 17 | 2,487 | 70.04% |
| `fitbit_resting_heart_rate_daily.csv` | `participant_object_id + calendar_date` | 12,118 | 3 | 3,551 | 100.00% |
| `fitbit_activity_minutes_daily.csv` | `participant_object_id + calendar_date` | 7,083 | 4 | 3,549 | 99.94% |
| `fitbit_daily_spo2_daily.csv` | `participant_object_id + calendar_date` | 1,270 | 4 | 1,230 | 34.64% |
| `fitbit_respiratory_rate_summary_daily.csv` | `participant_object_id + calendar_date` | 2,495 | 7 | 2,487 | 70.04% |
| `fitbit_steps_daily.csv` | `participant_object_id + calendar_date` | 4,777 | 2 | 3,541 | 99.72% |
| `fitbit_calories_daily.csv` | `participant_object_id + calendar_date` | 6,660 | 2 | 3,549 | 99.94% |
| `fitbit_wrist_temperature_daily.csv` | `participant_object_id + calendar_date` | 3,304 | 4 | 3,285 | 92.51% |
| `sema_daily_context_mood.csv` | `participant_object_id + calendar_date` | 3,914 | 41 | 2,395 | 67.45% |
| `surveys_participant_summary.csv` | `participant_object_id` | 67 | 7 | 3,471 | 97.75% |

## Highest Missing Columns

| column | missing count | missing rate |
| --- | ---: | ---: |
| `asleep_minutes` | 3,358 | 94.56% |
| `restless_minutes` | 3,358 | 94.56% |
| `awake_minutes` | 3,358 | 94.56% |
| `classic_asleep_ratio` | 3,358 | 94.56% |
| `classic_restless_ratio` | 3,358 | 94.56% |
| `classic_awake_ratio` | 3,358 | 94.56% |
| `respiratory_light_sleep_breathing_rate_mean` | 2,975 | 83.78% |
| `spo2_average_value_mean` | 2,321 | 65.36% |
| `spo2_lower_bound_mean` | 2,321 | 65.36% |
| `spo2_upper_bound_mean` | 2,321 | 65.36% |
| `spo2_record_count` | 2,321 | 65.36% |
| `stress_score_mean` | 1,686 | 47.48% |
| `stress_sleep_points_mean` | 1,686 | 47.48% |
| `stress_responsiveness_points_mean` | 1,686 | 47.48% |
| `stress_exertion_points_mean` | 1,686 | 47.48% |
| `stress_ready_rate` | 1,686 | 47.48% |
| `stress_calculation_failed_rate` | 1,686 | 47.48% |
| `stress_record_count` | 1,686 | 47.48% |
| `sema_response_count` | 1,156 | 32.55% |
| `mood_alert_count` | 1,156 | 32.55% |
| `mood_anger_count` | 1,156 | 32.55% |
| `mood_fear_count` | 1,156 | 32.55% |
| `mood_happy_count` | 1,156 | 32.55% |
| `mood_joy_count` | 1,156 | 32.55% |
| `mood_neutral_count` | 1,156 | 32.55% |
| `mood_rested_relaxed_count` | 1,156 | 32.55% |
| `mood_sad_count` | 1,156 | 32.55% |
| `mood_sadness_count` | 1,156 | 32.55% |
| `mood_surprise_count` | 1,156 | 32.55% |
| `mood_tense_anxious_count` | 1,156 | 32.55% |

## Notes

- Missingness is expected because not every participant-day has every Fitbit, SEMA, or survey-derived feature.
- Stress-related features may carry sleep/recovery leakage risk and should be handled carefully in modeling reports.
- The next step should be final dataset EDA before deciding imputation and feature selection rules.
- The merged participant-date table is the root table for the deep learning path after missing handling and feature finalization.
- Scaling and PCA are not the default deep learning path.

## Next Step

```text
final dataset EDA -> missing-value handling -> feature finalization -> participant-aware split -> deep learning sequence dataset
```
