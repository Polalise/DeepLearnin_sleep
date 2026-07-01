# Samsung Health External Prediction Interpretation

## Status

Samsung Health external/future-style inference was rebuilt after timezone correction.

## Pipeline

```text
scripts/30_build_samsung_sleep_episode_table.py
scripts/31_build_samsung_pre_sleep_stage1_features.py
scripts/32_run_samsung_pre_sleep_inference.py
```

## Outputs

```text
data/processed/samsung_health/pre_sleep_stage1/samsung_sleep_episodes.csv
data/processed/samsung_health/pre_sleep_stage1/samsung_raw_stage1_features.csv
data/processed/samsung_health/pre_sleep_stage1/samsung_pre_sleep_predictions.csv
data/processed/samsung_health/pre_sleep_stage1/samsung_pre_sleep_prediction_summary.csv
reports/samsung_pre_sleep_external_prediction_summary.md
```

## Timezone Correction Result

- Valid sleep episodes: `1493`
- Sleep start range: `2021-07-30 03:40:14` to `2026-06-27 03:39:00`
- Median sleep duration: `6.2464` hours
- Mean sleep duration: `6.7882` hours
- Cross-midnight rate after KST correction: `0.0891`

The earlier exported `16:00-18:00` high-probability sleep starts moved to plausible local overnight times after applying the Samsung `UTC+0900` offset.

## Feature Coverage

Strong coverage:

- `heart_rate_pre_sleep_mean`: `1411 / 1493`
- `heart_rate_pre_sleep_last_3h_mean`: `1398 / 1493`
- `heart_rate_pre_sleep_last_1h_mean`: `1383 / 1493`
- `previous_day_steps_sum`: `1493 / 1493`
- `previous_day_calories_sum`: `1493 / 1493`
- `previous_day_lightly_active_minutes_sum`: `1493 / 1493`

Sparse or unavailable coverage:

- `steps_pre_sleep_sum`: `14 / 1493`
- `steps_pre_sleep_last_1h_sum`: `10 / 1493`
- `calories_pre_sleep_sum`: `14 / 1493`
- `calories_pre_sleep_last_1h_sum`: `10 / 1493`
- resting-HR features: unavailable
- Fitbit-style moderate/sedentary/very-active minute buckets: unavailable

## Prediction Distribution

Official threshold `0.54`:

- Rows: `1493`
- Mean probability: `0.3848`
- Median probability: `0.3846`
- P10/P90 probability: `0.3503 / 0.4175`
- Max probability: `0.5886`
- Predicted positives: `8 / 1493`
- Predicted positive rate: `0.0054`

Threshold sensitivity from the same prediction scores:

| threshold | predicted positives | predicted positive rate |
|---:|---:|---:|
| 0.40 | 411 | 0.2753 |
| 0.45 | 33 | 0.0221 |
| 0.47 | 21 | 0.0141 |
| 0.50 | 16 | 0.0107 |
| 0.54 | 8 | 0.0054 |

## Interpretation

The Samsung external prediction run is technically contract-compatible, but the score distribution is shifted lower than the original held-out test setting.

Likely contributors:

- Device/domain shift from Fitbit-derived training data to Samsung Health export data.
- Missing or sparse pre-sleep intraday step/calorie features.
- Unavailable resting-HR and Fitbit-style activity intensity bucket features.
- Single-user external data distribution differing from the original multi-participant training/test population.

The official threshold `0.54` is very conservative on this Samsung export. The predictions are best interpreted as model scores for exploratory external application, not as validated Samsung Health sleep-quality classifications.

## Current Conclusion

Keep the official final model unchanged:

- `presleep_stage1_hp_tiny_dropout40_wd1e3_seed2027`
- threshold `0.54`

Samsung Health inference is now available as an external/future application workflow, but it should be reported with a strong domain-shift and feature-coverage caveat. Label-based external validation remains pending because Samsung sleep-score labels are not yet joined.

## Proxy Label Follow-Up

Samsung `sleep_score` proxy labels were later joined for a small subset of episodes.

- Matched proxy-labeled episodes: `64 / 1493`
- Match rate: `0.0429`
- Proxy rule: `sleep_score >= 80`
- Proxy positive rate: `0.0781`
- Mean sleep score: `57.2031`
- Median sleep score: `59.5`

Official-threshold proxy diagnostic:

- Predicted positive rate on matched rows: `0.0`
- Balanced accuracy: `0.5000`
- Sensitivity/recall: `0.0000`
- Specificity: `1.0000`
- Confusion matrix: TN `59`, FP `0`, FN `5`, TP `0`

Interpretation:

- The model predicted every matched proxy-labeled episode as negative at threshold `0.54`.
- The `0.5000` balanced accuracy reflects perfect specificity and zero sensitivity, not successful external validation.
- The matched set is too small and proxy-based to support a formal external validation claim.

See:

```text
reports/samsung_sleep_score_proxy_evaluation_interpretation.md
```
