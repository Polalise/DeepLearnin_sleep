# 최종 딥러닝 실험 요약

## 1. 데이터 개선 요약

- 기존 전체 feature 입력(`full_current`)은 validation 성능은 높았지만 test 일반화가 불안정했다.
- sleep-session 계열, recovery 계열, same-date feature timing 위험을 점검했다.
- 1차 개선에서는 feature subset ablation을 수행했다.
- 2차 개선에서는 `target_date - 1 day` feature만 사용하는 previous-day dataset을 생성해 timing sensitivity를 확인했다.

## 2. 최종 후보

- 최종 1순위 모델은 `same_date / daytime_only / window 7 / mlp_current_day`이다.
- test balanced accuracy는 `0.8440`이고, participant-level bootstrap 95% CI는 `[0.8042, 0.8924]`이다.
- test ROC AUC는 `0.9023`이고, ROC AUC bootstrap 95% CI는 `[0.8483, 0.9463]`이다.

## 3. 딥러닝 sequence 비교 후보

- sequence 모델 비교 후보는 `same_date / daytime_only / window 7 / gru`이다.
- test balanced accuracy는 `0.8317`이며, bootstrap 95% CI는 `[0.7886, 0.8859]`이다.

## 4. Previous-day 보수 실험

- strict previous-day 후보는 `previous_day / daytime_only / window 14 / bilstm`이다.
- test balanced accuracy는 `0.6098`이고, bootstrap 95% CI는 `[0.4758, 0.7413]`이다.
- previous-day 실험에서는 성능이 크게 낮아졌으므로, 현재 최고 모델은 strict prior-day forecasting 모델로 해석하면 안 된다.

## 5. 최종 해석

- 현재 가장 강한 결과는 same-date daytime-only feature를 사용한 sleep classification이다.
- same-date 성능은 높지만, sleep target의 `calendar_date`가 sleep end date 기준이므로 일부 feature timing 해석에 주의가 필요하다.
- previous-day 실험은 더 보수적인 timing control이며, 이 조건에서는 예측력이 낮아졌다.
- 따라서 최종 보고에서는 `same-date classification model`과 `previous-day timing sensitivity analysis`를 분리해서 제시하는 것이 적절하다.
