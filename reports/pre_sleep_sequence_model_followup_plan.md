# Pre-Sleep Sequence Model Follow-Up Plan

## Purpose

This follow-up plan defines optional strict pre-sleep sequence experiments.

The current final model remains the Stage 1 Design C PyTorch MLP:

```text
presleep_stage1_hp_tiny_dropout40_wd1e3_seed2027
```

Sequence models should be treated as follow-up research. They should not replace the final model unless they improve validation-selected performance and are evaluated fairly on the held-out participant test split.

## Forecasting Objective

The objective remains strict pre-sleep forecasting:

```text
Predict the upcoming sleep episode good_sleep_label using only wearable-derived data available before sleep_start_datetime.
```

The sequence design must avoid leakage:

- no same-episode post-sleep values,
- no sleep outcome features from the target episode,
- no future episodes,
- rolling/history values must use prior episodes only.

## Recommended Sequence Unit

Use sleep episodes ordered within participant.

Candidate sample definition:

```text
For each target sleep episode t:
  X = strict pre-sleep feature vectors from prior/available episodes up to t
  y = good_sleep_label for episode t
```

Two variants are possible:

1. Include current episode pre-sleep features in the final sequence step.
2. Use only prior episode features, with the current episode represented by timing/pre-sleep cutoff features separately.

Recommended first variant:

```text
Include current episode strict pre-sleep features.
```

Reason:

- It matches the current final MLP information set.
- It allows sequence models to compare against the current model without removing the strongest current-night pre-sleep signal.

## Candidate Windows

Recommended first windows:

```text
3 episodes
5 episodes
7 episodes
```

Rationale:

- The dataset has 3,551 episodes and 69 participants.
- Longer windows may sharply reduce usable samples for participants with sparse data.
- Small windows limit overfitting risk.

## Input Feature Set

Use the final Stage 1 feature contract:

```text
raw 70 features
-> train median imputer
-> train StandardScaler
-> remove 12 zero-variance features
-> 58 final model features
```

Recommended sequence tensor shape:

```text
samples x time_steps x 58
```

Do not use PCA as the default sequence input.

## Split Rule

Use the existing participant-level split from Design C Stage 1.

Rules:

- Fit imputer/scaler on train split only.
- Keep train/validation/test participants disjoint.
- Select model family, window length, and threshold using validation only.
- Evaluate the selected candidate once on the held-out test split.

## Candidate Models

First-pass sequence candidates:

- GRU
- LSTM
- BiLSTM
- 1D CNN

Recommended minimal first grid:

| Candidate | Window | Hidden / Channels | Dropout |
|---|---:|---:|---:|
| GRU | 3 | 16 | 0.40 |
| GRU | 5 | 16 | 0.40 |
| GRU | 7 | 16 | 0.40 |
| LSTM | 5 | 16 | 0.40 |
| BiLSTM | 5 | 12 per direction | 0.40 |
| 1D CNN | 5 | 16 channels | 0.40 |

Keep the first grid small. The current dataset is modest, and Stage 2 rolling/history features already showed overfitting risk.

## Metrics

Primary model-selection metric:

```text
validation balanced accuracy
```

Secondary metrics:

- ROC AUC
- average precision
- F1
- precision
- recall
- confusion matrix
- Brier score

Threshold rule:

- Select threshold on validation split only.
- Official sequence result should report the validation-selected threshold.
- Test-only threshold sweeps may be diagnostic only.

## Baseline Comparison

Compare sequence candidates against the current final model:

```text
presleep_stage1_hp_tiny_dropout40_wd1e3_seed2027
```

Reference performance:

- Test balanced accuracy: `0.6492`
- ROC AUC: `0.6937`
- Average precision: `0.6187`
- Participant bootstrap BA 95% CI: `[0.5436, 0.7259]`

Traditional ML models remain baseline/reference only.

## Suggested New Files

Sequence tensor creation:

```text
notebooks/18_pre_sleep_sequence_tensor_creation.ipynb
```

Sequence training:

```text
notebooks/19_pre_sleep_sequence_model_experiments.ipynb
```

Optional scripts after notebook logic stabilizes:

```text
scripts/25_create_pre_sleep_sequence_tensors.py
scripts/26_train_pre_sleep_sequence_models.py
```

Outputs:

```text
data/processed/pre_sleep_forecasting/design_c_stage1/sequence_tensors/
data/processed/pre_sleep_forecasting/design_c_stage1/experiments/sequence_model_outputs/
```

Report:

```text
reports/pre_sleep_sequence_model_followup_report.md
```

## Recommended Execution Order

1. Create sequence tensors from final Stage 1 features.
2. Validate tensor shapes and participant split separation.
3. Run a small sequence model grid.
4. Select candidate by validation balanced accuracy.
5. Evaluate selected candidate on held-out test once.
6. Compare against the current final MLP.
7. Only update final-model status if the sequence candidate improves under validation-first selection.

## Stop Criteria

Stop the first sequence-model pass if:

- validation improves but held-out test collapses,
- recall improves only by predicting nearly all positives,
- performance does not beat the current final MLP,
- model behavior is unstable across seeds.

In that case, keep the current Stage 1 MLP as the final model and report sequence models as follow-up experiments.
