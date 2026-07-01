from __future__ import annotations

from pathlib import Path
import pandas as pd
import numpy as np


PROJECT_ROOT = Path(r"C:\workSpace\DeepLearnin_sleep")

STAGE1_DIR = PROJECT_ROOT / "data" / "processed" / "samsung_health" / "pre_sleep_stage1"

EPISODE_PATH = STAGE1_DIR / "samsung_sleep_episodes.csv"
STAGE_SUMMARY_PATH = STAGE1_DIR / "samsung_sleep_stage_episode_stage_summary.csv"

OUTPUT_PATH = STAGE1_DIR / "samsung_sleep_episodes_with_stage_proxy_labels.csv"
QUALITY_SUMMARY_PATH = STAGE1_DIR / "samsung_stage_proxy_label_quality_summary.csv"
REPORT_PATH = PROJECT_ROOT / "reports" / "samsung_stage_based_proxy_label_summary.md"

MIN_DURATION_HOURS = 6.0
MAX_DURATION_HOURS = 9.0
MIN_STAGE_EFFICIENCY = 0.85
MAX_AWAKE_RATIO = 0.20

# Samsung sleep_stage codes inferred from common Samsung Health exports.
# Treat this as proxy-label engineering, not ground truth clinical staging.
STAGE_CODE_MAP = {
    40001: "awake",
    40002: "light",
    40003: "deep",
    40004: "rem",
}


def safe_divide(numerator: pd.Series, denominator: pd.Series) -> pd.Series:
    return numerator / denominator.replace(0, np.nan)


def main() -> None:
    episodes = pd.read_csv(EPISODE_PATH, encoding="utf-8-sig")
    stage_summary = pd.read_csv(STAGE_SUMMARY_PATH, encoding="utf-8-sig")

    required_episode_cols = [
        "sleep_episode_id",
        "source_sleep_id",
        "sleep_start_datetime",
        "sleep_end_datetime",
        "sleep_duration_hours",
    ]
    missing_episode_cols = [c for c in required_episode_cols if c not in episodes.columns]
    if missing_episode_cols:
        raise ValueError(f"Missing episode columns: {missing_episode_cols}")

    required_stage_cols = [
        "source_sleep_id",
        "samsung_stage_code",
        "stage_total_minutes",
    ]
    missing_stage_cols = [c for c in required_stage_cols if c not in stage_summary.columns]
    if missing_stage_cols:
        raise ValueError(f"Missing stage summary columns: {missing_stage_cols}")

    stage_summary = stage_summary.copy()
    stage_summary["samsung_stage_code"] = pd.to_numeric(
        stage_summary["samsung_stage_code"],
        errors="coerce",
    )
    stage_summary["stage_name"] = stage_summary["samsung_stage_code"].map(STAGE_CODE_MAP)
    stage_summary["stage_total_minutes"] = pd.to_numeric(
        stage_summary["stage_total_minutes"],
        errors="coerce",
    )

    unknown_stage_rows = stage_summary["stage_name"].isna().sum()

    stage_known = stage_summary.dropna(subset=["stage_name"]).copy()

    stage_pivot = (
        stage_known.pivot_table(
            index="source_sleep_id",
            columns="stage_name",
            values="stage_total_minutes",
            aggfunc="sum",
            fill_value=0.0,
        )
        .reset_index()
    )

    for col in ["awake", "light", "deep", "rem"]:
        if col not in stage_pivot.columns:
            stage_pivot[col] = 0.0

    stage_pivot = stage_pivot.rename(
        columns={
            "awake": "stage_awake_minutes",
            "light": "stage_light_minutes",
            "deep": "stage_deep_minutes",
            "rem": "stage_rem_minutes",
        }
    )

    stage_pivot["stage_known_minutes"] = (
        stage_pivot["stage_awake_minutes"]
        + stage_pivot["stage_light_minutes"]
        + stage_pivot["stage_deep_minutes"]
        + stage_pivot["stage_rem_minutes"]
    )
    stage_pivot["stage_asleep_minutes"] = (
        stage_pivot["stage_light_minutes"]
        + stage_pivot["stage_deep_minutes"]
        + stage_pivot["stage_rem_minutes"]
    )

    labeled = episodes.merge(stage_pivot, on="source_sleep_id", how="left")

    stage_cols = [
        "stage_awake_minutes",
        "stage_light_minutes",
        "stage_deep_minutes",
        "stage_rem_minutes",
        "stage_known_minutes",
        "stage_asleep_minutes",
    ]
    for col in stage_cols:
        labeled[col] = pd.to_numeric(labeled[col], errors="coerce")

    labeled["stage_proxy_has_stage_minutes"] = labeled["stage_known_minutes"].notna().astype(int)

    labeled["stage_awake_ratio"] = safe_divide(
        labeled["stage_awake_minutes"],
        labeled["stage_known_minutes"],
    )
    labeled["stage_sleep_efficiency"] = safe_divide(
        labeled["stage_asleep_minutes"],
        labeled["stage_known_minutes"],
    )
    labeled["stage_light_ratio"] = safe_divide(
        labeled["stage_light_minutes"],
        labeled["stage_known_minutes"],
    )
    labeled["stage_deep_ratio"] = safe_divide(
        labeled["stage_deep_minutes"],
        labeled["stage_known_minutes"],
    )
    labeled["stage_rem_ratio"] = safe_divide(
        labeled["stage_rem_minutes"],
        labeled["stage_known_minutes"],
    )

    labeled["stage_proxy_duration_ok"] = labeled["sleep_duration_hours"].between(
        MIN_DURATION_HOURS,
        MAX_DURATION_HOURS,
        inclusive="both",
    )
    labeled["stage_proxy_efficiency_ok"] = labeled["stage_sleep_efficiency"] >= MIN_STAGE_EFFICIENCY
    labeled["stage_proxy_awake_ok"] = labeled["stage_awake_ratio"] <= MAX_AWAKE_RATIO

    valid_label_mask = labeled["stage_proxy_has_stage_minutes"].eq(1)

    labeled["samsung_good_sleep_label_v1"] = np.where(
        valid_label_mask,
        (
            labeled["stage_proxy_duration_ok"]
            & labeled["stage_proxy_efficiency_ok"]
            & labeled["stage_proxy_awake_ok"]
        ).astype(int),
        np.nan,
    )

    labeled["samsung_good_sleep_label_v1_definition"] = (
        f"duration {MIN_DURATION_HOURS}-{MAX_DURATION_HOURS}h, "
        f"stage_efficiency >= {MIN_STAGE_EFFICIENCY}, "
        f"awake_ratio <= {MAX_AWAKE_RATIO}"
    )

    quality_rows = [
        {"metric": "episode_rows", "value": len(labeled)},
        {
            "metric": "stage_summary_rows",
            "value": len(stage_summary),
        },
        {
            "metric": "unknown_stage_rows",
            "value": int(unknown_stage_rows),
        },
        {
            "metric": "label_coverage_count",
            "value": int(valid_label_mask.sum()),
        },
        {
            "metric": "label_coverage_rate",
            "value": float(valid_label_mask.mean()),
        },
        {
            "metric": "positive_count",
            "value": int(labeled["samsung_good_sleep_label_v1"].fillna(0).sum()),
        },
        {
            "metric": "positive_rate_among_labeled",
            "value": float(labeled.loc[valid_label_mask, "samsung_good_sleep_label_v1"].mean()),
        },
        {
            "metric": "mean_duration_hours",
            "value": float(labeled["sleep_duration_hours"].mean()),
        },
        {
            "metric": "median_duration_hours",
            "value": float(labeled["sleep_duration_hours"].median()),
        },
        {
            "metric": "mean_stage_efficiency",
            "value": float(labeled["stage_sleep_efficiency"].mean()),
        },
        {
            "metric": "median_stage_efficiency",
            "value": float(labeled["stage_sleep_efficiency"].median()),
        },
        {
            "metric": "mean_awake_ratio",
            "value": float(labeled["stage_awake_ratio"].mean()),
        },
        {
            "metric": "median_awake_ratio",
            "value": float(labeled["stage_awake_ratio"].median()),
        },
        {
            "metric": "duration_ok_rate",
            "value": float(labeled.loc[valid_label_mask, "stage_proxy_duration_ok"].mean()),
        },
        {
            "metric": "efficiency_ok_rate",
            "value": float(labeled.loc[valid_label_mask, "stage_proxy_efficiency_ok"].mean()),
        },
        {
            "metric": "awake_ok_rate",
            "value": float(labeled.loc[valid_label_mask, "stage_proxy_awake_ok"].mean()),
        },
    ]

    quality = pd.DataFrame(quality_rows)

    labeled.to_csv(OUTPUT_PATH, index=False, encoding="utf-8-sig")
    quality.to_csv(QUALITY_SUMMARY_PATH, index=False, encoding="utf-8-sig")

    report_lines = [
        "# Samsung Stage-Based Proxy Label Summary",
        "",
        "## Purpose",
        "",
        "Create a Samsung sleep-stage-based proxy label for exploratory external evaluation.",
        "",
        "## Inputs",
        "",
        "```text",
        str(EPISODE_PATH.relative_to(PROJECT_ROOT)),
        str(STAGE_SUMMARY_PATH.relative_to(PROJECT_ROOT)),
        "```",
        "",
        "## Outputs",
        "",
        "```text",
        str(OUTPUT_PATH.relative_to(PROJECT_ROOT)),
        str(QUALITY_SUMMARY_PATH.relative_to(PROJECT_ROOT)),
        "```",
        "",
        "## Label Definition",
        "",
        f"- Duration: `{MIN_DURATION_HOURS}` to `{MAX_DURATION_HOURS}` hours",
        f"- Stage-based sleep efficiency: `>= {MIN_STAGE_EFFICIENCY}`",
        f"- Awake ratio: `<= {MAX_AWAKE_RATIO}`",
        "",
        "## Stage Code Mapping",
        "",
        "- `40001`: awake",
        "- `40002`: light",
        "- `40003`: deep",
        "- `40004`: rem",
        "",
        "## Quality Summary",
        "",
        *[f"- {row['metric']}: `{row['value']}`" for row in quality_rows],
        "",
        "## Caveat",
        "",
        "This is a Samsung stage-derived proxy label, not the original project good_sleep_label. It is intended to improve interpretability and diagnostic evaluation, not to claim formal clinical ground truth.",
        "",
    ]

    REPORT_PATH.write_text("\n".join(report_lines), encoding="utf-8")

    print("labeled episodes:", OUTPUT_PATH)
    print("quality summary:", QUALITY_SUMMARY_PATH)
    print("report:", REPORT_PATH)
    print(quality)


if __name__ == "__main__":
    main()