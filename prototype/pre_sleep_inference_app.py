from __future__ import annotations

from pathlib import Path
import sys
from io import BytesIO

import pandas as pd
import streamlit as st


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = PROJECT_ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from pre_sleep_forecasting.inference import PreSleepInferencePipeline


DEFAULT_MANIFEST_PATH = (
    PROJECT_ROOT
    / "data"
    / "processed"
    / "pre_sleep_forecasting"
    / "design_c_stage1"
    / "inference_package"
    / "pre_sleep_inference_manifest.json"
)
DEFAULT_SAMPLE_RAW_FEATURES = (
    PROJECT_ROOT
    / "data"
    / "processed"
    / "pre_sleep_forecasting"
    / "new_data"
    / "raw_stage1_features.csv"
)
DEFAULT_SAMSUNG_RAW_FEATURES = (
    PROJECT_ROOT
    / "data"
    / "processed"
    / "samsung_health"
    / "pre_sleep_stage1"
    / "samsung_raw_stage1_features.csv"
)
DEFAULT_OUTPUT_PATH = (
    PROJECT_ROOT
    / "data"
    / "processed"
    / "pre_sleep_forecasting"
    / "prototype_outputs"
    / "pre_sleep_predictions_from_app.csv"
)


@st.cache_resource(show_spinner=False)
def load_pipeline(manifest_path: str | None) -> PreSleepInferencePipeline:
    manifest = Path(manifest_path) if manifest_path else DEFAULT_MANIFEST_PATH
    return PreSleepInferencePipeline(
        project_root=PROJECT_ROOT,
        manifest_path=manifest,
    )


def read_csv_from_upload(uploaded_file) -> pd.DataFrame:
    return pd.read_csv(uploaded_file, encoding="utf-8-sig")


def read_csv_from_path(path_text: str) -> pd.DataFrame:
    path = Path(path_text)
    if not path.is_absolute():
        path = PROJECT_ROOT / path
    return pd.read_csv(path, encoding="utf-8-sig")


def prediction_download_bytes(df: pd.DataFrame) -> bytes:
    buffer = BytesIO()
    df.to_csv(buffer, index=False, encoding="utf-8-sig")
    return buffer.getvalue()


def show_distribution(predictions: pd.DataFrame) -> None:
    probability = predictions["good_sleep_probability"]
    pred = predictions["good_sleep_pred"]

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("행 수", f"{len(predictions):,}")
    col2.metric("Good 예측 수", f"{int(pred.sum()):,}")
    col3.metric("Good 예측 비율", f"{float(pred.mean()):.3f}")
    col4.metric("평균 점수", f"{float(probability.mean()):.3f}")

    summary = pd.DataFrame(
        [
            {"항목": "threshold", "값": float(predictions["threshold"].iloc[0])},
            {"항목": "평균 probability", "값": float(probability.mean())},
            {"항목": "중앙값 probability", "값": float(probability.median())},
            {"항목": "P10 probability", "값": float(probability.quantile(0.10))},
            {"항목": "P90 probability", "값": float(probability.quantile(0.90))},
            {"항목": "최소 probability", "값": float(probability.min())},
            {"항목": "최대 probability", "값": float(probability.max())},
        ]
    )
    st.dataframe(summary, use_container_width=True, hide_index=True)


def main() -> None:
    st.set_page_config(
        page_title="Raw Feature 추론 디버그 도구",
        layout="wide",
    )

    st.title("Raw Feature 추론 디버그 도구")
    st.caption("Design C Stage 1 MLP inference package 점검용")

    with st.sidebar:
        st.header("모델")
        manifest_path = st.text_input(
            "Manifest 경로",
            value=str(DEFAULT_MANIFEST_PATH),
        )
        threshold_mode = st.radio(
            "Threshold",
            options=["공식 threshold 0.54", "Recall 참고 threshold 0.47", "직접 입력"],
            index=0,
        )
        if threshold_mode == "공식 threshold 0.54":
            threshold = 0.54
        elif threshold_mode == "Recall 참고 threshold 0.47":
            threshold = 0.47
        else:
            threshold = st.number_input(
                "사용자 지정 threshold",
                min_value=0.0,
                max_value=1.0,
                value=0.54,
                step=0.01,
            )

        st.header("입력")
        input_mode = st.radio(
            "Raw Stage 1 feature CSV",
            options=[
                "CSV 업로드",
                "로컬 경로",
                "샘플 raw feature",
                "Samsung diagnostic raw feature",
            ],
        )

    st.info(
        "입력 CSV는 Design C Stage 1 raw feature 70개를 이미 포함하고 있어야 합니다. "
        "이 도구는 연구자용 디버그 UI이며, 원본 Samsung/Fitbit 데이터에서 feature를 생성하지 않습니다."
    )

    raw_df: pd.DataFrame | None = None
    source_label = ""

    if input_mode == "CSV 업로드":
        uploaded = st.file_uploader("Raw Stage 1 feature CSV 업로드", type=["csv"])
        if uploaded is not None:
            raw_df = read_csv_from_upload(uploaded)
            source_label = uploaded.name
    elif input_mode == "로컬 경로":
        path_text = st.text_input(
            "CSV 경로",
            value=str(DEFAULT_SAMPLE_RAW_FEATURES),
        )
        if st.button("CSV 불러오기"):
            raw_df = read_csv_from_path(path_text)
            source_label = path_text
    elif input_mode == "샘플 raw feature":
        if st.button("샘플 불러오기"):
            raw_df = read_csv_from_path(str(DEFAULT_SAMPLE_RAW_FEATURES))
            source_label = str(DEFAULT_SAMPLE_RAW_FEATURES)
    elif input_mode == "Samsung diagnostic raw feature":
        st.warning(
            "Samsung 모드는 cross-device transfer diagnostic입니다. formal external validation이 아닙니다."
        )
        if st.button("Samsung feature 불러오기"):
            raw_df = read_csv_from_path(str(DEFAULT_SAMSUNG_RAW_FEATURES))
            source_label = str(DEFAULT_SAMSUNG_RAW_FEATURES)

    if raw_df is None:
        st.stop()

    st.subheader("불러온 Raw Features")
    st.write(source_label)
    st.dataframe(raw_df.head(50), use_container_width=True)

    run_col, save_col = st.columns([1, 2])
    run_clicked = run_col.button("예측 실행", type="primary")
    output_path = save_col.text_input(
        "저장 경로",
        value=str(DEFAULT_OUTPUT_PATH),
    )

    if not run_clicked:
        st.stop()

    try:
        pipeline = load_pipeline(manifest_path)
        predictions = pipeline.predict(raw_df, threshold=float(threshold))
    except Exception as exc:
        st.error(f"예측 실행 실패: {exc}")
        st.stop()

    st.subheader("예측 요약")
    show_distribution(predictions)

    st.subheader("예측 결과")
    st.dataframe(predictions, use_container_width=True)

    out_path = Path(output_path)
    if not out_path.is_absolute():
        out_path = PROJECT_ROOT / out_path
    out_path.parent.mkdir(parents=True, exist_ok=True)
    predictions.to_csv(out_path, index=False, encoding="utf-8-sig")
    st.success(f"예측 결과 저장 완료: {out_path}")

    st.download_button(
        label="예측 결과 CSV 다운로드",
        data=prediction_download_bytes(predictions),
        file_name="pre_sleep_predictions.csv",
        mime="text/csv",
    )

    if input_mode == "Samsung diagnostic raw feature":
        st.warning(
            "Samsung 예측 결과는 Fitbit-compatible cross-device diagnostic으로만 해석해야 합니다. "
            "선택된 MLP는 Samsung stage-proxy label에 안정적으로 transfer되지 않았습니다."
        )


if __name__ == "__main__":
    main()
