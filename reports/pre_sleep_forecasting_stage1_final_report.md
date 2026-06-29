# Pre-Sleep Forecasting Final Report

## 1. Objective

The prediction objective was redefined as strict pre-sleep forecasting:

> Predict the quality label of the upcoming sleep episode using only wearable-derived data available before `sleep_start_datetime`.

This differs from earlier same-date classification. Earlier same-date models can perform well, but they are not aligned with the intended real-use timing because `calendar_date` in the sleep target data corresponds to sleep end date.

## 2. Dataset Design

The final forecasting unit is one sleep episode.

- Rows: 3,551 sleep episodes
- Participants: 69
- Target: `good_sleep_label`
- Positive class ratio: approximately 0.3937
- Prediction cutoff: `sleep_start_datetime`
- Split strategy: participant-level train/validation/test split
- Train / validation / test samples: 2,323 / 347 / 881
- Train / validation / test participants: 46 / 9 / 14

Strict Design C features were created from:

- MongoDB intraday steps before sleep onset
- MongoDB intraday calories before sleep onset
- MongoDB intraday heart rate before sleep onset
- Sleep start timing/calendar features known before prediction
- Previous-day daily activity/resting-HR features

MongoDB server-side aggregation was validated against raw-fetch aggregation on sample episodes with zero mismatched features.

## 3. Feature Sets Tested

### Stage 1: Strict Pre-Sleep Features

Stage 1 used the core strict pre-sleep feature set.

- Final features: 58
- Feature groups:
  - pre-sleep intraday
  - previous-day daily
  - timing/calendar
  - missing indicators
- No rolling/history features

### Stage 2: Full Rolling/History Features

Stage 2 added broad prior-episode rolling/history features.

- Final features: 380
- Rolling/history features: 319
- Result: did not improve held-out test generalization

### Stage 2B: Compact Rolling/History Features

Stage 2B reduced rolling features to compact prior-episode summaries.

- Final features: 148
- Compact rolling features: 87
- Result: improved recall but did not improve balanced accuracy

## 4. Model Experiments

All models in the pre-sleep workflow were neural-network MLP models trained in PyTorch.

Traditional ML baselines were not used for final model selection in this stage.

### Main Results

| Candidate | Feature set | Test balanced accuracy | ROC AUC | Average precision | F1 | Precision | Recall |
|---|---:|---:|---:|---:|---:|---:|---:|
| Stage 1 single seed | 58 | 0.6338 | 0.6875 | 0.6009 | 0.4904 | 0.6275 | 0.4025 |
| Stage 1 seed mean | 58 | 0.6107 | 0.6681 | 0.6016 | 0.5309 | 0.4942 | 0.6205 |
| Stage 2 full rolling | 380 | 0.6025 | 0.6628 | 0.5855 | 0.5307 | 0.4541 | 0.6384 |
| Stage 2B compact rolling | 148 | 0.5923 | 0.6852 | 0.5788 | 0.5530 | 0.4238 | 0.7956 |
| Best Stage 1 HP config mean | 58 | 0.6586 | 0.6942 | 0.6185 | 0.5298 | 0.6736 | 0.4371 |

## 5. Best Hyperparameter Configuration

The best stability configuration was:

- Config: `tiny_dropout40_wd1e3`
- Hidden dimensions: `(24, 12)`
- Dropout: 0.40
- Weight decay: 0.001
- Learning rate: 0.0008
- Seeds: 7, 123, 2026, 2027

Seed robustness for this config:

- Mean test balanced accuracy: 0.6586
- Std test balanced accuracy: 0.0078
- Min / max test balanced accuracy: 0.6492 / 0.6677
- Mean ROC AUC: 0.6942
- Mean average precision: 0.6185

This configuration improved over the previous Stage 1 seed mean by 0.0479 balanced accuracy.

## 6. Selected Representative Model

The representative checkpoint was selected by validation balanced accuracy only.

- Selected experiment: `presleep_stage1_hp_tiny_dropout40_wd1e3_seed2027`
- Selected seed: 2027
- Selected threshold: 0.54
- Validation balanced accuracy: 0.6770

Held-out test performance for the selected representative model:

- Test balanced accuracy: 0.6492
- Test ROC AUC: 0.6937
- Test average precision: 0.6187
- Test F1: 0.5153
- Test precision: 0.6553
- Test recall: 0.4245

## 7. Threshold Policy

The official threshold policy is validation balanced accuracy.

Official policy:

- Threshold: 0.54
- Test balanced accuracy: 0.6492
- Test precision: 0.6553
- Test recall: 0.4245

A recall-priority validation policy is also available as an operating option:

- Threshold: 0.47
- Test balanced accuracy: 0.6592
- Test precision: 0.5600
- Test recall: 0.5723

The recall-priority policy may be useful if the application values catching more likely good-sleep episodes, but it produces more false positives. It should be presented as an alternative operating policy, not as the primary model-selection result.

## 8. Interpretation

The best current model is a strict pre-sleep forecasting MLP using Stage 1 Design C features.

The model shows meaningful predictive signal:

- It outperforms the earlier previous-day reference in balanced accuracy.
- It is aligned with the intended real-use objective.
- The best hyperparameter configuration is stable across seeds.
- ROC AUC and average precision are moderate, not high.

The model should be considered useful for exploratory decision support or personal feedback research, but not yet reliable enough for high-stakes health decision-making.

## 9. Limitations

Important limitations remain:

- Test performance is moderate.
- Recall under the official threshold is limited.
- The validation split is relatively small.
- Participants are heterogeneous, and generalization to unseen people remains challenging.
- Rolling/history features did not improve generalization, likely due to overfitting or participant-specific noise.
- No external validation dataset has been used.

## 10. Current Recommendation

Use the selected Stage 1 hyperparameter-stabilized MLP as the current best pre-sleep forecasting candidate.

Current best candidate:

- Experiment family: `presleep_stage1_hp_tiny_dropout40_wd1e3`
- Representative model: `presleep_stage1_hp_tiny_dropout40_wd1e3_seed2027`
- Feature set: strict pre-sleep Stage 1
- Model: tiny regularized MLP
- Official threshold: 0.54
- Representative test balanced accuracy: 0.6492
- Robustness mean test balanced accuracy: 0.6586

Recommended next work:

1. Participant-level bootstrap confidence interval for the selected model.
2. Calibration analysis.
3. Optional sequence model using strict pre-sleep episode sequences.
4. External or future-period validation if more data becomes available.
