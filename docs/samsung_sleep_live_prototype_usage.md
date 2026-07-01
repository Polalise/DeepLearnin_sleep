# Samsung Sleep Forecasting Live Prototype Usage

## Purpose

Run a live-style sleep forecasting prototype with the existing final deep learning model:

```text
wearable data before sleep_start
-> Design C Stage 1 raw features
-> fitted median imputer
-> fitted StandardScaler
-> final PyTorch MLP
-> upcoming good_sleep_label probability
```

The trained model remains:

```text
presleep_stage1_hp_tiny_dropout40_wd1e3_seed2027
```

## Run

```powershell
cd C:\workSpace\DeepLearnin_sleep
.\.venv\Scripts\python.exe -m pip install -r requirements-prototype.txt
.\.venv\Scripts\python.exe -m streamlit run prototype\samsung_sleep_forecasting_app.py
```

## App Modes

### 1. Dashboard

The first screen is a live-style dashboard for presentation and review.

It shows:

```text
Samsung export file count
available prediction episode count
latest prediction target sleep_start_datetime
plain-language tonight/upcoming-sleep forecast sentence
latest good_sleep probability
snapshot probability delta, when a previous snapshot exists
current interpretation band
recent probability trend
model/caveat status panel
```

The dashboard is intentionally focused on the actual prediction surface rather than raw CSV/debug controls.

### 2. Tonight Forecast Update

This is the main live prototype flow.

The sidebar button is:

```text
오늘 밤 예측 갱신
```

The user selects an expected sleep-start date/time. The app then:

```text
Samsung Health latest export
-> completed sleep episode table update
-> today's target sleep episode CSV creation
-> Samsung-to-Fitbit raw Stage 1 feature build for that target
-> existing final MLP inference
-> plain-language tonight/upcoming-sleep forecast
```

This updates the model input features from current history and wearable data. It does not retrain the neural network.

The tonight forecast screen also shows feature coverage:

```text
history/baseline features reflected
current-day wearable features reflected
current-day wearable features left missing for imputer handling
raw feature values for key status fields
```

It also shows Samsung data freshness diagnostics:

```text
latest sleep-stage timestamp
latest sleep-summary timestamp
latest heart-rate timestamp
latest daily-step timestamp
latest interval-step timestamp
latest activity-summary timestamp
latest step-trend timestamp
```

This is used to explain whether a missing current-day feature is a model issue or an export coverage issue.

If Samsung Health does not include current-day intraday step or heart-rate rows, the user can enable manual current-day wearable supplements:

```text
today steps so far
steps in the last 3 hours
steps in the last 1 hour
pre-sleep mean heart rate
last 3-hour mean heart rate
last 1-hour mean heart rate
```

These supplement values are applied only to the today-forecast raw feature row before inference. They do not retrain the model and are recorded separately:

```text
data/processed/samsung_health/pre_sleep_stage1/live_forecast/today_manual_wearable_supplement_report.csv
```

The app also keeps a Samsung-only baseline prediction for the same target episode and compares it with the final prediction:

```text
data/processed/samsung_health/pre_sleep_stage1/live_forecast/today_samsung_only_raw_stage1_features.csv
data/processed/samsung_health/pre_sleep_stage1/live_forecast/today_samsung_only_prediction.csv
data/processed/samsung_health/pre_sleep_stage1/live_forecast/today_forecast_comparison.csv
```

Each successful today forecast run writes a timestamped snapshot:

```text
data/processed/samsung_health/pre_sleep_stage1/live_forecast/snapshots/
```

The UI reports:

```text
Samsung-only probability
final probability
supplement delta
label change
previous snapshot delta
```

The today forecast screen can also generate numeric sensitivity variants from the current raw feature row:

```text
today steps +1000 / -1000
last 1-hour steps +200 / -200
heart rate +5 / -5
expected sleep start +30 minutes / -30 minutes
```

Sensitivity output:

```text
data/processed/samsung_health/pre_sleep_stage1/live_forecast/today_numeric_sensitivity.csv
```

Tonight forecast outputs:

```text
data/processed/samsung_health/pre_sleep_stage1/live_forecast/today_sleep_target_episode.csv
data/processed/samsung_health/pre_sleep_stage1/live_forecast/today_raw_stage1_features.csv
data/processed/samsung_health/pre_sleep_stage1/live_forecast/today_sleep_forecast_prediction.csv
data/processed/samsung_health/pre_sleep_stage1/live_forecast/today_manual_wearable_supplement_report.csv
data/processed/samsung_health/pre_sleep_stage1/live_forecast/today_samsung_only_prediction.csv
data/processed/samsung_health/pre_sleep_stage1/live_forecast/today_forecast_comparison.csv
data/processed/samsung_health/pre_sleep_stage1/live_forecast/today_numeric_sensitivity.csv
data/processed/samsung_health/pre_sleep_stage1/live_forecast/snapshots/
data/processed/samsung_health/pre_sleep_stage1/live_forecast/today_stage1_feature_summary.csv
data/processed/samsung_health/pre_sleep_stage1/live_forecast/today_sleep_forecast_prediction_summary.csv
reports/samsung_today_sleep_forecast_feature_build_summary.md
reports/samsung_today_sleep_forecast_prediction_summary.md
```

### 3. Completed Episode Prediction

This mode uses a Samsung Health export folder as the default data source.

Default folder:

```text
C:\workSpace\DeepLearnin_sleep\docs\samsunghealth
```

The app also accepts another Samsung Health export folder path.

Expected Samsung Health files include:

```text
com.samsung.health.sleep_stage.*.csv
com.samsung.shealth.tracker.heart_rate.*.csv
com.samsung.shealth.tracker.pedometer_day_summary.*.csv
com.samsung.shealth.tracker.pedometer_step_count.*.csv
com.samsung.shealth.activity.day_summary.*.csv
```

When the user clicks `완료 episode 예측 갱신`, the app runs:

```text
scripts/30_build_samsung_sleep_episode_table.py
scripts/31_build_samsung_pre_sleep_stage1_features.py
scripts/32_run_samsung_pre_sleep_inference.py
```

The selected Samsung folder is passed through:

```text
SAMSUNG_HEALTH_DIR
```

Primary outputs:

```text
data/processed/samsung_health/pre_sleep_stage1/samsung_sleep_episodes.csv
data/processed/samsung_health/pre_sleep_stage1/samsung_raw_stage1_features.csv
data/processed/samsung_health/pre_sleep_stage1/samsung_pre_sleep_predictions.csv
data/processed/samsung_health/pre_sleep_stage1/samsung_pre_sleep_prediction_summary.csv
```

Prototype snapshots:

```text
data/processed/samsung_health/pre_sleep_stage1/prototype_snapshots/
```

### 4. Preset Quick Prediction

This mode is for partial-input prototype interaction.

The user enters directly available values such as:

```text
expected sleep start time
previous-day steps
steps before sleep
steps in the last 3 hours
steps in the last 1 hour
baseline calories
baseline resting heart rate
baseline active minutes
```

The user also chooses coarse presets:

```text
overall activity: increased / similar / decreased / unknown
calorie burn: high / similar / low / unknown
pre-sleep heart rate: high / similar / low / unknown
previous sleep condition: similar / good / bad / unknown
```

The app then builds a one-row Design C Stage 1 raw feature table:

```text
partial user inputs + presets
-> 70 raw Stage 1 features
-> missing indicators
-> existing imputer/scaler
-> existing final MLP
```

Preset mode outputs:

```text
data/processed/pre_sleep_forecasting/prototype_outputs/quick_preset_raw_stage1_features.csv
data/processed/pre_sleep_forecasting/prototype_outputs/quick_preset_prediction.csv
data/processed/pre_sleep_forecasting/prototype_outputs/quick_preset_feature_source_summary.csv
```

Important: this mode does not ask the user for the answer label. It asks for limited pre-sleep wearable context and coarse state presets, then uses the existing trained model to predict.

The quick prediction screen also reports feature-completeness status:

```text
raw feature count
directly entered or derived feature count
feature count left for the fitted imputer
missing/imputed ratio before imputation
probability interpretation band
```

### 5. Preset Scenario Comparison

This mode keeps the same direct numeric inputs and compares multiple preset combinations.

It is useful for showing that the prototype is not a fixed rule table:

```text
same sleep time and step inputs
-> activity preset variants
-> calorie preset variants
-> heart-rate preset variants
-> repeated final MLP inference
-> ranked probability comparison
```

Scenario comparison outputs:

```text
data/processed/pre_sleep_forecasting/prototype_outputs/quick_preset_scenario_comparison.csv
data/processed/pre_sleep_forecasting/prototype_outputs/quick_preset_scenario_raw_features.csv
```

### 6. Advanced Retraining Experiment

The app separates live prediction from model retraining.

The advanced tab currently creates a retraining experiment plan:

```text
reports/samsung_model_retraining_experiment_plan.md
```

It does not run training from the UI. A future retraining implementation should rebuild labeled data, train a candidate model, evaluate it, select a threshold, and save versioned artifacts without overwriting the selected final model.

## UI Behavior

The app shows:

- presentation-oriented dashboard
- tonight forecast update using the latest synchronized feature history/baseline inputs
- latest feature coverage status for history/baseline and current-day wearable inputs
- Samsung data freshness by source table
- explicit prediction target sleep-start time
- plain-language forecast such as "based on data so far, tonight's sleep is expected to..."
- Samsung Health file availability
- final deep learning model card
- Samsung prediction summary
- recent probability trend
- recent episode prediction table
- optional probability delta versus previous snapshot
- partial-input preset prediction
- feature source/completeness status for preset prediction
- preset scenario comparison
- highest/lowest scenario probability spread
- advanced retraining experiment planning surface
- generated raw feature source summary

## Caveat

This prototype uses the final Fitbit-trained Design C MLP. Samsung Health data and preset inputs are transformed into a Fitbit-compatible feature schema.

Samsung sync mode is a cross-device transfer diagnostic, not formal Samsung external validation.

Preset quick prediction is a limited-input demo mode. Missing values are handled by the training-time imputer, so the result should be interpreted as prototype feedback rather than a clinically reliable probability.
