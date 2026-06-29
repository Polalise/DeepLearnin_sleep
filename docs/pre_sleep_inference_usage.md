# Pre-Sleep Forecasting Inference Usage

## 목적

이 문서는 최종 선택된 strict pre-sleep forecasting 모델을 사용해서 새 sleep episode에 대한 예측을 실행하는 방법을 정리합니다.

이 모델의 목적은 `sleep_start_datetime` 이전까지 사용 가능한 웨어러블 데이터만으로, 곧 시작될 sleep episode의 `good_sleep_label`을 예측하는 것입니다.

## 선택된 모델

- Experiment family: `presleep_stage1_hp_tiny_dropout40_wd1e3`
- Representative checkpoint: `presleep_stage1_hp_tiny_dropout40_wd1e3_seed2027`
- Feature set: Design C Stage 1 strict pre-sleep features
- Model: PyTorch MLP
- Hidden dimensions: `(24, 12)`
- Dropout: `0.40`
- Weight decay: `0.001`
- 공식 threshold: `0.54`

성능 참고:

- Representative test balanced accuracy: `0.6492`
- ROC AUC: `0.6937`
- Average precision: `0.6187`
- Bootstrap balanced accuracy 95% CI: `[0.5436, 0.7259]`

## 해석상 주의점

이 모델은 연구용 개인 수면 quality 예측 실험에 사용할 수 있습니다.

사용하기 적절한 경우:

- threshold 기반 good sleep / not good sleep 예측
- 밤별 상대적 sleep quality ranking
- 개인 피드백 실험

사용하면 안 되는 경우:

- 임상 의사결정
- 고위험 의료 판단
- calibration caveat 없이 확률값을 실제 확률처럼 전달하는 것

현재 모델의 probability는 완벽하게 calibration되어 있지 않습니다.

Calibration 참고:

- Brier score: `0.2126`
- Expected calibration error: `0.1256`
- Mean predicted probability: `0.4396`
- Observed positive rate: `0.3610`

따라서 `good_sleep_probability`는 실제 좋은 수면 확률이라기보다는 모델 score에 가깝게 해석하는 것이 안전합니다.

## 입력 파일

Feature builder는 최소한 아래 컬럼을 가진 episode CSV를 입력으로 받습니다.

```csv
participant_object_id,sleep_start_datetime
621e2e8e67b776a24055b564,2021-05-24 23:48:30
```

선택 컬럼:

```csv
sleep_episode_id
```

`sleep_episode_id`가 없으면 feature builder가 `participant_object_id`와 `sleep_start_datetime`을 조합해서 자동 생성합니다.

## 필요한 데이터 소스

이 추론 파이프라인은 아래 데이터 소스에 의존합니다.

- 로컬 MongoDB 데이터베이스: `rais_anonymized`
- MongoDB 컬렉션: `fitbit`
- MongoDB Fitbit type:
  - `steps`
  - `calories`
  - `heart_rate`
- 일 단위 집계 파일:
  - `data/processed/modeling_dataset_daily.csv`
- 추론 manifest:
  - `data/processed/pre_sleep_forecasting/design_c_stage1/inference_package/pre_sleep_inference_manifest.json`

MongoDB에는 아래 인덱스가 있으면 좋습니다.

```javascript
db.fitbit.createIndex({ id: 1, type: 1, "data.dateTime": 1 })
```

## 추론 전처리 계약

추론 전처리 흐름은 아래와 같습니다.

```text
raw Stage 1 features 70개
-> train median imputer
-> train StandardScaler
-> zero-variance feature 12개 제거
-> 최종 model features 58개
-> MLP
-> sigmoid probability
-> threshold 적용
```

Feature contract는 아래 파일에 저장되어 있습니다.

```text
data/processed/pre_sleep_forecasting/design_c_stage1/inference_package/pre_sleep_inference_feature_contract.csv
```

중요한 점:

- `feature_builder.py`는 passthrough 컬럼 4개와 raw Stage 1 feature 70개를 만듭니다.
- `inference.py`는 raw feature 70개를 받아서 imputer/scaler를 적용합니다.
- 이후 zero-variance feature 12개를 제거하고 최종 58개 feature를 모델에 넣습니다.

## 스크립트

Feature builder:

```text
src/pre_sleep_forecasting/feature_builder.py
```

Inference script:

```text
src/pre_sleep_forecasting/inference.py
```

## 실행 환경

PowerShell에서 프로젝트 가상환경을 먼저 활성화한 뒤 실행합니다.

```powershell
cd C:\workSpace\DeepLearnin_sleep
.\.venv\Scripts\Activate.ps1
```

또는 가상환경 Python을 직접 지정할 수 있습니다.

```powershell
.\.venv\Scripts\python.exe src\pre_sleep_forecasting\inference.py --help
```

기본 시스템 Python에는 `torch`, `pymongo`, `bson`이 없을 수 있으므로, 이 프로젝트의 `.venv` 사용을 권장합니다.

Inference 전용 의존성 목록은 아래 파일에 정리되어 있습니다.

```text
requirements-inference.txt
```

## 1단계. 예측할 Episode 입력 CSV 만들기

예시 경로:

```text
data/processed/pre_sleep_forecasting/new_data/episodes_to_predict.csv
```

예시 내용:

```csv
participant_object_id,sleep_start_datetime
621e2e8e67b776a24055b564,2021-05-24 23:48:30
621e2e8e67b776a24055b564,2021-05-25 23:46:30
621e2e8e67b776a24055b564,2021-05-26 23:21:30
```

## 2단계. Raw Stage 1 Feature 생성

PowerShell에서 실행합니다.

```powershell
cd C:\workSpace\DeepLearnin_sleep

python src\pre_sleep_forecasting\feature_builder.py `
  --episodes data\processed\pre_sleep_forecasting\new_data\episodes_to_predict.csv `
  --output data\processed\pre_sleep_forecasting\new_data\raw_stage1_features.csv
```

예상 출력:

```text
raw Stage 1 features written: ...
rows: N
features: 74
```

74개 컬럼의 의미:

- passthrough 컬럼 4개
- imputation/scaling/zero-variance 제거 전 raw Stage 1 feature 70개

## 3단계. 추론 실행

공식 threshold `0.54`를 사용합니다.

```powershell
python src\pre_sleep_forecasting\inference.py `
  --input data\processed\pre_sleep_forecasting\new_data\raw_stage1_features.csv `
  --output data\processed\pre_sleep_forecasting\new_data\predictions.csv
```

예상 출력:

```text
predictions written: ...
rows: N
threshold: 0.54
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

## 선택 Threshold

공식 threshold는 `0.54`입니다.

Recall-priority threshold는 `0.47`입니다.

좋은 수면 후보를 더 많이 잡는 것이 precision보다 중요할 때 사용할 수 있습니다.

```powershell
python src\pre_sleep_forecasting\inference.py `
  --input data\processed\pre_sleep_forecasting\new_data\raw_stage1_features.csv `
  --output data\processed\pre_sleep_forecasting\new_data\predictions_recall_priority.csv `
  --threshold 0.47
```

성능 참고:

- 공식 threshold `0.54`
  - test balanced accuracy: `0.6492`
  - precision: `0.6553`
  - recall: `0.4245`
- recall-priority threshold `0.47`
  - test balanced accuracy: `0.6592`
  - precision: `0.5600`
  - recall: `0.5723`

## Smoke Test 상태

3-row smoke test가 성공했습니다.

입력:

```text
data/processed/pre_sleep_forecasting/new_data/episodes_to_predict.csv
```

생성된 feature:

```text
data/processed/pre_sleep_forecasting/new_data/raw_stage1_features.csv
```

생성된 prediction:

```text
data/processed/pre_sleep_forecasting/new_data/predictions.csv
```

실행 결과:

```text
rows: 3
threshold: 0.54
```

## 자주 나는 오류

### episodes CSV FileNotFoundError

Feature builder 실행 전에 episode 입력 파일이 먼저 존재해야 합니다.

생성할 파일:

```text
data/processed/pre_sleep_forecasting/new_data/episodes_to_predict.csv
```

### 필수 episode 컬럼 누락

Episode CSV에는 반드시 아래 컬럼이 있어야 합니다.

```text
participant_object_id
sleep_start_datetime
```

### inference 실행 중 raw feature 컬럼 누락

먼저 `feature_builder.py`를 실행해야 합니다.

`inference.py`는 raw Stage 1 feature 70개가 들어 있는 CSV를 입력으로 받습니다.

### MongoDB가 느림

아래 인덱스가 있는지 확인합니다.

```javascript
db.fitbit.getIndexes()
```

있으면 좋은 인덱스:

```javascript
{ id: 1, type: 1, "data.dateTime": 1 }
```

## 현재 한계

- 새로운 participant에 대한 일반화는 아직 불확실합니다.
- held-out test set은 participant 14명뿐입니다.
- bootstrap confidence interval이 아직 넓습니다.
- probability calibration이 완벽하지 않습니다.
- feature builder는 현재 프로젝트의 MongoDB 구조와 동일한 데이터 구조를 가정합니다.
- 현재 모델은 임상/의료 의사결정용 모델이 아닙니다.

## 최종 요약

현재 파이프라인은 새 episode CSV를 받아서 feature를 생성하고, 최종 선택된 pre-sleep MLP 모델로 예측을 수행할 수 있습니다.

즉 아래 흐름이 가능합니다.

```text
episodes_to_predict.csv
-> feature_builder.py
-> raw_stage1_features.csv
-> inference.py
-> predictions.csv
```

이 단계까지 완료되었기 때문에, 현재 프로젝트는 연구용 모델 선정뿐 아니라 재사용 가능한 추론 초안까지 갖춘 상태입니다.
