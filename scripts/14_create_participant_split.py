from __future__ import annotations

from datetime import datetime
from pathlib import Path

import pandas as pd
from sklearn.model_selection import StratifiedGroupKFold


# This script creates the participant-aware train/test split for modeling.
#
# Split unit:
# - Each row is a participant-day observation.
# - All rows from the same participant stay in the same split.
# - The target is good_sleep_label.
#
# Boundary:
# - This script does not scale, run PCA, or train models.
# - It writes split assignments that downstream modeling scripts can reuse.
PROJECT_ROOT = Path(__file__).resolve().parents[1]
INPUT_PATH = PROJECT_ROOT / "data" / "processed" / "modeling_dataset_encoded.csv"
OUTPUT_DIR = PROJECT_ROOT / "data" / "processed" / "splits"
TRAIN_PATH = OUTPUT_DIR / "train_participant_split.csv"
TEST_PATH = OUTPUT_DIR / "test_participant_split.csv"
ASSIGNMENTS_PATH = OUTPUT_DIR / "participant_split_assignments.csv"
REPORT_PATH = PROJECT_ROOT / "reports" / "participant_split_summary.md"

KEY_COLUMNS = ["participant_object_id", "calendar_date"]
TARGET_COLUMN = "good_sleep_label"
RANDOM_STATE = 42
N_SPLITS = 5


def validate_input(df: pd.DataFrame) -> None:
    """Validate key and target columns before assigning participant splits."""

    required_columns = KEY_COLUMNS + [TARGET_COLUMN]
    missing = [column for column in required_columns if column not in df.columns]
    if missing:
        raise ValueError(f"Required columns missing from input: {missing}")

    if df[KEY_COLUMNS].isna().any().any():
        raise ValueError("Key columns contain missing values.")

    if df[TARGET_COLUMN].isna().any():
        raise ValueError(f"{TARGET_COLUMN} contains missing values.")

    target_values = sorted(df[TARGET_COLUMN].unique().tolist())
    if target_values != [0, 1]:
        raise ValueError(f"{TARGET_COLUMN} should be binary 0/1, got {target_values}")

    duplicated_keys = int(df.duplicated(KEY_COLUMNS).sum())
    if duplicated_keys:
        raise ValueError(f"Input contains {duplicated_keys} duplicate participant-date rows.")


def choose_best_fold(df: pd.DataFrame) -> tuple[pd.Index, pd.Index, pd.DataFrame]:
    """Use stratified grouped folds and choose the fold closest to a 20% test split."""

    groups = df["participant_object_id"].astype(str)
    target = df[TARGET_COLUMN].astype(int)
    splitter = StratifiedGroupKFold(
        n_splits=N_SPLITS,
        shuffle=True,
        random_state=RANDOM_STATE,
    )

    overall_target_rate = float(target.mean())
    fold_rows: list[dict[str, float | int]] = []
    fold_indices: list[tuple[pd.Index, pd.Index]] = []

    for fold_number, (train_idx, test_idx) in enumerate(
        splitter.split(df, target, groups),
        start=1,
    ):
        train_index = df.index[train_idx]
        test_index = df.index[test_idx]
        train = df.loc[train_index]
        test = df.loc[test_index]

        # The score favors a test row share close to 20% and a target rate close
        # to the full dataset. Participant counts are recorded for diagnostics.
        test_row_share = len(test) / len(df)
        test_target_rate = float(test[TARGET_COLUMN].mean())
        train_target_rate = float(train[TARGET_COLUMN].mean())
        score = abs(test_row_share - 0.20) + abs(test_target_rate - overall_target_rate)

        fold_rows.append(
            {
                "fold": fold_number,
                "train_rows": len(train),
                "test_rows": len(test),
                "train_participants": train["participant_object_id"].nunique(),
                "test_participants": test["participant_object_id"].nunique(),
                "test_row_share": test_row_share,
                "train_target_rate": train_target_rate,
                "test_target_rate": test_target_rate,
                "overall_target_rate": overall_target_rate,
                "selection_score": score,
            }
        )
        fold_indices.append((train_index, test_index))

    fold_summary = pd.DataFrame(fold_rows).sort_values("selection_score", ascending=True)
    best_fold_number = int(fold_summary.iloc[0]["fold"])
    return (*fold_indices[best_fold_number - 1], fold_summary.sort_values("fold"))


def build_split_outputs(
    df: pd.DataFrame,
    train_index: pd.Index,
    test_index: pd.Index,
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """Add split labels and return train/test tables plus participant assignments."""

    split_df = df.copy()
    split_df["split"] = "train"
    split_df.loc[test_index, "split"] = "test"

    train = split_df.loc[train_index].copy()
    test = split_df.loc[test_index].copy()

    assignments = (
        split_df.groupby("participant_object_id", as_index=False)
        .agg(
            split=("split", "first"),
            rows=("calendar_date", "size"),
            first_date=("calendar_date", "min"),
            last_date=("calendar_date", "max"),
            target_mean=(TARGET_COLUMN, "mean"),
            target_positive_rows=(TARGET_COLUMN, "sum"),
        )
        .sort_values(["split", "participant_object_id"])
    )
    return train, test, assignments


def validate_split(train: pd.DataFrame, test: pd.DataFrame) -> None:
    """Ensure participants do not overlap and target classes exist in both splits."""

    train_participants = set(train["participant_object_id"].astype(str))
    test_participants = set(test["participant_object_id"].astype(str))
    overlap = train_participants & test_participants
    if overlap:
        raise RuntimeError(f"Participant overlap between train and test: {sorted(overlap)[:5]}")

    for split_name, split_df in [("train", train), ("test", test)]:
        target_values = sorted(split_df[TARGET_COLUMN].unique().tolist())
        if target_values != [0, 1]:
            raise RuntimeError(f"{split_name} split does not contain both target classes.")


def write_report(
    df: pd.DataFrame,
    train: pd.DataFrame,
    test: pd.DataFrame,
    assignments: pd.DataFrame,
    fold_summary: pd.DataFrame,
) -> None:
    """Write the split report with balance and leakage checks."""

    train_participants = train["participant_object_id"].nunique()
    test_participants = test["participant_object_id"].nunique()
    participant_overlap = len(
        set(train["participant_object_id"].astype(str))
        & set(test["participant_object_id"].astype(str))
    )

    lines = [
        "# Participant-Aware Split Summary",
        "",
        f"- Generated at: `{datetime.now().isoformat(timespec='seconds')}`",
        f"- Input file: `{INPUT_PATH}`",
        f"- Train output: `{TRAIN_PATH}`",
        f"- Test output: `{TEST_PATH}`",
        f"- Participant assignments: `{ASSIGNMENTS_PATH}`",
        "",
        "## Scope",
        "",
        "- This step creates a participant-aware train/test split.",
        "- Every participant belongs to exactly one split.",
        "- The split is selected from stratified grouped folds to keep the target distribution reasonably balanced.",
        "",
        "## Split Summary",
        "",
        "| split | rows | participants | good_sleep_label mean | class 0 rows | class 1 rows |",
        "| --- | ---: | ---: | ---: | ---: | ---: |",
    ]

    for split_name, split_df in [("train", train), ("test", test), ("all", df)]:
        class_counts = split_df[TARGET_COLUMN].value_counts().to_dict()
        participants = split_df["participant_object_id"].nunique()
        lines.append(
            f"| {split_name} | {len(split_df):,} | {participants:,} | "
            f"{split_df[TARGET_COLUMN].mean():.4f} | "
            f"{int(class_counts.get(0, 0)):,} | {int(class_counts.get(1, 0)):,} |"
        )

    lines.extend(
        [
            "",
            "## Leakage Checks",
            "",
            f"- Participant overlap between train and test: `{participant_overlap}`",
            f"- Train duplicate participant-date rows: `{int(train.duplicated(KEY_COLUMNS).sum()):,}`",
            f"- Test duplicate participant-date rows: `{int(test.duplicated(KEY_COLUMNS).sum()):,}`",
            f"- Train participants: `{train_participants:,}`",
            f"- Test participants: `{test_participants:,}`",
            "",
            "## Candidate Fold Diagnostics",
            "",
            "| fold | train rows | test rows | train participants | test participants | test row share | train target rate | test target rate | score |",
            "| ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |",
        ]
    )

    for _, row in fold_summary.iterrows():
        lines.append(
            f"| {int(row['fold'])} | {int(row['train_rows']):,} | {int(row['test_rows']):,} | "
            f"{int(row['train_participants']):,} | {int(row['test_participants']):,} | "
            f"{row['test_row_share']:.4f} | {row['train_target_rate']:.4f} | "
            f"{row['test_target_rate']:.4f} | {row['selection_score']:.4f} |"
        )

    lines.extend(
        [
            "",
            "## Participant Assignment Preview",
            "",
            "| participant_object_id | split | rows | target mean | first date | last date |",
            "| --- | --- | ---: | ---: | --- | --- |",
        ]
    )
    for _, row in assignments.head(20).iterrows():
        lines.append(
            f"| `{row['participant_object_id']}` | {row['split']} | {int(row['rows']):,} | "
            f"{row['target_mean']:.4f} | {row['first_date']} | {row['last_date']} |"
        )

    lines.extend(
        [
            "",
            "## Next Step",
            "",
            "```text",
            "baseline modeling",
            "```",
            "",
        ]
    )

    REPORT_PATH.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    df = pd.read_csv(INPUT_PATH)
    df["participant_object_id"] = df["participant_object_id"].astype(str)
    df["calendar_date"] = pd.to_datetime(df["calendar_date"], errors="coerce").dt.date.astype(str)

    validate_input(df)
    train_index, test_index, fold_summary = choose_best_fold(df)
    train, test, assignments = build_split_outputs(df, train_index, test_index)
    validate_split(train, test)

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    train.to_csv(TRAIN_PATH, index=False, encoding="utf-8-sig")
    test.to_csv(TEST_PATH, index=False, encoding="utf-8-sig")
    assignments.to_csv(ASSIGNMENTS_PATH, index=False, encoding="utf-8-sig")
    write_report(df, train, test, assignments, fold_summary)

    print(f"Input shape: {df.shape}")
    print(f"Train shape: {train.shape}")
    print(f"Test shape: {test.shape}")
    print(f"Train participants: {train['participant_object_id'].nunique()}")
    print(f"Test participants: {test['participant_object_id'].nunique()}")
    print(f"Participant overlap: {len(set(train['participant_object_id']) & set(test['participant_object_id']))}")
    print(f"Train target mean: {train[TARGET_COLUMN].mean():.4f}")
    print(f"Test target mean: {test[TARGET_COLUMN].mean():.4f}")
    print(f"Wrote train split: {TRAIN_PATH}")
    print(f"Wrote test split: {TEST_PATH}")
    print(f"Wrote report: {REPORT_PATH}")


if __name__ == "__main__":
    main()
