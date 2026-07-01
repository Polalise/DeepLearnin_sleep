from __future__ import annotations

from pathlib import Path
import argparse
import os
import sys

import pandas as pd


PROJECT_ROOT = Path(os.environ.get("PROJECT_ROOT", Path(__file__).resolve().parents[1]))
SRC_DIR = PROJECT_ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from pre_sleep_forecasting.inference import PreSleepInferencePipeline


SAMSUNG_STAGE1_DIR = PROJECT_ROOT / "data" / "processed" / "samsung_health" / "pre_sleep_stage1"
DEFAULT_INPUT_PATH = SAMSUNG_STAGE1_DIR / "samsung_raw_stage1_features.csv"
DEFAULT_OUTPUT_PATH = SAMSUNG_STAGE1_DIR / "samsung_pre_sleep_predictions.csv"
DEFAULT_SUMMARY_PATH = SAMSUNG_STAGE1_DIR / "samsung_pre_sleep_prediction_summary.csv"
DEFAULT_REPORT_PATH = PROJECT_ROOT / "reports" / "samsung_pre_sleep_external_prediction_summary.md"


def summarize_predictions(prediction_df: pd.DataFrame) -> pd.DataFrame:
    probability = prediction_df["good_sleep_probability"]
    pred = prediction_df["good_sleep_pred"]

    rows = [
        {"metric": "rows", "value": len(prediction_df)},
        {"metric": "threshold", "value": float(prediction_df["threshold"].iloc[0])},
        {"metric": "predicted_positive_count", "value": int(pred.sum())},
        {"metric": "predicted_negative_count", "value": int((pred == 0).sum())},
        {"metric": "predicted_positive_rate", "value": float(pred.mean())},
        {"metric": "mean_probability", "value": float(probability.mean())},
        {"metric": "std_probability", "value": float(probability.std(ddof=0))},
        {"metric": "min_probability", "value": float(probability.min())},
        {"metric": "p10_probability", "value": float(probability.quantile(0.10))},
        {"metric": "p25_probability", "value": float(probability.quantile(0.25))},
        {"metric": "median_probability", "value": float(probability.median())},
        {"metric": "p75_probability", "value": float(probability.quantile(0.75))},
        {"metric": "p90_probability", "value": float(probability.quantile(0.90))},
        {"metric": "max_probability", "value": float(probability.max())},
    ]
    return pd.DataFrame(rows)


def write_report(
    input_path: Path,
    output_path: Path,
    summary_path: Path,
    report_path: Path,
    prediction_df: pd.DataFrame,
    summary_df: pd.DataFrame,
) -> None:
    summary_lookup = dict(zip(summary_df["metric"], summary_df["value"]))
    top_rows = prediction_df.sort_values("good_sleep_probability", ascending=False).head(10)
    low_rows = prediction_df.sort_values("good_sleep_probability", ascending=True).head(10)

    def format_rows(df: pd.DataFrame) -> list[str]:
        cols = [
            col
            for col in [
                "sleep_episode_id",
                "sleep_start_datetime",
                "good_sleep_probability",
                "good_sleep_pred",
            ]
            if col in df.columns
        ]
        lines = []
        for _, row in df[cols].iterrows():
            episode_id = str(row.get("sleep_episode_id", ""))
            start_dt = str(row.get("sleep_start_datetime", ""))
            probability = float(row["good_sleep_probability"])
            pred = int(row["good_sleep_pred"])
            lines.append(f"- `{start_dt}` | pred={pred} | probability={probability:.4f} | `{episode_id}`")
        return lines

    report_lines = [
        "# Samsung Health External Pre-Sleep Prediction Summary",
        "",
        "## Purpose",
        "",
        "Apply the selected strict pre-sleep forecasting MLP to Samsung Health Stage 1 raw features.",
        "",
        "## Inputs",
        "",
        "```text",
        str(input_path.relative_to(PROJECT_ROOT)),
        "```",
        "",
        "## Outputs",
        "",
        "```text",
        str(output_path.relative_to(PROJECT_ROOT)),
        str(summary_path.relative_to(PROJECT_ROOT)),
        "```",
        "",
        "## Model",
        "",
        "- Experiment family: `presleep_stage1_hp_tiny_dropout40_wd1e3`",
        "- Representative checkpoint: `presleep_stage1_hp_tiny_dropout40_wd1e3_seed2027`",
        "- Official threshold: `0.54` unless overridden at runtime",
        "- Raw feature contract: 70 Samsung-adapted Stage 1 features",
        "",
        "## Prediction Distribution",
        "",
        f"- Rows: `{int(summary_lookup['rows'])}`",
        f"- Threshold: `{float(summary_lookup['threshold']):.4f}`",
        f"- Predicted positive rate: `{float(summary_lookup['predicted_positive_rate']):.4f}`",
        f"- Mean probability: `{float(summary_lookup['mean_probability']):.4f}`",
        f"- Median probability: `{float(summary_lookup['median_probability']):.4f}`",
        f"- P10/P90 probability: `{float(summary_lookup['p10_probability']):.4f}` / `{float(summary_lookup['p90_probability']):.4f}`",
        "",
        "## Highest Probability Episodes",
        "",
        *format_rows(top_rows),
        "",
        "## Lowest Probability Episodes",
        "",
        *format_rows(low_rows),
        "",
        "## Interpretation Caveats",
        "",
        "- This is external/future-style application to Samsung Health export data, not a retrained Samsung model.",
        "- Samsung adapter coverage is strong for pre-sleep heart rate and previous-day daily activity.",
        "- Samsung pre-sleep intraday step/calorie coverage is sparse in the current export.",
        "- Probabilities should be interpreted as model scores, not calibrated clinical probabilities.",
        "- No label-based external performance metric is computed by this script.",
        "",
    ]
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text("\n".join(report_lines), encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", default=str(DEFAULT_INPUT_PATH))
    parser.add_argument("--output", default=str(DEFAULT_OUTPUT_PATH))
    parser.add_argument("--summary", default=str(DEFAULT_SUMMARY_PATH))
    parser.add_argument("--report", default=str(DEFAULT_REPORT_PATH))
    parser.add_argument("--project-root", default=str(PROJECT_ROOT))
    parser.add_argument("--manifest", default=None)
    parser.add_argument("--threshold", type=float, default=None)
    args = parser.parse_args()

    input_path = Path(args.input)
    output_path = Path(args.output)
    summary_path = Path(args.summary)
    report_path = Path(args.report)

    raw_df = pd.read_csv(input_path, encoding="utf-8-sig")
    pipeline = PreSleepInferencePipeline(
        project_root=args.project_root,
        manifest_path=args.manifest,
    )
    prediction_df = pipeline.predict(raw_df, threshold=args.threshold)
    summary_df = summarize_predictions(prediction_df)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    prediction_df.to_csv(output_path, index=False, encoding="utf-8-sig")
    summary_df.to_csv(summary_path, index=False, encoding="utf-8-sig")
    write_report(
        input_path=input_path,
        output_path=output_path,
        summary_path=summary_path,
        report_path=report_path,
        prediction_df=prediction_df,
        summary_df=summary_df,
    )

    print("predictions:", output_path)
    print("summary:", summary_path)
    print("report:", report_path)
    print("rows:", len(prediction_df))
    print("threshold:", float(prediction_df["threshold"].iloc[0]))
    print("predicted positive rate:", float(prediction_df["good_sleep_pred"].mean()))
    print("mean probability:", float(prediction_df["good_sleep_probability"].mean()))


if __name__ == "__main__":
    main()
