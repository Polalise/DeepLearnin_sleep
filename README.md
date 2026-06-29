# DeepLearnin Sleep

이 프로젝트는 웨어러블 수면 데이터를 활용하여 **연구 수준의 엄격한 수면 전 예측 파이프라인**을 구축하는 것을 목표로 한다.

최종 목표:

```text
sleep_start_datetime 이전에 사용 가능한 웨어러블 기반 데이터만 사용하여
다가오는 수면 에피소드의 good_sleep_label을 예측한다.
```

## 현재 최종 모델

* 실험군: `presleep_stage1_hp_tiny_dropout40_wd1e3`
* 대표 체크포인트: `presleep_stage1_hp_tiny_dropout40_wd1e3_seed2027`
* Feature set: Design C Stage 1 strict pre-sleep features
* 모델: PyTorch MLP
* Hidden dimensions: `(24, 12)`
* Dropout: `0.40`
* Weight decay: `0.001`
* 공식 threshold: `0.54`

최종 모델 체크포인트:

```text
data/processed/pre_sleep_forecasting/design_c_stage1/experiments/stage1_hyperparameter_stability_outputs/models/presleep_stage1_hp_tiny_dropout40_wd1e3_seed2027_best.pt
```

## 성능 참고 지표

대표 held-out participant test 성능:

* Balanced accuracy: `0.6492`
* ROC AUC: `0.6937`
* Average precision: `0.6187`
* Precision: `0.6553`
* Recall: `0.4245`
* Participant bootstrap balanced accuracy 95% CI: `[0.5436, 0.7259]`
* Brier score: `0.2126`
* Expected calibration error: `0.1256`

해석:

* 이 모델은 유용하지만 중간 수준의 예측 신호를 보여준다.
* 확률 출력값은 완벽하게 보정된 실제 확률이라기보다는 **모델 점수**로 해석해야 한다.
* 이 모델은 임상, 의료, 또는 고위험 건강 관련 의사결정 목적으로 사용하기 위한 것이 아니다.

## 추론 전처리 계약

최종 추론 전처리 계약은 다음과 같다.

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

핵심 추론 관련 파일:

```text
src/pre_sleep_forecasting/feature_builder.py
src/pre_sleep_forecasting/inference.py
data/processed/pre_sleep_forecasting/design_c_stage1/inference_package/pre_sleep_inference_manifest.json
data/processed/pre_sleep_forecasting/design_c_stage1/inference_package/pre_sleep_inference_feature_contract.csv
```

## 새로운 수면 에피소드 예측하기

최소한 다음 컬럼을 포함하는 episode CSV 파일을 준비한다.

```text
participant_object_id
sleep_start_datetime
```

선택 컬럼:

```text
sleep_episode_id
```

표준 PowerShell 실행 흐름:

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

출력 컬럼:

```text
sleep_episode_id
participant_object_id
sleep_start_datetime
prediction_cutoff_datetime
good_sleep_probability
good_sleep_pred
threshold
```

## 주요 문서

최종 프로젝트 상태:

```text
reports/pre_sleep_forecasting_project_final_status.md
```

최종 산출물 목록:

```text
reports/pre_sleep_final_artifact_inventory.md
```

추론 사용 가이드:

```text
docs/pre_sleep_inference_usage.md
```

추론 패키지 QA 보고서:

```text
reports/pre_sleep_inference_package_qa.md
```

최종 모델 보고서:

```text
reports/pre_sleep_forecasting_stage1_final_report_updated.md
```

후속 작업 계획:

```text
reports/pre_sleep_sequence_model_followup_plan.md
reports/pre_sleep_calibration_followup_plan.md
reports/pre_sleep_external_future_validation_plan.md
```

추론 전용 의존성:

```text
requirements-inference.txt
```

프로젝트 규칙:

```text
Codex.Rule.md
```

## 모델링 참고 사항

* Logistic Regression과 Random Forest는 전통적인 머신러닝 baseline/reference 모델로만 사용한다.
* PCA는 feature 구조를 탐색하기 위한 분석 용도로만 사용한다.
* 현재 최종 모델은 Design C Stage 1 strict pre-sleep features를 사용해 학습한 PyTorch MLP이다.
* Sequence model 실험과 calibration correction은 선택적인 후속 작업으로 남아 있다.

## 현재 상태

완료된 작업:

* strict pre-sleep feature 설계
* participant-level split
* 최종 Stage 1 MLP 선정
* threshold 정책 선정
* participant bootstrap uncertainty 분석
* calibration diagnostics
* 재사용 가능한 추론 스크립트 작성
* 추론 사용 문서 작성
* 최종 산출물 목록 작성
* 최종 프로젝트 상태 보고서 작성

선택적인 다음 작업:

* strict pre-sleep sequence model follow-up plan 실행
* calibration correction follow-up plan 실행
* 외부 데이터 또는 미래 기간 validation plan 실행
