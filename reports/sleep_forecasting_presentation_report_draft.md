# AI 기반 취침 전 수면 건강 예측 모델 개발 발표 보고서 초안

작성 기준일: 2026-06-30  
분량 기준: PDF 발표 보고서 최대 30쪽 이내  
작성 목적: 내부 산출물과 실험 결과를 바탕으로 발표용 보고서 초안을 구성한다. 디자인은 제외하고, 페이지별 핵심 메시지와 포함할 데이터만 정리한다.

---

## 1쪽. 표지

### AI 기반 취침 전 수면 건강 예측 모델 개발

웨어러블 생체신호 데이터를 활용한 `good_sleep_label` 예측 및 Streamlit 프로토타입 구현

- 프로젝트 유형: 딥러닝 기반 수면 예측 프로젝트
- 핵심 모델: PyTorch MLP
- 핵심 기능: 취침 전까지 확보 가능한 데이터만 사용하여 오늘 밤 수면이 좋을 가능성을 예측
- 프로토타입: Samsung Health export 기반 live-style forecasting dashboard

시각화 필요 여부: 없음

---

## 2쪽. 목차

1. 프로젝트 개요 및 배경
2. 과제 범위
3. 데이터 수집 및 데이터셋 구성
4. 데이터 분석 및 전처리
5. 모델 설계
6. 모델 학습 및 튜닝
7. 모델 성능 평가
8. 결과 분석 및 인사이트
9. 수면 건강 예측 대시보드
10. 서비스 활용 시나리오
11. 한계점 및 개선 방향
12. 결론

시각화 필요 여부: 없음

---

## 3쪽. 프로젝트 개요 및 배경

### 수면 관리는 사후 기록보다 사전 예측이 더 중요하다

수면 건강은 피로, 집중력, 스트레스, 회복 상태와 연결되는 생활 건강 지표이다. 기존 수면 관리 방식은 수면이 끝난 뒤 점수나 통계를 확인하는 방식이 많다. 이 방식은 과거 상태를 이해하는 데는 유용하지만, 사용자가 오늘 밤 취침 전에 행동을 조정하는 데에는 한계가 있다.

본 프로젝트는 웨어러블 데이터의 시간 연속성과 생체신호 기록을 활용하여, 수면이 시작되기 전에 오늘 밤 수면 결과를 예측하는 방향으로 문제를 재정의했다. 최종 목표는 `sleep_start_datetime` 이전까지 관측 가능한 데이터만 사용해 upcoming sleep episode의 `good_sleep_label`을 예측하는 것이다.

핵심 차별점은 수면 후에야 알 수 있는 정보나 수면 도중 생성되는 정보를 모델 입력에서 제외했다는 점이다. 따라서 본 프로젝트는 단순한 수면 분류가 아니라 실제 서비스 흐름에 가까운 strict pre-sleep forecasting 문제로 정리된다.

주요 참조 자료: `README.md`, `reports/pre_sleep_forecasting_project_final_status.md`, `reports/deep_learning_project_roadmap.md`

시각화 필요 여부: 없음

---

## 4쪽. 프로젝트 목표 및 기대 효과

### 목표는 오늘 밤 수면의 good sleep 가능성을 예측하는 것이다

본 프로젝트의 최종 목표는 다음과 같다.

- 웨어러블 기반 수면, 심박, 활동량, HRV, 스트레스 관련 데이터를 수집하고 모델링 가능한 형태로 정리한다.
- 수면 시작 전까지 사용할 수 있는 feature만 선별하여 예측 문제를 설계한다.
- 딥러닝 모델을 학습하여 `good_sleep_label`을 예측한다.
- 모델 성능과 불확실성을 평가하고, 예측 결과를 사용자가 이해할 수 있는 대시보드로 구현한다.
- Samsung Health 데이터에 적용 가능한 프로토타입을 만들어 실시간에 가까운 사용 흐름을 검증한다.

기대 효과는 수면이 끝난 뒤 결과를 확인하는 수준에서 벗어나, 취침 전 사용자가 자신의 수면 상태 가능성을 참고할 수 있는 개인 피드백 시스템의 기반을 마련하는 것이다.

주의할 점은 본 프로젝트가 의료 진단 모델이 아니라 연구용 예측 및 개인 피드백 프로토타입이라는 점이다.

시각화 필요 여부: 없음

---

## 5쪽. 과제 범위

### 최종 범위는 strict pre-sleep forecasting과 프로토타입 구현이다

과제 범위는 크게 네 단계로 구성된다.

1. 데이터 파이프라인 구축
   - MongoDB 원천 데이터 확인
   - Fitbit, SEMA, survey 데이터 추출
   - daily aggregation 및 sleep episode 단위 구성

2. 모델링 데이터셋 구성
   - 결측치 처리
   - leakage-prone sleep outcome feature 제외
   - participant-aware train / validation / test split
   - strict pre-sleep Stage 1 feature 생성

3. 딥러닝 모델 학습 및 평가
   - PyTorch MLP 후보 학습
   - rolling/history feature 실험
   - sequence model follow-up
   - bootstrap uncertainty와 calibration 평가

4. 프로토타입 구현
   - Samsung Health export를 Fitbit-compatible Stage 1 schema로 변환
   - 오늘 밤 예상 취침 시각 기준 forecast 생성
   - Samsung-only baseline, manual supplement, sensitivity 비교

범위에서 제외하거나 확장 과제로 둔 항목은 임상 진단, 완전한 외부 검증, UI 버튼을 통한 즉시 재학습, 스트레스 위험도 자체 예측 모델이다.

시각화 필요 여부: 없음

---

## 6쪽. 데이터 출처 및 원천 구조

### 원천 데이터는 MongoDB 기반 Fitbit, SEMA, survey 데이터와 Samsung Health export로 구성된다

원천 연구 데이터는 `rais_anonymized` MongoDB에 저장된 Fitbit, SEMA, survey collection에서 출발했다. Fitbit collection은 약 71,284,346개 문서 규모였고, SEMA는 15,380개, survey는 935개 문서로 확인되었다.

주요 데이터 유형은 다음과 같다.

- Fitbit: 수면, 심박, HRV, 활동량, 칼로리, SpO2, 호흡, 피부온도, 스트레스 점수
- SEMA: 하루 중 맥락 및 기분 응답
- Survey: 참가자 단위 설문 응답
- Samsung Health: sleep stage, sleep summary, heart rate, daily steps, interval steps, activity summary

Samsung Health 데이터는 최종 모델 학습 데이터가 아니라, 학습된 Fitbit 기반 모델을 다른 웨어러블 export에 적용해보는 cross-device diagnostic 용도로 사용했다.

주요 참조 자료: `reports/mongodb_raw_overview.md`, `reports/variable_extraction_summary.md`, `docs/samsunghealth_structure_summary.txt`

시각화 필요 여부: 원천 데이터 소스 구조 다이어그램을 추가하면 좋음

---

## 7쪽. 추출 변수 및 daily aggregation

### 다양한 생체신호를 participant-date 단위로 집계했다

필요 변수 추출 단계에서는 raw MongoDB 문서에서 모델링에 사용할 테이블을 생성했다. 추출된 주요 테이블은 다음과 같다.

| 테이블 | 행 수 | 주요 내용 |
| --- | ---: | --- |
| `fitbit_stress_score` | 1,911 | Fitbit stress score |
| `fitbit_daily_hrv_summary` | 2,475 | 일별 HRV summary |
| `fitbit_hrv_details` | 220,512 | HRV 상세값 |
| `fitbit_resting_heart_rate` | 12,362 | 안정시 심박 |
| `fitbit_activity_minutes` | 28,812 | 활동 강도별 minute |
| `fitbit_daily_spo2` | 1,274 | 일별 SpO2 |
| `fitbit_respiratory_rate_summary` | 3,000 | 호흡률 |
| `sema_responses` | 15,380 | 기분/맥락 응답 |
| `surveys_responses` | 935 | 설문 응답 |

대용량 steps, calories, wrist temperature 데이터는 raw CSV 전체 추출 대신 MongoDB에서 날짜 단위로 직접 집계했다.

일별 집계 기준은 `participant_object_id + calendar_date`이다. 이 기준은 초기 daily modeling 단계에서 수면 outcome을 participant-day 단위로 맞추기 위해 사용되었다.

시각화 필요 여부: 추출 테이블별 row count 막대그래프 추가 권장

---

## 8쪽. 최종 daily modeling dataset

### merged daily dataset은 3,551개 행과 130개 컬럼으로 구성됐다

daily aggregation 결과를 sleep target row에 병합하여 최종 daily modeling dataset을 구성했다.

- 행 수: 3,551
- 컬럼 수: 130
- 참가자 수: 69
- 기간: 2021-05-24 ~ 2022-01-22
- duplicate participant-date row: 0
- `good_sleep_label=1`: 1,398건, 39.37%
- `good_sleep_label=0`: 2,153건, 60.63%

주요 source table의 match rate는 데이터 종류에 따라 달랐다. resting heart rate, activity minutes, steps, calories는 대부분의 base row와 매칭되었고, SpO2와 stress, SEMA는 부분적으로만 관측되었다.

이 단계의 daily dataset은 탐색과 baseline 검증에는 중요하지만, 최종 pre-sleep 모델에서는 수면 후 정보가 들어갈 수 있는 sleep outcome column을 제외하고 strict timing 기준에 맞춰 feature를 재구성했다.

시각화 필요 여부: 기존 `reports/figures/final_dataset_eda/target_distribution.png`, `missing_rate_by_feature_family.png` 사용 가능

---

## 9쪽. 데이터 분석: 결측과 target 분포

### wearable 데이터는 관측 밀도가 feature family별로 다르다

EDA 결과, 전체 target positive rate는 39.37%로 class imbalance가 존재했다. 따라서 Accuracy만으로 모델을 평가하면 다수 class에 유리한 판단이 될 수 있어 balanced accuracy를 주요 지표로 사용했다.

결측률은 feature family에 따라 큰 차이를 보였다.

| Feature family | 평균 결측률 |
| --- | ---: |
| SpO2 | 65.36% |
| Stress | 47.48% |
| Sleep stage | 43.63% |
| Respiratory | 37.65% |
| SEMA | 32.55% |
| HRV | 30.11% |
| Activity | 0.11% |
| Resting HR | 0.00% |

이는 웨어러블 센서 데이터가 모든 날짜에 동일하게 수집되지 않으며, feature availability 자체가 중요한 모델링 신호가 될 수 있음을 의미한다.

시각화 필요 여부: 기존 missing rate chart 사용 가능

---

## 10쪽. 전처리 전략

### 결측 처리와 leakage 방지가 전처리의 핵심이었다

전처리에서는 직접적인 sleep outcome 또는 수면 후에야 알 수 있는 feature를 제외했다. 예를 들어 `minutesAsleep`, `deep_minutes`, `rem_minutes`, `timeInBed`, `efficiency`와 같은 열은 sleep quality를 설명할 수는 있지만, 취침 전 예측 입력으로 사용하면 leakage가 발생할 수 있다.

결측 처리 전략은 다음과 같다.

- 결측률 70% 초과 feature column 제거
- 결측이 있던 retained column에 missing indicator 추가
- count, rate, sum, record-count 계열은 결측 시 0으로 대체
- 그 외 numeric feature는 median imputation
- 최종 missing-handled table의 결측 cell 수: 0
- missing indicator 추가 수: 97

categorical encoding 단계에서는 predictor로 사용할 categorical column이 없었기 때문에 one-hot column은 추가되지 않았다. participant ID와 calendar date는 key와 split 관리용으로 보존했다.

시각화 필요 여부: 결측 처리 전후 column 수 변화 도표 추가 가능

---

## 11쪽. 학습/검증/테스트 분리

### participant-aware split으로 사용자 간 누수를 방지했다

수면 데이터는 같은 사람의 반복 관측이 많기 때문에 row 단위 random split을 사용하면 같은 참가자의 패턴이 train과 test에 동시에 들어갈 수 있다. 이를 방지하기 위해 participant-aware split을 적용했다.

| Split | Rows | Participants | Positive rate |
| --- | ---: | ---: | ---: |
| Train | 2,944 | 55 | 0.3988 |
| Test | 607 | 14 | 0.3690 |
| All | 3,551 | 69 | 0.3937 |

최종 strict pre-sleep forecasting 단계에서는 train / validation / test가 다시 정리되었다.

| Split | Samples | Participants |
| --- | ---: | ---: |
| Train | 2,323 | 46 |
| Validation | 347 | 9 |
| Test | 881 | 14 |

참가자 overlap은 0으로 확인되었다.

시각화 필요 여부: split별 target rate 막대그래프 추가 권장

---

## 12쪽. 예측 문제 정의

### 최종 예측 대상은 upcoming sleep episode의 `good_sleep_label`이다

최종 문제는 strict pre-sleep binary classification이다.

```text
Input: sleep_start_datetime 이전까지 관측 가능한 wearable-derived feature
Output: upcoming sleep episode의 good_sleep_label
```

이 정의는 기존 same-date sleep classification과 다르다. 초기 daily target의 `calendar_date`는 수면 종료일 기준으로 해석될 수 있기 때문에, 같은 날짜 feature를 그대로 사용하면 실제 예측 시점에서 아직 알 수 없는 정보가 섞일 위험이 있다.

따라서 최종 workflow는 sleep episode를 기준 단위로 삼고, prediction cutoff를 `sleep_start_datetime`으로 고정했다. 모델은 수면 시작 전 intraday steps, calories, heart rate, 이전날 activity/resting HR, timing/calendar feature, missing indicator를 입력으로 사용한다.

이 보고서에서 “수면 품질 예측”은 수면 점수 회귀가 아니라 `good_sleep_label` binary classification을 의미한다.

시각화 필요 여부: 시간축 다이어그램 추가 권장

---

## 13쪽. 모델 입력 구조

### Stage 1 strict pre-sleep feature가 최종 모델 입력이다

최종 inference contract는 다음과 같다.

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

Stage 1 feature group은 다음과 같다.

- pre-sleep intraday steps
- pre-sleep intraday calories
- pre-sleep intraday heart rate
- sleep start timing/calendar features
- previous-day daily activity/resting-HR features
- missing indicators

이 구성은 모델이 수면 시작 전에 확보할 수 있는 정보만 사용하도록 설계되었다.

시각화 필요 여부: inference pipeline flow chart 추가 권장

---

## 14쪽. 기준 모델과 딥러닝 후보

### 전통 ML은 baseline, 최종 모델 후보는 딥러닝 모델로 구분했다

프로젝트에서는 Logistic Regression, Random Forest 등의 전통 ML 모델을 baseline/reference로 사용했다. 특히 wearable-only Logistic Regression baseline은 높은 성능을 보였지만, 보고서에서는 딥러닝 최종 모델과 구분하여 기준 모델로만 해석한다.

딥러닝 모델 실험은 다음 흐름으로 진행되었다.

- Stage 1 MLP: strict pre-sleep feature 기반 tabular MLP
- Stage 2 full rolling/history MLP: rolling/history feature 확장
- Stage 2B compact rolling/history MLP: rolling feature 축소
- Sequence follow-up: GRU, LSTM, BiLSTM, 1D CNN

최종 선정 모델은 Stage 1 strict pre-sleep PyTorch MLP이다. Sequence model은 follow-up 실험으로 평가했지만 최종 모델을 대체하지 않았다.

시각화 필요 여부: 모델 후보 비교 표 사용 가능

---

## 15쪽. 최종 모델 설계

### 작고 정규화된 MLP가 최종 후보로 선택됐다

최종 selected representative model은 다음과 같다.

- Experiment family: `presleep_stage1_hp_tiny_dropout40_wd1e3`
- Representative checkpoint: `presleep_stage1_hp_tiny_dropout40_wd1e3_seed2027`
- Model: PyTorch MLP
- Hidden dimensions: `(24, 12)`
- Dropout: 0.40
- Weight decay: 0.001
- Learning rate: 0.0008
- Official threshold: 0.54

모델이 작은 구조를 사용한 이유는 참가자 수와 episode 수가 제한된 상황에서 과적합을 줄이고, participant-level generalization을 우선하기 위해서이다.

시각화 필요 여부: MLP 구조 다이어그램 추가 가능

---

## 16쪽. 학습 및 튜닝 결과

### Stage 1 hyperparameter-stabilized MLP가 가장 안정적인 최종 후보였다

주요 후보의 test 성능은 다음과 같다.

| Candidate | Feature set | Test BA | ROC AUC | AP | F1 |
| --- | ---: | ---: | ---: | ---: | ---: |
| Stage 1 single seed | 58 | 0.6338 | 0.6875 | 0.6009 | 0.4904 |
| Stage 1 seed mean | 58 | 0.6107 | 0.6681 | 0.6016 | 0.5309 |
| Stage 2 full rolling | 380 | 0.6025 | 0.6628 | 0.5855 | 0.5307 |
| Stage 2B compact rolling | 148 | 0.5923 | 0.6852 | 0.5788 | 0.5530 |
| Best Stage 1 HP config mean | 58 | 0.6586 | 0.6942 | 0.6185 | 0.5298 |

Stage 2와 Stage 2B는 feature 수를 늘렸지만 held-out test balanced accuracy를 개선하지 못했다. 이는 rolling/history feature가 참가자별 noise 또는 overfitting을 증가시켰을 가능성을 시사한다.

시각화 필요 여부: 기존 또는 신규 모델별 metric bar chart 권장

---

## 17쪽. 최종 모델 성능 평가

### 최종 모델은 strict pre-sleep 조건에서 중간 수준의 예측 신호를 보였다

대표 checkpoint의 held-out participant test 성능은 다음과 같다.

| Metric | Value |
| --- | ---: |
| Balanced accuracy | 0.6492 |
| ROC AUC | 0.6937 |
| Average precision | 0.6187 |
| F1 | 0.5153 |
| Precision | 0.6553 |
| Recall | 0.4245 |
| Official threshold | 0.54 |

정확도보다 balanced accuracy를 중심으로 보는 이유는 target 분포가 완전히 균형적이지 않기 때문이다. 모델은 strict pre-sleep 조건에서 의미 있는 신호를 보였지만, recall은 제한적이다.

시각화 필요 여부: confusion matrix, ROC curve, PR curve 추가 권장

---

## 18쪽. 불확실성 및 calibration

### 확률값은 실제 확률보다 model score로 해석하는 것이 안전하다

participant-level bootstrap 결과, balanced accuracy의 95% confidence interval은 `[0.5436, 0.7259]`였다. test set 참가자가 14명으로 제한되어 있기 때문에 성능 불확실성은 여전히 크다.

Calibration summary는 다음과 같다.

- Brier score: 0.2126
- Expected calibration error: 0.1256
- Mean predicted probability: 0.4396
- Observed positive rate: 0.3610

모델은 전반적으로 good sleep probability를 다소 과대추정하는 경향이 있었다. 따라서 프로토타입에서는 `good_sleep_probability`를 임상적 의미의 실제 확률이 아니라 threshold 기반 판단과 ranking에 가까운 model score로 설명해야 한다.

시각화 필요 여부: 기존 `reports/figures/final_baseline_validation/probability_calibration.png`는 baseline용이므로, 최종 MLP calibration chart가 있으면 별도 추가 권장

---

## 19쪽. Sequence model follow-up

### GRU/LSTM 계열은 recall을 높였지만 최종 MLP를 명확히 넘지는 못했다

Sequence follow-up에서는 strict pre-sleep feature contract를 유지한 상태에서 window 3, 5, 7 episode sequence를 구성했다. 모델 후보는 GRU, LSTM, BiLSTM, 1D CNN이었다.

가장 높은 test balanced accuracy는 GRU window-3 후보에서 나왔다.

| Model | Window | Test BA | ROC AUC | AP | Recall |
| --- | ---: | ---: | ---: | ---: | ---: |
| GRU | 3 | 약 0.6466 | 0.6935 | 0.5996 | 0.7010 |
| BiLSTM | 5 | 약 0.6290 | 0.6778 | 0.5720 | 0.5118 |
| 1D CNN | 5 | 약 0.5905 | 0.6888 | 0.6147 | 0.7946 |
| Final Stage 1 MLP | - | 0.6492 | 0.6937 | 0.6187 | 0.4245 |

Sequence model은 recall 측면에서는 가능성을 보였지만 false positive가 증가했고, balanced accuracy와 average precision에서는 최종 MLP를 명확히 넘지 못했다.

시각화 필요 여부: sequence 후보별 BA/recall trade-off chart 추가 권장

---

## 20쪽. 결과 분석 및 인사이트

### 수면 예측에는 생체신호 자체뿐 아니라 데이터 가용성도 영향을 준다

EDA와 baseline 해석에서 activity, HRV, stress, record-count, missing indicator 계열 feature가 예측에 영향을 줄 수 있음이 확인되었다. 특히 wearable 데이터는 항상 동일하게 기록되지 않기 때문에, 특정 feature의 값뿐 아니라 해당 feature가 관측되었는지 여부도 모델에 의미 있는 신호가 될 수 있다.

다만 stress 관련 feature는 sleep/recovery leakage 가능성이 있으므로 해석에 주의가 필요하다. `stress_sleep_points_mean`처럼 명시적으로 수면 관련 의미를 갖는 feature는 제외했고, retained stress feature도 생리적 원인으로 단정하지 않는다.

핵심 인사이트는 다음과 같다.

- 수면 품질 예측은 단순히 전날 수면 시간만으로 결정되지 않는다.
- 심박, 활동량, HRV, 기록 밀도, missingness가 함께 작동한다.
- 참가자별 생체신호 baseline 차이가 크기 때문에 unseen participant generalization이 어렵다.
- feature를 많이 추가하는 것보다 prediction timing을 엄격히 맞추는 것이 중요하다.

시각화 필요 여부: 기존 `top_target_correlations.png`, `key_features_by_target.png` 사용 가능

---

## 21쪽. Samsung Health 적용 목적

### Samsung Health 적용은 외부 검증이 아니라 cross-device diagnostic이다

Samsung Health export는 최종 모델을 실제 사용자형 데이터 흐름에 적용해보기 위한 진단 환경으로 사용했다. 이 단계의 목적은 Fitbit으로 학습된 모델을 Samsung Health 원천 데이터에 그대로 적용했을 때, feature schema 변환과 inference pipeline이 작동하는지 확인하는 것이다.

Samsung workflow는 다음과 같다.

```text
Samsung Health export
-> sleep-stage 기반 sleep episode 생성
-> Samsung-to-Fitbit raw Stage 1 feature adapter
-> fitted imputer/scaler/model
-> Samsung prediction output
```

중요한 점은 Samsung data가 formal external validation을 제공하지 않는다는 것이다. proxy label은 제한적이며, Samsung raw feature distribution은 Fitbit training distribution과 다르다.

시각화 필요 여부: Samsung adapter pipeline flow chart 추가 권장

---

## 22쪽. Samsung Health 데이터 적용 결과

### feature contract는 맞췄지만 domain shift와 coverage 문제가 확인됐다

Samsung Health 적용 후 valid sleep episode는 1,493건이었다. timezone correction 이후 sleep start range는 2021-07-30 03:40:14부터 2026-06-27 03:39:00까지로 정리되었다.

강한 coverage를 보인 feature는 다음과 같다.

- `heart_rate_pre_sleep_mean`: 1,411 / 1,493
- `heart_rate_pre_sleep_last_3h_mean`: 1,398 / 1,493
- `heart_rate_pre_sleep_last_1h_mean`: 1,383 / 1,493
- `previous_day_steps_sum`: 1,493 / 1,493
- `previous_day_calories_sum`: 1,493 / 1,493

반면 pre-sleep step/calorie interval coverage는 매우 낮았다.

- `steps_pre_sleep_sum`: 14 / 1,493
- `steps_pre_sleep_last_1h_sum`: 10 / 1,493
- `calories_pre_sleep_sum`: 14 / 1,493
- `calories_pre_sleep_last_1h_sum`: 10 / 1,493

공식 threshold 0.54 기준 Samsung 전체 prediction에서는 mean probability 0.3848, predicted positives 8 / 1,493으로 낮은 score distribution이 확인되었다.

시각화 필요 여부: Samsung feature coverage bar chart 추가 권장

---

## 23쪽. 오늘 밤 수면 예측 프로토타입

### 프로토타입은 오늘 동기화된 데이터로 오늘 밤 수면을 예측한다

Streamlit 기반 Samsung live forecasting prototype은 사용자가 expected sleep start datetime을 지정하면 Samsung Health export를 기반으로 최신 sleep history와 wearable feature를 반영해 오늘 밤 forecast를 생성한다.

프로토타입 흐름은 다음과 같다.

```text
Samsung Health latest export
-> completed sleep episode table update
-> today's target sleep episode CSV creation
-> Samsung-to-Fitbit raw Stage 1 feature build
-> existing final MLP inference
-> plain-language tonight/upcoming-sleep forecast
```

중요한 설계 원칙은 feature update와 model retraining을 분리한 것이다. 오늘 forecast update는 최신 데이터를 feature history와 baseline에 반영하지만, neural network 자체를 재학습하지 않는다.

시각화 필요 여부: 앱 화면 캡처 `design/*.png` 또는 Streamlit screenshot 사용 가능

---

## 24쪽. 프로토타입 실행 결과 예시

### 2026-06-30 forecast에서는 manual supplement 반영 후 positive prediction이 생성됐다

현재 live forecast output은 다음과 같다.

- Sleep episode ID: `today_forecast__20260630233000`
- Forecast target sleep start: 2026-06-30 23:30:00
- Prediction cutoff: 2026-06-30 08:17:08
- Final probability: 0.6078624
- Official threshold: 0.54
- Final prediction: 1

Samsung-only baseline과 final supplement 반영 결과는 다르게 나타났다.

| Scenario | Probability | Prediction |
| --- | ---: | ---: |
| Samsung-only | 0.41335535 | 0 |
| Final with manual supplement | 0.6078624 | 1 |
| Delta | +0.19450705 | label changed |

이는 current-day wearable supplement가 prediction에 영향을 줄 수 있음을 보여준다. 다만 supplement는 모델 재학습이 아니라 오늘 forecast raw feature row에만 적용되는 보완 입력이다.

시각화 필요 여부: Samsung-only vs supplement probability comparison bar chart 추가 권장

---

## 25쪽. 민감도 분석

### 예측은 특히 취침 시각 변화와 심박 변화에 민감하게 반응했다

오늘 forecast row에 대해 numeric sensitivity 분석을 수행했다. 주요 결과는 다음과 같다.

| Scenario | Probability | Delta | Prediction |
| --- | ---: | ---: | ---: |
| Baseline | 0.607862 | 0.000000 | 1 |
| Heart rate +5 | 0.617688 | +0.009826 | 1 |
| Heart rate -5 | 0.598078 | -0.009784 | 1 |
| Last 1h steps +200 | 0.601362 | -0.006500 | 1 |
| Sleep time -30m | 0.606609 | -0.001253 | 1 |
| Sleep time +30m | 0.522453 | -0.085409 | 0 |

가장 큰 변화는 예상 취침 시각을 30분 늦추는 scenario에서 발생했으며, 이 경우 threshold 아래로 내려가 prediction label도 0으로 바뀌었다. 이 결과는 timing/calendar feature가 오늘 forecast 판단에 영향을 줄 수 있음을 보여준다.

시각화 필요 여부: sensitivity tornado/bar chart 추가 권장

---

## 26쪽. 서비스 활용 시나리오

### 개인 수면 관리와 회복 모니터링의 사전 피드백 도구로 활용할 수 있다

서비스 활용 가능성은 다음과 같다.

1. 개인 수면 관리
   - 오늘 밤 수면이 좋을 가능성을 취침 전에 확인
   - 최근 활동량, 심박, 취침 예정 시각 변화에 따른 score 변화를 비교

2. 직장인 번아웃 조기 경고
   - 반복적으로 낮은 sleep forecast score가 나타나는 경우 휴식 권고 또는 생활 리듬 점검 신호로 활용

3. 운동 후 회복 상태 모니터링
   - pre-sleep heart rate와 previous-day activity feature를 통해 회복 부담이 큰 날을 탐색

4. 웨어러블 앱 연동
   - Samsung Health, Fitbit 등 wearable export를 feature adapter로 연결
   - 단, device별 domain shift를 고려해 별도 calibration 또는 fine-tuning 필요

현재 단계에서는 “수면 건강 점수”를 임상적으로 확정하는 서비스가 아니라, 개인 피드백과 연구용 의사결정 지원으로 위치시키는 것이 적절하다.

시각화 필요 여부: 서비스 흐름도 추가 가능

---

## 27쪽. 한계점

### 모델은 research-grade candidate이며, 임상적 판단에는 사용할 수 없다

주요 한계는 다음과 같다.

- held-out test participant 수가 14명으로 제한되어 bootstrap confidence interval이 넓다.
- official threshold 기준 recall이 0.4245로 제한적이다.
- probability calibration이 완전하지 않아 실제 확률처럼 해석하기 어렵다.
- participant별 생체신호 baseline 차이가 커서 unseen participant generalization이 어렵다.
- Samsung Health 적용은 domain shift와 feature coverage 문제가 크다.
- Samsung proxy label은 formal external validation으로 보기 어렵다.
- pre-sleep interval step/calorie coverage가 sparse하여 일부 current-day activity feature는 imputer 또는 manual supplement에 의존한다.
- UI에서 model retraining을 바로 수행하지 않으며, 재학습은 별도 검증 프로세스가 필요하다.

따라서 본 프로젝트의 결과는 개인 피드백 연구와 프로토타입 수준의 적용 가능성을 보인 것으로 해석해야 한다.

시각화 필요 여부: 없음

---

## 28쪽. 개선 방향

### 다음 단계는 개인화, 외부 검증, calibration, 데이터 coverage 개선이다

향후 개선 방향은 다음과 같다.

1. 개인화 모델
   - 참가자별 baseline을 더 직접적으로 반영
   - 충분한 개인 history가 쌓인 뒤 personalization layer 또는 calibration 적용

2. 외부 검증
   - Fitbit 외 다른 wearable dataset에서 label 기반 검증 수행
   - Samsung Health는 proxy label이 아니라 신뢰 가능한 sleep quality label 확보 필요

3. 실시간 feature coverage 개선
   - current-day interval steps/calories export 확보
   - Samsung daily total을 post-sleep leakage 없이 사용할 수 있는지 timestamp 검증

4. calibration 개선
   - model score를 probability로 전달하기 전 calibration method 검토
   - validation participant 수 부족에 따른 overfitting 위험 점검

5. 설명 가능한 AI
   - sensitivity analysis, feature contribution, scenario comparison을 통해 사용자 설명력 강화

6. 재학습 workflow
   - labeled data rebuild
   - train/validation/test 재분리
   - threshold 및 calibration 재검토
   - artifact versioning 후 candidate promotion

시각화 필요 여부: 개선 roadmap 도표 추가 가능

---

## 29쪽. 결론

### 취침 전 데이터만으로 오늘 밤 수면 예측이 가능한 연구용 프로토타입을 완성했다

본 프로젝트는 기존의 사후 수면 분석을 넘어, 수면 시작 전에 사용 가능한 wearable-derived feature만으로 upcoming sleep episode의 `good_sleep_label`을 예측하는 strict pre-sleep forecasting 문제를 설계했다.

최종 모델은 Stage 1 strict pre-sleep PyTorch MLP이며, held-out participant test에서 balanced accuracy 0.6492, ROC AUC 0.6937을 기록했다. 성능은 높다고 단정할 수준은 아니지만, 엄격한 예측 시점 조건에서도 의미 있는 predictive signal이 확인되었다.

또한 Samsung Health export 기반 live-style prototype을 구현하여 오늘 밤 expected sleep start 기준 forecast, Samsung-only baseline 비교, manual wearable supplement 반영, numeric sensitivity 분석까지 수행할 수 있게 했다.

최종 결론은 다음과 같다.

- strict pre-sleep timing을 만족하는 수면 예측 pipeline을 구축했다.
- 딥러닝 MLP 모델은 moderate predictive signal을 보였다.
- 프로토타입은 오늘의 feature update와 forecast 흐름을 구현했다.
- 확률은 calibrated clinical probability가 아니라 model score로 해석해야 한다.
- 외부 검증, 개인화, calibration, feature coverage 개선이 다음 단계이다.

시각화 필요 여부: 최종 pipeline + 핵심 성능 요약 1장 추가 권장

---

## 30쪽. 시각화 자료 추가 필요 목록

### 이미 존재하는 시각화로 사용할 수 있는 자료

- Target distribution: `reports/figures/final_dataset_eda/target_distribution.png`
- Missing rate by feature family: `reports/figures/final_dataset_eda/missing_rate_by_feature_family.png`
- Key features by target: `reports/figures/final_dataset_eda/key_features_by_target.png`
- Top target correlations: `reports/figures/final_dataset_eda/top_target_correlations.png`
- Traditional baseline metric comparison: `reports/figures/baseline/metric_comparison.png`
- Traditional baseline ROC curves: `reports/figures/baseline/roc_curves.png`
- Traditional baseline confusion matrices: `reports/figures/baseline/confusion_matrices.png`
- Prototype design screenshots: `design/ver1_1.png` ~ `design/ver2_4.png`

### 추가로 만들면 좋은 시각화

1. 전체 데이터 파이프라인 다이어그램
   - MongoDB / Fitbit / SEMA / survey / Samsung Health -> feature table -> model -> dashboard

2. Strict pre-sleep timing diagram
   - 수면 시작 전 cutoff, 사용할 수 있는 데이터, 사용할 수 없는 데이터 구분

3. 모델 후보 성능 비교 bar chart
   - Stage 1, Stage 2, Stage 2B, sequence model, final model의 balanced accuracy / ROC AUC

4. 최종 MLP confusion matrix / ROC curve / PR curve
   - 기존 baseline용 figure와 구분되는 최종 딥러닝 모델 figure가 있으면 보고서 설득력이 커짐

5. Participant bootstrap confidence interval chart
   - balanced accuracy, ROC AUC, F1, recall interval

6. Samsung Health feature coverage chart
   - heart rate / previous-day activity / pre-sleep steps / calories coverage 비교

7. Today forecast comparison chart
   - Samsung-only 0.4134 vs supplement 반영 0.6079

8. Numeric sensitivity tornado chart
   - sleep time +30m, heart rate +/-5, steps 변화에 따른 probability delta

### 초안 작성에 부족한 자료

초안 작성 자체에는 자료가 충분하다. 다만 최종 PDF 품질을 높이려면 위 추가 시각화 중 3, 4, 6, 7, 8번을 생성하는 것이 가장 효과적이다.

