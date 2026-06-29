# Pre-Sleep Inference Package QA

- Generated at: `2026-06-29T15:50:31`
- Status: `PASS`
- Checks passed: `44/44`
- Selected experiment: `presleep_stage1_hp_tiny_dropout40_wd1e3_seed2027`
- Official threshold: `0.54`
- Raw features: `70`
- Removed zero-variance features: `12`
- Model input features: `58`

## Check Results

| Check | Status | Detail |
|---|---:|---|
| `file_exists:src\pre_sleep_forecasting\feature_builder.py` | `PASS` | C:\workSpace\DeepLearnin_sleep\src\pre_sleep_forecasting\feature_builder.py |
| `file_exists:src\pre_sleep_forecasting\inference.py` | `PASS` | C:\workSpace\DeepLearnin_sleep\src\pre_sleep_forecasting\inference.py |
| `file_exists:src\pre_sleep_forecasting\__init__.py` | `PASS` | C:\workSpace\DeepLearnin_sleep\src\pre_sleep_forecasting\__init__.py |
| `file_exists:data\processed\pre_sleep_forecasting\design_c_stage1\inference_package\pre_sleep_inference_manifest.json` | `PASS` | C:\workSpace\DeepLearnin_sleep\data\processed\pre_sleep_forecasting\design_c_stage1\inference_package\pre_sleep_inference_manifest.json |
| `file_exists:data\processed\pre_sleep_forecasting\design_c_stage1\inference_package\pre_sleep_inference_feature_contract.csv` | `PASS` | C:\workSpace\DeepLearnin_sleep\data\processed\pre_sleep_forecasting\design_c_stage1\inference_package\pre_sleep_inference_feature_contract.csv |
| `file_exists:docs\pre_sleep_inference_usage.md` | `PASS` | C:\workSpace\DeepLearnin_sleep\docs\pre_sleep_inference_usage.md |
| `py_compile:feature_builder.py` | `PASS` | ok |
| `py_compile:inference.py` | `PASS` | ok |
| `import:pre_sleep_forecasting.feature_builder` | `PASS` | C:\workSpace\DeepLearnin_sleep\src\pre_sleep_forecasting\feature_builder.py |
| `import:pre_sleep_forecasting.inference` | `PASS` | C:\workSpace\DeepLearnin_sleep\src\pre_sleep_forecasting\inference.py |
| `artifact_exists:raw_feature_columns` | `PASS` | C:\workSpace\DeepLearnin_sleep\data\processed\pre_sleep_forecasting\design_c_stage1\pre_sleep_design_c_stage1_feature_columns.csv |
| `artifact_exists:zero_variance_removed_features` | `PASS` | C:\workSpace\DeepLearnin_sleep\data\processed\pre_sleep_forecasting\design_c_stage1\pre_sleep_design_c_stage1_zero_variance_removed_features.csv |
| `artifact_exists:final_feature_columns` | `PASS` | C:\workSpace\DeepLearnin_sleep\data\processed\pre_sleep_forecasting\design_c_stage1\pre_sleep_design_c_stage1_final_feature_columns.csv |
| `artifact_exists:imputer` | `PASS` | C:\workSpace\DeepLearnin_sleep\data\processed\pre_sleep_forecasting\design_c_stage1\pre_sleep_design_c_stage1_median_imputer.joblib |
| `artifact_exists:scaler` | `PASS` | C:\workSpace\DeepLearnin_sleep\data\processed\pre_sleep_forecasting\design_c_stage1\pre_sleep_design_c_stage1_standard_scaler.joblib |
| `artifact_exists:model_checkpoint` | `PASS` | C:\workSpace\DeepLearnin_sleep\data\processed\pre_sleep_forecasting\design_c_stage1\experiments\stage1_hyperparameter_stability_outputs\models\presleep_stage1_hp_tiny_dropout40_wd1e3_seed2027_best.pt |
| `artifact_exists:selection_summary` | `PASS` | C:\workSpace\DeepLearnin_sleep\data\processed\pre_sleep_forecasting\design_c_stage1\experiments\stage1_hyperparameter_stability_outputs\stage1_best_config_seed_selection_summary.csv |
| `artifact_exists:threshold_policy` | `PASS` | C:\workSpace\DeepLearnin_sleep\data\processed\pre_sleep_forecasting\design_c_stage1\experiments\stage1_hyperparameter_stability_outputs\stage1_selected_model_threshold_policy_comparison.csv |
| `contract_rows` | `PASS` | rows=70 |
| `contract_duplicate_features` | `PASS` | duplicates=0 |
| `manifest_raw_feature_count` | `PASS` | raw=70 |
| `manifest_removed_feature_count` | `PASS` | removed=12 |
| `manifest_final_feature_count` | `PASS` | final=58 |
| `computed_final_matches_manifest` | `PASS` | computed=58, manifest=58 |
| `contract_order_matches_manifest` | `PASS` | contract feature order compared with manifest raw_feature_order |
| `smoke_raw_feature_file_exists` | `PASS` | C:\workSpace\DeepLearnin_sleep\data\processed\pre_sleep_forecasting\new_data\raw_stage1_features.csv |
| `smoke_prediction_file_exists` | `PASS` | C:\workSpace\DeepLearnin_sleep\data\processed\pre_sleep_forecasting\new_data\predictions.csv |
| `smoke_raw_rows` | `PASS` | rows=3 |
| `smoke_raw_columns` | `PASS` | columns=74 |
| `smoke_all_raw_features_present` | `PASS` | all manifest raw features present in smoke raw feature CSV |
| `smoke_prediction_rows` | `PASS` | rows=3 |
| `smoke_prediction_threshold` | `PASS` | thresholds=[0.54] |
| `smoke_prediction_columns` | `PASS` | sleep_episode_id, participant_object_id, sleep_start_datetime, prediction_cutoff_datetime, good_sleep_probability, good_sleep_pred, threshold |
| `pipeline_smoke_rows` | `PASS` | pipeline_rows=3 |
| `pipeline_smoke_threshold` | `PASS` | threshold=0.54 |
| `pipeline_smoke_probabilities_finite` | `PASS` | all generated probabilities are finite |
| `docs_contains:.\.venv\Scripts\Activate.ps1` | `PASS` | present |
| `docs_contains:src\pre_sleep_forecasting\feature_builder.py` | `PASS` | present |
| `docs_contains:--episodes data\processed\pre_sleep_forecasting\new_data\episodes_to_predict.csv` | `PASS` | present |
| `docs_contains:--output data\processed\pre_sleep_forecasting\new_data\raw_stage1_features.csv` | `PASS` | present |
| `docs_contains:src\pre_sleep_forecasting\inference.py` | `PASS` | present |
| `docs_contains:--input data\processed\pre_sleep_forecasting\new_data\raw_stage1_features.csv` | `PASS` | present |
| `docs_contains:--output data\processed\pre_sleep_forecasting\new_data\predictions.csv` | `PASS` | present |
| `docs_contains:threshold: 0.54` | `PASS` | present |

## Canonical Smoke Commands

```powershell
cd C:\workSpace\DeepLearnin_sleep
.\.venv\Scripts\Activate.ps1
python src\pre_sleep_forecasting\feature_builder.py `
  --episodes data\processed\pre_sleep_forecasting\new_data\episodes_to_predict.csv `
  --output data\processed\pre_sleep_forecasting\new_data\raw_stage1_features.csv
python src\pre_sleep_forecasting\inference.py `
  --input data\processed\pre_sleep_forecasting\new_data\raw_stage1_features.csv `
  --output data\processed\pre_sleep_forecasting\new_data\predictions.csv
```
