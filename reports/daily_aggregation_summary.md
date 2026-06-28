# Daily Aggregation Summary

- Generated at: `2026-06-27T02:35:28`
- Mongo URI: `mongodb://localhost:27017`
- Database: `rais_anonymized`

## Selected Unit

- Aggregation unit: `participant_object_id + calendar_date`
- This is the most appropriate unit because the prediction target is one sleep outcome per participant-day.
- SEMA responses are summarized to daily counts/rates.
- Surveys are summarized at participant level because they are not repeated daily measurements.

## Generated Tables

| table | rows | columns | path |
| --- | ---: | ---: | --- |
| `sleep_daily_target.csv` | 3,551 | 28 | `C:\workSpace\DeepLearnin_sleep\data\processed\daily_aggregates\sleep_daily_target.csv` |
| `fitbit_stress_daily.csv` | 1,876 | 9 | `C:\workSpace\DeepLearnin_sleep\data\processed\daily_aggregates\fitbit_stress_daily.csv` |
| `fitbit_daily_hrv_summary_daily.csv` | 2,475 | 6 | `C:\workSpace\DeepLearnin_sleep\data\processed\daily_aggregates\fitbit_daily_hrv_summary_daily.csv` |
| `fitbit_hrv_details_daily.csv` | 2,583 | 19 | `C:\workSpace\DeepLearnin_sleep\data\processed\daily_aggregates\fitbit_hrv_details_daily.csv` |
| `fitbit_resting_heart_rate_daily.csv` | 12,118 | 5 | `C:\workSpace\DeepLearnin_sleep\data\processed\daily_aggregates\fitbit_resting_heart_rate_daily.csv` |
| `fitbit_activity_minutes_daily.csv` | 7,083 | 6 | `C:\workSpace\DeepLearnin_sleep\data\processed\daily_aggregates\fitbit_activity_minutes_daily.csv` |
| `fitbit_daily_spo2_daily.csv` | 1,270 | 6 | `C:\workSpace\DeepLearnin_sleep\data\processed\daily_aggregates\fitbit_daily_spo2_daily.csv` |
| `fitbit_respiratory_rate_summary_daily.csv` | 2,495 | 9 | `C:\workSpace\DeepLearnin_sleep\data\processed\daily_aggregates\fitbit_respiratory_rate_summary_daily.csv` |
| `sema_daily_context_mood.csv` | 3,914 | 43 | `C:\workSpace\DeepLearnin_sleep\data\processed\daily_aggregates\sema_daily_context_mood.csv` |
| `surveys_participant_summary.csv` | 67 | 8 | `C:\workSpace\DeepLearnin_sleep\data\processed\daily_aggregates\surveys_participant_summary.csv` |
| `fitbit_steps_daily.csv` | 4,777 | 4 | `C:\workSpace\DeepLearnin_sleep\data\processed\daily_aggregates\fitbit_steps_daily.csv` |
| `fitbit_calories_daily.csv` | 6,660 | 4 | `C:\workSpace\DeepLearnin_sleep\data\processed\daily_aggregates\fitbit_calories_daily.csv` |
| `fitbit_wrist_temperature_daily.csv` | 3,304 | 6 | `C:\workSpace\DeepLearnin_sleep\data\processed\daily_aggregates\fitbit_wrist_temperature_daily.csv` |

## Boundary

- This step aggregates sources to the chosen unit.
- It does not yet merge all sources into one final modeling dataset.
- It does not impute missing values, encode categories beyond daily SEMA count/rate columns, scale, or run PCA.

## Next Step

```text
merge daily fitbit + daily sema + participant surveys -> final dataset EDA
```
