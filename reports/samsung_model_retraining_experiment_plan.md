# Samsung Model Retraining Experiment Plan

## Purpose

Define the safe research workflow for retraining or fine-tuning after new labeled sleep episodes are available.

## Important Distinction

- `오늘 밤 예측 갱신` updates feature history/baseline inputs and keeps the final MLP fixed.
- `모델 재학습 실험` would rebuild labeled data, train a candidate model, evaluate it, and version new artifacts.

## Required Inputs

```text
new labeled sleep episodes through at least the latest completed night
Samsung-compatible feature table
stable label definition
participant-aware validation design
```

## Safe Retraining Gates

- Do not include the current night's unlabeled sleep in training.
- Do not overwrite the selected final Fitbit-trained MLP checkpoint.
- Save retrained candidates under a new experiment directory.
- Recompute validation metrics, threshold policy, calibration diagnostics, and caveats before promotion.
- Treat this as research/fine-tuning, not the default live user flow.

## Suggested Future Workflow

```text
1. Build Samsung labeled training table
2. Rebuild feature matrix with the same leakage rules
3. Create participant/time-aware train/validation/test split
4. Train candidate MLP
5. Evaluate against held-out labeled episodes
6. Select threshold and write model card
7. Package candidate inference artifacts
```

## Current Prototype Status

The current app implements the planning/control surface only. It does not run training from the UI.
