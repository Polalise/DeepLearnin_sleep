# Pre-Modeling Design Report For Deep Learning

- Created at: `2026-06-29`
- Project framing: deep learning sleep prediction project
- Main downstream path: participant-date daily data before PCA -> rolling sequence tensors -> MLP / SimpleRNN / LSTM / GRU / BiLSTM / 1D CNN
- Reference only: Logistic Regression, Random Forest, DummyClassifier, Logistic Regression + PCA

## 1. Why This Pre-Modeling Design Matters

The current project is not just a model-training task. The most important design work happens before deep learning:

- deciding the prediction grain
- defining the target
- checking data coverage and leakage risk
- choosing missing-value rules
- preserving participant-aware splits
- understanding feature structure before sequence modeling

The final deep learning tensors are only meaningful because the earlier EDA, preprocessing, missing-value handling, and exploratory PCA steps established the modeling contract.

## 2. Data Unit And Target Design

The analysis was standardized to a participant-date daily unit:

```text
participant_object_id + calendar_date
```

Main target:

```text
good_sleep_label
```

Dataset after daily merge:

- rows: `3,551`
- columns before missing handling: `130`
- participants: `69`
- date range: `2021-05-24` to `2022-01-22`
- duplicate participant-date rows: `0`
- target class balance:
  - `good_sleep_label=0`: `2,153` rows, `60.63%`
  - `good_sleep_label=1`: `1,398` rows, `39.37%`

Design decision:

- The unit was kept at participant-day because sleep labels and wearable/context signals can be aligned naturally by date.
- Participant identity is preserved only for splitting and diagnostics, not used as a model feature.
- Calendar date is preserved for ordering, rolling windows, and temporal diagnostics, not used as a direct categorical feature.

Primary source report:

```text
reports/final_dataset_eda.md
```

## 3. EDA Design And What Was Checked

EDA was performed before imputation, encoding, scaling, PCA, or modeling.

Main EDA checks:

1. Dataset shape and participant coverage
2. Date range and duplicate participant-date rows
3. Target distribution
4. Missingness by feature family
5. Highest-missing columns
6. Feature mean differences by target
7. Absolute correlation with target
8. IQR-based outlier rates
9. Leakage-prone sleep outcome columns

Important EDA findings:

- The merged dataset has no duplicate participant-date rows.
- The target is moderately imbalanced but not a rare-event problem.
- Missingness varies strongly by data family:
  - SpO2 average missing rate: `65.36%`
  - Stress average missing rate: `47.48%`
  - SEMA average missing rate: `32.55%`
  - HRV average missing rate: about `30%`
  - Activity and resting heart rate have high coverage.
- Some direct sleep-stage columns are highly correlated with the target, but they are not valid predictors because they are derived from the same sleep event.

Examples from EDA:

- `asleep_minutes` had high target correlation (`0.830`) but was excluded as leakage-prone.
- `light_minutes`, `rem_minutes`, `deep_minutes`, `wake_minutes`, and related sleep-stage variables were treated as outcome-adjacent rather than predictor-safe.
- `stress_sleep_points_mean` was excluded because it is explicitly sleep-related.

Design interpretation:

- EDA was used not to select a final model, but to decide which feature families are safe, how missingness should be represented, and what risks must be documented before deep learning.

## 4. Preprocessing Design

The preprocessing flow created a reproducible daily feature table before deep learning sequence creation:

```text
modeling_dataset_daily.csv
-> modeling_dataset_missing_handled.csv
-> modeling_dataset_encoded.csv
-> participant-aware split
-> deep_learning_sequences/
```

Key preprocessing decisions:

- Preserve `participant_object_id`, `calendar_date`, and `good_sleep_label`.
- Exclude direct same-night sleep outcome columns from predictors.
- Keep candidate wearable, HRV, stress, activity, SpO2, respiratory, SEMA, survey, and temperature features where appropriate.
- Avoid using participant ID or calendar date as model predictors.
- Treat PCA and full-table scaling as exploratory/reference outputs, not default deep learning inputs.

Final encoded daily feature table:

```text
data/processed/modeling_dataset_encoded.csv
```

Feature metadata:

```text
data/processed/encoded_feature_columns.csv
```

Encoded feature count:

```text
197
```

Important note:

- No categorical predictor columns were found after missing-value handling, so no one-hot columns were added in this run.
- The encoded daily table is the main pre-PCA input for deep learning sequence creation.

## 5. Missing-Value Handling Design

Missing-value handling was explicit and feature-type aware.

Input:

```text
data/processed/modeling_dataset_daily.csv
```

Output:

```text
data/processed/modeling_dataset_missing_handled.csv
```

Metadata:

```text
data/processed/missing_value_feature_metadata.csv
```

Rules:

| rule | reason |
| --- | --- |
| Drop columns with missing rate greater than `70%` | Avoid extremely sparse predictors. |
| Add missing indicators for retained columns with missingness | Preserve whether a measurement was absent. |
| Fill count/rate/sum/record-count style missing values with `0` | Missing often means no record or no observed event for that day. |
| Fill other retained numeric columns with median | Conservative numeric imputation that limits outlier influence. |
| Exclude direct same-night sleep outcome columns | Avoid target leakage. |

Action counts:

| action | columns |
| --- | ---: |
| `fill_zero_add_indicator` | 64 |
| `median_impute_add_indicator` | 33 |
| `keep_no_missing` | 3 |
| `drop_high_missing` | 1 |

Output after missing handling:

- rows: `3,551`
- columns: `200`
- output missing cells: `0`
- missing indicators added: `97`

Dropped high-missing column:

```text
respiratory_light_sleep_breathing_rate_mean
```

Reason:

- missing rate `83.78%`

Leakage-prone or non-feature columns excluded included:

```text
asleep_minutes
awake_minutes
classic_asleep_ratio
classic_awake_ratio
classic_restless_ratio
deep_minutes
deep_ratio
efficiency
light_minutes
light_ratio
minutesAsleep
minutesAwake
rem_minutes
rem_ratio
sleep_duration_hours
stress_sleep_points_mean
timeInBed
time_in_bed_hours
wake_minutes
wake_ratio
```

Design interpretation:

- Missingness was treated as potentially informative, especially for wearable/device coverage.
- Missing indicators were kept so deep learning models can learn patterns of absent measurements without confusing them with true low values.
- Availability/count features remain a modeling-design question and should be reviewed during robustness analysis.

## 6. Scaling Design

Full-table scaling was performed for exploratory PCA and traditional ML reference work:

```text
data/processed/modeling_dataset_scaled.csv
```

But this full-table scaler is not the default deep learning scaler.

Reason:

- Full-table scaling was fit before final deep learning train/validation/test tensor creation and is therefore treated as exploratory/reference preprocessing.
- The deep learning sequence creation script fits a separate scaler on deep-learning train rows only, then applies it to validation and test rows.

Deep learning scaler:

```text
data/processed/deep_learning_sequences/deep_learning_standard_scaler.joblib
```

Design interpretation:

- This avoids train/validation/test leakage in the tensor workflow.
- The deep learning tensors are the correct scaled inputs for MLP, SimpleRNN, LSTM, GRU, BiLSTM, and 1D CNN experiments.

## 7. PCA Design And What It Revealed

PCA was run as exploratory feature-structure analysis, not as the default deep learning input.

Input:

```text
data/processed/modeling_dataset_scaled.csv
```

Outputs:

```text
data/processed/modeling_dataset_pca.csv
data/processed/pca_explained_variance.csv
data/processed/pca_components.csv
data/processed/pca_top_loadings.csv
reports/pca_summary.md
```

PCA configuration result:

- input feature columns: `187`
- selected PC columns: `38`
- selected cumulative explained variance: `0.9505`

Explained variance pattern:

| component | explained variance ratio | cumulative |
| --- | ---: | ---: |
| `PC001` | `0.2426` | `0.2426` |
| `PC002` | `0.1749` | `0.4175` |
| `PC003` | `0.0485` | `0.4660` |
| `PC004` | `0.0443` | `0.5103` |
| `PC005` | `0.0368` | `0.5471` |

Interpretation:

- The first two PCs explain about `41.75%` of variance, indicating strong feature-family structure and redundancy.
- Reaching 95% cumulative variance required `38` PCs, suggesting the feature space is structured but not reducible to only a few dimensions.

Top loading patterns:

| PC | dominant pattern | examples |
| --- | --- | --- |
| `PC001` | SEMA/context missingness and availability structure | `place_*_rate_missing_ind`, `mood_*_rate_missing_ind` |
| `PC002` | HRV missingness/coverage structure | `hrv_detail_*_missing_ind` |
| `PC003` | HRV physiological values | `hrv_detail_rmssd_mean`, `hrv_detail_high_frequency_mean`, `hrv_summary_rmssd_mean` |
| `PC004` | Survey availability and survey count structure | `survey_*_missing_ind`, `survey_*_count` |

What PCA did answer:

- Feature families cluster strongly.
- Missingness and measurement availability are major axes of variance.
- HRV values form a distinct physiological component.
- Survey and SEMA availability can dominate variance even when they are not necessarily the desired physiological signal.

What PCA did not answer:

- PCA loadings are not supervised feature importance.
- PCA does not prove causal importance.
- PCA should not decide final deep learning input by itself.
- PCA was fit on the full current dataset for exploration, so it should not be used as final model input without train-only fitting.

Design interpretation:

- PCA supports the decision to track feature families, missing indicators, and availability features carefully.
- PCA also supports later robustness checks comparing all features vs wearable-only vs availability-excluded variants.
- For deep learning, PCA remains diagnostic; sequence models should start from the daily feature tensor before PCA unless a PCA-specific experiment is explicitly requested.

## 8. Split And Leakage Design

Participant-aware splitting is required because each participant contributes multiple days.

Primary split outputs:

```text
data/processed/splits/train_participant_split.csv
data/processed/splits/test_participant_split.csv
data/processed/splits/participant_split_assignments.csv
```

Split summary:

| split | rows | participants | target mean |
| --- | ---: | ---: | ---: |
| train | `2,944` | `55` | `0.3988` |
| test | `607` | `14` | `0.3690` |

Deep learning sequence creation then split validation participants from the training participants:

```text
data/processed/deep_learning_sequences/deep_learning_participant_split_assignments.csv
```

Design interpretation:

- No participant should appear across train/validation/test.
- This is more important than random row-level splitting because participant-day rows are correlated.

## 9. Deep Learning Dataset Result

Deep learning sequence dataset creation is complete.

Output root:

```text
data/processed/deep_learning_sequences/
```

Window summary:

| window | train samples | validation samples | test samples | features |
| ---: | ---: | ---: | ---: | ---: |
| 7 | `1,393` | `269` | `314` | `197` |
| 14 | `933` | `146` | `214` | `197` |
| 30 | `435` | `55` | `106` | `197` |

Each `.npz` contains:

- `X_sequence`: for SimpleRNN, LSTM, GRU, BiLSTM, and 1D CNN
- `X_mlp_flattened`: for flattened-window MLP
- `X_mlp_current_day`: for current-day MLP
- `y`
- participant/date metadata
- feature names

## 10. Current Assessment

The pre-modeling design is coherent for a deep learning project:

- EDA established data shape, target balance, missingness, feature families, and leakage risks.
- Preprocessing preserved participant/date keys while excluding direct outcome-derived columns.
- Missing values were handled with explicit rules and missing indicators.
- PCA was used correctly as exploratory structure analysis, not default model input.
- Participant-aware splitting is in place.
- Deep learning rolling sequence tensors are ready.

Main unresolved design questions before final modeling:

1. Should same-day features be allowed, or should the task shift to predicting tomorrow's sleep from prior-day signals?
2. Should missingness/count/availability features be allowed in the final interpretation?
3. Should stress features be included in all experiments or isolated because of possible sleep/recovery leakage?
4. Are 30-day windows too sample-limited compared with 7-day and 14-day windows?
5. Which model-selection metric should dominate: balanced accuracy, ROC AUC, F1, recall, precision, or calibration?

## 11. Recommended Next Step

Proceed to deep learning training in this order:

```text
scripts/20_prepare_deep_learning_loaders.py
scripts/21_train_mlp_baselines.py
scripts/22_train_sequence_models.py
scripts/23_compare_deep_learning_models.py
```

The traditional ML baseline to compare against remains:

```text
wearable_only + Logistic Regression
```

It should be reported only as a reference baseline, not as a deep learning result.
