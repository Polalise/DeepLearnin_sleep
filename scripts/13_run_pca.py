from __future__ import annotations

from datetime import datetime
from pathlib import Path

import joblib
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from sklearn.decomposition import PCA


# This script runs the PCA step after scaling.
#
# PCA unit:
# - Use only the scaled model feature columns produced by 12_scale_features.py.
# - Preserve participant_object_id and calendar_date as diagnostic keys.
# - Preserve good_sleep_label as the modeling target.
#
# Boundary:
# - This script does not train predictive models.
# - PCA is fit on the full current dataset for preprocessing exploration.
#   For final model evaluation, PCA should be fit inside the training fold
#   after participant-aware split to avoid train/test leakage.
PROJECT_ROOT = Path(__file__).resolve().parents[1]
INPUT_PATH = PROJECT_ROOT / "data" / "processed" / "modeling_dataset_scaled.csv"
FEATURE_COLUMNS_PATH = PROJECT_ROOT / "data" / "processed" / "scaled_feature_columns.csv"
OUTPUT_PATH = PROJECT_ROOT / "data" / "processed" / "modeling_dataset_pca.csv"
PCA_MODEL_PATH = PROJECT_ROOT / "data" / "processed" / "pca_model.joblib"
PCA_COMPONENTS_PATH = PROJECT_ROOT / "data" / "processed" / "pca_components.csv"
PCA_VARIANCE_PATH = PROJECT_ROOT / "data" / "processed" / "pca_explained_variance.csv"
PCA_TOP_LOADINGS_PATH = PROJECT_ROOT / "data" / "processed" / "pca_top_loadings.csv"
REPORT_PATH = PROJECT_ROOT / "reports" / "pca_summary.md"
FIGURE_DIR = PROJECT_ROOT / "reports" / "figures" / "pca"

KEY_COLUMNS = ["participant_object_id", "calendar_date"]
TARGET_COLUMN = "good_sleep_label"
VARIANCE_THRESHOLD = 0.95
TOP_LOADING_COUNT = 10


def load_scaled_feature_columns() -> list[str]:
    """Load the feature list that was validated and scaled in the previous step."""

    feature_metadata = pd.read_csv(FEATURE_COLUMNS_PATH)
    if "feature" not in feature_metadata.columns:
        raise ValueError(f"`feature` column is missing from {FEATURE_COLUMNS_PATH}")
    return feature_metadata["feature"].tolist()


def validate_inputs(df: pd.DataFrame, feature_columns: list[str]) -> None:
    """Check that PCA receives a clean numeric feature matrix with stable keys."""

    required_columns = KEY_COLUMNS + [TARGET_COLUMN]
    missing_required = [column for column in required_columns if column not in df.columns]
    if missing_required:
        raise ValueError(f"Required columns missing from input: {missing_required}")

    missing_features = [column for column in feature_columns if column not in df.columns]
    if missing_features:
        raise ValueError(f"Feature columns missing from input: {missing_features[:10]}")

    non_numeric = [
        column for column in feature_columns if not pd.api.types.is_numeric_dtype(df[column])
    ]
    if non_numeric:
        raise ValueError(f"PCA feature columns must be numeric: {non_numeric[:10]}")

    missing_cells = int(df[feature_columns].isna().sum().sum())
    if missing_cells:
        raise ValueError(f"PCA feature matrix contains {missing_cells} missing cells.")

    duplicated_keys = int(df.duplicated(KEY_COLUMNS).sum())
    if duplicated_keys:
        raise ValueError(f"Input contains {duplicated_keys} duplicate participant-date rows.")


def run_pca(df: pd.DataFrame, feature_columns: list[str]) -> tuple[PCA, pd.DataFrame, int]:
    """Fit PCA and return principal-component scores selected by variance threshold."""

    feature_matrix = df[feature_columns].to_numpy()

    # Fit all possible components first so the explained-variance curve can be
    # inspected, then keep enough leading PCs to explain the target variance.
    pca = PCA()
    all_scores = pca.fit_transform(feature_matrix)
    cumulative_variance = np.cumsum(pca.explained_variance_ratio_)
    selected_components = int(np.searchsorted(cumulative_variance, VARIANCE_THRESHOLD) + 1)

    pc_columns = [f"PC{i:03d}" for i in range(1, selected_components + 1)]
    selected_scores = pd.DataFrame(
        all_scores[:, :selected_components],
        columns=pc_columns,
        index=df.index,
    )

    output = pd.concat([df[KEY_COLUMNS + [TARGET_COLUMN]].copy(), selected_scores], axis=1)
    return pca, output, selected_components


def build_variance_table(pca: PCA) -> pd.DataFrame:
    """Create one row per principal component with cumulative variance metrics."""

    component_numbers = np.arange(1, len(pca.explained_variance_ratio_) + 1)
    return pd.DataFrame(
        {
            "component": [f"PC{i:03d}" for i in component_numbers],
            "component_number": component_numbers,
            "explained_variance": pca.explained_variance_,
            "explained_variance_ratio": pca.explained_variance_ratio_,
            "cumulative_explained_variance_ratio": np.cumsum(pca.explained_variance_ratio_),
        }
    )


def build_components_table(pca: PCA, feature_columns: list[str]) -> pd.DataFrame:
    """Store PCA loadings in a feature-by-component table for later interpretation."""

    component_columns = [f"PC{i:03d}" for i in range(1, pca.components_.shape[0] + 1)]
    components = pd.DataFrame(
        pca.components_.T,
        columns=component_columns,
        index=feature_columns,
    )
    components.index.name = "feature"
    return components.reset_index()


def build_top_loadings_table(
    components: pd.DataFrame,
    selected_components: int,
    top_count: int = TOP_LOADING_COUNT,
) -> pd.DataFrame:
    """List the strongest positive/negative feature loadings for selected PCs."""

    rows: list[dict[str, object]] = []
    selected_pc_columns = [f"PC{i:03d}" for i in range(1, selected_components + 1)]
    for component in selected_pc_columns:
        ranked = components[["feature", component]].copy()
        ranked["abs_loading"] = ranked[component].abs()
        ranked = ranked.sort_values("abs_loading", ascending=False).head(top_count)
        for rank, row in enumerate(ranked.itertuples(index=False), start=1):
            loading = getattr(row, component)
            rows.append(
                {
                    "component": component,
                    "rank": rank,
                    "feature": row.feature,
                    "loading": loading,
                    "abs_loading": abs(loading),
                }
            )
    return pd.DataFrame(rows)


def save_figures(
    pca_scores: pd.DataFrame,
    variance: pd.DataFrame,
    selected_components: int,
) -> dict[str, Path]:
    """Save compact PCA diagnostics as PNG files for the report and notebook."""

    FIGURE_DIR.mkdir(parents=True, exist_ok=True)
    figure_paths = {
        "explained_variance": FIGURE_DIR / "explained_variance_ratio.png",
        "cumulative_variance": FIGURE_DIR / "cumulative_explained_variance.png",
        "pc1_pc2_target": FIGURE_DIR / "pc1_pc2_by_target.png",
    }

    plt.figure(figsize=(10, 5))
    plt.plot(
        variance["component_number"],
        variance["explained_variance_ratio"],
        marker="o",
        linewidth=1,
        markersize=3,
    )
    plt.axvline(selected_components, color="crimson", linestyle="--", linewidth=1)
    plt.title("PCA Explained Variance Ratio")
    plt.xlabel("Principal component")
    plt.ylabel("Explained variance ratio")
    plt.tight_layout()
    plt.savefig(figure_paths["explained_variance"], dpi=160)
    plt.close()

    plt.figure(figsize=(10, 5))
    plt.plot(
        variance["component_number"],
        variance["cumulative_explained_variance_ratio"],
        marker="o",
        linewidth=1,
        markersize=3,
    )
    plt.axhline(VARIANCE_THRESHOLD, color="crimson", linestyle="--", linewidth=1)
    plt.axvline(selected_components, color="crimson", linestyle="--", linewidth=1)
    plt.title("PCA Cumulative Explained Variance")
    plt.xlabel("Principal component")
    plt.ylabel("Cumulative explained variance ratio")
    plt.tight_layout()
    plt.savefig(figure_paths["cumulative_variance"], dpi=160)
    plt.close()

    if {"PC001", "PC002"}.issubset(pca_scores.columns):
        plt.figure(figsize=(7, 6))
        for target_value, group in pca_scores.groupby(TARGET_COLUMN):
            plt.scatter(
                group["PC001"],
                group["PC002"],
                s=14,
                alpha=0.45,
                label=f"{TARGET_COLUMN}={target_value}",
            )
        plt.title("PC1 vs PC2 by Sleep Target")
        plt.xlabel("PC001")
        plt.ylabel("PC002")
        plt.legend(title=TARGET_COLUMN)
        plt.tight_layout()
        plt.savefig(figure_paths["pc1_pc2_target"], dpi=160)
        plt.close()

    return figure_paths


def write_report(
    original: pd.DataFrame,
    pca_scores: pd.DataFrame,
    feature_columns: list[str],
    variance: pd.DataFrame,
    top_loadings: pd.DataFrame,
    selected_components: int,
    figure_paths: dict[str, Path],
) -> None:
    """Write a PCA report with shape checks, variance, and interpretability tables."""

    selected_variance = float(
        variance.loc[
            variance["component_number"] == selected_components,
            "cumulative_explained_variance_ratio",
        ].iloc[0]
    )
    missing_cells = int(pca_scores.isna().sum().sum())
    duplicated_keys = int(pca_scores.duplicated(KEY_COLUMNS).sum())
    target_distribution = pca_scores[TARGET_COLUMN].value_counts(dropna=False).sort_index()

    lines = [
        "# PCA Summary",
        "",
        f"- Generated at: `{datetime.now().isoformat(timespec='seconds')}`",
        f"- Input file: `{INPUT_PATH}`",
        f"- Output file: `{OUTPUT_PATH}`",
        f"- PCA model file: `{PCA_MODEL_PATH}`",
        "",
        "## Scope",
        "",
        "- This step applies PCA to scaled numeric model features.",
        "- It preserves `participant_object_id`, `calendar_date`, and `good_sleep_label`.",
        "- It does not train models.",
        "",
        "## Important Leakage Note",
        "",
        "- PCA is fit on the full current dataset for preprocessing exploration.",
        "- For final model evaluation, PCA should be fit only on training folds inside a participant-aware pipeline.",
        "",
        "## Output Shape",
        "",
        f"- Input rows: `{len(original):,}`",
        f"- Input columns: `{len(original.columns):,}`",
        f"- Input feature columns: `{len(feature_columns):,}`",
        f"- Output rows: `{len(pca_scores):,}`",
        f"- Output columns: `{len(pca_scores.columns):,}`",
        f"- Selected PC columns: `{selected_components:,}`",
        f"- Selected cumulative explained variance: `{selected_variance:.4f}`",
        f"- Output missing cells: `{missing_cells:,}`",
        f"- Duplicate participant-date rows: `{duplicated_keys:,}`",
        "",
        "## Target Distribution",
        "",
        "| good_sleep_label | rows |",
        "| ---: | ---: |",
    ]
    for target_value, count in target_distribution.items():
        lines.append(f"| {target_value} | {count:,} |")

    lines.extend(
        [
            "",
            "## Explained Variance Preview",
            "",
            "| component | explained variance ratio | cumulative explained variance ratio |",
            "| --- | ---: | ---: |",
        ]
    )
    for _, row in variance.head(20).iterrows():
        lines.append(
            f"| `{row['component']}` | {row['explained_variance_ratio']:.4f} | "
            f"{row['cumulative_explained_variance_ratio']:.4f} |"
        )

    lines.extend(
        [
            "",
            "## Top Loadings Preview",
            "",
            "| component | rank | feature | loading |",
            "| --- | ---: | --- | ---: |",
        ]
    )
    for _, row in top_loadings.head(40).iterrows():
        lines.append(
            f"| `{row['component']}` | {int(row['rank'])} | `{row['feature']}` | "
            f"{row['loading']:.4f} |"
        )

    lines.extend(
        [
            "",
            "## Figures",
            "",
        ]
    )
    for name, path in figure_paths.items():
        lines.append(f"- {name}: `{path}`")

    lines.extend(
        [
            "",
            "## Next Step",
            "",
            "```text",
            "participant-aware train/test split and baseline modeling",
            "```",
            "",
        ]
    )

    REPORT_PATH.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    df = pd.read_csv(INPUT_PATH)
    feature_columns = load_scaled_feature_columns()

    df["participant_object_id"] = df["participant_object_id"].astype(str)
    df["calendar_date"] = pd.to_datetime(df["calendar_date"], errors="coerce").dt.date.astype(str)

    validate_inputs(df, feature_columns)
    pca, pca_scores, selected_components = run_pca(df, feature_columns)
    variance = build_variance_table(pca)
    components = build_components_table(pca, feature_columns)
    top_loadings = build_top_loadings_table(components, selected_components)
    figure_paths = save_figures(pca_scores, variance, selected_components)

    if len(pca_scores) != len(df):
        raise RuntimeError("PCA changed row count.")
    if pca_scores[KEY_COLUMNS].duplicated().sum() != 0:
        raise RuntimeError("PCA output has duplicate participant-date rows.")
    if pca_scores.isna().sum().sum() != 0:
        raise RuntimeError("PCA output contains missing values.")

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    pca_scores.to_csv(OUTPUT_PATH, index=False, encoding="utf-8-sig")
    variance.to_csv(PCA_VARIANCE_PATH, index=False, encoding="utf-8-sig")
    components.to_csv(PCA_COMPONENTS_PATH, index=False, encoding="utf-8-sig")
    top_loadings.to_csv(PCA_TOP_LOADINGS_PATH, index=False, encoding="utf-8-sig")
    joblib.dump(pca, PCA_MODEL_PATH)
    write_report(
        original=df,
        pca_scores=pca_scores,
        feature_columns=feature_columns,
        variance=variance,
        top_loadings=top_loadings,
        selected_components=selected_components,
        figure_paths=figure_paths,
    )

    selected_variance = variance.loc[
        variance["component_number"] == selected_components,
        "cumulative_explained_variance_ratio",
    ].iloc[0]
    print(f"Input shape: {df.shape}")
    print(f"Output shape: {pca_scores.shape}")
    print(f"Input features: {len(feature_columns)}")
    print(f"Selected PCs: {selected_components}")
    print(f"Cumulative explained variance: {selected_variance:.4f}")
    print(f"Output missing cells: {int(pca_scores.isna().sum().sum())}")
    print(f"Wrote dataset: {OUTPUT_PATH}")
    print(f"Wrote report: {REPORT_PATH}")


if __name__ == "__main__":
    main()
