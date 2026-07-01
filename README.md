# DeepLearnin Sleep

`sleep_start_datetime` 이전에 이용 가능한 데이터만 사용해 다가오는 수면 episode의 `good_sleep_label`을 예측하는 엄격한 pre-sleep forecasting 프로젝트입니다.

## 최종 목표

```text
이전 수면/웨어러블 이력과 수면 시작 전까지 관측된 웨어러블 데이터를 이용해,
다가오는 수면 episode가 좋은 수면인지 예측합니다.
```

최종 workflow는 수면 시작 이후 또는 수면 완료 이후의 정보를 사용하지 않도록 설계되어 있습니다.

## 최종 모델

- 실험군: `presleep_stage1_hp_tiny_dropout40_wd1e3`
- 대표 checkpoint: `presleep_stage1_hp_tiny_dropout40_wd1e3_seed2027`
- 특성 세트: Design C Stage 1 strict pre-sleep features
- 모델: PyTorch MLP
- Hidden dimensions: `(24, 12)`
- Dropout: `0.40`
- Weight decay: `0.001`
- 공식 threshold: `0.54`

Checkpoint:

```text
data/processed/pre_sleep_forecasting/design_c_stage1/experiments/stage1_hyperparameter_stability_outputs/models/presleep_stage1_hp_tiny_dropout40_wd1e3_seed2027_best.pt
```

## 성능 참고 지표

대표 held-out participant test 성능:

- Balanced accuracy: `0.6492`
- ROC AUC: `0.6937`
- Average precision: `0.6187`
- Precision: `0.6553`
- Recall: `0.4245`
- Participant bootstrap balanced accuracy 95% CI: `[0.5436, 0.7259]`
- Brier score: `0.2126`
- Expected calibration error: `0.1256`

해석:

- 이 모델은 엄격한 pre-sleep timing 정의 아래에서 중간 수준의 예측 신호를 보입니다.
- 확률 출력은 완벽히 보정된 현실 확률이 아니라 모델 점수로 해석해야 합니다.
- 이 모델은 임상, 의료, 고위험 의사결정 용도로 사용하기 위한 것이 아닙니다.

## 추론 계약

```text
raw Stage 1 features 70
-> train median imputer
-> train StandardScaler
-> remove 12 zero-variance features
-> final model input features 58
-> PyTorch MLP
-> sigmoid probability
-> threshold 0.54
```

핵심 파일:

```text
src/pre_sleep_forecasting/feature_builder.py
src/pre_sleep_forecasting/inference.py
data/processed/pre_sleep_forecasting/design_c_stage1/inference_package/pre_sleep_inference_manifest.json
data/processed/pre_sleep_forecasting/design_c_stage1/inference_package/pre_sleep_inference_feature_contract.csv
```

## 새 episode 예측

입력 episode CSV에는 다음 컬럼이 필요합니다.

```text
participant_object_id
sleep_start_datetime
```

선택 컬럼:

```text
sleep_episode_id
```

PowerShell workflow:

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

예측 결과 컬럼:

```text
sleep_episode_id
participant_object_id
sleep_start_datetime
prediction_cutoff_datetime
good_sleep_probability
good_sleep_pred
threshold
```

## Samsung Health 진단

Samsung Health 데이터는 cross-device transfer 진단을 위해 Fitbit 호환 특성 schema로 변환되었습니다.

이는 Samsung 원천 데이터가 Fitbit 원천 데이터로 변환되었다는 뜻이 아니며, 공식적인 외부 검증도 아닙니다.

Samsung workflow:

```text
scripts/29_profile_samsung_health_core_tables.py
scripts/30_build_samsung_sleep_episode_table.py
scripts/31_build_samsung_pre_sleep_stage1_features.py
scripts/32_run_samsung_pre_sleep_inference.py
scripts/33_join_samsung_sleep_score_proxy_labels.py
scripts/34_build_samsung_stage_based_proxy_labels.py
scripts/35_evaluate_samsung_predictions_against_stage_proxy_labels.py
scripts/36_diagnose_samsung_presleep_activity_coverage.py
```

Samsung 진단의 주요 결론:

- adapter는 70개 특성의 Fitbit 호환 Stage 1 테이블을 생성할 수 있습니다.
- 수면 전 심박과 전날 daily activity 특성은 사용할 수 있습니다.
- 현재 export에서는 수면 전 step/calorie interval 데이터가 희소합니다.
- Samsung proxy label은 공식 외부 검증으로 볼 수 없습니다.
- 선택된 Fitbit 학습 MLP는 Samsung stage-proxy label에 안정적으로 전이되지 않습니다.

주요 Samsung report:

```text
reports/samsung_pre_sleep_external_prediction_interpretation.md
reports/samsung_stage_proxy_external_evaluation_report.md
reports/samsung_to_fitbit_feature_mapping_confidence.md
reports/samsung_to_fitbit_adapter_high_priority_improvements.md
reports/samsung_presleep_activity_coverage_diagnostic.md
```

## Raw Feature 추론 디버그 도구

이미 생성된 raw Stage 1 feature CSV 파일에 대해 선택된 inference pipeline을 실행할 수 있는 경량 Streamlit 디버그 도구가 있습니다.

Debug app:

```text
prototype/pre_sleep_inference_app.py
```

실행:

```powershell
cd C:\workSpace\DeepLearnin_sleep
.\.venv\Scripts\python.exe -m pip install -r requirements-prototype.txt
.\.venv\Scripts\python.exe -m streamlit run prototype\pre_sleep_inference_app.py
```

Debug tool 사용 가이드:

```text
docs/pre_sleep_prototype_usage.md
```

이 도구는 end-to-end Samsung live forecasting prototype이 아닙니다. Samsung Health export 폴더를 읽거나 원천 wearable 파일에서 특성을 생성하지 않습니다.

## Samsung Live Forecasting Prototype

Samsung live prototype은 Samsung Health export 폴더에서 시작해 최종 학습 MLP까지 이어지는 end-to-end 진단 workflow를 실행합니다. 빠른 프로토타입 상호작용을 위한 일부 입력 프리셋 모드도 포함합니다.

App:

```text
prototype/samsung_sleep_forecasting_app.py
```

실행:

```powershell
cd C:\workSpace\DeepLearnin_sleep
.\.venv\Scripts\python.exe -m pip install -r requirements-prototype.txt
.\.venv\Scripts\python.exe -m streamlit run prototype\samsung_sleep_forecasting_app.py
```

기본 데이터 소스:

```text
docs/samsunghealth
```

사용 가이드:

```text
docs/samsung_sleep_live_prototype_usage.md
```

Flow:

```text
Samsung Health export
-> sleep episode generation
-> Samsung-to-Fitbit feature adapter
-> final Design C PyTorch MLP
-> prediction trend and latest results
```

첫 화면은 live-style dashboard이며 다음 정보를 보여줍니다.

```text
Samsung 데이터 가용성
최신 예측 대상 수면 시작 시간
오늘 밤/다음 수면에 대한 자연어 예측 문장
최신 예측 상태
스냅샷 확률 변화
최근 확률 추세
모델/주의사항 상태
```

주요 live forecast update:

```text
오늘 밤 예측 갱신
-> 완료된 Samsung 수면 이력 갱신
-> 선택한 예상 수면 시작 시간의 target sleep episode 생성
-> 최신 Samsung wearable feature build
-> 기존 최종 MLP inference
-> 오늘 밤/다음 수면 예측 문장
```

이 과정은 inference를 위한 feature history/baseline 입력을 갱신합니다. 신경망을 재학습하지는 않습니다.

오늘 밤 예측 산출물:

```text
data/processed/samsung_health/pre_sleep_stage1/live_forecast/today_sleep_target_episode.csv
data/processed/samsung_health/pre_sleep_stage1/live_forecast/today_raw_stage1_features.csv
data/processed/samsung_health/pre_sleep_stage1/live_forecast/today_sleep_forecast_prediction.csv
data/processed/samsung_health/pre_sleep_stage1/live_forecast/today_stage1_feature_summary.csv
data/processed/samsung_health/pre_sleep_stage1/live_forecast/today_sleep_forecast_prediction_summary.csv
reports/samsung_today_sleep_forecast_feature_build_summary.md
reports/samsung_today_sleep_forecast_prediction_summary.md
```

프로토타입은 어떤 핵심 입력이 실제로 반영되었는지도 보고합니다.

```text
history/baseline feature coverage
current-day wearable feature coverage
missing current-day features handled by fitted imputer/missing indicators
```

또한 table별 Samsung source freshness를 보고하므로, current-day feature 누락이 export coverage 문제인지 추적할 수 있습니다.

```text
sleep stage
sleep summary
heart rate
daily steps
interval steps
daily activity
step trend
```

current-day Samsung intraday 값이 없을 때, 오늘 예측 flow는 inference 전에 수동 wearable 보완값을 선택적으로 적용할 수 있습니다.

```text
today steps so far
last 3-hour / last 1-hour steps
pre-sleep / last 3-hour / last 1-hour heart rate
```

보완값은 별도 파일에 기록되며 모델을 재학습하지 않습니다.

```text
data/processed/samsung_health/pre_sleep_stage1/live_forecast/today_manual_wearable_supplement_report.csv
```

앱은 Samsung-only baseline prediction, final prediction, comparison table, timestamped snapshot도 저장합니다.

```text
data/processed/samsung_health/pre_sleep_stage1/live_forecast/today_samsung_only_prediction.csv
data/processed/samsung_health/pre_sleep_stage1/live_forecast/today_forecast_comparison.csv
data/processed/samsung_health/pre_sleep_stage1/live_forecast/today_numeric_sensitivity.csv
data/processed/samsung_health/pre_sleep_stage1/live_forecast/snapshots/
```

고급 재학습은 live prediction과 분리되어 있습니다.

```text
고급 재학습
-> retraining experiment plan
-> 기본적으로 UI에서 학습을 직접 실행하지 않음
```

프리셋 빠른 예측 flow:

```text
steps and coarse user presets
-> 70 raw Design C Stage 1 features
-> existing imputer/scaler
-> final Design C PyTorch MLP
-> good_sleep probability
```

프리셋 빠른 예측은 raw feature가 직접 입력, 파생값, 프리셋 추정값, fitted-imputer 보완 중 어디에서 왔는지도 집계합니다.

프리셋 시나리오 비교 flow:

```text
same direct inputs
-> multiple activity / calorie / heart-rate preset combinations
-> repeated final Design C PyTorch MLP inference
-> ranked probability comparison
```

시나리오 화면은 원본 feature table을 읽지 않아도 preset 상태 변화에 따른 최고/최저 확률 차이를 볼 수 있게 표시합니다.

Preset feature builder:

```text
src/pre_sleep_forecasting/preset_feature_builder.py
```

Preset mode outputs:

```text
data/processed/pre_sleep_forecasting/prototype_outputs/quick_preset_raw_stage1_features.csv
data/processed/pre_sleep_forecasting/prototype_outputs/quick_preset_prediction.csv
data/processed/pre_sleep_forecasting/prototype_outputs/quick_preset_feature_source_summary.csv
data/processed/pre_sleep_forecasting/prototype_outputs/quick_preset_scenario_comparison.csv
data/processed/pre_sleep_forecasting/prototype_outputs/quick_preset_scenario_raw_features.csv
```

## 주요 보고서

최종 프로젝트 상태:

```text
reports/pre_sleep_forecasting_project_final_status.md
```

최종 artifact inventory:

```text
reports/pre_sleep_final_artifact_inventory.md
```

Inference 사용 가이드:

```text
docs/pre_sleep_inference_usage.md
```

Inference package QA report:

```text
reports/pre_sleep_inference_package_qa.md
```

최종 모델 report:

```text
reports/pre_sleep_forecasting_stage1_final_report_updated.md
```

## 모델링 메모

- Logistic Regression과 Random Forest는 전통적 ML baseline/reference model로만 사용됩니다.
- PCA는 feature structure를 탐색하기 위한 분석입니다.
- Sequence model과 calibration correction은 후속 실험으로 평가했지만, 최종 선택 모델은 Design C Stage 1 MLP입니다.
- Samsung Health transfer는 cross-device 진단으로 완료되었으며, 강한 domain-shift caveat와 함께 보고해야 합니다.

## 의존성

Inference dependency reference:

```text
requirements-inference.txt
```

Project rules:

```text
Codex.Rule.md
```
