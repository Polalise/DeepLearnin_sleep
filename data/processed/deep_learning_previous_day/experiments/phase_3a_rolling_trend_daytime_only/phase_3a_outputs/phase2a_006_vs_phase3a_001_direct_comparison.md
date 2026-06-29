# Phase 2A Reference Vs Phase 3A Rolling/Trend Candidate

## Purpose

This file directly compares the current strict previous-day reference candidate with the closest Phase 3A rolling/trend candidate.

Important correction: `phase2a_006` is compared using the validation-selected threshold value recorded in the participant-bootstrap summary, not the raw threshold-0.5 row from `phase_2a_previous_day_model_metrics.csv`.

## Direct Comparison

| role | experiment_id | subset | model | window | threshold | test balanced accuracy | test ROC AUC | test F1 | test precision | test recall | delta balanced accuracy |
| --- | --- | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| `current_previous_day_reference` | `phase2a_006` | `daytime_only` | `bilstm` | 14 | 0.51 | 0.6098 | 0.6063 | 0.5833 | 0.5895 | 0.5773 | 0.0000 |
| `phase3a_close_rolling_trend_candidate` | `phase3a_001` | `daytime_only_rolling_trend` | `gru` | 7 | 0.35 | 0.6054 | 0.6385 | 0.6145 | 0.4880 | 0.8293 | -0.0044 |


## Conclusion

`phase3a_001` is a close rolling/trend comparison candidate, but it does not clearly exceed `phase2a_006` under validation-selected thresholding.

Therefore, the strict previous-day reference candidate remains:

`phase2a_006 / previous_day / daytime_only / window 14 / BiLSTM`

The Phase 3A result should be reported as a useful feature-engineering sensitivity analysis rather than a replacement final model.
