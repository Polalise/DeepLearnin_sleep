# Codex Guide: LifeSnaps Sleep Health Prediction

Last updated: 2026-06-26

## 1. Project Goal

This project predicts sleep health using wearable data and stress-related indicators.

The key modeling direction is:

```text
Input variables:
wearable physiological data + activity data + stress/emotion/context indicators

Prediction target:
sleep health
```

Stress is not the final prediction target. Stress is an explanatory/input variable for predicting sleep quality, sleep efficiency, sleep duration, or a good/bad sleep label.

Recommended project title:

```text
Sleep Health Prediction Using Wearable Physiological Signals and Stress Indicators
```

## 2. Selected Dataset

Main dataset:

```text
LifeSnaps Dataset
Zenodo latest open version: https://zenodo.org/records/7229547
Downloaded file: rais_anonymized.zip
```

Local extracted path:

```text
C:\Users\human-23\Downloads\rais_anonymized
```

Important subfolders:

```text
C:\Users\human-23\Downloads\rais_anonymized\mongo_rais_anonymized
C:\Users\human-23\Downloads\rais_anonymized\csv_rais_anonymized
C:\Users\human-23\Downloads\rais_anonymized\scored_surveys
```

MongoDB BSON files:

```text
C:\Users\human-23\Downloads\rais_anonymized\mongo_rais_anonymized\fitbit.bson
C:\Users\human-23\Downloads\rais_anonymized\mongo_rais_anonymized\sema.bson
C:\Users\human-23\Downloads\rais_anonymized\mongo_rais_anonymized\surveys.bson
```

CSV files:

```text
C:\Users\human-23\Downloads\rais_anonymized\csv_rais_anonymized\daily_fitbit_sema_df_unprocessed.csv
C:\Users\human-23\Downloads\rais_anonymized\csv_rais_anonymized\hourly_fitbit_sema_df_unprocessed.csv
```

Survey score files:

```text
C:\Users\human-23\Downloads\rais_anonymized\scored_surveys\breq.csv
C:\Users\human-23\Downloads\rais_anonymized\scored_surveys\panas.csv
C:\Users\human-23\Downloads\rais_anonymized\scored_surveys\personality.csv
C:\Users\human-23\Downloads\rais_anonymized\scored_surveys\stai.csv
C:\Users\human-23\Downloads\rais_anonymized\scored_surveys\ttm.csv
```

## 3. Current Data Status

CSV data has already been uploaded to MongoDB Atlas:

```text
Database: rais_anonymized
Collections:
- daily_fitbit_sema
- hourly_fitbit_sema
```

Local MongoDB is used for the large BSON source data, especially `fitbit.bson`.

Observed local MongoDB document counts:

```text
fitbit  ~= 71M
sema    = 15,380
surveys = 935
```

These counts are plausible. `fitbit` is very large because it contains original Fitbit-derived logs.

## 4. MongoDB Setup

Installed MongoDB server:

```text
C:\Program Files\MongoDB\Server\8.0.25\bin\mongod.exe
```

Installed MongoDB Database Tools:

```text
C:\Program Files\MongoDB\Tools\100.17.0\bin\mongorestore.exe
C:\Program Files\MongoDB\Tools\100.17.0\bin\mongoimport.exe
```

Local DB storage path:

```text
F:\mongodb-lifesnaps\data
```

Start local MongoDB:

```powershell
& "C:\Program Files\MongoDB\Server\8.0.25\bin\mongod.exe" --dbpath "F:\mongodb-lifesnaps\data" --bind_ip 127.0.0.1 --port 27017
```

The PowerShell or BAT window running `mongod` must stay open while using local MongoDB.

Local connection string:

```text
mongodb://localhost:27017
```

Recommended helper BAT file content:

```bat
@echo off
"C:\Program Files\MongoDB\Server\8.0.25\bin\mongod.exe" --dbpath "F:\mongodb-lifesnaps\data" --bind_ip 127.0.0.1 --port 27017
pause
```

## 5. Restore Commands

Use `--drop` if a collection may already exist and should be rebuilt from the BSON source.

Restore `fitbit`:

```powershell
& "C:\Program Files\MongoDB\Tools\100.17.0\bin\mongorestore.exe" `
  --host localhost:27017 `
  --db rais_anonymized `
  --collection fitbit `
  --drop `
  "C:\Users\human-23\Downloads\rais_anonymized\mongo_rais_anonymized\fitbit.bson"
```

Restore `sema`:

```powershell
& "C:\Program Files\MongoDB\Tools\100.17.0\bin\mongorestore.exe" `
  --host localhost:27017 `
  --db rais_anonymized `
  --collection sema `
  --drop `
  "C:\Users\human-23\Downloads\rais_anonymized\mongo_rais_anonymized\sema.bson"
```

Restore `surveys`:

```powershell
& "C:\Program Files\MongoDB\Tools\100.17.0\bin\mongorestore.exe" `
  --host localhost:27017 `
  --db rais_anonymized `
  --collection surveys `
  --drop `
  "C:\Users\human-23\Downloads\rais_anonymized\mongo_rais_anonymized\surveys.bson"
```

## 6. Atlas vs Local MongoDB

Use Atlas for small or modeling-ready tables:

```text
daily_fitbit_sema
hourly_fitbit_sema
```

Use local MongoDB for the original large BSON:

```text
fitbit
sema
surveys
```

Do not try to upload the full `fitbit.bson` to a small/free Atlas cluster. It is too large and unnecessary for early analysis.

## 7. Recommended Analysis Strategy

Start with CSV for fast EDA and baseline modeling:

```text
daily_fitbit_sema_df_unprocessed.csv
```

Then use local MongoDB `fitbit` only when deeper feature engineering is needed.

Practical workflow:

1. Load daily CSV.
2. Define sleep health target.
3. Run EDA and missing-value checks.
4. Train baseline model.
5. Identify which additional raw Fitbit features are needed.
6. Query local MongoDB for only those raw records.
7. Add engineered features and compare model performance.

## 8. Core Variables

Important daily CSV columns already confirmed:

```text
id
date
nightly_temperature
nremhr
rmssd
spo2
full_sleep_breathing_rate
stress_score
sleep_points_percentage
exertion_points_percentage
responsiveness_points_percentage
daily_temperature_variation
calories
bpm
lightly_active_minutes
moderately_active_minutes
very_active_minutes
sedentary_minutes
scl_avg
resting_hr
sleep_duration
minutesToFallAsleep
minutesAsleep
minutesAwake
minutesAfterWakeup
sleep_efficiency
sleep_deep_ratio
sleep_wake_ratio
sleep_light_ratio
sleep_rem_ratio
steps
age
gender
bmi
ALERT
HAPPY
NEUTRAL
RESTED/RELAXED
SAD
TENSE/ANXIOUS
TIRED
ENTERTAINMENT
GYM
HOME
HOME_OFFICE
OTHER
OUTDOORS
TRANSIT
WORK/SCHOOL
```

Recommended input groups:

```text
Stress/emotion:
stress_score, TENSE/ANXIOUS, TIRED, RESTED/RELAXED, HAPPY, SAD

Physiology:
rmssd, resting_hr, nremhr, bpm, spo2, nightly_temperature, scl_avg

Activity:
steps, calories, sedentary_minutes, lightly_active_minutes,
moderately_active_minutes, very_active_minutes

Context:
HOME, HOME_OFFICE, WORK/SCHOOL, GYM, OUTDOORS, TRANSIT, ENTERTAINMENT

Demographics:
age, gender, bmi
```

## 9. Prediction Targets

Recommended target options:

```text
Regression:
- sleep_efficiency
- sleep_duration
- minutesAsleep
- minutesAwake

Classification:
- good_sleep_label
```

Suggested first classification rule:

```text
good_sleep_label = 1 if sleep_efficiency >= 85 and minutesAsleep >= 420
good_sleep_label = 0 otherwise
```

This is a practical rule for a student project, not a medical diagnosis.

## 10. Modeling Plan

Baseline models:

```text
Regression:
- Linear Regression
- Random Forest Regressor
- XGBoost or Gradient Boosting if available

Classification:
- Logistic Regression
- Random Forest Classifier
- XGBoost or Gradient Boosting if available
```

Evaluation:

```text
Regression:
- MAE
- RMSE
- R2

Classification:
- Accuracy
- F1-score
- ROC-AUC if class balance allows
```

Important split guidance:

```text
Avoid random row split if possible.
Prefer participant-aware split or time-based split.
Reason: multiple rows from the same person can leak personal patterns into train/test.
```

Recommended first split:

```text
Group split by id
```

## 11. Leakage Caution

Be careful with `stress_score`.

Fitbit stress score may internally depend on sleep or recovery-related signals. If predicting the same night's sleep, this can create leakage.

Safer feature choices:

```text
- previous-day stress_score
- daytime emotion/EMA variables
- activity before sleep
- previous sleep history
```

For a first presentation model, it is acceptable to include `stress_score`, but mention the leakage risk as a limitation.

## 12. Presentation Framing

Use this framing:

```text
LifeSnaps provides wearable, EMA, and survey data from real-life Fitbit use.
The project uses stress and affective indicators as explanatory variables for sleep health prediction.
The large original Fitbit BSON data was restored locally, while the provided daily/hourly CSV tables support reproducible baseline modeling.
```

Expected conclusion style:

```text
Wearable data can be used not only for passive tracking, but also for sleep health prediction.
Stress and emotion indicators can be used as meaningful input variables for explaining sleep health risk.
```

Limitations:

```text
- Not a medical diagnostic model.
- Fitbit-derived values are consumer wearable estimates.
- Stress score may include recovery/sleep-related components.
- Individual differences are large.
- Participant-aware validation is needed.
```

## 13. Next Tasks for Codex

When continuing this project, do these in order:

1. Create a project notebook or script under this repository.
2. Load `daily_fitbit_sema_df_unprocessed.csv`.
3. Print shape, columns, missing values, and basic target distributions.
4. Build `good_sleep_label`.
5. Train a simple baseline model using group split by `id`.
6. Report feature importance.
7. Compare model with and without stress/emotion variables.
8. If needed, query local MongoDB `fitbit` to engineer more detailed sleep or HRV features.

Suggested output files:

```text
deepLearning/wearable_project/notebooks/01_lifesnaps_eda.ipynb
deepLearning/wearable_project/notebooks/02_sleep_prediction_baseline.ipynb
deepLearning/wearable_project/reports/lifesnaps_sleep_prediction_summary.md
```
