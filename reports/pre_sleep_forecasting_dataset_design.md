# Pre-Sleep Forecasting Dataset Design

## Purpose

The new prediction goal is:

`Use wearable/context data available before sleep onset on the same day, plus prior history, to predict the quality of the upcoming sleep episode.`

The prediction unit is a participant-level sleep episode.

## Key Alignment Rule

Prediction time:

`prediction_time = sleep_start_datetime`

Allowed predictors:

`feature_timestamp < sleep_start_datetime`

Forbidden predictors:

- target sleep episode outcomes
- sleep duration, time in bed, efficiency, sleep stages
- target sleep respiratory summaries
- target sleep HRV or SpO2
- any feature generated after sleep onset/end

## Source Findings

Sleep episode source files:

- `data/processed/daily_aggregates/sleep_daily_target.csv`
- `data/processed/modeling_dataset_daily.csv`

Both contain:

- `participant_object_id`
- `calendar_date`
- `startTime`
- `endTime`
- `good_sleep_label`

The existing `calendar_date` matches sleep end date for all rows.

| item | value |
| --- | ---: |
| sleep episodes | 3551 |
| participants | 69 |
| target mean | 0.3937 |
| calendar date matches sleep end date | 1.0000 |
| cross-midnight sleep ratio | 0.3799 |

This means the previous same-date experiments used sleep-end-date alignment and should not be interpreted as pre-sleep forecasting.

## Design Options

### Design A: Conservative Previous-Day History

Uses `sleep_start_date - 1` daily features.

- Low leakage risk
- Does not include same-day pre-sleep activity
- Useful as conservative baseline

### Design B: Sleep-Start-Date Daily Approximation

Uses daily aggregate features from `sleep_start_date`.

- Coverage: approximately 95.7%
- More aligned with pre-sleep prediction than sleep-end-date same-date features
- But full-day daily aggregates can include small post-bedtime activity
- Useful as approximation/comparison only

### Design C: Strict Intraday Pre-Sleep Aggregation

Uses MongoDB intraday Fitbit documents and cuts every feature at `sleep_start_datetime`.

Confirmed MongoDB source types:

| Fitbit type | timestamp field | value field | notes |
| --- | --- | --- | --- |
| `steps` | `data.dateTime` | `data.value` | intraday step counts |
| `calories` | `data.dateTime` | `data.value` | minute-level calories |
| `heart_rate` | `data.dateTime` | `data.value.bpm`, `data.value.confidence` | high-frequency heart rate |

Prototype aggregation confirmed nonzero records for pre-sleep windows and timestamps stopped before sleep onset.

## Selected Design

Selected design:

`Design C: strict intraday pre-sleep forecasting dataset`

Reason:

- It best matches the real prediction objective.
- It uses only data available before sleep onset.
- It avoids sleep-end-date leakage.
- MongoDB contains enough intraday steps, calories, and heart-rate data to build the dataset.

## Feature Specification

| feature group | source | time window | include first dataset | leakage risk |
| --- | --- | --- | --- | --- |
| `pre_sleep_steps` | MongoDB fitbit type=steps | sleep_start_date 00:00 <= timestamp < sleep_start_datetime | True | low |
| `pre_sleep_calories` | MongoDB fitbit type=calories | sleep_start_date 00:00 <= timestamp < sleep_start_datetime | True | low |
| `pre_sleep_heart_rate` | MongoDB fitbit type=heart_rate | sleep_start_date 00:00 <= timestamp < sleep_start_datetime | True | low |
| `pre_sleep_window_timing` | sleep_daily_target.csv startTime | known at prediction time | True | low |
| `previous_day_daily_activity` | processed daily aggregates | sleep_start_date - 1 day | True | low |
| `rolling_history` | Design C pre-sleep features and previous-day daily features | previous 3/7 available days before current sleep episode | True | low |
| `target_sleep_outcome_features` | target sleep episode | after sleep onset/end | False | high |
| `same_day_daily_aggregate` | processed daily aggregates | full sleep_start_date | False | medium |


## Recommended Implementation Staging

### Stage 1

Create a strict Design C tabular dataset with:

- pre-sleep steps
- pre-sleep calories
- pre-sleep heart rate
- pre-sleep timing/calendar features
- previous-day daily activity/resting-HR features

### Stage 2

Add rolling/trend features after Stage 1 validation:

- 3-day rolling mean/std/min/max
- 7-day rolling mean/std/min/max
- 1-day difference
- deviation from rolling means

### Stage 3

Create tensors for:

- MLP current episode
- GRU window 7
- optional GRU window 14

## Next Notebook

Recommended next notebook:

`notebooks/11_create_pre_sleep_forecasting_dataset.ipynb`

Goal:

Create the strict Design C dataset from MongoDB intraday steps/calories/heart_rate plus previous-day daily features.

## Interpretation Boundary

The earlier best model remains useful as a same-date sleep classification result:

`phase1a_003 / same_date / daytime_only / window 7 / mlp_current_day`

However, the new pre-sleep forecasting objective requires a new sleep-start-aligned dataset. The earlier same-date model should not be used as evidence of strict pre-sleep forecasting performance.
