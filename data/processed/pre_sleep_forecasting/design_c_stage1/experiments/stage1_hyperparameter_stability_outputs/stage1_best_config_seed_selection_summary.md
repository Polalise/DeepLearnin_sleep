# Stage 1 Best Config Seed Selection Summary

Representative model selection is based on validation metrics only.

- Best config: `tiny_dropout40_wd1e3`
- Selected experiment: `presleep_stage1_hp_tiny_dropout40_wd1e3_seed2027`
- Selected seed: `2027`
- Selection metric: validation balanced accuracy
- Selected validation balanced accuracy: 0.6770
- Selected test balanced accuracy: 0.6492
- Selected test ROC AUC: 0.6937
- Selected test average precision: 0.6187
- Selected test F1: 0.5153
- Selected test precision: 0.6553
- Selected test recall: 0.4245

Best-config seed robustness:

- Runs: 4
- Mean test balanced accuracy: 0.6586
- Std test balanced accuracy: 0.0078
- Min test balanced accuracy: 0.6492
- Max test balanced accuracy: 0.6677
- Mean test ROC AUC: 0.6942
- Mean test average precision: 0.6185

Interpretation:

- This is the current best strict pre-sleep forecasting candidate.
- It uses only Stage 1 strict pre-sleep features, not rolling/history features.
- The selected representative checkpoint is chosen without looking at test performance.