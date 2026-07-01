# Korean Presentation Figure Index

Generated at: 2026-06-30

These figures are Korean-language static chart assets for
`sleep_forecasting_presentation_report.pdf`.

## Figure Map

| PDF page | Figure | Source data |
| ---: | --- | --- |
| 6 | `ko_06_source_data_structure.png` | `mongodb_raw_overview.md`, `variable_extraction_summary.md`, Samsung prototype docs |
| 7 | `ko_07_extracted_table_row_counts.png` | `variable_extraction_summary.md` |
| 8 | `ko_08_target_distribution.png` | `modeling_dataset_daily.csv` |
| 8 | `ko_08_missing_rate_by_feature_family.png` | `final_dataset_eda.md` |
| 9 | `ko_09_top_missing_columns.png` | `modeling_dataset_daily.csv` |
| 10 | `ko_10_missing_handling_column_flow.png` | `missing_value_handling_summary.md`, `scaling_summary.md` |
| 11 | `ko_11_split_target_rate.png` | `train_participant_split.csv`, `test_participant_split.csv` |
| 12 | `ko_12_strict_presleep_timeline.png` | `README.md`, `pre_sleep_forecasting_stage1_final_report_updated.md` |
| 13 | `ko_13_inference_pipeline.png` | `README.md`, inference package contract |
| 14 | `ko_14_model_candidate_table.png` | `pre_sleep_forecasting_stage1_final_report_updated.md`, sequence follow-up report |
| 15 | `ko_15_mlp_architecture.png` | `pre_sleep_forecasting_stage1_final_report_updated.md` |
| 16 | `ko_16_model_candidate_metrics.png` | `reports/pre_sleep_forecasting_stage1_final_report_updated.md` |
| 17 | `ko_17_final_mlp_confusion_matrix.png` | `stage1_hyperparameter_stability_predictions.csv` |
| 17 | `ko_17_final_mlp_roc_pr.png` | `stage1_hyperparameter_stability_predictions.csv` |
| 18 | `ko_18_participant_bootstrap_ci.png` | `selected_model_participant_bootstrap_summary.csv` |
| 19 | `ko_19_sequence_ba_recall_tradeoff.png` | `pre_sleep_sequence_model_metrics.csv` |
| 20 | `ko_20_top_target_correlations.png` | `modeling_dataset_daily.csv` |
| 20 | `ko_20_key_features_by_target.png` | `modeling_dataset_daily.csv` |
| 21 | `ko_21_samsung_adapter_pipeline.png` | Samsung adapter scripts and reports |
| 22 | `ko_22_samsung_feature_coverage.png` | `samsung_stage1_feature_summary.csv` |
| 24 | `ko_24_today_forecast_comparison.png` | `today_forecast_comparison.csv` |
| 25 | `ko_25_numeric_sensitivity.png` | `today_numeric_sensitivity.csv` |
| 26 | `ko_26_service_flow.png` | Prototype usage docs and project README |

Each chart is also exported as SVG with the same base filename.

## Regeneration

```powershell
cd C:\workSpace\DeepLearnin_sleep
.\.venv\Scripts\python.exe -X utf8 scripts\create_presentation_korean_figures.py
```
