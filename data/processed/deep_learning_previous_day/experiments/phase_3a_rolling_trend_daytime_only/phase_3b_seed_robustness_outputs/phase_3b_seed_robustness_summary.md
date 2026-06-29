# Phase 3B Seed Robustness Summary

## Purpose

Phase 3B repeated the closest Phase 3A GRU candidates across additional random seeds to check whether the rolling/trend result was stable.

## Reference

The current strict previous-day reference remains:

`phase2a_006 / previous_day / daytime_only / window 14 / BiLSTM`

Reference test balanced accuracy: `0.6098`

## Seed Robustness Summary

| base_experiment_id | model | window | runs | mean test balanced accuracy | std | min | max | mean ROC AUC | mean F1 | mean precision | mean recall | delta mean vs phase2a_006 |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| `phase3a_001` | `gru` | 7 | 3 | 0.5986 | 0.0231 | 0.5798 | 0.6244 | 0.6508 | 0.6074 | 0.4842 | 0.8157 | -0.0112 |
| `phase3a_002` | `gru` | 14 | 3 | 0.5223 | 0.0468 | 0.4865 | 0.5752 | 0.5377 | 0.5763 | 0.4861 | 0.7113 | -0.0874 |


## Interpretation

`phase3a_001` remained the stronger Phase 3A rolling/trend candidate, but its mean seed-robust test balanced accuracy did not exceed `phase2a_006`.

`phase3a_002` was weaker and less stable across seeds, supporting the interpretation that its high validation score in the original Phase 3A run did not transfer reliably.

## Conclusion

Phase 3B does not justify replacing the strict previous-day reference candidate.

Current strict previous-day reference:

`phase2a_006 / previous_day / daytime_only / window 14 / BiLSTM`

Close but not replacement candidate:

`phase3a_001 / previous_day / daytime_only_rolling_trend / window 7 / GRU`
