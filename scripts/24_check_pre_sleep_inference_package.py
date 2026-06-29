from __future__ import annotations

import argparse
import importlib
import json
import py_compile
import sys
from datetime import datetime
from pathlib import Path

import numpy as np
import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = PROJECT_ROOT / "src"

INFERENCE_PACKAGE_DIR = (
    PROJECT_ROOT
    / "data"
    / "processed"
    / "pre_sleep_forecasting"
    / "design_c_stage1"
    / "inference_package"
)

MANIFEST_PATH = INFERENCE_PACKAGE_DIR / "pre_sleep_inference_manifest.json"
FEATURE_CONTRACT_PATH = INFERENCE_PACKAGE_DIR / "pre_sleep_inference_feature_contract.csv"
DOC_PATH = PROJECT_ROOT / "docs" / "pre_sleep_inference_usage.md"
REPORT_PATH = PROJECT_ROOT / "reports" / "pre_sleep_inference_package_qa.md"

SMOKE_RAW_FEATURE_PATH = (
    PROJECT_ROOT
    / "data"
    / "processed"
    / "pre_sleep_forecasting"
    / "new_data"
    / "raw_stage1_features.csv"
)
SMOKE_PREDICTION_PATH = (
    PROJECT_ROOT
    / "data"
    / "processed"
    / "pre_sleep_forecasting"
    / "new_data"
    / "predictions.csv"
)

REQUIRED_SOURCE_FILES = [
    PROJECT_ROOT / "src" / "pre_sleep_forecasting" / "feature_builder.py",
    PROJECT_ROOT / "src" / "pre_sleep_forecasting" / "inference.py",
    PROJECT_ROOT / "src" / "pre_sleep_forecasting" / "__init__.py",
]


def add_result(results: list[dict], check: str, passed: bool, detail: str) -> None:
    results.append(
        {
            "check": check,
            "passed": bool(passed),
            "detail": detail,
        }
    )


def load_manifest() -> dict:
    return json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))


def check_required_files(results: list[dict]) -> None:
    for path in REQUIRED_SOURCE_FILES + [MANIFEST_PATH, FEATURE_CONTRACT_PATH, DOC_PATH]:
        add_result(
            results,
            f"file_exists:{path.relative_to(PROJECT_ROOT)}",
            path.exists(),
            str(path),
        )


def check_py_compile(results: list[dict]) -> None:
    for path in REQUIRED_SOURCE_FILES[:2]:
        try:
            py_compile.compile(str(path), doraise=True)
        except py_compile.PyCompileError as exc:
            add_result(results, f"py_compile:{path.name}", False, str(exc))
        else:
            add_result(results, f"py_compile:{path.name}", True, "ok")


def check_imports(results: list[dict]) -> None:
    if str(SRC_DIR) not in sys.path:
        sys.path.insert(0, str(SRC_DIR))

    modules = [
        "pre_sleep_forecasting.feature_builder",
        "pre_sleep_forecasting.inference",
    ]
    for module_name in modules:
        try:
            module = importlib.import_module(module_name)
        except Exception as exc:
            add_result(results, f"import:{module_name}", False, repr(exc))
        else:
            add_result(results, f"import:{module_name}", True, str(Path(module.__file__)))


def check_manifest_artifacts(results: list[dict], manifest: dict) -> None:
    artifact_paths = manifest.get("artifact_paths", {})
    for artifact_name, relative_path in artifact_paths.items():
        path = PROJECT_ROOT / relative_path
        add_result(
            results,
            f"artifact_exists:{artifact_name}",
            path.exists(),
            str(path),
        )


def check_feature_contract(results: list[dict], manifest: dict) -> None:
    contract_df = pd.read_csv(FEATURE_CONTRACT_PATH, encoding="utf-8-sig")
    raw_features = manifest["raw_feature_order"]
    removed_features = set(manifest["zero_variance_removed_features"])
    final_features = manifest["final_model_feature_order"]

    add_result(results, "contract_rows", len(contract_df) == 70, f"rows={len(contract_df)}")
    add_result(
        results,
        "contract_duplicate_features",
        contract_df["feature"].duplicated().sum() == 0,
        f"duplicates={int(contract_df['feature'].duplicated().sum())}",
    )
    add_result(
        results,
        "manifest_raw_feature_count",
        len(raw_features) == 70,
        f"raw={len(raw_features)}",
    )
    add_result(
        results,
        "manifest_removed_feature_count",
        len(removed_features) == 12,
        f"removed={len(removed_features)}",
    )
    add_result(
        results,
        "manifest_final_feature_count",
        len(final_features) == 58,
        f"final={len(final_features)}",
    )

    computed_final = [feature for feature in raw_features if feature not in removed_features]
    add_result(
        results,
        "computed_final_matches_manifest",
        computed_final == final_features,
        f"computed={len(computed_final)}, manifest={len(final_features)}",
    )
    add_result(
        results,
        "contract_order_matches_manifest",
        contract_df["feature"].tolist() == raw_features,
        "contract feature order compared with manifest raw_feature_order",
    )


def check_smoke_outputs(results: list[dict], manifest: dict, run_pipeline: bool) -> None:
    raw_features = manifest["raw_feature_order"]
    official_threshold = float(manifest["official_threshold"])

    add_result(
        results,
        "smoke_raw_feature_file_exists",
        SMOKE_RAW_FEATURE_PATH.exists(),
        str(SMOKE_RAW_FEATURE_PATH),
    )
    add_result(
        results,
        "smoke_prediction_file_exists",
        SMOKE_PREDICTION_PATH.exists(),
        str(SMOKE_PREDICTION_PATH),
    )

    if not SMOKE_RAW_FEATURE_PATH.exists() or not SMOKE_PREDICTION_PATH.exists():
        return

    raw_df = pd.read_csv(SMOKE_RAW_FEATURE_PATH, encoding="utf-8-sig")
    pred_df = pd.read_csv(SMOKE_PREDICTION_PATH, encoding="utf-8-sig")

    add_result(results, "smoke_raw_rows", len(raw_df) == 3, f"rows={len(raw_df)}")
    add_result(results, "smoke_raw_columns", len(raw_df.columns) == 74, f"columns={len(raw_df.columns)}")
    add_result(
        results,
        "smoke_all_raw_features_present",
        all(feature in raw_df.columns for feature in raw_features),
        "all manifest raw features present in smoke raw feature CSV",
    )
    add_result(results, "smoke_prediction_rows", len(pred_df) == 3, f"rows={len(pred_df)}")
    add_result(
        results,
        "smoke_prediction_threshold",
        "threshold" in pred_df.columns and np.allclose(pred_df["threshold"], official_threshold),
        f"thresholds={sorted(pred_df['threshold'].unique().tolist()) if 'threshold' in pred_df.columns else 'missing'}",
    )

    expected_prediction_columns = [
        "sleep_episode_id",
        "participant_object_id",
        "sleep_start_datetime",
        "prediction_cutoff_datetime",
        "good_sleep_probability",
        "good_sleep_pred",
        "threshold",
    ]
    add_result(
        results,
        "smoke_prediction_columns",
        pred_df.columns.tolist() == expected_prediction_columns,
        ", ".join(pred_df.columns.tolist()),
    )

    if run_pipeline:
        from pre_sleep_forecasting.inference import PreSleepInferencePipeline

        pipeline = PreSleepInferencePipeline(project_root=PROJECT_ROOT)
        qa_pred_df = pipeline.predict(raw_df)
        add_result(
            results,
            "pipeline_smoke_rows",
            len(qa_pred_df) == len(pred_df) == 3,
            f"pipeline_rows={len(qa_pred_df)}",
        )
        add_result(
            results,
            "pipeline_smoke_threshold",
            np.allclose(qa_pred_df["threshold"], official_threshold),
            f"threshold={official_threshold}",
        )
        add_result(
            results,
            "pipeline_smoke_probabilities_finite",
            np.isfinite(qa_pred_df["good_sleep_probability"]).all(),
            "all generated probabilities are finite",
        )


def check_docs(results: list[dict]) -> None:
    text = DOC_PATH.read_text(encoding="utf-8")
    required_snippets = [
        r".\.venv\Scripts\Activate.ps1",
        r"src\pre_sleep_forecasting\feature_builder.py",
        r"--episodes data\processed\pre_sleep_forecasting\new_data\episodes_to_predict.csv",
        r"--output data\processed\pre_sleep_forecasting\new_data\raw_stage1_features.csv",
        r"src\pre_sleep_forecasting\inference.py",
        r"--input data\processed\pre_sleep_forecasting\new_data\raw_stage1_features.csv",
        r"--output data\processed\pre_sleep_forecasting\new_data\predictions.csv",
        "threshold: 0.54",
    ]
    for snippet in required_snippets:
        add_result(
            results,
            f"docs_contains:{snippet}",
            snippet in text,
            "present" if snippet in text else "missing",
        )


def build_report(results: list[dict], manifest: dict) -> str:
    passed_count = sum(1 for row in results if row["passed"])
    failed_rows = [row for row in results if not row["passed"]]
    status = "PASS" if not failed_rows else "FAIL"

    lines = [
        "# Pre-Sleep Inference Package QA",
        "",
        f"- Generated at: `{datetime.now().isoformat(timespec='seconds')}`",
        f"- Status: `{status}`",
        f"- Checks passed: `{passed_count}/{len(results)}`",
        f"- Selected experiment: `{manifest['selected_experiment_id']}`",
        f"- Official threshold: `{manifest['official_threshold']}`",
        f"- Raw features: `{len(manifest['raw_feature_order'])}`",
        f"- Removed zero-variance features: `{len(manifest['zero_variance_removed_features'])}`",
        f"- Model input features: `{len(manifest['final_model_feature_order'])}`",
        "",
        "## Check Results",
        "",
        "| Check | Status | Detail |",
        "|---|---:|---|",
    ]

    for row in results:
        mark = "PASS" if row["passed"] else "FAIL"
        detail = str(row["detail"]).replace("|", "\\|")
        lines.append(f"| `{row['check']}` | `{mark}` | {detail} |")

    if failed_rows:
        lines.extend(["", "## Failed Checks", ""])
        for row in failed_rows:
            lines.append(f"- `{row['check']}`: {row['detail']}")

    lines.extend(
        [
            "",
            "## Canonical Smoke Commands",
            "",
            "```powershell",
            r"cd C:\workSpace\DeepLearnin_sleep",
            r".\.venv\Scripts\Activate.ps1",
            r"python src\pre_sleep_forecasting\feature_builder.py `",
            r"  --episodes data\processed\pre_sleep_forecasting\new_data\episodes_to_predict.csv `",
            r"  --output data\processed\pre_sleep_forecasting\new_data\raw_stage1_features.csv",
            r"python src\pre_sleep_forecasting\inference.py `",
            r"  --input data\processed\pre_sleep_forecasting\new_data\raw_stage1_features.csv `",
            r"  --output data\processed\pre_sleep_forecasting\new_data\predictions.csv",
            "```",
            "",
        ]
    )
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--skip-pipeline-smoke",
        action="store_true",
        help="Skip in-memory inference smoke prediction.",
    )
    parser.add_argument(
        "--report",
        default=str(REPORT_PATH),
        help="Markdown QA report output path.",
    )
    args = parser.parse_args()

    results: list[dict] = []

    check_required_files(results)
    manifest = load_manifest()
    check_py_compile(results)
    check_imports(results)
    check_manifest_artifacts(results, manifest)
    check_feature_contract(results, manifest)
    check_smoke_outputs(results, manifest, run_pipeline=not args.skip_pipeline_smoke)
    check_docs(results)

    report_text = build_report(results, manifest)
    report_path = Path(args.report)
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(report_text, encoding="utf-8")

    failed = [row for row in results if not row["passed"]]
    print(f"QA report written: {report_path}")
    print(f"checks: {len(results) - len(failed)}/{len(results)} passed")
    if failed:
        for row in failed:
            print(f"FAILED {row['check']}: {row['detail']}")
        raise SystemExit(1)


if __name__ == "__main__":
    main()
