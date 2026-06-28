# Deep Learning Model Comparison Roadmap

- Created at: `2026-06-29`
- Current status: comparison roadmap defined; deep learning model training has not started yet.
- Data status: rolling tensor datasets are ready under `data/processed/deep_learning_sequences/`.

## 1. Purpose

This roadmap defines how deep learning models will be trained, selected, and compared.

The goal is not to simply pick the highest single test score. The goal is to select a model that:

- improves over the traditional ML reference baseline,
- is stable across participant-aware validation/test evaluation,
- has an acceptable precision/recall trade-off,
- is not unnecessarily complex when a simpler model performs similarly,
- and is defensible given the limited participant count.

## 2. Reference Baseline

The reference baseline is:

```text
wearable_only + Logistic Regression
```

This is a traditional ML baseline only. It is not a deep learning result.

Held-out participant test metrics:

| metric | value |
| --- | ---: |
| balanced accuracy | `0.8076` |
| ROC AUC | `0.9046` |
| F1 | `0.7556` |
| precision | `0.6996` |
| recall | `0.8214` |

Deep learning models should be compared against this baseline as a reference threshold.

## 3. Candidate Model Families

### Deep Learning Baselines

| family | input array | role |
| --- | --- | --- |
| MLP current-day | `X_mlp_current_day` | Daily tabular neural baseline. |
| MLP flattened-window | `X_mlp_flattened` | Window-aware but order-agnostic neural baseline. |

### Sequence Models

| family | input array | role |
| --- | --- | --- |
| SimpleRNN | `X_sequence` | Minimal recurrent sequence baseline. |
| LSTM | `X_sequence` | Gated recurrent model for longer dependencies. |
| GRU | `X_sequence` | Lighter gated recurrent model. |
| BiLSTM | `X_sequence` | Bidirectional recurrent model for full-window pattern extraction. |
| 1D CNN | `X_sequence` | Local temporal-pattern model. |

Important note:

- `BiLSTM` uses the whole input window in both directions. That is acceptable for a fixed historical window classification setup, where the model sees all days inside the window to classify the endpoint label.
- If the task is later changed to strict online forecasting, BiLSTM should be reconsidered because bidirectional context may not match deployment constraints.

## 4. Window Lengths

All candidate model families should be compared across:

```text
7 days
14 days
30 days
```

Current sample counts:

| window | train | validation | test | feature count |
| ---: | ---: | ---: | ---: | ---: |
| 7 | `1,393` | `269` | `314` | `197` |
| 14 | `933` | `146` | `214` | `197` |
| 30 | `435` | `55` | `106` | `197` |

Design implication:

- 7-day and 14-day windows should be prioritized for stable comparison.
- 30-day models should be treated cautiously because validation/test sample counts are small.

## 5. Model Selection Rule

Selection should be validation-first.

Recommended procedure:

1. Train all candidate models on the training split.
2. Use validation metrics to choose:
   - model family,
   - window length,
   - key hyperparameters,
   - early stopping checkpoint.
3. Evaluate the selected candidate once on the held-out test split.
4. Compare held-out test performance against the traditional ML reference baseline.
5. Run participant-level bootstrap uncertainty for the selected candidate.

Do not use test metrics to tune model architecture or hyperparameters.

## 6. Primary And Secondary Metrics

### Primary Metric

```text
balanced accuracy
```

Reason:

- The target is moderately imbalanced.
- Existing traditional ML baseline comparisons already use balanced accuracy.
- It avoids selecting a model that performs well mainly on the majority class.

### Secondary Metrics

Use these to understand trade-offs:

- ROC AUC
- average precision
- F1
- precision
- recall
- confusion matrix
- calibration table or probability deciles

### Tie-Breakers

If two models have similar validation/test performance:

1. Prefer the simpler model.
2. Prefer the shorter window if performance is similar.
3. Prefer the model with more stable participant-level bootstrap intervals.
4. Prefer the model with the precision/recall trade-off that matches the intended use case.
5. Prefer GRU over LSTM/BiLSTM if performance is similar and model size/training stability is better.

## 7. Experiment Matrix

Minimum comparison grid:

| model family | 7-day | 14-day | 30-day |
| --- | --- | --- | --- |
| MLP current-day | yes | yes | yes |
| MLP flattened-window | yes | yes | yes |
| SimpleRNN | yes | yes | yes |
| LSTM | yes | yes | yes |
| GRU | yes | yes | yes |
| BiLSTM | yes | yes | yes |
| 1D CNN | yes | yes | yes |

Total minimum runs:

```text
7 model/input families x 3 windows = 21 runs
```

Recommended first pass:

```text
Use small, fixed architecture grids first.
Do not run broad hyperparameter tuning until the model family ranking is clear.
```

## 8. Suggested Training Controls

Use consistent training controls across model families:

- fixed random seed
- class weighting or balanced loss handling if needed
- early stopping on validation loss or validation balanced accuracy
- restore best validation checkpoint
- same train/validation/test split for every candidate
- save predictions and probabilities for every run
- save model config, window, input type, seed, and metrics

Recommended common outputs:

```text
data/processed/deep_learning_model_metrics.csv
data/processed/deep_learning_model_predictions.csv
data/processed/deep_learning_training_history.csv
models/deep_learning/
reports/deep_learning_model_comparison_report.md
```

Manual experiment notebook:

```text
notebooks/03_deep_learning_model_experiments.ipynb
```

This notebook contains runnable code for direct user-side verification. It starts with `RUN_FULL_EXPERIMENTS = False` so the full 21-run comparison does not start accidentally.

## 9. Suggested Scripts

```text
scripts/20_prepare_deep_learning_loaders.py
scripts/21_train_mlp_baselines.py
scripts/22_train_sequence_models.py
scripts/23_compare_deep_learning_models.py
```

Recommended responsibilities:

| script | responsibility |
| --- | --- |
| `20_prepare_deep_learning_loaders.py` | Load `.npz` tensors, validate shapes, create reusable dataset/dataloader objects. |
| `21_train_mlp_baselines.py` | Train MLP current-day and flattened-window baselines. |
| `22_train_sequence_models.py` | Train SimpleRNN, LSTM, GRU, BiLSTM, and 1D CNN. |
| `23_compare_deep_learning_models.py` | Compare all DL models against the traditional ML reference baseline and write reports. |

The notebook can be used before converting the final settled workflow into scripts.

## 10. Final Decision Criteria

A deep learning model should be considered the leading candidate only if:

1. It is selected using validation performance, not test-set tuning.
2. Its held-out test balanced accuracy is competitive with or better than the traditional ML baseline.
3. Secondary metrics do not reveal an unacceptable precision/recall collapse.
4. Participant-level uncertainty is acceptable.
5. The chosen model/window is defensible given sample counts.

If deep learning does not beat the traditional ML reference baseline:

- report that clearly,
- keep the traditional ML model as the reference winner for now,
- and explain whether the limitation is likely sample size, sequence length, feature quality, or model instability.

## 11. Current Status

Completed:

```text
deep learning tensors for 7/14/30-day windows
traditional ML reference baseline
model comparison roadmap
```

Not started:

```text
MLP training
SimpleRNN training
LSTM training
GRU training
BiLSTM training
1D CNN training
deep learning model comparison report
```
