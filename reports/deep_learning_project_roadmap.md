# Deep Learning Project Roadmap

- Created at: `2026-06-29`
- Project focus: deep learning sleep prediction from participant-date daily LifeSnaps data.
- Current status: deep learning sequence dataset creation is complete; deep learning model training has not started yet.

## Project Framing

This project should be read as a deep learning project.

Traditional ML outputs are retained only as baseline/reference material:

- DummyClassifier
- Logistic Regression
- Logistic Regression + PCA
- Random Forest
- Logistic Regression / Random Forest feature-set comparisons
- Logistic Regression / Random Forest tuning

PCA is retained only as exploratory feature-structure analysis:

- variance structure
- redundancy/correlation patterns
- feature-family clustering
- PC-space target visualization

PCA is not the default input for deep learning experiments.

## Target

- Prediction target: `good_sleep_label`
- Grain: participant-day
- Main modeling question: predict whether a participant-day is a good-sleep day using daily wearable/context/survey-derived signals.
- Split rule: participant-aware; the same participant must not appear across train/validation/test.

## Completed Work

| stage | status | main outputs | notes |
| --- | --- | --- | --- |
| MongoDB/raw data orientation | complete | `reports/mongodb_raw_overview.md`, `reports/fitbit_type_profile.md` | Source structure inspected. |
| Collection EDA | complete | `reports/collection_eda_summary.md` | Fitbit, SEMA, survey collections profiled. |
| Variable extraction | complete | `data/raw/extracted_variables/`, `reports/variable_extraction_summary.md` | Needed variables extracted from raw source. |
| Daily aggregation | complete | `data/processed/daily/`, `reports/daily_aggregation_summary.md` | Participant-date daily tables created. |
| Daily aggregate validation | complete | `reports/daily_aggregation_validation.md` | Duplicate/missing/date checks completed. |
| Merged participant-date dataset | complete | `data/processed/modeling_dataset_daily.csv`, `reports/merge_summary.md` | Daily feature tables joined to sleep target. |
| Final dataset EDA | complete | `reports/final_dataset_eda.md` | Missingness, target, correlations inspected. |
| Missing-value handling | complete | `data/processed/modeling_dataset_missing_handled.csv` | Leakage-prone sleep outcome columns excluded. |
| Feature finalization / encoding | complete | `data/processed/modeling_dataset_encoded.csv`, `data/processed/encoded_feature_columns.csv` | Main pre-PCA daily feature table for deep learning. |
| Exploratory scaling | complete | `data/processed/modeling_dataset_scaled.csv` | Full-table scaler retained for exploratory PCA/reference only. |
| Exploratory PCA | complete | `data/processed/modeling_dataset_pca.csv`, `reports/pca_summary.md` | Exploratory feature-structure analysis only. |
| Participant-aware train/test split | complete | `data/processed/splits/` | Reused by traditional ML and deep learning sequence creation. |
| Traditional ML reference baselines | complete | `reports/baseline_modeling_summary.md`, `reports/tuned_modeling_summary.md`, `reports/final_baseline_validation_report.md` | Reference only; not deep learning results. |
| Deep learning sequence dataset | complete | `data/processed/deep_learning_sequences/`, `reports/deep_learning_sequence_dataset_summary.md` | Rolling 7/14/30-day tensors created. |

## Current Deep Learning Dataset

Input source:

```text
data/processed/modeling_dataset_encoded.csv
data/processed/encoded_feature_columns.csv
data/processed/splits/participant_split_assignments.csv
```

Sequence output root:

```text
data/processed/deep_learning_sequences/
```

Tensor files:

```text
window_7/train.npz
window_7/validation.npz
window_7/test.npz
window_14/train.npz
window_14/validation.npz
window_14/test.npz
window_30/train.npz
window_30/validation.npz
window_30/test.npz
```

Each `.npz` contains:

- `X_sequence`: samples x time_steps x features for SimpleRNN, LSTM, GRU, BiLSTM, and 1D CNN.
- `X_mlp_flattened`: samples x time_steps*features for a flattened-window MLP.
- `X_mlp_current_day`: samples x features for a current-day tabular MLP.
- `y`
- `participant_object_id`
- `window_start_date`
- `window_end_date`
- `feature_names`

Current tensor summary:

| window | train | validation | test | feature count |
| ---: | ---: | ---: | ---: | ---: |
| 7 | 1,393 | 269 | 314 | 197 |
| 14 | 933 | 146 | 214 | 197 |
| 30 | 435 | 55 | 106 | 197 |

## Main Deep Learning Roadmap

### Phase 1. Dataset Contract And Loader

Status: next.

Tasks:

- Create reusable tensor loading utilities.
- Standardize batch format across MLP, SimpleRNN, LSTM, GRU, BiLSTM, and 1D CNN.
- Confirm label dtype, feature dtype, sequence axis convention, and metadata preservation.
- Add smoke tests that load every window/split `.npz`.

Recommended script:

```text
scripts/20_prepare_deep_learning_loaders.py
```

### Phase 2. MLP Baselines

Status: not started.

Purpose:

- Establish deep learning tabular baselines before sequence models.
- Compare current-day MLP against flattened-window MLP.

Experiments:

- `X_mlp_current_day` for windows 7/14/30.
- `X_mlp_flattened` for windows 7/14/30.
- Early stopping on validation balanced accuracy or validation loss.

Recommended script:

```text
scripts/21_train_mlp_baselines.py
```

### Phase 3. Sequence Deep Learning Models

Status: not started.

Purpose:

- Evaluate whether temporal order improves over daily tabular baselines.

Experiments:

- SimpleRNN on `X_sequence`.
- LSTM on `X_sequence`.
- GRU on `X_sequence`.
- BiLSTM on `X_sequence`.
- 1D CNN on `X_sequence`.
- Windows: 7, 14, 30 days.

Recommended script:

```text
scripts/22_train_sequence_models.py
```

### Phase 4. Model Comparison

Status: not started.

Purpose:

- Compare all deep learning experiments against the traditional ML reference baseline.
- Avoid calling LR/RF the final model unless they remain stronger after deep learning evaluation.
- Select the final candidate by validation-first model selection, then held-out participant test evaluation.

Metrics:

- balanced accuracy
- ROC AUC
- average precision
- F1
- precision
- recall
- confusion matrix
- participant-level bootstrap intervals for the selected candidate

Comparison stages:

1. Use validation metrics for model family, window length, and hyperparameter selection.
2. Evaluate the selected candidate once on the held-out participant test split.
3. Compare against `wearable_only + Logistic Regression` as the traditional ML reference baseline.
4. Prefer the simpler model when performance differences are within uncertainty.
5. Report participant-level uncertainty before calling any model final.

Recommended script:

```text
scripts/23_compare_deep_learning_models.py
```

Detailed roadmap:

```text
reports/deep_learning_model_comparison_roadmap.md
```

### Phase 5. Robustness And Leakage Review

Status: not started.

Questions:

- Should same-day features be allowed?
- Should the target be tomorrow's sleep from prior-day features instead?
- Should availability/count features be allowed in final interpretation?
- How sensitive are results to participant composition?
- Are there enough samples for 30-day sequence models, or should 7/14-day windows be prioritized?

Recommended report:

```text
reports/deep_learning_robustness_and_leakage_review.md
```

### Phase 6. Final Deep Learning Report

Status: not started.

Contents:

- selected deep learning model family
- selected window length
- comparison against traditional ML reference baseline
- participant-aware validation limitations
- calibration and threshold notes
- recommended next data/model improvements

Recommended report:

```text
reports/final_deep_learning_model_report.md
```

## Current Position

The project is here:

```text
raw data / EDA
-> daily participant-date dataset
-> missing handling / encoding
-> exploratory PCA and traditional ML reference baselines
-> deep learning sequence tensors
-> NEXT: deep learning loaders and first MLP/sequence experiments
```

In short:

```text
Deep learning data preparation is complete.
Deep learning model training is the next unfinished stage.
```

## Immediate Next Actions

1. Create a reusable deep learning data loader script.
2. Train MLP baselines on `X_mlp_current_day` and `X_mlp_flattened`.
3. Train SimpleRNN, LSTM, GRU, BiLSTM, and 1D CNN on `X_sequence`.
4. Compare deep learning models against `wearable_only + Logistic Regression` as a reference baseline only.
5. Write the first deep learning model comparison report.
