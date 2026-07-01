# Samsung Sleep Score Proxy Evaluation Interpretation

## Status

Samsung sleep-score proxy labels were joined to the Samsung external prediction output.

## Outputs

```text
data/processed/samsung_health/pre_sleep_stage1/samsung_sleep_episodes_with_proxy_labels.csv
data/processed/samsung_health/pre_sleep_stage1/samsung_pre_sleep_predictions_with_proxy_labels.csv
data/processed/samsung_health/pre_sleep_stage1/samsung_sleep_score_proxy_label_match_report.csv
data/processed/samsung_health/pre_sleep_stage1/samsung_pre_sleep_proxy_label_evaluation.csv
reports/samsung_sleep_score_proxy_label_join_summary.md
```

## Label Source

- Source table: `docs/samsunghealth/com.samsung.shealth.sleep.20260629163038.csv`
- Proxy label: `samsung_good_sleep_label`
- Rule: `sleep_score >= 80`
- Matching rule: nearest sleep start within `30` minutes
- Matched rows: `64 / 1493`
- Match rate: `0.0429`

## Proxy Label Distribution

- Sleep-score rows with score: `1640`
- Matched episode rows: `64`
- Proxy positive rate: `0.0781`
- Mean sleep score: `57.2031`
- Median sleep score: `59.5`
- Median match time difference: `18.7333` minutes

## Proxy Diagnostic Metrics

Official threshold `0.54`:

- Labeled rows: `64`
- Proxy positives: `5`
- Proxy negatives: `59`
- Predicted positives: `0`
- Predicted positive rate: `0.0`
- Mean probability on matched rows: `0.3623`
- Balanced accuracy: `0.5000`
- Sensitivity/recall: `0.0000`
- Specificity: `1.0000`
- Confusion matrix:
  - TN: `59`
  - FP: `0`
  - FN: `5`
  - TP: `0`

## Interpretation

This is not evidence that the model externally validates on Samsung Health. At the official threshold, the model predicts every matched proxy-labeled episode as negative. The balanced accuracy of `0.5000` comes from perfect specificity and zero sensitivity in a small, imbalanced proxy-labeled subset.

The proxy-labeled subset is also small:

- only `64` matched episodes
- only `5` proxy-positive episodes
- median match offset is about `18.7` minutes

Therefore these metrics should be reported only as proxy-label diagnostics.

## Conclusion

The Samsung external workflow is complete as an exploratory application pipeline:

1. Build Samsung sleep episodes.
2. Build Samsung Stage 1 raw features.
3. Run selected MLP inference.
4. Optionally join Samsung sleep-score proxy labels.
5. Report proxy diagnostics with strong caveats.

The selected final model remains unchanged:

- `presleep_stage1_hp_tiny_dropout40_wd1e3_seed2027`
- official threshold `0.54`

The Samsung result supports a domain-shift caveat rather than a claim of external validation.
