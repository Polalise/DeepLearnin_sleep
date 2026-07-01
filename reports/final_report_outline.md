# 딥러닝 기반 웨어러블 수면 건강 예측 시스템 최종 보고서 목차

## 1. 프로젝트 개요 및 배경

- 프로젝트 주제 선정 배경
- 수면 건강 관리의 필요성
- 웨어러블 생체신호 데이터 활용 가능성
- 기존 수면 관리 방식과 사후 분석 중심 접근의 한계
- 본 프로젝트의 최종 목표
  - 수면 시작 전 데이터만으로 다가오는 수면의 `good_sleep_label` 예측
- 기대 효과 및 활용 가능성

## 2. 프로젝트 범위 및 최종 문제 정의

- 초기 수면 건강 예측 구상과 최종 범위 조정
- 최종 예측 문제 정의
  - strict pre-sleep forecasting
  - 예측 기준 시점: `sleep_start_datetime`
  - 예측 대상: `good_sleep_label`
- 분류 문제로서의 모델링 방향
- 프로젝트에서 제외하거나 보조적으로 다룬 범위
  - 수면 점수 회귀
  - 스트레스 위험도 직접 예측
  - 회복 부족 여부 직접 예측
- 최종 산출물 개요
  - 모델
  - 추론 파이프라인
  - Streamlit 프로토타입
  - Samsung Health 전이 진단

## 3. 데이터 출처 및 데이터셋 구성

- 원천 데이터 구조
  - MongoDB `rais_anonymized`
  - Fitbit 데이터
  - SEMA 설문 데이터
  - participant survey 데이터
- 주요 웨어러블 변수
  - 수면 기록
  - 심박수 및 안정 시 심박수
  - HRV
  - 활동량
  - 칼로리
  - SpO2
  - 호흡수
  - 손목 온도
  - 스트레스 점수
- 분석 단위 정의
  - 초기 daily participant-date 단위
  - 최종 sleep episode 단위
- 예측 대상 정의
  - `good_sleep_label`
  - 클래스 분포
- 데이터 규모
  - 수면 에피소드 수
  - 참여자 수
  - 학습/검증/테스트 구성

## 4. 데이터 수집, 병합 및 전처리

- MongoDB 원천 데이터 확인
- 필요한 변수 추출
- 일 단위 집계 데이터 생성
- 수면 타깃 테이블과 웨어러블/설문 데이터 병합
- 결측치 분석
- 결측치 처리 전략
  - 고결측 변수 제거
  - median imputation
  - zero filling
  - missing indicator 생성
- 범주형 변수 인코딩
- 표준화 및 스케일링
- 참가자 단위 train/validation/test split
- 데이터 누수 방지를 위한 처리 기준

## 5. 탐색적 데이터 분석

- 최종 모델링 데이터셋 구조
- `good_sleep_label` 분포
- 변수군별 결측률
- 주요 변수와 수면 라벨의 관계
- 상관관계 분석
- 타깃별 주요 변수 차이
- 이상치 및 데이터 품질 이슈
- EDA 기반 모델링 시사점

## 6. Strict Pre-Sleep Feature 설계

- 기존 same-date 예측 방식의 한계
- `calendar_date`와 수면 종료 시점 문제
- 예측 가능 시점 기준 재정의
- Design C Stage 1 feature set
  - 수면 시작 전 intraday steps
  - 수면 시작 전 intraday calories
  - 수면 시작 전 heart rate
  - 수면 시작 시각/calendar features
  - 전일 daily activity/resting HR
  - missing indicators
- 최종 feature contract
  - raw feature 70개
  - zero-variance 제거 후 최종 58개
- Stage 2 rolling/history feature 실험 개요
- Stage 2B compact rolling feature 실험 개요

## 7. 기준 모델 및 비교 실험

- 전통 머신러닝 기준 모델의 역할
  - Logistic Regression
  - Random Forest
- feature set 비교
  - all features
  - wearable-only
- 기준 모델 성능 요약
- 기준 모델을 최종 모델로 선택하지 않은 이유
- 딥러닝 모델 비교 계획
  - MLP
  - SimpleRNN
  - LSTM
  - GRU
  - BiLSTM
  - 1D-CNN

## 8. 딥러닝 모델 설계

- 최종 모델링 방향
  - PyTorch 기반 MLP
  - 이진 분류
- 입력 데이터 구조
- 모델 구조
  - hidden dimensions `(24, 12)`
  - dropout `0.40`
  - weight decay `0.001`
- 손실 함수 및 학습 방식
- threshold 정책
- Early stopping 및 validation 기반 모델 선택
- 시퀀스 모델 설계
  - episode sequence window 3/5/7
  - GRU/LSTM/BiLSTM/1D-CNN 후보

## 9. 모델 학습 및 하이퍼파라미터 튜닝

- 학습 환경 및 주요 라이브러리
- Stage 1 MLP 학습
- Stage 2 rolling/history feature 실험
- Stage 2B compact rolling feature 실험
- 하이퍼파라미터 안정성 실험
- seed robustness 평가
- 최종 대표 모델 선정 기준
- 최종 선택 모델
  - `presleep_stage1_hp_tiny_dropout40_wd1e3_seed2027`

## 10. 모델 성능 평가

- 평가 지표
  - Balanced Accuracy
  - ROC AUC
  - Average Precision
  - Precision
  - Recall
  - F1-score
  - Brier Score
  - Expected Calibration Error
- 최종 대표 모델 성능
- threshold `0.54` 기준 성능
- recall-priority threshold `0.47` 대안
- participant-level bootstrap confidence interval
- calibration 분석
- 전통 ML 기준 모델과 최종 모델 비교
- 시퀀스 모델 후속 실험 결과
- 최종 모델 성능 해석

## 11. 결과 분석 및 인사이트

- 수면 예측에 유의미했던 주요 변수군
- 활동량, 심박, HRV, 수면 시작 시각의 관계
- 스트레스 관련 변수의 활용 가능성과 누수 위험
- 모델이 잘 예측한 패턴
- 모델이 어려워한 패턴
- recall과 precision의 trade-off
- probability score 해석 시 주의점
- 개인별 일반화 성능 이슈

## 12. 추론 파이프라인 및 패키징

- 최종 inference contract
  - raw Stage 1 features 70개
  - median imputer
  - StandardScaler
  - zero-variance feature 제거
  - 최종 58개 feature
  - PyTorch MLP
  - sigmoid probability
  - threshold `0.54`
- 주요 코드 구성
  - feature builder
  - inference runner
  - feature contract
  - model checkpoint
- 신규 수면 에피소드 예측 절차
- smoke test 결과
- 재사용 가능한 산출물 목록

## 13. Streamlit 기반 수면 예측 프로토타입

- 프로토타입 목적
- Raw feature inference debug tool
- Samsung Sleep Forecasting Live Prototype
- 주요 화면 구성
  - 대시보드
  - 오늘/다가오는 수면 예측
  - Samsung Health sync prediction
  - partial-input preset prediction
  - scenario comparison
  - advanced retraining experiment plan
- 사용자 입력 및 데이터 업로드 흐름
- 예측 결과 시각화
- 개인별/최근 수면 예측 리포트 기능
- 프로토타입의 한계

## 14. Samsung Health 전이 진단

- Samsung Health 데이터 적용 목적
- Samsung-to-Fitbit feature adapter
- Samsung 수면 에피소드 생성
- Fitbit-compatible Stage 1 feature 생성
- Samsung proxy label 구성
  - sleep score proxy
  - stage-based proxy label
- Samsung 적용 결과
- 전이 성능 한계
- 공식 외부 검증이 아닌 diagnostic으로 해석해야 하는 이유
- Samsung-specific retraining 필요성

## 15. 서비스 활용 시나리오

- 개인 수면 관리 서비스
- 취침 전 수면 품질 예측 피드백
- 웨어러블 기반 생활 패턴 점검
- 직장인 피로/번아웃 조기 모니터링 보조
- 운동 후 회복 상태 모니터링 보조
- 헬스케어 앱 및 웨어러블 기기 연동 가능성
- 연구용 개인화 수면 예측 시스템

## 16. 한계점 및 개선 방향

- 테스트 참여자 수 제한
- 개인별 생체신호 편차
- 일반화 성능 한계
- calibration 불완전성
- recall 제한
- 외부 검증 부족
- Samsung Health 도메인 차이
- 스트레스/수면 관련 변수의 누수 가능성
- 개선 방향
  - 개인화 모델
  - 추가 센서 데이터 활용
  - 더 긴 기간의 데이터 수집
  - Samsung-specific retraining
  - calibration 개선
  - threshold 정책 다변화
  - 설명 가능한 AI 적용
  - 실시간 예측 기능 강화

## 17. 결론

- 프로젝트 요약
- 최종 모델 및 파이프라인 요약
- 최종 성능 요약
- 프로젝트의 의의
- 기대 효과
- 향후 확장 가능성
