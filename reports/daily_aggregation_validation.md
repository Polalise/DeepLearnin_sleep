# Daily Aggregation Validation

- Generated at: `2026-06-27T02:35:40`
- Input directory: `C:\workSpace\DeepLearnin_sleep\data\processed\daily_aggregates`

## Scope

- This is a light validation and visualization pass for the date-level aggregate outputs.
- It checks duplicate keys, date ranges, missing cells, target distribution, and selected feature ranges.
- It does not merge the final modeling dataset or perform imputation/encoding/scaling/PCA.

## Table Validation

| table | rows | columns | duplicate key rows | date min | date max | missing rate |
| --- | ---: | ---: | ---: | --- | --- | ---: |
| `fitbit_activity_minutes_daily.csv` | 7,083 | 6 | 0 | `2021-05-24` | `2022-01-22` | 0.00% |
| `fitbit_calories_daily.csv` | 6,660 | 4 | 0 | `2021-05-24` | `2022-01-22` | 0.00% |
| `fitbit_daily_hrv_summary_daily.csv` | 2,475 | 6 | 0 | `2021-05-24` | `2022-01-22` | 0.00% |
| `fitbit_daily_spo2_daily.csv` | 1,270 | 6 | 0 | `2021-05-24` | `2022-01-22` | 0.00% |
| `fitbit_hrv_details_daily.csv` | 2,583 | 19 | 0 | `2021-05-24` | `2022-01-22` | 0.06% |
| `fitbit_respiratory_rate_summary_daily.csv` | 2,495 | 9 | 0 | `2021-05-24` | `2022-01-21` | 8.54% |
| `fitbit_resting_heart_rate_daily.csv` | 12,118 | 5 | 0 | `2021-05-24` | `2022-01-22` | 0.00% |
| `fitbit_steps_daily.csv` | 4,777 | 4 | 0 | `2021-05-24` | `2022-01-22` | 0.00% |
| `fitbit_stress_daily.csv` | 1,876 | 9 | 0 | `2021-05-24` | `2022-01-22` | 0.00% |
| `fitbit_wrist_temperature_daily.csv` | 3,304 | 6 | 0 | `2021-05-24` | `2022-01-22` | 0.00% |
| `sema_daily_context_mood.csv` | 3,914 | 43 | 0 | `2021-04-07` | `2022-01-17` | 0.00% |
| `sleep_daily_target.csv` | 3,551 | 28 | 0 | `2021-05-24` | `2022-01-22` | 21.82% |
| `surveys_participant_summary.csv` | 67 | 8 | 0 | `None` | `None` | 0.00% |

## Sleep Target Summary

- Sleep target rows: `3,551`
- Participants: `69`
- Date range: `2021-05-24` to `2022-01-22`
- Good sleep days: `1,398`
- Bad sleep days: `2,153`
- Good sleep rate: `39.37%`

## Selected Feature Summary

| feature | count | mean | std | min | p25 | median | p75 | max |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| `minutesAsleep` | 3,551 | 393.072 | 98.383 | 0.000 | 343.000 | 401.000 | 454.000 | 1094.000 |
| `efficiency` | 3,551 | 93.776 | 6.297 | 34.000 | 93.000 | 95.000 | 97.000 | 100.000 |
| `stress_score_mean` | 1,876 | 64.181 | 28.471 | 0.000 | 67.000 | 75.000 | 80.000 | 94.000 |
| `hrv_summary_rmssd_mean` | 2,475 | 40.021 | 21.305 | 0.000 | 25.442 | 34.072 | 48.723 | 122.089 |
| `resting_hr_resting_heart_rate_mean` | 12,118 | 24.104 | 32.145 | 0.000 | 0.000 | 0.000 | 63.097 | 86.000 |
| `steps_sum` | 4,777 | 8261.636 | 5475.529 | 0.000 | 4461.000 | 7420.000 | 11046.000 | 43112.000 |
| `calories_sum` | 6,660 | 2182.955 | 704.189 | 0.690 | 1669.470 | 2073.600 | 2579.765 | 8387.030 |
| `wrist_temperature_mean` | 3,304 | -1.472 | 0.968 | -5.689 | -2.183 | -1.415 | -0.722 | 3.394 |

## Figures

- `C:\workSpace\DeepLearnin_sleep\reports\figures\sleep_target_distribution.png`
- `C:\workSpace\DeepLearnin_sleep\reports\figures\sleep_metric_histograms.png`
- `C:\workSpace\DeepLearnin_sleep\reports\figures\daily_table_row_coverage.png`
- `C:\workSpace\DeepLearnin_sleep\reports\figures\key_feature_boxplots.png`
- `C:\workSpace\DeepLearnin_sleep\reports\figures\sleep_daily_time_series.png`

## Notes

- `surveys_participant_summary.csv` is participant-level, so duplicate checks use only `participant_object_id`.
- Missing rates here describe each standalone aggregate table before cross-source merging.
- High missingness in sleep-stage columns can be expected because Fitbit has both stages and classic sleep formats.

## Next Step

```text
merge daily fitbit + daily sema + participant surveys -> final dataset EDA
```
