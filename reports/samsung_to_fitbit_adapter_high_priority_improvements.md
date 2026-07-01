# Samsung-to-Fitbit Adapter High-Priority Improvements

## Decision

Proceed with the Samsung-to-Fitbit feature adapter direction as a cross-device transfer diagnostic.

Do not claim that Samsung Health raw data are equivalent to Fitbit raw data. The adapter goal is to reproduce the existing Fitbit-trained model's feature schema as closely as possible and document feature-level mapping confidence.

## High-Priority Items

### 1. Feature Mapping Confidence Table

Status: completed.

Artifact:

```text
reports/samsung_to_fitbit_feature_mapping_confidence.md
```

Purpose:

- Identify which Fitbit-compatible features are well supported by Samsung Health.
- Mark each feature group as high, medium, low-current, or low confidence.
- Prevent overclaiming one-to-one semantic equivalence.

### 2. Pre-Sleep Step/Calorie Coverage Diagnosis

Status: completed.

Artifact:

```text
scripts/36_diagnose_samsung_presleep_activity_coverage.py
```

Purpose:

- Compare coverage for:
  - midnight-to-sleep-start
  - last 6h before sleep start
  - last 3h before sleep start
  - last 1h before sleep start
- Confirm whether `pedometer_step_count` can improve the sparse current pre-sleep step/calorie features.
- Profile `calories_burned.details` as a candidate source while avoiding daily-total leakage.

Expected outputs:

```text
data/processed/samsung_health/pre_sleep_stage1/diagnostics/samsung_presleep_activity_window_coverage_summary.csv
data/processed/samsung_health/pre_sleep_stage1/diagnostics/samsung_presleep_activity_episode_window_diagnostics.csv
data/processed/samsung_health/pre_sleep_stage1/diagnostics/samsung_presleep_activity_source_profile.csv
reports/samsung_presleep_activity_coverage_diagnostic.md
```

Result:

- last 1h coverage: `10 / 1493`
- last 3h coverage: `14 / 1493`
- last 6h coverage: `14 / 1493`
- midnight-to-sleep-start coverage: `14 / 1493`
- `pedometer_step_count` source date range: `2026-05-25` to `2026-06-29`
- sleep episode date range: `2021-07-30` to `2026-06-27`

Conclusion:

- Sparse pre-sleep step/calorie coverage is caused mainly by interval source availability, not by the window definition.
- Do not fill same-day pre-sleep step/calorie from daily totals because of leakage risk.

### 3. Daily Summary Leakage Guardrail

Status: documented.

Rule:

- Daily totals may be used for previous-day features.
- Daily totals should not be used for same-day pre-sleep features unless timestamp granularity proves the data occurred before `sleep_start_datetime`.
- Same-day pre-sleep aggregation should prefer interval timestamped sources such as `pedometer_step_count`, heart-rate rows, or verified bin-level data.

Reason:

- If sleep starts after midnight, same-day daily totals can include activity after sleep start and create leakage.
- The current Design C target requires strict pre-sleep forecasting.

### 4. Fixed 6h Pre-Sleep Window Check

Status: diagnostic script prepared.

Reason:

- The existing Fitbit-compatible Design C contract uses features tied to the original strict pre-sleep design.
- For Samsung, a fixed trailing window such as last 6h may better represent the behavioral pre-sleep period and reduce midnight boundary artifacts.

Scope:

- Treat fixed 6h as diagnostics/future-work for now.
- Do not change the official Design C inference contract without a separate formalized workflow.

### 5. Report Wording

Status: standardized.

Preferred wording:

> Samsung Health data were transformed into a Fitbit-compatible feature schema for cross-device transfer diagnostics.

Avoid:

> Samsung Health data were converted into Fitbit data.

Avoid:

> Samsung Health externally validated the Fitbit-trained model.

## Additional Data-Processing Improvements Worth Considering

These are useful but should not be started unless time allows.

| Improvement | Why it may help | Risk |
|---|---|---|
| Parse Samsung `binning_data.json` activity bins | May recover pre-sleep steps/calories at better time granularity | JSON structure may be inconsistent and time-consuming |
| Build resting-HR proxy from stable low-activity HR | Could reduce missingness for resting-HR-like features | May not match Fitbit resting HR semantics |
| Add same-person baseline-normalized HR diagnostics | Could explain Samsung probability shift | Existing MLP cannot consume new features without retraining |
| Relax Samsung stage proxy label v2 | Current v1 is very strict and imbalanced | Changes label definition; diagnostic only |
| Improve sleep table to sleep_stage matching by overlap | Could increase sleep_score proxy coverage | Still vendor proxy, not original label |

## Current Recommendation

Document that Samsung interval step/calorie data are insufficient in the current export and stop further adapter patching for pre-sleep activity recovery.

Fixed-window recovery did not materially improve coverage, so it should remain a future Design D/canonical-schema idea that requires richer interval Samsung export data.
