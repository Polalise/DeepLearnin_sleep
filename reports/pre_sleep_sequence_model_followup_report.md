# Pre-Sleep Sequence Model Follow-Up Report

## 1. Purpose

This follow-up experiment tested whether strict pre-sleep episode sequences improve over the current final Stage 1 MLP.

The final model before this follow-up was:

```text
presleep_stage1_hp_tiny_dropout40_wd1e3_seed2027
```

This sequence experiment was optional follow-up work. It was not used to tune or redefine the original final model.

## 2. Sequence Tensor Design

Sequence tensors were created from the final Design C Stage 1 inference feature contract.

Feature contract:

```text
raw Stage 1 features 70
-> train median imputer
-> train StandardScaler
-> remove 12 zero-variance features
-> final model features 58
```

Sequence design:

- Unit: sleep episode sequence within participant
- Sequence final step: current target episode's strict pre-sleep feature vector
- Windows tested: 3, 5, and 7 episodes
- Feature count: 58
- Split column: `pre_sleep_split`
- Split rule: existing participant-level train / validation / test split

Sequence tensor summary:

| Window | Split | Samples | Participants | Time steps | Features |
|---:|---|---:|---:|---:|---:|
| 3 | train | 2234 | 41 | 3 | 58 |
| 3 | validation | 329 | 9 | 3 | 58 |
| 3 | test | 853 | 14 | 3 | 58 |
| 5 | train | 2153 | 40 | 5 | 58 |
| 5 | validation | 312 | 8 | 5 | 58 |
| 5 | test | 825 | 14 | 5 | 58 |
| 7 | train | 2073 | 39 | 7 | 58 |
| 7 | validation | 296 | 8 | 7 | 58 |
| 7 | test | 797 | 14 | 7 | 58 |

## 3. Candidate Grid

The first sequence grid used six compact neural candidates:

| Experiment | Model | Window | Hidden / Channels | Dropout | Weight decay |
|---|---|---:|---:|---:|---:|
| `presleep_seq_000` | GRU | 3 | 16 | 0.40 | 0.001 |
| `presleep_seq_001` | GRU | 5 | 16 | 0.40 | 0.001 |
| `presleep_seq_002` | GRU | 7 | 16 | 0.40 | 0.001 |
| `presleep_seq_003` | LSTM | 5 | 16 | 0.40 | 0.001 |
| `presleep_seq_004` | BiLSTM | 5 | 12 per direction | 0.40 | 0.001 |
| `presleep_seq_005` | 1D CNN | 5 | 16 | 0.40 | 0.001 |

Model selection used validation balanced accuracy and validation-selected thresholds.

## 4. Test Results

The best held-out test balanced accuracy came from the GRU window-3 candidate.

| Experiment | Model | Window | Best epoch | Threshold | Test BA | ROC AUC | AP | Recall |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| `presleep_seq_000` | GRU | 3 | 1 | 0.41 | ~0.6466 | 0.6935 | 0.5996 | 0.7010 |
| `presleep_seq_004` | BiLSTM | 5 | 4 | validation-selected | ~0.6290 | 0.6778 | 0.5720 | 0.5118 |
| `presleep_seq_001` | GRU | 5 | 1 | validation-selected | ~0.6104 | 0.6910 | 0.6000 | 0.7946 |
| `presleep_seq_002` | GRU | 7 | 20 | validation-selected | ~0.6013 | 0.6767 | 0.5712 | 0.7596 |
| `presleep_seq_005` | 1D CNN | 5 | 18 | validation-selected | ~0.5905 | 0.6888 | 0.6147 | 0.7946 |
| `presleep_seq_003` | LSTM | 5 | 22 | validation-selected | ~0.5693 | 0.6134 | 0.5215 | 0.6027 |

Reference final MLP:

| Model | Test BA | ROC AUC | AP | Recall |
|---|---:|---:|---:|---:|
| Final Stage 1 MLP | 0.6492 | 0.6937 | 0.6187 | 0.4245 |

## 5. Interpretation

The sequence models did not clearly outperform the current final Stage 1 MLP by balanced accuracy.

Main findings:

- `presleep_seq_000` was very close to the final MLP in balanced accuracy.
- Several sequence models substantially increased recall.
- Higher recall came with many more false positives.
- Average precision did not improve over the final MLP.
- The best sequence candidate is useful as a recall-priority comparison model, not as a replacement final model.

Current final model remains:

```text
presleep_stage1_hp_tiny_dropout40_wd1e3_seed2027
```

## 6. Artifacts

Sequence tensors:

```text
data/processed/pre_sleep_forecasting/design_c_stage1/sequence_tensors/
```

Experiment grid:

```text
data/processed/pre_sleep_forecasting/design_c_stage1/experiments/sequence_model_outputs/pre_sleep_sequence_experiment_grid.csv
```

Grid validation:

```text
data/processed/pre_sleep_forecasting/design_c_stage1/experiments/sequence_model_outputs/pre_sleep_sequence_grid_validation.csv
```

Combined metrics:

```text
data/processed/pre_sleep_forecasting/design_c_stage1/experiments/sequence_model_outputs/pre_sleep_sequence_model_metrics.csv
```

Rankings:

```text
data/processed/pre_sleep_forecasting/design_c_stage1/experiments/sequence_model_outputs/pre_sleep_sequence_model_validation_rank.csv
data/processed/pre_sleep_forecasting/design_c_stage1/experiments/sequence_model_outputs/pre_sleep_sequence_model_test_rank.csv
```

Best sequence checkpoint:

```text
data/processed/pre_sleep_forecasting/design_c_stage1/experiments/sequence_model_outputs/models/presleep_seq_000_best.pt
```

## 7. Recommendation

Do not replace the final Stage 1 MLP with a sequence model based on this grid.

Recommended framing:

```text
Sequence models were explored as optional strict pre-sleep follow-up experiments. The best GRU sequence candidate was close to the final MLP by balanced accuracy and improved recall, but it did not clearly exceed the final MLP overall.
```

Possible future sequence work:

- test seed robustness for `presleep_seq_000`,
- tune recall-priority operating thresholds explicitly,
- try smaller dropout or hidden dimension variants,
- add participant-level bootstrap confidence intervals for the best sequence candidate.
