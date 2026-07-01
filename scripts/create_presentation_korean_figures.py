from __future__ import annotations

from pathlib import Path
import textwrap

import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import numpy as np
import pandas as pd
import seaborn as sns
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch
from sklearn.metrics import auc, precision_recall_curve, roc_curve


ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "reports" / "figures" / "presentation_korean"

TOKENS = {
    "surface": "#FCFCFD",
    "panel": "#FFFFFF",
    "ink": "#1F2430",
    "muted": "#6F768A",
    "grid": "#E6E8F0",
    "axis": "#D7DBE7",
}

NEUTRAL = {
    "open": TOKENS["panel"],
    "xlight": "#F4F5F7",
    "light": "#E2E5EA",
    "base": "#C5CAD3",
    "mid": "#7A828F",
    "dark": "#464C55",
}

COLORS = {
    "blue": {"xlight": "#EAF1FE", "light": "#CEDFFE", "base": "#A3BEFA", "mid": "#5477C4", "dark": "#2E4780"},
    "gold": {"xlight": "#FFF4C2", "light": "#FFEA8F", "base": "#FFE15B", "mid": "#B8A037", "dark": "#736422"},
    "orange": {"xlight": "#FFEDDE", "light": "#FFBDA1", "base": "#F0986E", "mid": "#CC6F47", "dark": "#804126"},
    "olive": {"xlight": "#D8ECBD", "light": "#BEEB96", "base": "#A3D576", "mid": "#71B436", "dark": "#386411"},
    "pink": {"xlight": "#FCDAD6", "light": "#F5BACC", "base": "#F390CA", "mid": "#BD569B", "dark": "#8A3A6F"},
}


def set_theme() -> None:
    sns.set_theme(
        style="whitegrid",
        rc={
            "figure.facecolor": TOKENS["surface"],
            "axes.facecolor": TOKENS["panel"],
            "axes.edgecolor": TOKENS["axis"],
            "axes.labelcolor": TOKENS["ink"],
            "axes.grid": True,
            "axes.spines.top": False,
            "axes.spines.right": False,
            "grid.color": TOKENS["grid"],
            "grid.linewidth": 0.8,
            "font.family": "sans-serif",
            "font.sans-serif": ["Malgun Gothic", "Noto Sans KR", "Segoe UI", "Arial", "sans-serif"],
            "axes.unicode_minus": False,
        },
    )


def add_header(fig, ax, title: str, subtitle: str, *, title_width: int = 68, subtitle_width: int = 100) -> None:
    title = textwrap.fill(title, width=title_width, break_long_words=False)
    subtitle = textwrap.fill(subtitle, width=subtitle_width, break_long_words=False)
    ax.set_title("")
    fig.subplots_adjust(top=0.82)
    left = ax.get_position().x0
    fig.text(left, 0.97, title, ha="left", va="top", fontsize=15, fontweight="bold", color=TOKENS["ink"])
    fig.text(left, 0.91, subtitle, ha="left", va="top", fontsize=10, color=TOKENS["muted"])
    sns.despine(ax=ax)


def save(fig, name: str) -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    png = OUT_DIR / f"{name}.png"
    svg = OUT_DIR / f"{name}.svg"
    fig.savefig(png, dpi=180, bbox_inches="tight", facecolor=TOKENS["surface"])
    fig.savefig(svg, bbox_inches="tight", facecolor=TOKENS["surface"])
    plt.close(fig)
    print(png)
    print(svg)


def figure_source_data_diagram() -> None:
    fig, ax = plt.subplots(figsize=(12, 6.8))
    ax.set_xlim(0, 12)
    ax.set_ylim(0, 7)
    ax.axis("off")

    def box(x, y, w, h, text, color, edge):
        patch = FancyBboxPatch(
            (x, y),
            w,
            h,
            boxstyle="round,pad=0.03,rounding_size=0.08",
            facecolor=color,
            edgecolor=edge,
            linewidth=1.3,
        )
        ax.add_patch(patch)
        ax.text(x + w / 2, y + h / 2, text, ha="center", va="center", fontsize=11, color=TOKENS["ink"], linespacing=1.25)

    def arrow(x1, y1, x2, y2):
        ax.add_patch(
            FancyArrowPatch(
                (x1, y1),
                (x2, y2),
                arrowstyle="-|>",
                mutation_scale=14,
                linewidth=1.1,
                color=NEUTRAL["dark"],
            )
        )

    sources = [
        (0.7, 5.2, "Fitbit\n수면·심박·HRV·활동량\n약 7,128만 문서", COLORS["blue"]["xlight"], COLORS["blue"]["dark"]),
        (0.7, 3.7, "SEMA\n기분·맥락 응답\n15,380건", COLORS["gold"]["xlight"], COLORS["gold"]["dark"]),
        (0.7, 2.2, "Survey\n참가자 설문\n935건", COLORS["olive"]["xlight"], COLORS["olive"]["dark"]),
        (0.7, 0.7, "Samsung Health\nsleep stage·심박·걸음\n프로토타입/진단용", COLORS["orange"]["xlight"], COLORS["orange"]["dark"]),
    ]
    for args in sources:
        box(args[0], args[1], 2.7, 0.9, args[2], args[3], args[4])

    box(4.4, 4.2, 2.4, 1.2, "원천 변수 추출\nraw/extracted_variables", NEUTRAL["xlight"], NEUTRAL["dark"])
    box(4.4, 2.5, 2.4, 1.2, "일 단위 집계\nparticipant + date", NEUTRAL["xlight"], NEUTRAL["dark"])
    box(7.6, 3.4, 2.5, 1.2, "모델링 데이터셋\n3,551 rows / 130 cols", COLORS["pink"]["xlight"], COLORS["pink"]["dark"])
    box(7.6, 1.6, 2.5, 1.2, "Strict pre-sleep\nStage 1 feature\n70 raw -> 58 input", COLORS["blue"]["xlight"], COLORS["blue"]["dark"])
    box(10.5, 2.5, 1.2, 1.2, "MLP\n예측", COLORS["gold"]["xlight"], COLORS["gold"]["dark"])

    for y in [5.65, 4.15, 2.65]:
        arrow(3.4, y, 4.4, 4.8 if y > 3 else 3.1)
    arrow(3.4, 1.15, 7.6, 2.2)
    arrow(5.6, 4.2, 5.6, 3.7)
    arrow(6.8, 3.1, 7.6, 3.95)
    arrow(8.85, 3.4, 8.85, 2.8)
    arrow(10.1, 2.2, 10.5, 3.1)

    fig.text(0.08, 0.96, "원천 데이터는 Fitbit 연구 데이터와 Samsung Health 프로토타입 데이터로 나뉜다", ha="left", va="top", fontsize=15, fontweight="bold", color=TOKENS["ink"])
    fig.text(0.08, 0.90, "Fitbit·SEMA·survey는 학습/평가 데이터셋 구성에 사용했고, Samsung Health는 cross-device diagnostic 및 live prototype에 사용했다.", ha="left", va="top", fontsize=10, color=TOKENS["muted"])
    save(fig, "ko_06_source_data_structure")


def figure_extracted_table_row_counts() -> None:
    df = pd.DataFrame(
        [
            ("fitbit_hrv_details", 220_512),
            ("fitbit_activity_minutes", 28_812),
            ("sema_responses", 15_380),
            ("fitbit_resting_heart_rate", 12_362),
            ("fitbit_respiratory_rate_summary", 3_000),
            ("fitbit_daily_hrv_summary", 2_475),
            ("fitbit_stress_score", 1_911),
            ("fitbit_daily_spo2", 1_274),
            ("surveys_responses", 935),
        ],
        columns=["table", "rows"],
    ).sort_values("rows", ascending=True)
    fig, ax = plt.subplots(figsize=(10, 6.4))
    bars = ax.barh(df["table"], df["rows"], color=COLORS["blue"]["base"], edgecolor=COLORS["blue"]["dark"], linewidth=1.0)
    ax.set_xlabel("추출 row 수")
    ax.xaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f"{x/1000:.0f}k" if x >= 1000 else f"{x:.0f}"))
    for bar in bars:
        ax.text(bar.get_width() * 1.01, bar.get_y() + bar.get_height() / 2, f"{int(bar.get_width()):,}", va="center", fontsize=9, color=TOKENS["ink"])
    ax.set_xlim(0, df["rows"].max() * 1.18)
    add_header(
        fig,
        ax,
        "HRV 상세값과 활동 minute 테이블이 가장 큰 추출 테이블이었다",
        "MongoDB에서 모델링 후보 변수로 추출한 9개 raw table 기준. 대용량 steps/calories/temperature는 MongoDB에서 날짜 단위로 직접 집계했다.",
    )
    save(fig, "ko_07_extracted_table_row_counts")


def figure_target_distribution() -> None:
    df = pd.read_csv(ROOT / "data/processed/modeling_dataset_daily.csv")
    counts = df["good_sleep_label"].value_counts().sort_index()
    plot = pd.DataFrame(
        {
            "label": ["0: not good", "1: good"],
            "rows": [counts.get(0, 0), counts.get(1, 0)],
        }
    )
    plot["rate"] = plot["rows"] / plot["rows"].sum()
    fig, ax = plt.subplots(figsize=(7.5, 5.8))
    colors = [NEUTRAL["light"], COLORS["blue"]["base"]]
    edges = [NEUTRAL["dark"], COLORS["blue"]["dark"]]
    bars = ax.bar(plot["label"], plot["rows"], color=colors, edgecolor=edges, linewidth=1.0)
    ax.set_ylabel("episode 수")
    ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f"{x:,.0f}"))
    for bar, rate in zip(bars, plot["rate"]):
        ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 55, f"{int(bar.get_height()):,}\n{rate:.1%}", ha="center", va="bottom", fontsize=10, color=TOKENS["ink"])
    ax.set_ylim(0, plot["rows"].max() * 1.18)
    add_header(
        fig,
        ax,
        "good_sleep_label=1은 전체의 39.4%였다",
        "Merged daily modeling dataset 3,551 rows, 69 participants, 2021-05-24~2022-01-22.",
    )
    save(fig, "ko_08_target_distribution")


def missing_family_df() -> pd.DataFrame:
    return pd.DataFrame(
        [
            ("SpO2", 65.36),
            ("Stress", 47.48),
            ("Sleep stage", 43.63),
            ("Respiratory", 37.65),
            ("SEMA", 32.55),
            ("HRV", 30.11),
            ("Temperature", 7.49),
            ("Survey", 2.25),
            ("Activity", 0.11),
            ("Resting HR", 0.00),
        ],
        columns=["family", "missing_rate"],
    )


def figure_missing_rate_by_family() -> None:
    df = missing_family_df().sort_values("missing_rate", ascending=True)
    fig, ax = plt.subplots(figsize=(9, 6.2))
    bars = ax.barh(df["family"], df["missing_rate"], color=COLORS["orange"]["base"], edgecolor=COLORS["orange"]["dark"], linewidth=1.0)
    ax.set_xlabel("평균 결측률")
    ax.xaxis.set_major_formatter(mticker.PercentFormatter(100))
    ax.set_xlim(0, 75)
    for bar in bars:
        ax.text(bar.get_width() + 1.0, bar.get_y() + bar.get_height() / 2, f"{bar.get_width():.1f}%", va="center", fontsize=9, color=TOKENS["ink"])
    add_header(
        fig,
        ax,
        "SpO2·Stress·Sleep stage 계열은 결측률이 높았다",
        "Final dataset EDA의 feature family별 평균 결측률. Activity와 Resting HR은 거의 완전하게 관측됐다.",
    )
    save(fig, "ko_08_missing_rate_by_feature_family")


def figure_top_missing_columns() -> None:
    df = pd.read_csv(ROOT / "data/processed/modeling_dataset_daily.csv")
    exclude = {"participant_object_id", "calendar_date", "good_sleep_label"}
    rates = df.drop(columns=[c for c in exclude if c in df.columns]).isna().mean().sort_values(ascending=False).head(15)
    plot = rates.reset_index()
    plot.columns = ["column", "missing_rate"]
    plot = plot.sort_values("missing_rate", ascending=True)
    fig, ax = plt.subplots(figsize=(10, 6.8))
    bars = ax.barh(plot["column"], plot["missing_rate"] * 100, color=COLORS["pink"]["base"], edgecolor=COLORS["pink"]["dark"], linewidth=1.0)
    ax.set_xlabel("결측률")
    ax.xaxis.set_major_formatter(mticker.PercentFormatter(100))
    ax.set_xlim(0, 100)
    for bar in bars:
        ax.text(bar.get_width() + 1.0, bar.get_y() + bar.get_height() / 2, f"{bar.get_width():.1f}%", va="center", fontsize=8.5, color=TOKENS["ink"])
    add_header(
        fig,
        ax,
        "상위 결측 컬럼은 classic sleep stage와 일부 호흡·SpO2 변수에 집중됐다",
        "Merged daily modeling dataset 기준 상위 15개 결측률. 일부 수면 결과성 컬럼은 최종 pre-sleep feature에서 제외됐다.",
    )
    save(fig, "ko_09_top_missing_columns")


def figure_missing_handling_columns() -> None:
    df = pd.DataFrame(
        [
            ("원본 merged dataset", 130, 0),
            ("결측 처리 후", 200, 97),
            ("인코딩 후", 200, 97),
            ("스케일링 후", 190, 97),
        ],
        columns=["stage", "columns", "indicators"],
    )
    fig, ax = plt.subplots(figsize=(9, 5.8))
    bars = ax.bar(df["stage"], df["columns"], color=[NEUTRAL["light"], COLORS["blue"]["base"], COLORS["blue"]["light"], COLORS["olive"]["base"]], edgecolor=TOKENS["ink"], linewidth=1.0)
    ax.set_ylabel("column 수")
    ax.set_ylim(0, 235)
    for bar, indicators in zip(bars, df["indicators"]):
        label = f"{int(bar.get_height())} cols"
        if indicators:
            label += f"\nmissing indicator {indicators}"
        ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 5, label, ha="center", va="bottom", fontsize=9, color=TOKENS["ink"])
    ax.tick_params(axis="x", labelrotation=12)
    add_header(
        fig,
        ax,
        "결측 처리 후 missing indicator가 추가되어 column 수가 130개에서 200개로 늘었다",
        "결측률 70% 초과 feature는 제거하고, retained missing feature에는 indicator를 추가했다. Scaling output은 zero-variance feature 10개를 제거했다.",
    )
    save(fig, "ko_10_missing_handling_column_flow")


def figure_split_target_rate() -> None:
    train = pd.read_csv(ROOT / "data/processed/splits/train_participant_split.csv")
    test = pd.read_csv(ROOT / "data/processed/splits/test_participant_split.csv")
    all_df = pd.concat([train, test], ignore_index=True)
    rows = []
    for name, part in [("Train", train), ("Test", test), ("All", all_df)]:
        rows.append(
            {
                "split": name,
                "rows": len(part),
                "participants": part["participant_object_id"].nunique(),
                "positive_rate": part["good_sleep_label"].mean(),
            }
        )
    plot = pd.DataFrame(rows)
    fig, ax = plt.subplots(figsize=(8.5, 5.8))
    bars = ax.bar(plot["split"], plot["positive_rate"] * 100, color=[COLORS["blue"]["base"], COLORS["orange"]["base"], NEUTRAL["light"]], edgecolor=TOKENS["ink"], linewidth=1.0)
    ax.set_ylim(0, 50)
    ax.set_ylabel("good_sleep_label=1 비율")
    ax.yaxis.set_major_formatter(mticker.PercentFormatter(100))
    for bar, row in zip(bars, plot.to_dict("records")):
        ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 1.2, f"{row['positive_rate']:.1%}\n{row['rows']:,} rows / {row['participants']}명", ha="center", va="bottom", fontsize=9, color=TOKENS["ink"])
    add_header(
        fig,
        ax,
        "participant-aware split 이후 train/test의 target rate는 비슷한 범위로 유지됐다",
        "Train 55명, test 14명. 참가자 overlap 없이 분리해 같은 사용자의 패턴 누수를 방지했다.",
    )
    save(fig, "ko_11_split_target_rate")


def figure_strict_presleep_timeline() -> None:
    fig, ax = plt.subplots(figsize=(12, 5.8))
    ax.set_xlim(0, 12.6)
    ax.set_ylim(0, 5)
    ax.axis("off")

    y = 2.55
    for x in [5.2, 7.7, 10.1]:
        ax.plot([x, x], [y - 0.55, y + 0.55], color=TOKENS["surface"], linewidth=3.0, zorder=2)

    spans = [
        (0.8, 5.2, COLORS["blue"]["xlight"], "사용 가능", "이전날 활동·안정시 심박\n과거 sleep history/baseline"),
        (5.2, 7.7, COLORS["olive"]["xlight"], "사용 가능", "취침 전 intraday\nsteps·calories·heart rate"),
        (7.7, 10.1, COLORS["orange"]["xlight"], "사용 금지", "수면 도중 정보\nsleep stage\ndeep/rem 등"),
        (10.1, 12.1, COLORS["pink"]["xlight"], "사용 금지", "수면 종료 후 outcome\nminutesAsleep\nefficiency 등"),
    ]
    for x1, x2, color, badge, text in spans:
        ax.add_patch(FancyBboxPatch((x1, y - 0.55), x2 - x1, 1.1, boxstyle="round,pad=0.02,rounding_size=0.06", facecolor=color, edgecolor="none"))
        ax.text((x1 + x2) / 2, y + 0.26, badge, ha="center", va="center", fontsize=10, fontweight="bold", color=TOKENS["ink"])
        ax.text((x1 + x2) / 2, y - 0.20, text, ha="center", va="center", fontsize=9.2, color=TOKENS["ink"], linespacing=1.16)

    ax.text(2.0, y - 0.8, "전날", ha="center", va="top", fontsize=10, color=TOKENS["muted"])
    ax.text(5.2, y - 0.8, "오늘 낮/저녁", ha="center", va="top", fontsize=10, color=TOKENS["muted"])
    ax.text(7.7, y - 0.8, "sleep_start_datetime\nprediction cutoff", ha="center", va="top", fontsize=10, color=COLORS["orange"]["dark"], fontweight="bold")
    ax.text(10.1, y - 0.8, "sleep_end", ha="center", va="top", fontsize=10, color=TOKENS["muted"])

    ax.annotate(
        "모델 입력은 이 선의 왼쪽 데이터만 사용",
        xy=(7.7, y + 0.65),
        xytext=(6.1, 4.15),
        arrowprops={"arrowstyle": "->", "color": COLORS["orange"]["dark"], "linewidth": 1.4},
        fontsize=11,
        color=COLORS["orange"]["dark"],
        ha="center",
    )
    fig.text(0.08, 0.96, "최종 문제는 수면 시작 전 정보만 사용하는 strict pre-sleep forecasting이다", ha="left", va="top", fontsize=15, fontweight="bold", color=TOKENS["ink"])
    fig.text(0.08, 0.90, "Prediction cutoff는 sleep_start_datetime이다. 수면 도중/종료 후에야 알 수 있는 sleep outcome feature는 leakage 방지를 위해 제외했다.", ha="left", va="top", fontsize=10, color=TOKENS["muted"])
    save(fig, "ko_12_strict_presleep_timeline")


def figure_inference_pipeline() -> None:
    fig, ax = plt.subplots(figsize=(12, 6.2))
    ax.set_xlim(0, 12)
    ax.set_ylim(0, 6)
    ax.axis("off")

    boxes = [
        (0.5, 3.6, 2.0, 1.1, "예측 대상 episode\nparticipant_id\nsleep_start", COLORS["blue"]["xlight"], COLORS["blue"]["dark"]),
        (0.5, 1.8, 2.0, 1.1, "웨어러블 원천 데이터\nsteps·calories·HR\nprevious-day activity", COLORS["olive"]["xlight"], COLORS["olive"]["dark"]),
        (3.2, 2.7, 2.1, 1.2, "Stage 1 feature builder\nraw feature 70개", NEUTRAL["xlight"], NEUTRAL["dark"]),
        (6.0, 2.7, 2.0, 1.2, "Train median imputer\n+ StandardScaler", COLORS["gold"]["xlight"], COLORS["gold"]["dark"]),
        (8.5, 2.7, 1.9, 1.2, "Zero-variance 제거\n최종 input 58개", COLORS["pink"]["xlight"], COLORS["pink"]["dark"]),
        (10.8, 2.7, 1.0, 1.2, "MLP\nsigmoid", COLORS["blue"]["xlight"], COLORS["blue"]["dark"]),
        (8.7, 0.75, 2.6, 0.95, "good_sleep_probability\nthreshold 0.54\n→ good_sleep_pred", COLORS["orange"]["xlight"], COLORS["orange"]["dark"]),
    ]

    def box(x, y, w, h, text, color, edge):
        ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.03,rounding_size=0.08", facecolor=color, edgecolor=edge, linewidth=1.3))
        ax.text(x + w / 2, y + h / 2, text, ha="center", va="center", fontsize=10.5, color=TOKENS["ink"], linespacing=1.18)

    def arrow(x1, y1, x2, y2):
        ax.add_patch(FancyArrowPatch((x1, y1), (x2, y2), arrowstyle="-|>", mutation_scale=14, linewidth=1.2, color=NEUTRAL["dark"]))

    for args in boxes:
        box(*args)
    arrow(2.5, 4.15, 3.2, 3.35)
    arrow(2.5, 2.35, 3.2, 3.15)
    arrow(5.3, 3.3, 6.0, 3.3)
    arrow(8.0, 3.3, 8.5, 3.3)
    arrow(10.4, 3.3, 10.8, 3.3)
    arrow(11.3, 2.7, 10.0, 1.7)

    fig.text(0.08, 0.96, "Inference pipeline은 70개 raw feature를 58개 MLP 입력으로 변환한다", ha="left", va="top", fontsize=15, fontweight="bold", color=TOKENS["ink"])
    fig.text(0.08, 0.90, "학습 시 저장한 median imputer와 StandardScaler를 재사용하고, 공식 threshold 0.54로 good_sleep_pred를 산출한다.", ha="left", va="top", fontsize=10, color=TOKENS["muted"])
    save(fig, "ko_13_inference_pipeline")


def figure_model_candidate_table() -> None:
    data = [
        ("전통 ML 기준선", "Logistic Regression", "wearable-only baseline", "기준 성능/해석용", "최종 딥러닝 아님"),
        ("전통 ML 기준선", "Random Forest", "baseline/reference", "비선형 기준선", "최종 딥러닝 아님"),
        ("딥러닝 후보", "Stage 1 MLP", "strict pre-sleep 58 features", "최종 선정", "최종 모델"),
        ("딥러닝 후보", "Stage 2 MLP", "rolling/history 380 features", "성능 개선 실패", "overfitting 가능"),
        ("딥러닝 후보", "Stage 2B MLP", "compact rolling 148 features", "recall↑, BA 개선 실패", "후보 탈락"),
        ("딥러닝 follow-up", "GRU / LSTM / BiLSTM", "episode sequence window 3/5/7", "recall 우선 비교", "대체 모델 아님"),
        ("딥러닝 follow-up", "1D CNN", "sequence tensor", "recall 우선 비교", "대체 모델 아님"),
    ]
    columns = ["구분", "모델", "입력 구조", "역할", "최종 해석"]
    df = pd.DataFrame(data, columns=columns)

    fig, ax = plt.subplots(figsize=(13, 6.5))
    ax.axis("off")
    fig.text(0.06, 0.96, "모델 후보는 baseline과 딥러닝 후보를 명확히 분리해 비교했다", ha="left", va="top", fontsize=15, fontweight="bold", color=TOKENS["ink"])
    fig.text(0.06, 0.90, "Logistic Regression과 Random Forest는 전통 ML baseline이며, 최종 선정 모델은 strict pre-sleep Stage 1 PyTorch MLP이다.", ha="left", va="top", fontsize=10, color=TOKENS["muted"])

    col_widths = [0.17, 0.20, 0.28, 0.18, 0.17]
    table = ax.table(
        cellText=df.values,
        colLabels=columns,
        cellLoc="center",
        colLoc="center",
        colWidths=col_widths,
        bbox=[0.03, 0.03, 0.94, 0.76],
    )
    table.auto_set_font_size(False)
    table.set_fontsize(10)
    table.scale(1, 1.55)
    for (r, c), cell in table.get_celld().items():
        cell.set_edgecolor(TOKENS["axis"])
        cell.set_linewidth(0.8)
        if r == 0:
            cell.set_facecolor(COLORS["blue"]["xlight"])
            cell.set_text_props(weight="bold", color=TOKENS["ink"])
        elif "최종 모델" in cell.get_text().get_text():
            cell.set_facecolor(COLORS["olive"]["xlight"])
        elif r % 2 == 0:
            cell.set_facecolor("#FAFAFC")
        else:
            cell.set_facecolor(TOKENS["panel"])
    save(fig, "ko_14_model_candidate_table")


def figure_mlp_architecture() -> None:
    fig, ax = plt.subplots(figsize=(12, 5.8))
    ax.set_xlim(0, 12)
    ax.set_ylim(0, 6)
    ax.axis("off")

    layers = [
        (1.0, "Input\n58 features", 58, COLORS["blue"]),
        (3.3, "Hidden 1\n24 units", 24, COLORS["gold"]),
        (5.6, "Dropout\n0.40", 12, COLORS["orange"]),
        (7.9, "Hidden 2\n12 units", 12, COLORS["gold"]),
        (10.2, "Output\nsigmoid", 1, COLORS["olive"]),
    ]
    for x, label, units, family in layers:
        if units == 1:
            ys = [3.0]
        else:
            n = min(6, max(3, units // 4 if units < 30 else 6))
            ys = np.linspace(1.4, 4.6, n)
        for yy in ys:
            circle = plt.Circle((x, yy), 0.18, facecolor=family["base"], edgecolor=family["dark"], linewidth=1.0)
            ax.add_patch(circle)
        ax.text(x, 0.65, label, ha="center", va="center", fontsize=10.5, color=TOKENS["ink"], linespacing=1.2)
        if units not in [1, 12, 24, 58]:
            ax.text(x, 5.1, f"{units}", ha="center")

    for i in range(len(layers) - 1):
        x1 = layers[i][0] + 0.22
        x2 = layers[i + 1][0] - 0.22
        ax.add_patch(FancyArrowPatch((x1, 3.0), (x2, 3.0), arrowstyle="-|>", mutation_scale=14, linewidth=1.2, color=NEUTRAL["dark"]))

    ax.text(6.0, 5.15, "Regularization: dropout 0.40, weight decay 0.001, learning rate 0.0008", ha="center", fontsize=10, color=TOKENS["muted"])
    ax.text(10.2, 4.65, "threshold\n0.54", ha="center", fontsize=10, color=COLORS["orange"]["dark"], fontweight="bold")
    fig.text(0.08, 0.96, "최종 모델은 작은 MLP 구조로 과적합을 줄이는 방향을 선택했다", ha="left", va="top", fontsize=15, fontweight="bold", color=TOKENS["ink"])
    fig.text(0.08, 0.90, "Representative checkpoint: presleep_stage1_hp_tiny_dropout40_wd1e3_seed2027. Hidden dimensions는 (24, 12)이다.", ha="left", va="top", fontsize=10, color=TOKENS["muted"])
    save(fig, "ko_15_mlp_architecture")


def figure_sequence_ba_recall_tradeoff() -> None:
    seq_path = ROOT / "data/processed/pre_sleep_forecasting/design_c_stage1/experiments/sequence_model_outputs/pre_sleep_sequence_model_metrics.csv"
    seq = pd.read_csv(seq_path)
    plot = seq[seq["split"] == "test"].copy()
    plot["label"] = plot["model_family"].str.upper() + " w" + plot["window"].astype(str)
    final = pd.DataFrame(
        [
            {
                "label": "Final MLP",
                "balanced_accuracy": 0.6492,
                "recall": 0.4245,
                "model_family": "final_mlp",
                "window": 0,
            }
        ]
    )
    plot = pd.concat([plot[["label", "balanced_accuracy", "recall", "model_family", "window"]], final], ignore_index=True)
    fig, ax = plt.subplots(figsize=(9.5, 6.4))
    colors = []
    for _, row in plot.iterrows():
        if row["label"] == "Final MLP":
            colors.append(COLORS["blue"]["mid"])
        elif "GRU" in row["label"]:
            colors.append(COLORS["olive"]["base"])
        elif "LSTM" in row["label"]:
            colors.append(COLORS["gold"]["base"])
        elif "BILSTM" in row["label"]:
            colors.append(COLORS["orange"]["base"])
        else:
            colors.append(COLORS["pink"]["base"])
    ax.scatter(plot["recall"], plot["balanced_accuracy"], s=180, c=colors, edgecolors=TOKENS["ink"], linewidths=1.0, zorder=3)
    for _, row in plot.iterrows():
        dx = 0.012 if row["label"] != "Final MLP" else -0.105
        ax.text(row["recall"] + dx, row["balanced_accuracy"] + 0.002, row["label"], fontsize=9, color=TOKENS["ink"], va="center")
    ax.set_xlabel("Recall")
    ax.set_ylabel("Balanced accuracy")
    ax.set_xlim(0.35, 0.86)
    ax.set_ylim(0.55, 0.67)
    ax.axhline(0.6492, color=COLORS["blue"]["mid"], linestyle=":", linewidth=1.2)
    ax.text(0.36, 0.651, "Final MLP BA", fontsize=9, color=COLORS["blue"]["dark"])
    add_header(
        fig,
        ax,
        "Sequence 후보는 recall을 높였지만 balanced accuracy는 최종 MLP를 넘지 못했다",
        "Strict pre-sleep sequence follow-up test 결과. GRU/CNN 일부 후보는 recall이 높지만 false positive 증가와 함께 BA 개선은 제한적이었다.",
    )
    save(fig, "ko_19_sequence_ba_recall_tradeoff")


def figure_top_target_correlations() -> None:
    df = pd.read_csv(ROOT / "data/processed/modeling_dataset_daily.csv")
    numeric = df.select_dtypes(include=[np.number]).copy()
    corrs = numeric.drop(columns=["good_sleep_label"], errors="ignore").corrwith(numeric["good_sleep_label"]).dropna()
    top = corrs.reindex(corrs.abs().sort_values(ascending=False).head(15).index).sort_values()
    plot = top.reset_index()
    plot.columns = ["feature", "corr"]
    fig, ax = plt.subplots(figsize=(10, 6.8))
    colors = np.where(plot["corr"] >= 0, COLORS["olive"]["base"], COLORS["orange"]["base"])
    edges = np.where(plot["corr"] >= 0, COLORS["olive"]["dark"], COLORS["orange"]["dark"])
    bars = ax.barh(plot["feature"], plot["corr"], color=colors, edgecolor=edges, linewidth=1.0)
    ax.axvline(0, color=TOKENS["ink"], linewidth=1.0)
    ax.set_xlabel("good_sleep_label과의 Pearson correlation")
    ax.set_xlim(-0.35, 0.90)
    for bar, val in zip(bars, plot["corr"]):
        x = val + (0.015 if val >= 0 else -0.015)
        ha = "left" if val >= 0 else "right"
        ax.text(x, bar.get_y() + bar.get_height() / 2, f"{val:+.3f}", va="center", ha=ha, fontsize=8.5, color=TOKENS["ink"])
    add_header(
        fig,
        ax,
        "EDA 상관분석에서는 수면 단계·활동량·HRV 계열이 target과 크게 연결됐다",
        "Merged daily dataset 기준 상위 15개 절대상관. 일부 sleep outcome성 변수는 최종 pre-sleep 모델 입력에서 제외됐다.",
    )
    save(fig, "ko_20_top_target_correlations")


def figure_key_features_by_target() -> None:
    df = pd.read_csv(ROOT / "data/processed/modeling_dataset_daily.csv")
    features = [
        ("minutesAsleep", "수면 시간\nminutesAsleep"),
        ("efficiency", "수면 효율\nefficiency"),
        ("stress_score_mean", "스트레스 점수"),
        ("hrv_summary_rmssd_mean", "HRV RMSSD"),
        ("steps_sum", "걸음 수"),
        ("calories_sum", "칼로리"),
        ("wrist_temperature_mean", "손목 온도"),
        ("sema_response_count", "SEMA 응답 수"),
    ]
    fig, axes = plt.subplots(2, 4, figsize=(14, 7.2))
    axes = axes.ravel()
    for ax, (feature, label) in zip(axes, features):
        plot = df[["good_sleep_label", feature]].dropna()
        sns.boxplot(
            data=plot,
            x="good_sleep_label",
            y=feature,
            ax=ax,
            color=COLORS["orange"]["base"],
            fliersize=2.2,
            linewidth=1.0,
        )
        ax.set_title(label, fontsize=11, fontweight="bold")
        ax.set_xlabel("0: not good / 1: good", fontsize=9)
        ax.set_ylabel("")
        ax.set_xticklabels(["0", "1"])
        ax.grid(True, axis="y")
        sns.despine(ax=ax)
    fig.subplots_adjust(top=0.78, wspace=0.28, hspace=0.52)
    fig.text(0.06, 0.97, "주요 feature 분포는 good sleep 여부에 따라 다른 패턴을 보였다", ha="left", va="top", fontsize=15, fontweight="bold", color=TOKENS["ink"])
    fig.text(0.06, 0.91, "Final dataset EDA의 key features by target 한글화. 수면 결과성 변수는 해석용 EDA이며 최종 pre-sleep 입력에서는 제외된다.", ha="left", va="top", fontsize=10, color=TOKENS["muted"])
    save(fig, "ko_20_key_features_by_target")


def figure_samsung_adapter_pipeline() -> None:
    fig, ax = plt.subplots(figsize=(12.5, 6.2))
    ax.set_xlim(0, 12.5)
    ax.set_ylim(0, 6)
    ax.axis("off")

    def box(x, y, w, h, text, color, edge):
        ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.03,rounding_size=0.08", facecolor=color, edgecolor=edge, linewidth=1.3))
        ax.text(x + w / 2, y + h / 2, text, ha="center", va="center", fontsize=10.3, color=TOKENS["ink"], linespacing=1.18)

    def arrow(x1, y1, x2, y2):
        ax.add_patch(FancyArrowPatch((x1, y1), (x2, y2), arrowstyle="-|>", mutation_scale=14, linewidth=1.2, color=NEUTRAL["dark"]))

    items = [
        (0.5, 3.0, 1.8, 1.0, "Samsung Health\nexport folder", COLORS["orange"]["xlight"], COLORS["orange"]["dark"]),
        (2.8, 3.0, 1.9, 1.0, "sleep_stage 기반\nsleep episode 생성", COLORS["blue"]["xlight"], COLORS["blue"]["dark"]),
        (5.2, 3.0, 1.9, 1.0, "UTC+0900\n시간 보정", COLORS["gold"]["xlight"], COLORS["gold"]["dark"]),
        (7.6, 3.0, 2.0, 1.0, "Fitbit-compatible\nStage 1 raw 70 features", COLORS["pink"]["xlight"], COLORS["pink"]["dark"]),
        (10.1, 3.0, 1.8, 1.0, "기존 imputer\nscaler + MLP", COLORS["olive"]["xlight"], COLORS["olive"]["dark"]),
        (10.1, 1.2, 1.8, 0.9, "Samsung prediction\n+ coverage 진단", NEUTRAL["xlight"], NEUTRAL["dark"]),
    ]
    for item in items:
        box(*item)
    for x1, x2 in [(2.3, 2.8), (4.7, 5.2), (7.1, 7.6), (9.6, 10.1)]:
        arrow(x1, 3.5, x2, 3.5)
    arrow(11.0, 3.0, 11.0, 2.1)
    ax.text(7.1, 4.55, "주의: raw data 변환이 아니라 schema-compatible adapter", ha="center", fontsize=10, color=COLORS["orange"]["dark"], fontweight="bold")
    ax.text(7.1, 0.55, "공식 외부 검증 아님: single-user/domain shift, proxy label 제한, pre-sleep step/calorie coverage 희소", ha="center", fontsize=10, color=TOKENS["muted"])
    fig.text(0.06, 0.96, "Samsung adapter는 Fitbit 학습 모델을 Samsung export에 진단적으로 적용하기 위한 변환층이다", ha="left", va="top", fontsize=15, fontweight="bold", color=TOKENS["ink"])
    fig.text(0.06, 0.90, "Feature contract는 맞추지만 Samsung raw data를 Fitbit raw data로 바꾸는 것이 아니며, formal external validation도 아니다.", ha="left", va="top", fontsize=10, color=TOKENS["muted"])
    save(fig, "ko_21_samsung_adapter_pipeline")


def figure_service_flow() -> None:
    fig, ax = plt.subplots(figsize=(12.5, 6.4))
    ax.set_xlim(0, 12.5)
    ax.set_ylim(0, 6.5)
    ax.axis("off")

    def box(x, y, w, h, text, color, edge):
        ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.03,rounding_size=0.08", facecolor=color, edgecolor=edge, linewidth=1.3))
        ax.text(x + w / 2, y + h / 2, text, ha="center", va="center", fontsize=10.5, color=TOKENS["ink"], linespacing=1.2)

    def arrow(x1, y1, x2, y2):
        ax.add_patch(FancyArrowPatch((x1, y1), (x2, y2), arrowstyle="-|>", mutation_scale=14, linewidth=1.2, color=NEUTRAL["dark"]))

    top = [
        (0.5, 3.9, 1.8, 1.0, "Wearable sync\nFitbit / Samsung", COLORS["blue"]["xlight"], COLORS["blue"]["dark"]),
        (2.8, 3.9, 1.8, 1.0, "오늘 feature update\nhistory + baseline", COLORS["olive"]["xlight"], COLORS["olive"]["dark"]),
        (5.1, 3.9, 1.8, 1.0, "취침 전 예측\nMLP score", COLORS["gold"]["xlight"], COLORS["gold"]["dark"]),
        (7.4, 3.9, 1.8, 1.0, "대시보드 표시\nscore / delta / trend", COLORS["pink"]["xlight"], COLORS["pink"]["dark"]),
        (9.7, 3.9, 2.1, 1.0, "개인 피드백\n수면 관리 참고", COLORS["orange"]["xlight"], COLORS["orange"]["dark"]),
    ]
    for item in top:
        box(*item)
    for x1, x2 in [(2.3, 2.8), (4.6, 5.1), (6.9, 7.4), (9.2, 9.7)]:
        arrow(x1, 4.4, x2, 4.4)

    use_cases = [
        (1.0, 1.25, "개인 수면 관리\n오늘 밤 score 확인"),
        (3.5, 1.25, "번아웃 조기 경고\n낮은 score 반복 감지"),
        (6.0, 1.25, "운동 후 회복 모니터링\n심박·활동 부담 확인"),
        (8.7, 1.25, "웨어러블 앱 연동\nadapter + calibration"),
    ]
    for x, y, text in use_cases:
        box(x, y, 2.1, 1.0, text, NEUTRAL["xlight"], NEUTRAL["dark"])
        arrow(8.45 if x < 8 else 10.75, 3.9, x + 1.05, y + 1.0)

    ax.text(6.25, 0.45, "현재 단계: clinical decision이 아니라 research-grade personal feedback prototype", ha="center", fontsize=10.5, color=COLORS["orange"]["dark"], fontweight="bold")
    fig.text(0.06, 0.96, "서비스 흐름은 취침 전 예측을 개인 피드백으로 돌려주는 구조다", ha="left", va="top", fontsize=15, fontweight="bold", color=TOKENS["ink"])
    fig.text(0.06, 0.90, "동기화된 웨어러블 데이터를 feature update에 반영하고, 기존 MLP로 오늘 밤 good_sleep score를 산출해 대시보드에서 설명한다.", ha="left", va="top", fontsize=10, color=TOKENS["muted"])
    save(fig, "ko_26_service_flow")


def figure_model_comparison() -> None:
    df = pd.DataFrame(
        [
            ("Stage 1\nsingle seed", 0.6338, 0.6875, 0.6009),
            ("Stage 1\nseed mean", 0.6107, 0.6681, 0.6016),
            ("Stage 2\nfull rolling", 0.6025, 0.6628, 0.5855),
            ("Stage 2B\ncompact rolling", 0.5923, 0.6852, 0.5788),
            ("Best Stage 1\nHP config mean", 0.6586, 0.6942, 0.6185),
        ],
        columns=["후보", "Balanced Accuracy", "ROC AUC", "Average Precision"],
    )
    long = df.melt(id_vars="후보", var_name="지표", value_name="값")
    fig, ax = plt.subplots(figsize=(11, 6.2))
    palette = {
        "Balanced Accuracy": COLORS["blue"]["base"],
        "ROC AUC": COLORS["gold"]["base"],
        "Average Precision": COLORS["olive"]["base"],
    }
    sns.barplot(data=long, x="후보", y="값", hue="지표", palette=palette, ax=ax, edgecolor=TOKENS["ink"], linewidth=0.8)
    ax.set_ylim(0.50, 0.73)
    ax.yaxis.set_major_formatter(mticker.FormatStrFormatter("%.2f"))
    ax.set_xlabel("")
    ax.set_ylabel("Held-out test score")
    ax.legend(loc="lower left", bbox_to_anchor=(0, 1.02), frameon=False, ncol=3, borderaxespad=0)
    for container in ax.containers:
        ax.bar_label(container, fmt="%.3f", fontsize=8, padding=2)
    add_header(
        fig,
        ax,
        "Stage 1 HP MLP가 가장 안정적인 최종 후보였다",
        "Strict pre-sleep 조건의 test 지표 비교. Stage 2 rolling/history 확장은 balanced accuracy를 개선하지 못했다.",
    )
    save(fig, "ko_16_model_candidate_metrics")


def selected_predictions() -> pd.DataFrame:
    path = ROOT / "data/processed/pre_sleep_forecasting/design_c_stage1/experiments/stage1_hyperparameter_stability_outputs/stage1_hyperparameter_stability_predictions.csv"
    df = pd.read_csv(path)
    return df[
        (df["experiment_id"] == "presleep_stage1_hp_tiny_dropout40_wd1e3_seed2027")
        & (df["split"] == "test")
    ].copy()


def figure_final_confusion_matrix() -> None:
    pred = selected_predictions()
    cm = pd.crosstab(pred["y_true"], pred["y_pred"]).reindex(index=[0, 1], columns=[0, 1], fill_value=0)
    labels = np.array(
        [
            [f"TN\n{cm.loc[0, 0]:,}", f"FP\n{cm.loc[0, 1]:,}"],
            [f"FN\n{cm.loc[1, 0]:,}", f"TP\n{cm.loc[1, 1]:,}"],
        ]
    )
    fig, ax = plt.subplots(figsize=(7.2, 6.4))
    cmap = sns.blend_palette([TOKENS["panel"], COLORS["blue"]["xlight"], COLORS["blue"]["base"], COLORS["blue"]["mid"]], as_cmap=True)
    sns.heatmap(cm, annot=labels, fmt="", cmap=cmap, cbar=False, linewidths=1.2, linecolor=TOKENS["panel"], ax=ax)
    ax.set_xlabel("예측 label")
    ax.set_ylabel("실제 label")
    ax.set_xticklabels(["0: not good", "1: good"])
    ax.set_yticklabels(["0: not good", "1: good"], rotation=0)
    add_header(
        fig,
        ax,
        "최종 MLP는 good sleep 재현율보다 정밀도가 높은 운영점에 있다",
        f"Test split {len(pred):,}개 episode, official threshold 0.54. "
        f"TN={cm.loc[0, 0]:,}, FP={cm.loc[0, 1]:,}, FN={cm.loc[1, 0]:,}, TP={cm.loc[1, 1]:,}.",
    )
    save(fig, "ko_17_final_mlp_confusion_matrix")


def figure_final_roc_pr() -> None:
    pred = selected_predictions()
    y = pred["y_true"].to_numpy()
    score = pred["y_probability"].to_numpy()
    fpr, tpr, _ = roc_curve(y, score)
    precision, recall, _ = precision_recall_curve(y, score)
    roc_auc = auc(fpr, tpr)
    pr_auc = auc(recall, precision)
    fig, axes = plt.subplots(1, 2, figsize=(12, 5.5))
    axes[0].plot(fpr, tpr, color=COLORS["blue"]["mid"], linewidth=2.0)
    axes[0].plot([0, 1], [0, 1], color=NEUTRAL["mid"], linestyle=":", linewidth=1.2)
    axes[0].set_xlabel("False positive rate")
    axes[0].set_ylabel("True positive rate")
    axes[0].set_title(f"ROC curve\nAUC={roc_auc:.3f}", fontsize=12, fontweight="bold")
    axes[1].plot(recall, precision, color=COLORS["orange"]["mid"], linewidth=2.0)
    axes[1].axhline(y.mean(), color=NEUTRAL["mid"], linestyle=":", linewidth=1.2)
    axes[1].set_xlabel("Recall")
    axes[1].set_ylabel("Precision")
    axes[1].set_title(f"Precision-Recall curve\nAP=0.619", fontsize=12, fontweight="bold")
    for ax in axes:
        ax.set_xlim(0, 1)
        ax.set_ylim(0, 1)
        ax.grid(True, axis="both")
        sns.despine(ax=ax)
    fig.subplots_adjust(top=0.78, wspace=0.28)
    left = axes[0].get_position().x0
    fig.text(left, 0.97, "최종 MLP는 strict pre-sleep 조건에서 중간 수준의 ranking 성능을 보였다", ha="left", va="top", fontsize=15, fontweight="bold", color=TOKENS["ink"])
    fig.text(left, 0.91, "Held-out participant test split. ROC AUC=0.694, Average Precision=0.619.", ha="left", va="top", fontsize=10, color=TOKENS["muted"])
    save(fig, "ko_17_final_mlp_roc_pr")


def figure_bootstrap_ci() -> None:
    path = ROOT / "data/processed/pre_sleep_forecasting/design_c_stage1/experiments/stage1_final_uncertainty_calibration_outputs/selected_model_participant_bootstrap_summary.csv"
    df = pd.read_csv(path)
    metrics = ["balanced_accuracy", "roc_auc", "average_precision", "f1", "precision", "recall"]
    label_map = {
        "balanced_accuracy": "Balanced accuracy",
        "roc_auc": "ROC AUC",
        "average_precision": "Average precision",
        "f1": "F1",
        "precision": "Precision",
        "recall": "Recall",
    }
    plot = df[df["metric"].isin(metrics)].copy()
    plot["label"] = plot["metric"].map(label_map)
    plot = plot.set_index("label").loc[list(label_map.values())].reset_index()
    fig, ax = plt.subplots(figsize=(9, 6.2))
    y = np.arange(len(plot))
    ax.errorbar(
        plot["point_estimate"],
        y,
        xerr=[
            plot["point_estimate"] - plot["ci_lower_2_5"],
            plot["ci_upper_97_5"] - plot["point_estimate"],
        ],
        fmt="o",
        color=COLORS["gold"]["mid"],
        markerfacecolor=COLORS["gold"]["base"],
        markeredgecolor=COLORS["gold"]["dark"],
        capsize=4,
        linewidth=1.5,
    )
    ax.set_yticks(y, plot["label"])
    ax.invert_yaxis()
    ax.set_xlim(0.15, 0.90)
    ax.set_xlabel("점 추정치와 participant bootstrap 95% CI")
    for _, row in plot.iterrows():
        ax.text(row["ci_upper_97_5"] + 0.012, list(plot["label"]).index(row["label"]), f"{row['point_estimate']:.3f}", va="center", fontsize=9, color=TOKENS["ink"])
    add_header(
        fig,
        ax,
        "성능 신호는 있으나 test participant 수 때문에 불확실성이 남아 있다",
        "Bootstrap unit은 participant, test participant 14명, 5,000회 반복. Balanced accuracy 95% CI=[0.544, 0.726].",
    )
    save(fig, "ko_18_participant_bootstrap_ci")


def figure_samsung_feature_coverage() -> None:
    path = ROOT / "data/processed/samsung_health/pre_sleep_stage1/samsung_stage1_feature_summary.csv"
    df = pd.read_csv(path)
    wanted = [
        ("heart_rate_pre_sleep_mean", "취침 전 심박 평균"),
        ("heart_rate_pre_sleep_last_3h_mean", "최근 3시간 심박"),
        ("heart_rate_pre_sleep_last_1h_mean", "최근 1시간 심박"),
        ("previous_day_steps_sum", "전날 걸음 수"),
        ("previous_day_calories_sum", "전날 칼로리"),
        ("steps_pre_sleep_sum", "취침 전 걸음 수"),
        ("steps_pre_sleep_last_1h_sum", "최근 1시간 걸음"),
        ("calories_pre_sleep_sum", "취침 전 칼로리"),
        ("calories_pre_sleep_last_1h_sum", "최근 1시간 칼로리"),
    ]
    plot = df[df["feature"].isin([w[0] for w in wanted])].copy()
    label_map = dict(wanted)
    plot["label"] = plot["feature"].map(label_map)
    plot = plot.set_index("label").loc[[w[1] for w in wanted]].reset_index()
    plot["coverage_pct"] = plot["non_missing_ratio"] * 100
    fig, ax = plt.subplots(figsize=(10, 6.5))
    colors = [COLORS["olive"]["base"] if v >= 90 else COLORS["orange"]["base"] for v in plot["coverage_pct"]]
    edge = [COLORS["olive"]["dark"] if v >= 90 else COLORS["orange"]["dark"] for v in plot["coverage_pct"]]
    bars = ax.barh(plot["label"], plot["coverage_pct"], color=colors, edgecolor=edge, linewidth=1.0)
    ax.invert_yaxis()
    ax.set_xlim(0, 105)
    ax.xaxis.set_major_formatter(mticker.PercentFormatter(100))
    ax.set_xlabel("비결측 coverage")
    for bar, count, total in zip(bars, plot["non_missing_count"], plot["non_missing_count"] + plot["missing_count"]):
        ax.text(bar.get_width() + 1.0, bar.get_y() + bar.get_height() / 2, f"{count:,}/{total:,}", va="center", fontsize=9, color=TOKENS["ink"])
    add_header(
        fig,
        ax,
        "Samsung Health는 심박과 전날 활동은 충분하지만 취침 전 step/calorie가 희소하다",
        "Samsung sleep episode 1,493건 기준. Current-day interval activity coverage 부족이 주요 domain-shift 요인이다.",
    )
    save(fig, "ko_22_samsung_feature_coverage")


def figure_today_comparison() -> None:
    path = ROOT / "data/processed/samsung_health/pre_sleep_stage1/live_forecast/today_forecast_comparison.csv"
    row = pd.read_csv(path).iloc[0]
    plot = pd.DataFrame(
        {
            "scenario": ["Samsung-only", "보완 입력 반영"],
            "probability": [row["samsung_only_probability"], row["final_probability"]],
            "prediction": [row["samsung_only_pred"], row["final_pred"]],
        }
    )
    fig, ax = plt.subplots(figsize=(8, 5.8))
    colors = [NEUTRAL["light"], COLORS["blue"]["base"]]
    edges = [NEUTRAL["dark"], COLORS["blue"]["dark"]]
    bars = ax.bar(plot["scenario"], plot["probability"], color=colors, edgecolor=edges, linewidth=1.0)
    ax.axhline(0.54, color=COLORS["orange"]["dark"], linestyle=":", linewidth=1.5)
    ax.text(1.42, 0.54, "threshold 0.54", va="center", fontsize=9, color=COLORS["orange"]["dark"])
    ax.set_ylim(0, 0.75)
    ax.set_ylabel("good_sleep model score")
    for bar, pred in zip(bars, plot["prediction"]):
        ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 0.02, f"{bar.get_height():.3f}\n예측 {int(pred)}", ha="center", va="bottom", fontsize=10, color=TOKENS["ink"])
    add_header(
        fig,
        ax,
        "보완 입력 반영 후 오늘 밤 예측 label이 0에서 1로 바뀌었다",
        "Target sleep start 2026-06-30 23:30. Manual supplement는 재학습이 아니라 오늘 forecast feature row에만 반영됐다.",
    )
    save(fig, "ko_24_today_forecast_comparison")


def figure_sensitivity() -> None:
    path = ROOT / "data/processed/samsung_health/pre_sleep_stage1/live_forecast/today_numeric_sensitivity.csv"
    df = pd.read_csv(path)
    plot = df[df["scenario_id"] != "baseline"].copy()
    plot = plot.sort_values("probability_delta")
    fig, ax = plt.subplots(figsize=(10, 6.2))
    colors = np.where(plot["probability_delta"] >= 0, COLORS["olive"]["base"], COLORS["orange"]["base"])
    edge_colors = np.where(plot["probability_delta"] >= 0, COLORS["olive"]["dark"], COLORS["orange"]["dark"])
    bars = ax.barh(plot["description"], plot["probability_delta"], color=colors, edgecolor=edge_colors, linewidth=1.0)
    ax.axvline(0, color=TOKENS["ink"], linewidth=1.0)
    ax.set_xlabel("baseline 대비 probability delta")
    ax.xaxis.set_major_formatter(mticker.FormatStrFormatter("%+.3f"))
    for bar, delta, prob, changed in zip(bars, plot["probability_delta"], plot["good_sleep_probability"], plot["label_changed"]):
        x = delta + (0.003 if delta >= 0 else -0.003)
        ha = "left" if delta >= 0 else "right"
        suffix = " / label 변경" if changed else ""
        ax.text(x, bar.get_y() + bar.get_height() / 2, f"{delta:+.3f}{suffix}", ha=ha, va="center", fontsize=9, color=TOKENS["ink"])
    ax.set_xlim(min(plot["probability_delta"].min() - 0.025, -0.11), max(plot["probability_delta"].max() + 0.025, 0.035))
    add_header(
        fig,
        ax,
        "오늘 forecast는 취침 시각 +30분 시나리오에서 threshold 아래로 내려갔다",
        "Baseline probability=0.608. Sensitivity는 같은 raw feature row에서 일부 입력만 바꾼 진단 결과다.",
    )
    save(fig, "ko_25_numeric_sensitivity")


def main() -> None:
    set_theme()
    figure_source_data_diagram()
    figure_extracted_table_row_counts()
    figure_target_distribution()
    figure_missing_rate_by_family()
    figure_top_missing_columns()
    figure_missing_handling_columns()
    figure_split_target_rate()
    figure_strict_presleep_timeline()
    figure_inference_pipeline()
    figure_model_candidate_table()
    figure_mlp_architecture()
    figure_model_comparison()
    figure_final_confusion_matrix()
    figure_final_roc_pr()
    figure_bootstrap_ci()
    figure_sequence_ba_recall_tradeoff()
    figure_top_target_correlations()
    figure_key_features_by_target()
    figure_samsung_adapter_pipeline()
    figure_samsung_feature_coverage()
    figure_today_comparison()
    figure_sensitivity()
    figure_service_flow()


if __name__ == "__main__":
    main()
