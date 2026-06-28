# -*- coding: utf-8 -*-
"""
Feature subset별 deep learning sequence tensor 생성 스크립트.

입력:
- data/processed/modeling_dataset_encoded.csv
- data/processed/deep_learning_sequences/deep_learning_participant_split_assignments.csv
- data/processed/deep_learning_feature_subsets/*_features.csv

출력:
- data/processed/deep_learning_sequences_by_subset/{subset_name}/window_{7,14,30}/
"""

from pathlib import Path
import json

import joblib
import numpy as np
import pandas as pd
from sklearn.preprocessing import StandardScaler


PROJECT_ROOT = Path(r"c:\workSpace\DeepLearnin_sleep")
PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"

DATA_PATH = PROCESSED_DIR / "modeling_dataset_encoded.csv"
SPLIT_PATH = PROCESSED_DIR / "deep_learning_sequences" / "deep_learning_participant_split_assignments.csv"
SUBSET_DIR = PROCESSED_DIR / "deep_learning_feature_subsets"
OUTPUT_ROOT = PROCESSED_DIR / "deep_learning_sequences_by_subset"

WINDOW_SIZES = [7, 14, 30]
TARGET_COL = "good_sleep_label"
ID_COL = "participant_object_id"
DATE_COL = "calendar_date"
SPLIT_COL = "deep_learning_split"


def load_inputs():
    df = pd.read_csv(DATA_PATH, encoding="utf-8-sig")
    split_df = pd.read_csv(SPLIT_PATH, encoding="utf-8-sig")

    split_df = split_df[[ID_COL, SPLIT_COL]].drop_duplicates()
    df = df.merge(split_df, on=ID_COL, how="left")

    df[DATE_COL] = pd.to_datetime(df[DATE_COL])
    df = df.sort_values([ID_COL, DATE_COL]).reset_index(drop=True)

    if df[SPLIT_COL].isna().any():
        missing_count = int(df[SPLIT_COL].isna().sum())
        raise ValueError(f"split이 없는 row가 있습니다: {missing_count}")

    return df


def load_feature_subsets():
    subset_paths = sorted(SUBSET_DIR.glob("*_features.csv"))

    if not subset_paths:
        raise FileNotFoundError(f"feature subset CSV를 찾지 못했습니다: {SUBSET_DIR}")

    subsets = {}

    for path in subset_paths:
        subset_name = path.name.replace("_features.csv", "")
        subset_df = pd.read_csv(path, encoding="utf-8-sig")

        if "feature" not in subset_df.columns:
            raise ValueError(f"{path} 파일에 feature 컬럼이 없습니다.")

        features = subset_df["feature"].tolist()
        subsets[subset_name] = features

    return subsets


def validate_features(df, subsets):
    available = set(df.columns)

    for subset_name, features in subsets.items():
        missing = [feature for feature in features if feature not in available]
        if missing:
            raise ValueError(
                f"{subset_name} subset에 현재 데이터에 없는 feature가 있습니다: {missing[:20]}"
            )


def scale_subset_features(df, features):
    result = df.copy()

    train_mask = result[SPLIT_COL] == "train"

    scaler = StandardScaler()
    scaler.fit(result.loc[train_mask, features])

    result.loc[:, features] = scaler.transform(result[features]).astype(np.float32)

    return result, scaler


def build_windows_for_split(df, features, split_name, window_size):
    split_df = df[df[SPLIT_COL] == split_name].copy()
    split_df = split_df.sort_values([ID_COL, DATE_COL])

    X_sequence = []
    X_mlp_flattened = []
    X_mlp_current_day = []
    y = []
    participant_ids = []
    window_start_dates = []
    window_end_dates = []

    for participant_id, group in split_df.groupby(ID_COL, sort=False):
        group = group.sort_values(DATE_COL).reset_index(drop=True)

        feature_values = group[features].to_numpy(dtype=np.float32)
        target_values = group[TARGET_COL].to_numpy(dtype=np.int64)
        date_values = group[DATE_COL].to_numpy()

        for end_idx in range(window_size - 1, len(group)):
            start_idx = end_idx - window_size + 1

            window_dates = pd.to_datetime(date_values[start_idx : end_idx + 1])
            expected_dates = pd.date_range(
                start=window_dates[0],
                periods=window_size,
                freq="D",
            )

            if not np.array_equal(window_dates.to_numpy(), expected_dates.to_numpy()):
                continue

            window_x = feature_values[start_idx : end_idx + 1]

            X_sequence.append(window_x)
            X_mlp_flattened.append(window_x.reshape(-1))
            X_mlp_current_day.append(window_x[-1])
            y.append(target_values[end_idx])
            participant_ids.append(participant_id)
            window_start_dates.append(str(pd.Timestamp(window_dates[0]).date()))
            window_end_dates.append(str(pd.Timestamp(window_dates[-1]).date()))

    if X_sequence:
        X_sequence = np.stack(X_sequence).astype(np.float32)
        X_mlp_flattened = np.stack(X_mlp_flattened).astype(np.float32)
        X_mlp_current_day = np.stack(X_mlp_current_day).astype(np.float32)
        y = np.asarray(y, dtype=np.int64)
    else:
        X_sequence = np.empty((0, window_size, len(features)), dtype=np.float32)
        X_mlp_flattened = np.empty((0, window_size * len(features)), dtype=np.float32)
        X_mlp_current_day = np.empty((0, len(features)), dtype=np.float32)
        y = np.empty((0,), dtype=np.int64)

    return {
        "X_sequence": X_sequence,
        "X_mlp_flattened": X_mlp_flattened,
        "X_mlp_current_day": X_mlp_current_day,
        "y": y,
        "participant_object_id": np.asarray(participant_ids, dtype=object),
        "window_start_date": np.asarray(window_start_dates, dtype=object),
        "window_end_date": np.asarray(window_end_dates, dtype=object),
        "feature_names": np.asarray(features, dtype=object),
    }


def save_split_arrays(output_dir, split_name, arrays):
    output_dir.mkdir(parents=True, exist_ok=True)

    npz_path = output_dir / f"{split_name}.npz"
    np.savez_compressed(npz_path, **arrays)

    sample_index = pd.DataFrame({
        "split": split_name,
        "participant_object_id": arrays["participant_object_id"],
        "window_start_date": arrays["window_start_date"],
        "window_end_date": arrays["window_end_date"],
        "good_sleep_label": arrays["y"],
    })

    return npz_path, sample_index


def main():
    df = load_inputs()
    subsets = load_feature_subsets()
    validate_features(df, subsets)

    OUTPUT_ROOT.mkdir(parents=True, exist_ok=True)

    summary_rows = []

    for subset_name, features in subsets.items():
        print(f"\n=== subset: {subset_name} ({len(features)} features) ===")

        scaled_df, scaler = scale_subset_features(df, features)

        subset_root = OUTPUT_ROOT / subset_name
        subset_root.mkdir(parents=True, exist_ok=True)

        joblib.dump(scaler, subset_root / "standard_scaler.joblib")

        pd.DataFrame({"feature": features}).to_csv(
            subset_root / "feature_columns.csv",
            index=False,
            encoding="utf-8-sig",
        )

        for window_size in WINDOW_SIZES:
            window_dir = subset_root / f"window_{window_size}"
            all_sample_index = []

            for split_name in ["train", "validation", "test"]:
                arrays = build_windows_for_split(
                    scaled_df,
                    features,
                    split_name,
                    window_size,
                )

                npz_path, sample_index = save_split_arrays(
                    window_dir,
                    split_name,
                    arrays,
                )
                all_sample_index.append(sample_index)

                y = arrays["y"]
                class_0 = int((y == 0).sum())
                class_1 = int((y == 1).sum())

                summary_rows.append({
                    "subset_name": subset_name,
                    "window": window_size,
                    "split": split_name,
                    "samples": int(len(y)),
                    "participants": int(len(set(arrays["participant_object_id"]))),
                    "features": int(len(features)),
                    "sequence_shape": " x ".join(map(str, arrays["X_sequence"].shape)),
                    "mlp_flattened_shape": " x ".join(map(str, arrays["X_mlp_flattened"].shape)),
                    "mlp_current_day_shape": " x ".join(map(str, arrays["X_mlp_current_day"].shape)),
                    "class_0_samples": class_0,
                    "class_1_samples": class_1,
                    "good_sleep_label_mean": float(y.mean()) if len(y) else np.nan,
                    "tensor_path": str(npz_path),
                })

                print(
                    f"window={window_size:>2} split={split_name:<10} "
                    f"samples={len(y):>4} shape={arrays['X_sequence'].shape}"
                )

            pd.concat(all_sample_index, ignore_index=True).to_csv(
                window_dir / "sample_index.csv",
                index=False,
                encoding="utf-8-sig",
            )

        metadata = {
            "subset_name": subset_name,
            "feature_count": len(features),
            "windows": WINDOW_SIZES,
            "target_col": TARGET_COL,
            "id_col": ID_COL,
            "date_col": DATE_COL,
            "split_col": SPLIT_COL,
            "source_data": str(DATA_PATH),
            "source_split": str(SPLIT_PATH),
        }

        with open(subset_root / "metadata.json", "w", encoding="utf-8") as f:
            json.dump(metadata, f, ensure_ascii=False, indent=2)

    summary = pd.DataFrame(summary_rows)
    summary.to_csv(
        OUTPUT_ROOT / "sequence_tensor_summary_by_subset.csv",
        index=False,
        encoding="utf-8-sig",
    )

    print("\n저장 완료:")
    print(OUTPUT_ROOT)
    print(summary)


if __name__ == "__main__":
    main()