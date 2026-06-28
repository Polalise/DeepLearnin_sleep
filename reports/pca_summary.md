# Exploratory PCA Summary

- Generated at: `2026-06-28T20:57:09`
- Input file: `C:\workSpace\DeepLearnin_sleep\data\processed\modeling_dataset_scaled.csv`
- Output file: `C:\workSpace\DeepLearnin_sleep\data\processed\modeling_dataset_pca.csv`
- PCA model file: `C:\workSpace\DeepLearnin_sleep\data\processed\pca_model.joblib`

## Scope

- This step applies PCA to scaled numeric model features for exploratory feature-structure analysis.
- It preserves `participant_object_id`, `calendar_date`, and `good_sleep_label`.
- It does not train models.
- PCA is not the default input path for deep learning experiments.
- The main deep learning path uses participant-date daily features before PCA.

## Important Leakage Note

- PCA is fit on the full current dataset for preprocessing exploration.
- For final model evaluation, PCA should be fit only on training folds inside a participant-aware pipeline.

## Output Shape

- Input rows: `3,551`
- Input columns: `190`
- Input feature columns: `187`
- Output rows: `3,551`
- Output columns: `41`
- Selected PC columns: `38`
- Selected cumulative explained variance: `0.9505`
- Output missing cells: `0`
- Duplicate participant-date rows: `0`

## Target Distribution

| good_sleep_label | rows |
| ---: | ---: |
| 0 | 2,153 |
| 1 | 1,398 |

## Explained Variance Preview

| component | explained variance ratio | cumulative explained variance ratio |
| --- | ---: | ---: |
| `PC001` | 0.2426 | 0.2426 |
| `PC002` | 0.1749 | 0.4175 |
| `PC003` | 0.0485 | 0.4660 |
| `PC004` | 0.0443 | 0.5103 |
| `PC005` | 0.0368 | 0.5471 |
| `PC006` | 0.0358 | 0.5829 |
| `PC007` | 0.0312 | 0.6141 |
| `PC008` | 0.0221 | 0.6362 |
| `PC009` | 0.0211 | 0.6573 |
| `PC010` | 0.0199 | 0.6772 |
| `PC011` | 0.0180 | 0.6952 |
| `PC012` | 0.0150 | 0.7102 |
| `PC013` | 0.0139 | 0.7241 |
| `PC014` | 0.0135 | 0.7376 |
| `PC015` | 0.0132 | 0.7508 |
| `PC016` | 0.0129 | 0.7637 |
| `PC017` | 0.0118 | 0.7756 |
| `PC018` | 0.0114 | 0.7870 |
| `PC019` | 0.0112 | 0.7981 |
| `PC020` | 0.0112 | 0.8093 |

## Top Loadings Preview

| component | rank | feature | loading |
| --- | ---: | --- | ---: |
| `PC001` | 1 | `place_outdoors_rate_missing_ind` | 0.1476 |
| `PC001` | 2 | `place_gym_rate_missing_ind` | 0.1476 |
| `PC001` | 3 | `place_work_school_rate_missing_ind` | 0.1476 |
| `PC001` | 4 | `place_entertainment_rate_missing_ind` | 0.1476 |
| `PC001` | 5 | `place_other_rate_missing_ind` | 0.1476 |
| `PC001` | 6 | `mood_tense_anxious_rate_missing_ind` | 0.1476 |
| `PC001` | 7 | `mood_neutral_rate_missing_ind` | 0.1476 |
| `PC001` | 8 | `mood_fear_rate_missing_ind` | 0.1476 |
| `PC001` | 9 | `mood_rested_relaxed_rate_missing_ind` | 0.1476 |
| `PC001` | 10 | `mood_surprise_rate_missing_ind` | 0.1476 |
| `PC002` | 1 | `hrv_detail_rmssd_max_missing_ind` | 0.1709 |
| `PC002` | 2 | `hrv_detail_coverage_min_missing_ind` | 0.1709 |
| `PC002` | 3 | `hrv_detail_coverage_mean_missing_ind` | 0.1709 |
| `PC002` | 4 | `hrv_detail_rmssd_min_missing_ind` | 0.1709 |
| `PC002` | 5 | `hrv_detail_high_frequency_mean_missing_ind` | 0.1709 |
| `PC002` | 6 | `hrv_detail_low_frequency_mean_missing_ind` | 0.1709 |
| `PC002` | 7 | `hrv_detail_low_frequency_min_missing_ind` | 0.1709 |
| `PC002` | 8 | `hrv_detail_low_frequency_max_missing_ind` | 0.1709 |
| `PC002` | 9 | `hrv_detail_coverage_max_missing_ind` | 0.1709 |
| `PC002` | 10 | `hrv_detail_rmssd_mean_missing_ind` | 0.1709 |
| `PC003` | 1 | `hrv_detail_rmssd_mean` | 0.2448 |
| `PC003` | 2 | `hrv_detail_high_frequency_mean` | 0.2279 |
| `PC003` | 3 | `hrv_summary_rmssd_mean` | 0.2269 |
| `PC003` | 4 | `hrv_detail_low_frequency_mean` | 0.2170 |
| `PC003` | 5 | `hrv_detail_rmssd_min` | 0.2065 |
| `PC003` | 6 | `hrv_detail_rmssd_max` | 0.2032 |
| `PC003` | 7 | `hrv_detail_low_frequency_std` | 0.1979 |
| `PC003` | 8 | `hrv_detail_rmssd_std` | 0.1959 |
| `PC003` | 9 | `hrv_detail_high_frequency_min` | 0.1900 |
| `PC003` | 10 | `hrv_detail_high_frequency_std` | 0.1839 |
| `PC004` | 1 | `survey_ttmspbf_count_missing_ind` | 0.2333 |
| `PC004` | 2 | `survey_panas_count_missing_ind` | 0.2333 |
| `PC004` | 3 | `survey_stai_count_missing_ind` | 0.2333 |
| `PC004` | 4 | `survey_response_count_missing_ind` | 0.2333 |
| `PC004` | 5 | `survey_bfpt_count_missing_ind` | 0.2333 |
| `PC004` | 6 | `survey_breq_count_missing_ind` | 0.2333 |
| `PC004` | 7 | `survey_dq_count_missing_ind` | 0.2333 |
| `PC004` | 8 | `survey_dq_count` | -0.2333 |
| `PC004` | 9 | `hrv_detail_low_frequency_mean` | -0.1766 |
| `PC004` | 10 | `hrv_detail_rmssd_mean` | -0.1651 |

## Figures

- explained_variance: `C:\workSpace\DeepLearnin_sleep\reports\figures\pca\explained_variance_ratio.png`
- cumulative_variance: `C:\workSpace\DeepLearnin_sleep\reports\figures\pca\cumulative_explained_variance.png`
- pc1_pc2_target: `C:\workSpace\DeepLearnin_sleep\reports\figures\pca\pc1_pc2_by_target.png`

## Next Step

```text
deep learning sequence dataset creation from participant-date daily data before PCA
```
