# Selected Pre-Sleep Model Calibration Follow-Up Summary

- Selected experiment: `presleep_stage1_hp_tiny_dropout40_wd1e3_seed2027`
- Calibration fitting split: `validation`
- Evaluation split: `test`
- Official original threshold: `0.54`

## Test Metrics

| method   |   threshold |   balanced_accuracy |   roc_auc |   average_precision |   brier_score |   expected_calibration_error |   precision |   recall |
|:---------|------------:|--------------------:|----------:|--------------------:|--------------:|-----------------------------:|------------:|---------:|
| isotonic |        0.34 |            0.649209 |  0.690154 |            0.55844  |      0.20807  |                    0.0485806 |     0.65534 | 0.424528 |
| platt    |        0.4  |            0.656459 |  0.693695 |            0.618684 |      0.208325 |                    0.074481  |     0.65    | 0.449686 |
| original |        0.54 |            0.649209 |  0.693695 |            0.618684 |      0.212638 |                    0.125631  |     0.65534 | 0.424528 |

## Best Calibration By Metric

- Best Brier score: `isotonic` = `0.2081`
- Best ECE: `isotonic` = `0.0486`

## Interpretation Guardrail

Calibration correction is optional probability post-processing. The model remains research-grade and should not be used for clinical or high-stakes decisions.
