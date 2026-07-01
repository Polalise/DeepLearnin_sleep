# Samsung Stage Proxy External Evaluation Report

## Purpose

Compare selected MLP predictions against Samsung stage-based proxy label v1.

## Inputs

```text
data\processed\samsung_health\pre_sleep_stage1\samsung_pre_sleep_predictions.csv
data\processed\samsung_health\pre_sleep_stage1\samsung_sleep_episodes_with_stage_proxy_labels.csv
```

## Outputs

```text
data\processed\samsung_health\pre_sleep_stage1\samsung_predictions_with_stage_proxy_labels.csv
data\processed\samsung_health\pre_sleep_stage1\samsung_stage_proxy_prediction_evaluation.csv
data\processed\samsung_health\pre_sleep_stage1\samsung_stage_proxy_threshold_sensitivity.csv
```

## Label Caveat

The target is `samsung_good_sleep_label_v1`, a Samsung stage-derived proxy label. It is not the original project `good_sleep_label`.

## Label Distribution

- Labeled rows: `1493`
- Positive count: `39`
- Positive rate: `0.0261`

## Ranking Metrics

- ROC AUC rank approximation: `0.3224`
- Average precision: `0.0180`

## Official Threshold 0.54

- Predicted positive count: `8`
- Predicted positive rate: `0.0054`
- Balanced accuracy: `0.4972`
- Sensitivity/recall: `0.0000`
- Specificity: `0.9945`
- Precision: `0.0`
- Confusion matrix: TN `1446`, FP `8`, FN `39`, TP `0`

## Best Thresholds

- Best balanced accuracy threshold: `0.32`
- Best balanced accuracy: `0.5124`
- Best F1 threshold: `0.32`
- Best F1: `0.0521`

## Probability Separation

- Mean probability, proxy positive: `0.3697`
- Mean probability, proxy negative: `0.3852`
- Median probability, proxy positive: `0.3711`
- Median probability, proxy negative: `0.3850`

## Interpretation Guardrail

This is a diagnostic evaluation against a strict, imbalanced proxy label. It should guide threshold and label-definition decisions, not be reported as formal external validation.

## Interpretation

The selected MLP does not transfer well to this Samsung stage-proxy label setting.

- At the official threshold `0.54`, no proxy-positive episodes are detected.
- Lowering the threshold does not recover a useful operating point: the best balanced-accuracy threshold is `0.32`, but it predicts almost all episodes as positive.
- Ranking is weak and directionally unfavorable: proxy-positive episodes have lower mean probability than proxy-negative episodes.
- ROC AUC rank approximation is below random at `0.3224`.

This supports the domain-shift conclusion: the existing Fitbit-trained strict pre-sleep model can be applied to Samsung data technically, but should not be used as a reliable Samsung good-sleep classifier without Samsung-specific label design, calibration, and likely retraining or fine-tuning.
