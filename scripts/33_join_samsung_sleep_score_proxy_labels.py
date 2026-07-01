from __future__ import annotations

from pathlib import Path
import csv
import os

import numpy as np
import pandas as pd


PROJECT_ROOT = Path(os.environ.get("PROJECT_ROOT", Path(__file__).resolve().parents[1]))

SAMSUNG_DIR_CANDIDATES = [
    PROJECT_ROOT / "docs" / "samsung",
    PROJECT_ROOT / "docs" / "samsunghealth",
    PROJECT_ROOT / "docs",
    PROJECT_ROOT / "data" / "raw" / "samsung_health",
]

SLEEP_DATASET = "com.samsung.shealth.sleep"
STAGE1_DIR = PROJECT_ROOT / "data" / "processed" / "samsung_health" / "pre_sleep_stage1"
EPISODE_PATH = STAGE1_DIR / "samsung_sleep_episodes.csv"
PREDICTION_PATH = STAGE1_DIR / "samsung_pre_sleep_predictions.csv"

OUTPUT_EPISODE_PATH = STAGE1_DIR / "samsung_sleep_episodes_with_proxy_labels.csv"
OUTPUT_PREDICTION_PATH = STAGE1_DIR / "samsung_pre_sleep_predictions_with_proxy_labels.csv"
MATCH_REPORT_PATH = STAGE1_DIR / "samsung_sleep_score_proxy_label_match_report.csv"
EVALUATION_PATH = STAGE1_DIR / "samsung_pre_sleep_proxy_label_evaluation.csv"
REPORT_PATH = PROJECT_ROOT / "reports" / "samsung_sleep_score_proxy_label_join_summary.md"

GOOD_SLEEP_SCORE_THRESHOLD = 80
MAX_MATCH_TIME_DIFF_MINUTES = 30


def find_dataset_file(dataset_name: str) -> Path:
    for root in SAMSUNG_DIR_CANDIDATES:
        if not root.exists():
            continue
        matches = sorted(root.glob(f"{dataset_name}.*.csv"))
        if matches:
            return matches[0]
        recursive_matches = sorted(root.rglob(f"{dataset_name}.*.csv"))
        if recursive_matches:
            return recursive_matches[0]
    raise FileNotFoundError(f"Could not find Samsung Health CSV for dataset: {dataset_name}")


def read_samsung_csv_with_leading_extra(path: Path) -> pd.DataFrame:
    with open(path, "r", encoding="utf-8-sig", newline="") as f:
        reader = csv.reader(f)
        _metadata = next(reader)
        header = next(reader)
        rows = list(reader)

    fixed_rows = []
    for row in rows:
        if len(row) == len(header) + 1 and row[-1] == "":
            row = row[:-1]
        if len(row) < len(header):
            row = row + [""] * (len(header) - len(row))
        elif len(row) > len(header):
            row = row[: len(header)]
        fixed_rows.append(row)

    df = pd.DataFrame(fixed_rows, columns=header)
    return df.replace("", np.nan).infer_objects(copy=False)


def parse_datetime(series: pd.Series) -> pd.Series:
    return pd.to_datetime(series, errors="coerce")


def parse_utc_offset_minutes(value) -> float:
    if pd.isna(value):
        return np.nan
    text = str(value).strip()
    if not text.startswith("UTC") or len(text) < 8:
        return np.nan
    sign = 1 if text[3] == "+" else -1
    hours = pd.to_numeric(text[4:6], errors="coerce")
    minutes = pd.to_numeric(text[6:8], errors="coerce")
    if pd.isna(hours) or pd.isna(minutes):
        return np.nan
    return float(sign * (hours * 60 + minutes))


def apply_utc_offset(datetime_series: pd.Series, offset_series: pd.Series) -> pd.Series:
    offsets = offset_series.map(parse_utc_offset_minutes)
    return datetime_series + pd.to_timedelta(offsets.fillna(0), unit="m")


def first_existing_column(df: pd.DataFrame, candidates: list[str]) -> str:
    for candidate in candidates:
        if candidate in df.columns:
            return candidate
    raise ValueError(f"None of the candidate columns exist: {candidates}")


def prepare_sleep_score_table() -> tuple[pd.DataFrame, Path]:
    sleep_path = find_dataset_file(SLEEP_DATASET)
    sleep_df = read_samsung_csv_with_leading_extra(sleep_path)

    start_col = first_existing_column(
        sleep_df,
        [
            "com.samsung.health.sleep.end_time",
            "end_time",
        ],
    )
    end_col = first_existing_column(
        sleep_df,
        [
            "com.samsung.health.sleep.update_time",
            "update_time",
        ],
    )
    offset_col = first_existing_column(
        sleep_df,
        [
            "com.samsung.health.sleep.time_offset",
            "time_offset",
            "com.samsung.health.sleep.client_data_ver",
            "client_data_ver",
        ],
    )
    datauuid_col = first_existing_column(
        sleep_df,
        [
            "com.samsung.health.sleep.datauuid",
            "datauuid",
        ],
    )
    score_col = first_existing_column(sleep_df, ["sleep_score"])
    efficiency_col = "efficiency" if "efficiency" in sleep_df.columns else None
    duration_col = "sleep_duration" if "sleep_duration" in sleep_df.columns else None

    # Observed mapping for this export after dropping one trailing blank field:
    # - com.samsung.health.sleep.end_time contains sleep start time
    # - com.samsung.health.sleep.update_time contains sleep end time
    # - com.samsung.health.sleep.time_offset contains UTC offset
    # - com.samsung.health.sleep.datauuid contains the row datauuid
    score_df = pd.DataFrame(
        {
            "sleep_score_source_id": sleep_df[datauuid_col].astype(str),
            "sleep_start_datetime_raw": parse_datetime(sleep_df[start_col]),
            "sleep_end_datetime_raw": parse_datetime(sleep_df[end_col]),
            "sleep_utc_offset": sleep_df[offset_col].astype(str),
            "samsung_sleep_score": pd.to_numeric(sleep_df[score_col], errors="coerce"),
            "sleep_efficiency": (
                pd.to_numeric(sleep_df[efficiency_col], errors="coerce")
                if efficiency_col
                else pd.Series(np.nan, index=sleep_df.index)
            ),
            "sleep_duration_raw": (
                pd.to_numeric(sleep_df[duration_col], errors="coerce")
                if duration_col
                else pd.Series(np.nan, index=sleep_df.index)
            ),
        }
    )
    score_df["sleep_start_datetime"] = apply_utc_offset(
        score_df["sleep_start_datetime_raw"],
        score_df["sleep_utc_offset"],
    )
    score_df["sleep_end_datetime"] = apply_utc_offset(
        score_df["sleep_end_datetime_raw"],
        score_df["sleep_utc_offset"],
    )
    score_df = score_df.dropna(subset=["sleep_start_datetime", "samsung_sleep_score"]).copy()
    score_df["samsung_good_sleep_label"] = (
        score_df["samsung_sleep_score"] >= GOOD_SLEEP_SCORE_THRESHOLD
    ).astype(int)
    score_df = score_df.sort_values("sleep_start_datetime").reset_index(drop=True)
    return score_df, sleep_path


def attach_nearest_sleep_score(episode_df: pd.DataFrame, score_df: pd.DataFrame) -> pd.DataFrame:
    episode_df = episode_df.copy()
    placeholder_label_cols = [
        "samsung_sleep_score",
        "samsung_good_sleep_label",
        "has_samsung_sleep_score",
        "sleep_efficiency",
    ]
    episode_df = episode_df.drop(
        columns=[col for col in placeholder_label_cols if col in episode_df.columns],
        errors="ignore",
    )
    episode_df["sleep_start_datetime"] = pd.to_datetime(episode_df["sleep_start_datetime"])
    episode_df = episode_df.sort_values("sleep_start_datetime").reset_index(drop=True)

    joined = pd.merge_asof(
        episode_df,
        score_df[
            [
                "sleep_score_source_id",
                "sleep_start_datetime",
                "sleep_end_datetime",
                "samsung_sleep_score",
                "samsung_good_sleep_label",
                "sleep_efficiency",
            ]
        ].rename(
            columns={
                "sleep_start_datetime": "score_sleep_start_datetime",
                "sleep_end_datetime": "score_sleep_end_datetime",
            }
        ),
        left_on="sleep_start_datetime",
        right_on="score_sleep_start_datetime",
        direction="nearest",
        tolerance=pd.Timedelta(minutes=MAX_MATCH_TIME_DIFF_MINUTES),
    )
    joined["score_match_time_diff_minutes"] = (
        joined["sleep_start_datetime"] - joined["score_sleep_start_datetime"]
    ).abs().dt.total_seconds() / 60
    joined["has_samsung_sleep_score"] = joined["samsung_sleep_score"].notna().astype(int)
    return joined


def compute_proxy_evaluation(prediction_df: pd.DataFrame) -> pd.DataFrame:
    labeled = prediction_df.dropna(subset=["samsung_good_sleep_label"]).copy()
    if labeled.empty:
        return pd.DataFrame(
            [
                {"metric": "labeled_rows", "value": 0},
                {"metric": "note", "value": "No matched Samsung sleep-score proxy labels."},
            ]
        )

    y_true = labeled["samsung_good_sleep_label"].astype(int)
    y_pred = labeled["good_sleep_pred"].astype(int)
    prob = labeled["good_sleep_probability"].astype(float)

    tp = int(((y_true == 1) & (y_pred == 1)).sum())
    tn = int(((y_true == 0) & (y_pred == 0)).sum())
    fp = int(((y_true == 0) & (y_pred == 1)).sum())
    fn = int(((y_true == 1) & (y_pred == 0)).sum())

    sensitivity = tp / (tp + fn) if (tp + fn) else np.nan
    specificity = tn / (tn + fp) if (tn + fp) else np.nan
    balanced_accuracy = np.nanmean([sensitivity, specificity])
    precision = tp / (tp + fp) if (tp + fp) else np.nan
    recall = sensitivity

    rows = [
        {"metric": "labeled_rows", "value": len(labeled)},
        {"metric": "proxy_positive_rate", "value": float(y_true.mean())},
        {"metric": "predicted_positive_rate", "value": float(y_pred.mean())},
        {"metric": "mean_probability", "value": float(prob.mean())},
        {"metric": "balanced_accuracy", "value": float(balanced_accuracy)},
        {"metric": "sensitivity", "value": float(sensitivity) if not pd.isna(sensitivity) else np.nan},
        {"metric": "specificity", "value": float(specificity) if not pd.isna(specificity) else np.nan},
        {"metric": "precision", "value": float(precision) if not pd.isna(precision) else np.nan},
        {"metric": "recall", "value": float(recall) if not pd.isna(recall) else np.nan},
        {"metric": "tn", "value": tn},
        {"metric": "fp", "value": fp},
        {"metric": "fn", "value": fn},
        {"metric": "tp", "value": tp},
    ]
    return pd.DataFrame(rows)


def main() -> None:
    score_df, sleep_path = prepare_sleep_score_table()
    episode_df = pd.read_csv(EPISODE_PATH, encoding="utf-8-sig")
    joined_episode_df = attach_nearest_sleep_score(episode_df, score_df)
    joined_episode_df.to_csv(OUTPUT_EPISODE_PATH, index=False, encoding="utf-8-sig")

    prediction_joined_df = pd.DataFrame()
    evaluation_df = pd.DataFrame()
    if PREDICTION_PATH.exists():
        prediction_df = pd.read_csv(PREDICTION_PATH, encoding="utf-8-sig")
        label_cols = [
            "sleep_episode_id",
            "sleep_score_source_id",
            "score_sleep_start_datetime",
            "score_sleep_end_datetime",
            "score_match_time_diff_minutes",
            "samsung_sleep_score",
            "samsung_good_sleep_label",
            "has_samsung_sleep_score",
            "sleep_efficiency",
        ]
        prediction_joined_df = prediction_df.merge(
            joined_episode_df[label_cols],
            on="sleep_episode_id",
            how="left",
        )
        prediction_joined_df.to_csv(OUTPUT_PREDICTION_PATH, index=False, encoding="utf-8-sig")
        evaluation_df = compute_proxy_evaluation(prediction_joined_df)
        evaluation_df.to_csv(EVALUATION_PATH, index=False, encoding="utf-8-sig")

    match_report_rows = [
        {"metric": "sleep_score_source_file", "value": str(sleep_path.relative_to(PROJECT_ROOT))},
        {"metric": "sleep_score_source_rows_with_score", "value": len(score_df)},
        {"metric": "episode_rows", "value": len(joined_episode_df)},
        {"metric": "matched_episode_rows", "value": int(joined_episode_df["has_samsung_sleep_score"].sum())},
        {
            "metric": "matched_episode_rate",
            "value": float(joined_episode_df["has_samsung_sleep_score"].mean()),
        },
        {"metric": "good_sleep_score_threshold", "value": GOOD_SLEEP_SCORE_THRESHOLD},
        {"metric": "max_match_time_diff_minutes", "value": MAX_MATCH_TIME_DIFF_MINUTES},
    ]
    if joined_episode_df["has_samsung_sleep_score"].sum() > 0:
        matched = joined_episode_df[joined_episode_df["has_samsung_sleep_score"] == 1]
        match_report_rows.extend(
            [
                {"metric": "proxy_positive_rate", "value": float(matched["samsung_good_sleep_label"].mean())},
                {"metric": "mean_sleep_score", "value": float(matched["samsung_sleep_score"].mean())},
                {"metric": "median_sleep_score", "value": float(matched["samsung_sleep_score"].median())},
                {
                    "metric": "median_match_time_diff_minutes",
                    "value": float(matched["score_match_time_diff_minutes"].median()),
                },
            ]
        )
    match_report_df = pd.DataFrame(match_report_rows)
    match_report_df.to_csv(MATCH_REPORT_PATH, index=False, encoding="utf-8-sig")

    report_lines = [
        "# Samsung Sleep Score Proxy Label Join Summary",
        "",
        "## Purpose",
        "",
        "Join Samsung sleep-score proxy labels to sleep_stage-derived episodes and external prediction outputs.",
        "",
        "## Inputs",
        "",
        "```text",
        str(EPISODE_PATH.relative_to(PROJECT_ROOT)),
        str(PREDICTION_PATH.relative_to(PROJECT_ROOT)),
        str(sleep_path.relative_to(PROJECT_ROOT)),
        "```",
        "",
        "## Outputs",
        "",
        "```text",
        str(OUTPUT_EPISODE_PATH.relative_to(PROJECT_ROOT)),
        str(OUTPUT_PREDICTION_PATH.relative_to(PROJECT_ROOT)),
        str(MATCH_REPORT_PATH.relative_to(PROJECT_ROOT)),
        str(EVALUATION_PATH.relative_to(PROJECT_ROOT)),
        "```",
        "",
        "## Matching Rule",
        "",
        f"- Proxy label source: Samsung `sleep_score`",
        f"- Good-sleep proxy threshold: `sleep_score >= {GOOD_SLEEP_SCORE_THRESHOLD}`",
        f"- Episode matching: nearest sleep start within `{MAX_MATCH_TIME_DIFF_MINUTES}` minutes",
        "- Samsung shifted sleep-table mapping is used for this export.",
        "- Sleep start/end times are adjusted by the exported UTC offset before matching.",
        "",
        "## Match Summary",
        "",
        *[f"- {row['metric']}: `{row['value']}`" for row in match_report_rows],
        "",
        "## Caveat",
        "",
        "Samsung `sleep_score` is a device/vendor proxy label, not the original project `good_sleep_label`. Any metrics computed here are proxy-label diagnostics only.",
        "",
    ]
    REPORT_PATH.write_text("\n".join(report_lines), encoding="utf-8")

    print("episodes with proxy labels:", OUTPUT_EPISODE_PATH)
    if PREDICTION_PATH.exists():
        print("predictions with proxy labels:", OUTPUT_PREDICTION_PATH)
        print("proxy evaluation:", EVALUATION_PATH)
    print("match report:", MATCH_REPORT_PATH)
    print("report:", REPORT_PATH)
    print(match_report_df)
    if not evaluation_df.empty:
        print(evaluation_df)


if __name__ == "__main__":
    main()
