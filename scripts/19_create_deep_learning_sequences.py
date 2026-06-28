from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from sklearn.model_selection import StratifiedGroupKFold
from sklearn.preprocessing import StandardScaler


# This script creates participant-date rolling-window tensors for deep learning.
#
# Input boundary:
# - Use the daily participant-level table before PCA.
# - Reuse the participant-aware train/test assignments from script 14.
# - Split validation participants from the training participants only.
#
# Output boundary:
# - Save leakage-aware train/validation/test tensors for window-based models.
# - Sequence tensors are for 1D CNN, LSTM, and GRU experiments.
# - Flattened and endpoint tensors are included for MLP baselines.
# - This script does not train deep learning models.
PROJECT_ROOT = Path(__file__).resolve().parents[1]
INPUT_PATH = PROJECT_ROOT / "data" / "processed" / "modeling_dataset_encoded.csv"
FEATURE_COLUMNS_PATH = PROJECT_ROOT / "data" / "processed" / "encoded_feature_columns.csv"
SPLIT_ASSIGNMENTS_PATH = PROJECT_ROOT / "data" / "processed" / "splits" / "participant_split_assignments.csv"
OUTPUT_ROOT = PROJECT_ROOT / "data" / "processed" / "deep_learning_sequences"
REPORT_PATH = PROJECT_ROOT / "reports" / "deep_learning_sequence_dataset_summary.md"

KEY_COLUMNS = ["participant_object_id", "calendar_date"]
TARGET_COLUMN = "good_sleep_label"
WINDOWS = [7, 14, 30]
RANDOM_STATE = 42
VALIDATION_N_SPLITS = 5
REQUIRE_CONTIGUOUS_DATES = True


def validate_inputs(
    df: pd.DataFrame,
    feature_columns: list[str],
    assignments: pd.DataFrame,
) -> None:
    """Validate daily rows, feature columns, and participant assignments."""

    required_columns = KEY_COLUMNS + [TARGET_COLUMN]
    missing_required = [column for column in required_columns if column not in df.columns]
    if missing_required:
        raise ValueError(f"Input data is missing required columns: {missing_required}")

    missing_features = [column for column in feature_columns if column not in df.columns]
    if missing_features:
        raise ValueError(f"Input data is missing feature columns: {missing_features[:10]}")

    if df[KEY_COLUMNS].isna().any().any():
        raise ValueError("Key columns contain missing values.")

    if df[TARGET_COLUMN].isna().any():
        raise ValueError(f"{TARGET_COLUMN} contains missing values.")

    duplicate_rows = int(df.duplicated(KEY_COLUMNS).sum())
    if duplicate_rows:
        raise ValueError(f"Input contains {duplicate_rows} duplicate participant-date rows.")

    non_numeric = [
        column for column in feature_columns if not pd.api.types.is_numeric_dtype(df[column])
    ]
    if non_numeric:
        raise ValueError(f"Feature columns must be numeric: {non_numeric[:10]}")

    missing_feature_cells = int(df[feature_columns].isna().sum().sum())
    if missing_feature_cells:
        raise ValueError(f"Feature matrix contains {missing_feature_cells} missing cells.")

    if not {"participant_object_id", "split"}.issubset(assignments.columns):
        raise ValueError("Participant assignments must contain participant_object_id and split.")

    assigned_participants = set(assignments["participant_object_id"].astype(str))
    data_participants = set(df["participant_object_id"].astype(str))
    missing_assignments = sorted(data_participants - assigned_participants)
    if missing_assignments:
        raise ValueError(f"Participants missing split assignments: {missing_assignments[:5]}")


def choose_validation_participants(df: pd.DataFrame, base_assignments: pd.DataFrame) -> pd.DataFrame:
    """Create a validation split from train participants with grouped stratification."""

    assignments = base_assignments[["participant_object_id", "split"]].copy()
    assignments["participant_object_id"] = assignments["participant_object_id"].astype(str)

    split_map = assignments.set_index("participant_object_id")["split"].to_dict()
    train_df = df[df["participant_object_id"].map(split_map) == "train"].copy()
    if train_df.empty:
        raise ValueError("No training rows are available for validation split creation.")

    groups = train_df["participant_object_id"].astype(str)
    target = train_df[TARGET_COLUMN].astype(int)
    splitter = StratifiedGroupKFold(
        n_splits=VALIDATION_N_SPLITS,
        shuffle=True,
        random_state=RANDOM_STATE,
    )

    overall_target_rate = float(target.mean())
    candidate_rows: list[dict[str, float | int | set[str]]] = []
    for fold_number, (train_idx, val_idx) in enumerate(
        splitter.split(train_df, target, groups),
        start=1,
    ):
        inner_train = train_df.iloc[train_idx]
        validation = train_df.iloc[val_idx]
        validation_participants = set(validation["participant_object_id"].astype(str))
        validation_row_share = len(validation) / len(train_df)
        validation_target_rate = float(validation[TARGET_COLUMN].mean())
        score = abs(validation_row_share - 0.20) + abs(validation_target_rate - overall_target_rate)
        candidate_rows.append(
            {
                "fold": fold_number,
                "validation_participants": validation_participants,
                "train_rows": len(inner_train),
                "validation_rows": len(validation),
                "validation_row_share": validation_row_share,
                "validation_target_rate": validation_target_rate,
                "selection_score": score,
            }
        )

    best = sorted(candidate_rows, key=lambda row: float(row["selection_score"]))[0]
    validation_participants = best["validation_participants"]

    assignments["deep_learning_split"] = assignments["split"]
    assignments.loc[
        assignments["participant_object_id"].isin(validation_participants),
        "deep_learning_split",
    ] = "validation"

    return assignments


def scale_features(
    df: pd.DataFrame,
    feature_columns: list[str],
    split_assignments: pd.DataFrame,
) -> tuple[pd.DataFrame, StandardScaler]:
    """Fit the scaler on deep-learning train rows and transform all rows."""

    split_map = split_assignments.set_index("participant_object_id")["deep_learning_split"].to_dict()
    train_mask = df["participant_object_id"].map(split_map) == "train"
    if not train_mask.any():
        raise ValueError("No train rows are available for scaler fitting.")

    scaler = StandardScaler()
    scaler.fit(df.loc[train_mask, feature_columns])

    scaled = df.copy()
    scaled_values = scaler.transform(df[feature_columns]).astype(np.float32)
    scaled_features = pd.DataFrame(scaled_values, columns=feature_columns, index=df.index)
    scaled = pd.concat([scaled.drop(columns=feature_columns), scaled_features], axis=1)
    scaled = scaled[df.columns]
    return scaled, scaler


def is_contiguous_window(dates: pd.Series, start: int, end: int) -> bool:
    """Check whether a sorted row window covers consecutive calendar days."""

    if not REQUIRE_CONTIGUOUS_DATES:
        return True
    return int((dates.iloc[end] - dates.iloc[start]).days) == (end - start)


def build_window_tensors(
    df: pd.DataFrame,
    feature_columns: list[str],
    split_assignments: pd.DataFrame,
    window: int,
) -> tuple[dict[str, dict[str, np.ndarray]], pd.DataFrame]:
    """Build rolling-window tensors and sample metadata for one window length."""

    split_map = split_assignments.set_index("participant_object_id")["deep_learning_split"].to_dict()
    rows_by_split: dict[str, list[np.ndarray | int | str]] = {
        split: [] for split in ["train", "validation", "test"]
    }
    sample_rows: list[dict[str, str | int]] = []

    for participant_id, participant_df in df.groupby("participant_object_id", sort=True):
        participant_df = participant_df.sort_values("calendar_date").reset_index(drop=True)
        participant_split = split_map[str(participant_id)]
        feature_values = participant_df[feature_columns].to_numpy(dtype=np.float32)
        target_values = participant_df[TARGET_COLUMN].to_numpy(dtype=np.int64)
        dates = participant_df["calendar_date"]

        for end_idx in range(window - 1, len(participant_df)):
            start_idx = end_idx - window + 1
            if not is_contiguous_window(dates, start_idx, end_idx):
                continue

            sequence = feature_values[start_idx : end_idx + 1]
            rows_by_split[participant_split].append(
                (
                    sequence,
                    int(target_values[end_idx]),
                    str(participant_id),
                    dates.iloc[start_idx].date().isoformat(),
                    dates.iloc[end_idx].date().isoformat(),
                )
            )
            sample_rows.append(
                {
                    "window": window,
                    "split": participant_split,
                    "participant_object_id": str(participant_id),
                    "window_start_date": dates.iloc[start_idx].date().isoformat(),
                    "window_end_date": dates.iloc[end_idx].date().isoformat(),
                    "good_sleep_label": int(target_values[end_idx]),
                }
            )

    tensors: dict[str, dict[str, np.ndarray]] = {}
    for split_name, split_rows in rows_by_split.items():
        if split_rows:
            sequences, targets, participants, start_dates, end_dates = zip(*split_rows)
            x_sequence = np.stack(sequences).astype(np.float32)
            y = np.asarray(targets, dtype=np.int64)
            participant_ids = np.asarray(participants, dtype=str)
            window_start_dates = np.asarray(start_dates, dtype=str)
            window_end_dates = np.asarray(end_dates, dtype=str)
        else:
            x_sequence = np.empty((0, window, len(feature_columns)), dtype=np.float32)
            y = np.empty((0,), dtype=np.int64)
            participant_ids = np.empty((0,), dtype=str)
            window_start_dates = np.empty((0,), dtype=str)
            window_end_dates = np.empty((0,), dtype=str)

        tensors[split_name] = {
            "X_sequence": x_sequence,
            "X_mlp_flattened": x_sequence.reshape((x_sequence.shape[0], window * len(feature_columns))),
            "X_mlp_current_day": x_sequence[:, -1, :] if x_sequence.shape[0] else np.empty((0, len(feature_columns)), dtype=np.float32),
            "y": y,
            "participant_object_id": participant_ids,
            "window_start_date": window_start_dates,
            "window_end_date": window_end_dates,
            "feature_names": np.asarray(feature_columns, dtype=str),
        }

    sample_index = pd.DataFrame(sample_rows).sort_values(
        ["split", "participant_object_id", "window_end_date"]
    )
    return tensors, sample_index


def validate_tensors(
    tensors_by_window: dict[int, dict[str, dict[str, np.ndarray]]],
    split_assignments: pd.DataFrame,
) -> None:
    """Check tensor shape, missing values, and participant split leakage."""

    for window, tensors in tensors_by_window.items():
        participants_by_split: dict[str, set[str]] = {}
        for split_name, arrays in tensors.items():
            x_sequence = arrays["X_sequence"]
            y = arrays["y"]
            if x_sequence.ndim != 3:
                raise RuntimeError(f"{split_name} window {window} X_sequence is not 3D.")
            if x_sequence.shape[0] != len(y):
                raise RuntimeError(f"{split_name} window {window} X/y row count mismatch.")
            if x_sequence.shape[1] != window:
                raise RuntimeError(f"{split_name} window {window} has wrong time dimension.")
            if np.isnan(x_sequence).any():
                raise RuntimeError(f"{split_name} window {window} contains NaN feature values.")
            participants_by_split[split_name] = set(arrays["participant_object_id"].astype(str))

        split_names = ["train", "validation", "test"]
        for left_idx, left_name in enumerate(split_names):
            for right_name in split_names[left_idx + 1 :]:
                overlap = participants_by_split[left_name] & participants_by_split[right_name]
                if overlap:
                    raise RuntimeError(
                        f"Participant overlap for window {window} between "
                        f"{left_name} and {right_name}: {sorted(overlap)[:5]}"
                    )

    expected_splits = {"train", "validation", "test"}
    observed_splits = set(split_assignments["deep_learning_split"].unique())
    if observed_splits != expected_splits:
        raise RuntimeError(f"Unexpected deep learning splits: {sorted(observed_splits)}")


def save_outputs(
    tensors_by_window: dict[int, dict[str, dict[str, np.ndarray]]],
    sample_indices: dict[int, pd.DataFrame],
    feature_columns: list[str],
    split_assignments: pd.DataFrame,
    scaler: StandardScaler,
) -> pd.DataFrame:
    """Write tensors, per-window metadata, feature columns, and scaler."""

    OUTPUT_ROOT.mkdir(parents=True, exist_ok=True)
    feature_table = pd.DataFrame({"feature": feature_columns})
    feature_table.to_csv(OUTPUT_ROOT / "feature_columns.csv", index=False, encoding="utf-8-sig")
    split_assignments.to_csv(
        OUTPUT_ROOT / "deep_learning_participant_split_assignments.csv",
        index=False,
        encoding="utf-8-sig",
    )
    joblib.dump(scaler, OUTPUT_ROOT / "deep_learning_standard_scaler.joblib")

    summary_rows: list[dict[str, float | int | str]] = []
    for window, tensors in tensors_by_window.items():
        window_dir = OUTPUT_ROOT / f"window_{window}"
        window_dir.mkdir(parents=True, exist_ok=True)

        sample_index = sample_indices[window]
        sample_index.to_csv(window_dir / "sample_index.csv", index=False, encoding="utf-8-sig")

        for split_name, arrays in tensors.items():
            np.savez_compressed(window_dir / f"{split_name}.npz", **arrays)
            y = arrays["y"]
            class_0 = int((y == 0).sum())
            class_1 = int((y == 1).sum())
            participants = int(len(set(arrays["participant_object_id"].astype(str))))
            target_rate = float(y.mean()) if len(y) else float("nan")
            summary_rows.append(
                {
                    "window": window,
                    "split": split_name,
                    "samples": int(len(y)),
                    "participants": participants,
                    "features": len(feature_columns),
                    "sequence_shape": " x ".join(map(str, arrays["X_sequence"].shape)),
                    "mlp_flattened_shape": " x ".join(map(str, arrays["X_mlp_flattened"].shape)),
                    "mlp_current_day_shape": " x ".join(map(str, arrays["X_mlp_current_day"].shape)),
                    "class_0_samples": class_0,
                    "class_1_samples": class_1,
                    "good_sleep_label_mean": target_rate,
                    "tensor_path": str(window_dir / f"{split_name}.npz"),
                }
            )

        metadata = {
            "window": window,
            "created_at": datetime.now().isoformat(timespec="seconds"),
            "input_path": str(INPUT_PATH),
            "feature_columns_path": str(FEATURE_COLUMNS_PATH),
            "split_assignments_path": str(SPLIT_ASSIGNMENTS_PATH),
            "require_contiguous_dates": REQUIRE_CONTIGUOUS_DATES,
            "feature_count": len(feature_columns),
            "sample_index_path": str(window_dir / "sample_index.csv"),
            "tensor_files": {
                split_name: str(window_dir / f"{split_name}.npz")
                for split_name in ["train", "validation", "test"]
            },
        }
        (window_dir / "metadata.json").write_text(
            json.dumps(metadata, indent=2),
            encoding="utf-8",
        )

    summary = pd.DataFrame(summary_rows).sort_values(["window", "split"])
    summary.to_csv(OUTPUT_ROOT / "sequence_tensor_summary.csv", index=False, encoding="utf-8-sig")
    return summary


def write_report(
    df: pd.DataFrame,
    feature_columns: list[str],
    split_assignments: pd.DataFrame,
    tensor_summary: pd.DataFrame,
) -> None:
    """Write a human-readable summary for the sequence dataset creation step."""

    split_rows = (
        df.assign(
            deep_learning_split=df["participant_object_id"].map(
                split_assignments.set_index("participant_object_id")["deep_learning_split"].to_dict()
            )
        )
        .groupby("deep_learning_split")
        .agg(
            rows=(TARGET_COLUMN, "size"),
            participants=("participant_object_id", "nunique"),
            target_mean=(TARGET_COLUMN, "mean"),
        )
        .reset_index()
    )

    lines = [
        "# Deep Learning Sequence Dataset Summary",
        "",
        f"- Generated at: `{datetime.now().isoformat(timespec='seconds')}`",
        f"- Input file: `{INPUT_PATH}`",
        f"- Feature column file: `{FEATURE_COLUMNS_PATH}`",
        f"- Base participant split file: `{SPLIT_ASSIGNMENTS_PATH}`",
        f"- Output directory: `{OUTPUT_ROOT}`",
        "",
        "## Scope",
        "",
        "- This step creates deep-learning tensors from participant-date daily data before PCA.",
        "- Rows are sorted by `participant_object_id` and `calendar_date` before windowing.",
        "- PCA outputs are not used as model inputs in this step.",
        "- Logistic Regression and Random Forest remain traditional ML baseline/reference only.",
        "- Validation participants are split from the original training participants.",
        "- Feature scaling is fit on deep-learning train rows only, then applied to validation/test rows.",
        "",
        "## Windowing",
        "",
        f"- Windows: `{WINDOWS}` days",
        f"- Require contiguous calendar dates: `{REQUIRE_CONTIGUOUS_DATES}`",
        f"- Feature count: `{len(feature_columns):,}`",
        "",
        "Each `.npz` file contains:",
        "",
        "- `X_sequence`: samples x time_steps x features for 1D CNN, LSTM, and GRU.",
        "- `X_mlp_flattened`: samples x (time_steps * features) for a window-flattened MLP.",
        "- `X_mlp_current_day`: samples x features for a daily tabular MLP baseline at the window endpoint.",
        "- `y`, `participant_object_id`, `window_start_date`, `window_end_date`, and `feature_names`.",
        "",
        "## Daily Row Split Summary",
        "",
        "| split | rows | participants | good_sleep_label mean |",
        "| --- | ---: | ---: | ---: |",
    ]

    for _, row in split_rows.sort_values("deep_learning_split").iterrows():
        lines.append(
            f"| {row['deep_learning_split']} | {int(row['rows']):,} | "
            f"{int(row['participants']):,} | {row['target_mean']:.4f} |"
        )

    lines.extend(
        [
            "",
            "## Tensor Summary",
            "",
            "| window | split | samples | participants | sequence shape | MLP flattened shape | MLP current-day shape | class 0 | class 1 | target mean |",
            "| ---: | --- | ---: | ---: | --- | --- | --- | ---: | ---: | ---: |",
        ]
    )

    for _, row in tensor_summary.iterrows():
        target_mean = row["good_sleep_label_mean"]
        target_text = "nan" if pd.isna(target_mean) else f"{target_mean:.4f}"
        lines.append(
            f"| {int(row['window'])} | {row['split']} | {int(row['samples']):,} | "
            f"{int(row['participants']):,} | `{row['sequence_shape']}` | "
            f"`{row['mlp_flattened_shape']}` | `{row['mlp_current_day_shape']}` | "
            f"{int(row['class_0_samples']):,} | {int(row['class_1_samples']):,} | {target_text} |"
        )

    lines.extend(
        [
            "",
            "## Output Files",
            "",
            f"- Feature columns: `{OUTPUT_ROOT / 'feature_columns.csv'}`",
            f"- Deep-learning participant split assignments: `{OUTPUT_ROOT / 'deep_learning_participant_split_assignments.csv'}`",
            f"- Train-only scaler: `{OUTPUT_ROOT / 'deep_learning_standard_scaler.joblib'}`",
            f"- Tensor summary: `{OUTPUT_ROOT / 'sequence_tensor_summary.csv'}`",
            "",
        ]
    )

    for window in WINDOWS:
        lines.extend(
            [
                f"### Window {window}",
                "",
                f"- Train tensors: `{OUTPUT_ROOT / f'window_{window}' / 'train.npz'}`",
                f"- Validation tensors: `{OUTPUT_ROOT / f'window_{window}' / 'validation.npz'}`",
                f"- Test tensors: `{OUTPUT_ROOT / f'window_{window}' / 'test.npz'}`",
                f"- Sample index: `{OUTPUT_ROOT / f'window_{window}' / 'sample_index.csv'}`",
                "",
            ]
        )

    lines.extend(
        [
            "## Next Step",
            "",
            "```text",
            "Train MLP / 1D CNN / LSTM / GRU deep learning experiments using these tensors.",
            "```",
            "",
        ]
    )

    REPORT_PATH.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    df = pd.read_csv(INPUT_PATH)
    feature_metadata = pd.read_csv(FEATURE_COLUMNS_PATH)
    base_assignments = pd.read_csv(SPLIT_ASSIGNMENTS_PATH)

    feature_columns = feature_metadata["feature"].tolist()
    df["participant_object_id"] = df["participant_object_id"].astype(str)
    df["calendar_date"] = pd.to_datetime(df["calendar_date"], errors="coerce")
    base_assignments["participant_object_id"] = base_assignments["participant_object_id"].astype(str)

    df = df.sort_values(["participant_object_id", "calendar_date"]).reset_index(drop=True)
    validate_inputs(df, feature_columns, base_assignments)

    split_assignments = choose_validation_participants(df, base_assignments)
    scaled_df, scaler = scale_features(df, feature_columns, split_assignments)

    tensors_by_window: dict[int, dict[str, dict[str, np.ndarray]]] = {}
    sample_indices: dict[int, pd.DataFrame] = {}
    for window in WINDOWS:
        tensors, sample_index = build_window_tensors(
            scaled_df,
            feature_columns,
            split_assignments,
            window,
        )
        tensors_by_window[window] = tensors
        sample_indices[window] = sample_index

    validate_tensors(tensors_by_window, split_assignments)
    tensor_summary = save_outputs(
        tensors_by_window,
        sample_indices,
        feature_columns,
        split_assignments,
        scaler,
    )

    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    write_report(df, feature_columns, split_assignments, tensor_summary)

    print(f"Input shape: {df.shape}")
    print(f"Feature count: {len(feature_columns)}")
    print(f"Output directory: {OUTPUT_ROOT}")
    print(tensor_summary[["window", "split", "samples", "participants", "sequence_shape"]].to_string(index=False))
    print(f"Wrote report: {REPORT_PATH}")


if __name__ == "__main__":
    main()
