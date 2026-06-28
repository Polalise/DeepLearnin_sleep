# Missing Value Handling Summary

- Generated at: `2026-06-28T20:46:32`
- Input file: `C:\workSpace\DeepLearnin_sleep\data\processed\modeling_dataset_daily.csv`
- Output file: `C:\workSpace\DeepLearnin_sleep\data\processed\modeling_dataset_missing_handled.csv`
- Metadata file: `C:\workSpace\DeepLearnin_sleep\data\processed\missing_value_feature_metadata.csv`

## Scope

- This step handles missing values for numeric modeling features.
- It excludes direct same-night sleep outcome columns from model features.
- It does not perform categorical encoding, scaling, PCA, or modeling.

## Strategy

- Drop feature columns with missing rate greater than `70%`.
- Add missing indicators for retained columns that originally had missing values.
- Fill count/rate/sum/record-count style columns with `0` when missing.
- Fill other retained numeric columns with the column median.
- Preserve `participant_object_id`, `calendar_date`, and `good_sleep_label`.

## Output Shape

- Input rows: `3,551`
- Input columns: `130`
- Output rows: `3,551`
- Output columns: `200`
- Output missing cells: `0`
- Missing indicators added: `97`

## Action Counts

| action | columns |
| --- | ---: |
| `fill_zero_add_indicator` | 64 |
| `median_impute_add_indicator` | 33 |
| `keep_no_missing` | 3 |
| `drop_high_missing` | 1 |

## Actions By Feature Family

| family | action | columns |
| --- | --- | ---: |
| `activity` | `fill_zero_add_indicator` | 8 |
| `hrv` | `fill_zero_add_indicator` | 2 |
| `hrv` | `median_impute_add_indicator` | 19 |
| `respiratory` | `drop_high_missing` | 1 |
| `respiratory` | `fill_zero_add_indicator` | 1 |
| `respiratory` | `median_impute_add_indicator` | 5 |
| `resting_hr` | `keep_no_missing` | 3 |
| `sema` | `fill_zero_add_indicator` | 41 |
| `spo2` | `fill_zero_add_indicator` | 1 |
| `spo2` | `median_impute_add_indicator` | 3 |
| `stress` | `fill_zero_add_indicator` | 3 |
| `stress` | `median_impute_add_indicator` | 3 |
| `survey` | `fill_zero_add_indicator` | 7 |
| `temperature` | `fill_zero_add_indicator` | 1 |
| `temperature` | `median_impute_add_indicator` | 3 |

## Dropped High-Missing Columns

| column | family | missing rate |
| --- | --- | ---: |
| `respiratory_light_sleep_breathing_rate_mean` | `respiratory` | 83.78% |

## Excluded Non-Feature Or Leakage-Prone Columns

These columns are retained in earlier EDA outputs but excluded from the missing-handled modeling feature table.

```text
asleep_minutes
awake_minutes
awake_ratio
classic_asleep_ratio
classic_awake_ratio
classic_restless_ratio
deep_minutes
deep_ratio
efficiency
endTime
light_minutes
light_ratio
logId
minutesAsleep
minutesAwake
mongo_doc_id
rem_minutes
rem_ratio
restless_minutes
sleep_duration_hours
startTime
stress_sleep_points_mean
timeInBed
time_in_bed_hours
wake_minutes
wake_ratio
```

## Notes

- Stress score is retained as a candidate explanatory feature, but it may still carry sleep/recovery leakage risk.
- `stress_sleep_points_mean` is excluded because it is explicitly sleep-related.
- Missing indicators should help downstream models distinguish true low values from absent measurements.
- This missing-handled daily table is a valid starting point for the deep learning path after feature finalization.
- PCA is not required for the default deep learning workflow.

## Next Step

```text
categorical encoding / feature table finalization -> participant-aware split -> deep learning sequence dataset
```
