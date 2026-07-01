# Raw Feature Inference Debug Tool Usage

## Purpose

Run the selected Design C Stage 1 MLP through a lightweight Streamlit debug UI.

This tool accepts a CSV that already contains the 70 raw Stage 1 inference features. It is a researcher/debug tool for checking the inference package with an already-built raw feature table.

This is not the final end-to-end Samsung Health live prototype.

## Install Dependency

```powershell
cd C:\workSpace\DeepLearnin_sleep
.\.venv\Scripts\python.exe -m pip install -r requirements-prototype.txt
```

## Run Debug App

```powershell
cd C:\workSpace\DeepLearnin_sleep
.\.venv\Scripts\python.exe -m streamlit run prototype\pre_sleep_inference_app.py
```

## Supported Input Modes

- Upload raw Stage 1 feature CSV.
- Load raw Stage 1 feature CSV from a local path.
- Load the existing sample raw feature CSV.
- Load Samsung diagnostic raw features.

This app does not:

- read Samsung Health raw export folders directly
- create sleep episodes
- build Stage 1 features from raw wearable files
- simulate mobile sync

Those functions belong in the separate Samsung live forecasting prototype.

## Expected Input

The CSV must contain the 70 raw Design C Stage 1 features expected by:

```text
data/processed/pre_sleep_forecasting/design_c_stage1/inference_package/pre_sleep_inference_manifest.json
```

Optional passthrough columns:

```text
sleep_episode_id
participant_object_id
sleep_start_datetime
prediction_cutoff_datetime
```

## Output

The app writes and offers a download for prediction CSV output with:

```text
sleep_episode_id
participant_object_id
sleep_start_datetime
prediction_cutoff_datetime
good_sleep_probability
good_sleep_pred
threshold
```

Default output path:

```text
data/processed/pre_sleep_forecasting/prototype_outputs/pre_sleep_predictions_from_app.csv
```

## Thresholds

Available UI options:

- official threshold: `0.54`
- recall reference threshold: `0.47`
- custom threshold

## Samsung Caveat

Samsung mode is for cross-device transfer diagnostics only.

Samsung Health data can be transformed into a Fitbit-compatible feature schema, but the current Samsung diagnostic did not provide formal external validation and should not be interpreted as a reliable Samsung good-sleep classifier.
