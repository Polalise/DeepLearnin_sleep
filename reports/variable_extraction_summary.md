# Variable Extraction Summary

- Mongo URI: `mongodb://localhost:27017`
- Database: `rais_anonymized`
- Generated at: `2026-06-27T01:57:39`

## Scope

- This report covers the needed-variable extraction step.
- Output tables are first-extract/raw tables saved under `data/raw/extracted_variables/`.
- No cross-source merge, imputation, categorical encoding, scaling, or PCA was performed.

## Extracted Tables

| table | source | rows | columns | path |
| --- | --- | ---: | ---: | --- |
| `fitbit_stress_score` | `fitbit.Stress Score` | 1,911 | 14 | `C:\workSpace\DeepLearnin_sleep\data\raw\extracted_variables\fitbit_stress_score.csv` |
| `fitbit_daily_hrv_summary` | `fitbit.Daily Heart Rate Variability Summary` | 2,475 | 7 | `C:\workSpace\DeepLearnin_sleep\data\raw\extracted_variables\fitbit_daily_hrv_summary.csv` |
| `fitbit_hrv_details` | `fitbit.Heart Rate Variability Details` | 220,512 | 8 | `C:\workSpace\DeepLearnin_sleep\data\raw\extracted_variables\fitbit_hrv_details.csv` |
| `fitbit_resting_heart_rate` | `fitbit.resting_heart_rate` | 12,362 | 7 | `C:\workSpace\DeepLearnin_sleep\data\raw\extracted_variables\fitbit_resting_heart_rate.csv` |
| `fitbit_activity_minutes` | `fitbit activity-minute types` | 28,812 | 5 | `C:\workSpace\DeepLearnin_sleep\data\raw\extracted_variables\fitbit_activity_minutes.csv` |
| `fitbit_daily_spo2` | `fitbit.Daily SpO2` | 1,274 | 7 | `C:\workSpace\DeepLearnin_sleep\data\raw\extracted_variables\fitbit_daily_spo2.csv` |
| `fitbit_respiratory_rate_summary` | `fitbit.Respiratory Rate Summary` | 3,000 | 10 | `C:\workSpace\DeepLearnin_sleep\data\raw\extracted_variables\fitbit_respiratory_rate_summary.csv` |
| `sema_responses` | `sema` | 15,380 | 26 | `C:\workSpace\DeepLearnin_sleep\data\raw\extracted_variables\sema_responses.csv` |
| `surveys_responses` | `surveys` | 935 | 212 | `C:\workSpace\DeepLearnin_sleep\data\raw\extracted_variables\surveys_responses.csv` |

## Large Sources Reserved For Date-Level Aggregation

The following Fitbit sources are useful but very large. They should be aggregated
directly from MongoDB in the next step instead of exporting full raw CSV files now.

| source | count from EDA | aggregation idea |
| --- | ---: | --- |
| `fitbit.steps` | 3,010,529 | daily sum by participant/date |
| `fitbit.calories` | 9,675,782 | daily sum by participant/date |
| `fitbit.Wrist Temperature` | 4,372,238 | daily mean/min/max by participant/date |

## Next Step

```text
date-level aggregation -> merge fitbit/sema/surveys -> final dataset EDA
```
