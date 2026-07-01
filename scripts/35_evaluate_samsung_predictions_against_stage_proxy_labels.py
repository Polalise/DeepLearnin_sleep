from __future__ import annotations

from pathlib import Path
import os
import numpy as np
import pandas as pd


PROJECT_ROOT = Path(os.environ.get("PROJECT_ROOT", Path(__file__).resolve().parents[1]))
STAGE1_DIR = PROJECT_ROOT / "data" / "processed" / "samsung_health" / "pre_sleep_stage1"

PREDICTION_PATH = STAGE1_DIR / "samsung_pre_sleep_predictions.csv"
LABEL_PATH = STAGE1_DIR / "samsung_sleep_episodes_with_stage_proxy_labels.csv"

OUTPUT_JOINED_PATH = STAGE1_DIR / "samsung_predictions_with_stage_proxy_labels.csv"
OUTPUT_EVAL_PATH = STAGE1_DIR / "samsung_stage_proxy_prediction_evaluation.csv"
OUTPUT_THRESHOLD_PATH = STAGE1_DIR / "samsung_stage_proxy_threshold_sensitivity.csv"
REPORT_PATH = PROJECT_ROOT / "reports" / "samsung_stage_proxy_external_evaluation_report.md"

OFFICIAL_THRESHOLD = 0.54
THRESHOLDS = np.round(np.arange(0.30, 0.61, 0.01), 2)


def binary_metrics(y_true: pd.Series, y_prob: pd.Series, threshold: float) -> dict:
    y_true = y_true.astype(int)
    y_prob = y_prob.astype(float)
    y_pred = (y_prob >= threshold).astype(int)

    tp = int(((y_true == 1) & (y_pred == 1)).sum())
    tn = int(((y_true == 0) & (y_pred == 0)).sum())
    fp = int(((y_true == 0) & (y_pred == 1)).sum())
    fn = int(((y_true == 1) & (y_pred == 0)).sum())

    sensitivity = tp / (tp + fn) if (tp + fn) else np.nan
    specificity = tn / (tn + fp) if (tn + fp) else np.nan
    balanced_accuracy = np.nanmean([sensitivity, specificity])
    precision = tp / (tp + fp) if (tp + fp) else np.nan
    recall = sensitivity
    f1 = (
        2 * precision * recall / (precision + recall)
        if precision == precision and recall == recall and (precision + recall) > 0
        else np.nan
    )

    return {
        "threshold": float(threshold),
        "rows": int(len(y_true)),
        "positive_count": int(y_true.sum()),
        "positive_rate": float(y_true.mean()),
        "predicted_positive_count": int(y_pred.sum()),
        "predicted_positive_rate": float(y_pred.mean()),
        "mean_probability": float(y_prob.mean()),
        "median_probability": float(y_prob.median()),
        "balanced_accuracy": float(balanced_accuracy),
        "sensitivity": float(sensitivity) if sensitivity == sensitivity else np.nan,
        "specificity": float(specificity) if specificity == specificity else np.nan,
        "precision": float(precision) if precision == precision else np.nan,
        "recall": float(recall) if recall == recall else np.nan,
        "f1": float(f1) if f1 == f1 else np.nan,
        "tn": tn,
        "fp": fp,
        "fn": fn,
        "tp": tp,
    }


def rank_auc(y_true: pd.Series, y_prob: pd.Series) -> float:
    y_true = y_true.astype(int).to_numpy()
    y_prob = y_prob.astype(float).to_numpy()

    pos = y_prob[y_true == 1]
    neg = y_prob[y_true == 0]

    if len(pos) == 0 or len(neg) == 0:
        return np.nan

    comparisons = []
    for p in pos:
        comparisons.append((p > neg).mean() + 0.5 * (p == neg).mean())

    return float(np.mean(comparisons))


def average_precision_manual(y_true: pd.Series, y_prob: pd.Series) -> float:
    df = pd.DataFrame({"y_true": y_true.astype(int), "y_prob": y_prob.astype(float)})
    df = df.sort_values("y_prob", ascending=False).reset_index(drop=True)

    positives = int(df["y_true"].sum())
    if positives == 0:
        return np.nan

    df["tp_cumsum"] = df["y_true"].cumsum()
    df["rank"] = np.arange(1, len(df) + 1)
    df["precision_at_k"] = df["tp_cumsum"] / df["rank"]

    return float((df["precision_at_k"] * df["y_true"]).sum() / positives)


def main() -> None:
    predictions = pd.read_csv(PREDICTION_PATH, encoding="utf-8-sig")
    labels = pd.read_csv(LABEL_PATH, encoding="utf-8-sig")

    required_prediction_cols = [
        "sleep_episode_id",
        "good_sleep_probability",
        "good_sleep_pred",
        "threshold",
    ]
    missing_prediction_cols = [c for c in required_prediction_cols if c not in predictions.columns]
    if missing_prediction_cols:
        raise ValueError(f"Missing prediction columns: {missing_prediction_cols}")

    required_label_cols = [
        "sleep_episode_id",
        "samsung_good_sleep_label_v1",
        "stage_sleep_efficiency",
        "stage_awake_ratio",
        "sleep_duration_hours",
    ]
    missing_label_cols = [c for c in required_label_cols if c not in labels.columns]
    if missing_label_cols:
        raise ValueError(f"Missing label columns: {missing_label_cols}")

    label_cols = [
        "sleep_episode_id",
        "samsung_good_sleep_label_v1",
        "stage_sleep_efficiency",
        "stage_awake_ratio",
        "stage_light_ratio",
        "stage_deep_ratio",
        "stage_rem_ratio",
        "sleep_duration_hours",
        "stage_proxy_duration_ok",
        "stage_proxy_efficiency_ok",
        "stage_proxy_awake_ok",
        "samsung_good_sleep_label_v1_definition",
    ]

    joined = predictions.merge(labels[label_cols], on="sleep_episode_id", how="left")
    joined["samsung_good_sleep_label_v1"] = pd.to_numeric(
        joined["samsung_good_sleep_label_v1"],
        errors="coerce",
    )

    labeled = joined.dropna(subset=["samsung_good_sleep_label_v1"]).copy()
    labeled["samsung_good_sleep_label_v1"] = labeled["samsung_good_sleep_label_v1"].astype(int)
    labeled["good_sleep_probability"] = pd.to_numeric(
        labeled["good_sleep_probability"],
        errors="coerce",
    )

    y_true = labeled["samsung_good_sleep_label_v1"]
    y_prob = labeled["good_sleep_probability"]

    official_metrics = binary_metrics(y_true, y_prob, OFFICIAL_THRESHOLD)
    official_metrics["evaluation"] = "official_threshold"

    threshold_rows = []
    for threshold in THRESHOLDS:
        row = binary_metrics(y_true, y_prob, float(threshold))
        threshold_rows.append(row)

    threshold_df = pd.DataFrame(threshold_rows)
    best_ba_row = threshold_df.sort_values(
        ["balanced_accuracy", "threshold"],
        ascending=[False, True],
    ).iloc[0]
    best_f1_row = threshold_df.sort_values(
        ["f1", "threshold"],
        ascending=[False, True],
    ).iloc[0]

    roc_auc = rank_auc(y_true, y_prob)
    average_precision = average_precision_manual(y_true, y_prob)

    eval_rows = [
        official_metrics,
        {
            **best_ba_row.to_dict(),
            "evaluation": "best_balanced_accuracy_threshold",
        },
        {
            **best_f1_row.to_dict(),
            "evaluation": "best_f1_threshold",
        },
    ]
    eval_df = pd.DataFrame(eval_rows)

    extra_rows = pd.DataFrame(
        [
            {"metric": "roc_auc_rank", "value": roc_auc},
            {"metric": "average_precision_manual", "value": average_precision},
            {"metric": "labeled_rows", "value": len(labeled)},
            {"metric": "positive_count", "value": int(y_true.sum())},
            {"metric": "positive_rate", "value": float(y_true.mean())},
            {"metric": "mean_probability_positive", "value": float(y_prob[y_true == 1].mean())},
            {"metric": "mean_probability_negative", "value": float(y_prob[y_true == 0].mean())},
            {"metric": "median_probability_positive", "value": float(y_prob[y_true == 1].median())},
            {"metric": "median_probability_negative", "value": float(y_prob[y_true == 0].median())},
        ]
    )

    joined.to_csv(OUTPUT_JOINED_PATH, index=False, encoding="utf-8-sig")
    eval_df.to_csv(OUTPUT_EVAL_PATH, index=False, encoding="utf-8-sig")
    threshold_df.to_csv(OUTPUT_THRESHOLD_PATH, index=False, encoding="utf-8-sig")

    report_lines = [
        "# Samsung Stage Proxy External Evaluation Report",
        "",
        "## Purpose",
        "",
        "Compare selected MLP predictions against Samsung stage-based proxy label v1.",
        "",
        "## Inputs",
        "",
        "```text",
        str(PREDICTION_PATH.relative_to(PROJECT_ROOT)),
        str(LABEL_PATH.relative_to(PROJECT_ROOT)),
        "```",
        "",
        "## Outputs",
        "",
        "```text",
        str(OUTPUT_JOINED_PATH.relative_to(PROJECT_ROOT)),
        str(OUTPUT_EVAL_PATH.relative_to(PROJECT_ROOT)),
        str(OUTPUT_THRESHOLD_PATH.relative_to(PROJECT_ROOT)),
        "```",
        "",
        "## Label Caveat",
        "",
        "The target is `samsung_good_sleep_label_v1`, a Samsung stage-derived proxy label. It is not the original project `good_sleep_label`.",
        "",
        "## Label Distribution",
        "",
        f"- Labeled rows: `{len(labeled)}`",
        f"- Positive count: `{int(y_true.sum())}`",
        f"- Positive rate: `{float(y_true.mean()):.4f}`",
        "",
        "## Ranking Metrics",
        "",
        f"- ROC AUC rank approximation: `{roc_auc:.4f}`",
        f"- Average precision: `{average_precision:.4f}`",
        "",
        "## Official Threshold 0.54",
        "",
        f"- Predicted positive count: `{official_metrics['predicted_positive_count']}`",
        f"- Predicted positive rate: `{official_metrics['predicted_positive_rate']:.4f}`",
        f"- Balanced accuracy: `{official_metrics['balanced_accuracy']:.4f}`",
        f"- Sensitivity/recall: `{official_metrics['recall']:.4f}`",
        f"- Specificity: `{official_metrics['specificity']:.4f}`",
        f"- Precision: `{official_metrics['precision']}`",
        f"- Confusion matrix: TN `{official_metrics['tn']}`, FP `{official_metrics['fp']}`, FN `{official_metrics['fn']}`, TP `{official_metrics['tp']}`",
        "",
        "## Best Thresholds",
        "",
        f"- Best balanced accuracy threshold: `{best_ba_row['threshold']:.2f}`",
        f"- Best balanced accuracy: `{best_ba_row['balanced_accuracy']:.4f}`",
        f"- Best F1 threshold: `{best_f1_row['threshold']:.2f}`",
        f"- Best F1: `{best_f1_row['f1']:.4f}`",
        "",
        "## Probability Separation",
        "",
        f"- Mean probability, proxy positive: `{float(y_prob[y_true == 1].mean()):.4f}`",
        f"- Mean probability, proxy negative: `{float(y_prob[y_true == 0].mean()):.4f}`",
        f"- Median probability, proxy positive: `{float(y_prob[y_true == 1].median()):.4f}`",
        f"- Median probability, proxy negative: `{float(y_prob[y_true == 0].median()):.4f}`",
        "",
        "## Interpretation Guardrail",
        "",
        "This is a diagnostic evaluation against a strict, imbalanced proxy label. It should guide threshold and label-definition decisions, not be reported as formal external validation.",
        "",
    ]

    REPORT_PATH.write_text("\n".join(report_lines), encoding="utf-8")

    print("joined predictions:", OUTPUT_JOINED_PATH)
    print("evaluation:", OUTPUT_EVAL_PATH)
    print("threshold sensitivity:", OUTPUT_THRESHOLD_PATH)
    print("report:", REPORT_PATH)
    print()
    print("official threshold metrics")
    print(pd.DataFrame([official_metrics]).T)
    print()
    print("best balanced accuracy row")
    print(best_ba_row)
    print()
    print("extra metrics")
    print(extra_rows)


if __name__ == "__main__":
    main()
