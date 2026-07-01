# Pre-Sleep Forecasting Final One-Page Summary

## What Was Done

This project built a strict pre-sleep forecasting workflow:

```text
Use wearable-derived data available before sleep_start_datetime to predict the upcoming sleep episode good_sleep_label.
```

Completed work:

- Reframed the task from same-date sleep classification to strict pre-sleep forecasting.
- Built Design C Stage 1 raw pre-sleep features.
- Trained and compared PyTorch MLP candidates.
- Selected a compact regularized MLP as the final model.
- Added uncertainty, calibration, sequence-model follow-up, and inference packaging.
- Built a reusable inference package with feature contract, imputer, scaler, model checkpoint, and documentation.
- Tested Samsung Health as a Fitbit-compatible cross-device transfer diagnostic.

## Final Model

- Experiment family: `presleep_stage1_hp_tiny_dropout40_wd1e3`
- Representative checkpoint: `presleep_stage1_hp_tiny_dropout40_wd1e3_seed2027`
- Feature set: Design C Stage 1 strict pre-sleep features
- Model: PyTorch MLP
- Hidden dimensions: `(24, 12)`
- Dropout: `0.40`
- Weight decay: `0.001`
- Official threshold: `0.54`

Inference contract:

```text
70 raw Stage 1 features
-> train median imputer
-> train StandardScaler
-> remove 12 zero-variance features
-> 58 model input features
-> MLP sigmoid probability
-> threshold 0.54
```

## Performance And Limits

Held-out participant test performance:

- Balanced accuracy: `0.6492`
- ROC AUC: `0.6937`
- Average precision: `0.6187`
- Precision: `0.6553`
- Recall: `0.4245`
- Participant bootstrap BA 95% CI: `[0.5436, 0.7259]`
- Brier score: `0.2126`
- ECE: `0.1256`

Interpretation:

- The final model shows moderate strict pre-sleep predictive signal.
- Recall is limited at the official threshold.
- Probability should be treated as a model score, not a calibrated real-world probability.
- This is research-grade and not suitable for clinical or high-stakes use.

## Samsung Health Conclusion

Samsung Health data were processed as a cross-device transfer diagnostic:

```text
Samsung raw data
-> Samsung sleep episodes
-> Fitbit-compatible Stage 1 features
-> existing Design C inference package
-> proxy-label diagnostics
```

Findings:

- Samsung feature adaptation is technically possible.
- Pre-sleep heart-rate and previous-day activity features are usable.
- Pre-sleep step/calorie interval coverage is sparse because interval source data cover only a short recent date range.
- Samsung sleep-score proxy labels matched only `64 / 1493` episodes.
- Samsung stage proxy label v1 covered all `1493` episodes but was highly imbalanced.
- Existing Fitbit-trained MLP did not transfer reliably to Samsung stage-proxy labels:
  - ROC AUC rank approximation: `0.3224`
  - official threshold BA: `0.4972`
  - sensitivity: `0.0000`

Conclusion:

```text
Samsung Health can be transformed into a Fitbit-compatible feature schema for diagnostics,
but the current Samsung run is not formal external validation.
```

## How To Predict New Data

General Design C inference:

```powershell
cd C:\workSpace\DeepLearnin_sleep
.\.venv\Scripts\Activate.ps1

python src\pre_sleep_forecasting\feature_builder.py `
  --episodes data\processed\pre_sleep_forecasting\new_data\episodes_to_predict.csv `
  --output data\processed\pre_sleep_forecasting\new_data\raw_stage1_features.csv

python src\pre_sleep_forecasting\inference.py `
  --input data\processed\pre_sleep_forecasting\new_data\raw_stage1_features.csv `
  --output data\processed\pre_sleep_forecasting\new_data\predictions.csv
```

Samsung diagnostic workflow is documented in:

```text
docs/samsung_pre_sleep_external_inference_usage.md
reports/samsung_to_fitbit_feature_mapping_confidence.md
```

## Final State

The final deliverable is the Design C Stage 1 MLP inference package plus documented follow-up diagnostics. Samsung Health work is included as a cross-device transfer diagnostic and future-work guide, not as a validated deployment target.
