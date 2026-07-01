from __future__ import annotations

from datetime import datetime, time
from itertools import product
from math import cos, pi, sin
from pathlib import Path
import base64
import json
import os
import re
import shutil
import subprocess
import sys
import csv
import html
import tempfile
import zipfile

import altair as alt
import pandas as pd
import streamlit as st

try:
    from google.cloud import storage
except ImportError:  # Local fallback when GCS dependency is not installed yet.
    storage = None


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = PROJECT_ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from pre_sleep_forecasting.inference import PreSleepInferencePipeline
from pre_sleep_forecasting.preset_feature_builder import (
    QuickPresetInput,
    build_quick_preset_features,
)


DEFAULT_SAMSUNG_DIR = PROJECT_ROOT / "docs" / "samsunghealth"
SVG_DIR = PROJECT_ROOT / "design" / "svg"
STAGE1_DIR = PROJECT_ROOT / "data" / "processed" / "samsung_health" / "pre_sleep_stage1"
SNAPSHOT_DIR = STAGE1_DIR / "prototype_snapshots"
PROFILE_ROOT = PROJECT_ROOT / "data" / "profiles"
DEFAULT_UPLOAD_WORK_ROOT = PROJECT_ROOT / "_upload_work" if os.name == "nt" else Path(tempfile.gettempdir()) / "sleep_forecast_uploads"
UPLOAD_WORK_ROOT = Path(os.getenv("UPLOAD_WORK_ROOT", str(DEFAULT_UPLOAD_WORK_ROOT)))
PRESET_OUTPUT_DIR = PROJECT_ROOT / "data" / "processed" / "pre_sleep_forecasting" / "prototype_outputs"
GCP_PROJECT_ID = os.getenv("GCP_PROJECT_ID", "project-166d19de-1fb9-4ab5-b2f")
GCS_BUCKET_NAME = os.getenv("GCS_BUCKET_NAME", "deeplearnin_sleep")
GCS_PROFILE_PREFIX = os.getenv("GCS_PROFILE_PREFIX", "sleep-forecast/profiles").strip("/")
GCP_REGION = os.getenv("GCP_REGION", "asia-northeast3")
CLOUD_RUN_SERVICE_ACCOUNT = os.getenv(
    "CLOUD_RUN_SERVICE_ACCOUNT",
    "deeplearning-sleep-ybh@project-166d19de-1fb9-4ab5-b2f.iam.gserviceaccount.com",
)

PREDICTION_PATH = STAGE1_DIR / "samsung_pre_sleep_predictions.csv"
LIVE_FORECAST_DIR = STAGE1_DIR / "live_forecast"
TODAY_TARGET_EPISODE_PATH = LIVE_FORECAST_DIR / "today_sleep_target_episode.csv"
TODAY_RAW_FEATURE_PATH = LIVE_FORECAST_DIR / "today_raw_stage1_features.csv"
TODAY_PREDICTION_PATH = LIVE_FORECAST_DIR / "today_sleep_forecast_prediction.csv"
TODAY_SAMSUNG_ONLY_RAW_FEATURE_PATH = LIVE_FORECAST_DIR / "today_samsung_only_raw_stage1_features.csv"
TODAY_SAMSUNG_ONLY_PREDICTION_PATH = LIVE_FORECAST_DIR / "today_samsung_only_prediction.csv"
TODAY_COMPARISON_PATH = LIVE_FORECAST_DIR / "today_forecast_comparison.csv"
TODAY_NUMERIC_SENSITIVITY_PATH = LIVE_FORECAST_DIR / "today_numeric_sensitivity.csv"
TODAY_SNAPSHOT_DIR = LIVE_FORECAST_DIR / "snapshots"
TODAY_FEATURE_SUMMARY_PATH = LIVE_FORECAST_DIR / "today_stage1_feature_summary.csv"
TODAY_MAPPING_REPORT_PATH = LIVE_FORECAST_DIR / "today_stage1_feature_mapping_report.csv"
TODAY_SUPPLEMENT_REPORT_PATH = LIVE_FORECAST_DIR / "today_manual_wearable_supplement_report.csv"
TODAY_FEATURE_REPORT_PATH = PROJECT_ROOT / "reports" / "samsung_today_sleep_forecast_feature_build_summary.md"
TODAY_PREDICTION_SUMMARY_PATH = LIVE_FORECAST_DIR / "today_sleep_forecast_prediction_summary.csv"
TODAY_PREDICTION_REPORT_PATH = PROJECT_ROOT / "reports" / "samsung_today_sleep_forecast_prediction_summary.md"
RETRAIN_PLAN_PATH = PROJECT_ROOT / "reports" / "samsung_model_retraining_experiment_plan.md"

PIPELINE_STEPS = [
    ("수면 episode 생성", "scripts/30_build_samsung_sleep_episode_table.py"),
    ("Samsung-to-Fitbit feature 생성", "scripts/31_build_samsung_pre_sleep_stage1_features.py"),
    ("최종 MLP 예측 실행", "scripts/32_run_samsung_pre_sleep_inference.py"),
]

ACTIVITY_PRESETS = ["전날과 비슷", "전날보다 증가", "전날보다 감소", "모름"]
CALORIE_PRESETS = ["평소와 비슷", "평소보다 높음", "평소보다 낮음", "모름"]
HEART_RATE_PRESETS = ["평소와 비슷", "평소보다 높음", "평소보다 낮음", "모름"]
PREVIOUS_SLEEP_PRESETS = ["평소와 비슷", "좋았음", "나빴음", "모름"]

SOURCE_LABELS = {
    "time_input": "시간 입력",
    "user_numeric_input": "직접 입력",
    "preset_estimate": "프리셋 추정",
    "step_based_estimate": "걸음 기반 추정",
    "derived_count": "파생 count",
    "derived_missing_indicator": "missing indicator",
    "missing_imputed": "결측치 보완",
    "not_used_by_design_c_stage1_contract": "모델 미사용",
}

TODAY_FORECAST_FEATURE_STATUS = [
    ("previous_day_steps_sum", "이전날 걸음", "history"),
    ("previous_day_calories_sum", "이전날 칼로리", "history"),
    ("previous_day_lightly_active_minutes_sum", "이전날 active minutes", "history"),
    ("steps_pre_sleep_sum", "오늘 현재까지 걸음", "current_day"),
    ("steps_pre_sleep_last_3h_sum", "최근 3시간 걸음", "current_day"),
    ("steps_pre_sleep_last_1h_sum", "최근 1시간 걸음", "current_day"),
    ("heart_rate_pre_sleep_mean", "오늘 취침 전 심박", "current_day"),
    ("heart_rate_pre_sleep_last_3h_mean", "최근 3시간 심박", "current_day"),
    ("heart_rate_pre_sleep_last_1h_mean", "최근 1시간 심박", "current_day"),
]

FRESHNESS_DATASETS = [
    ("수면 단계", "com.samsung.health.sleep_stage", ["start_time", "end_time", "create_time", "update_time"]),
    ("수면 요약", "com.samsung.shealth.sleep", ["start_time", "end_time", "create_time", "update_time"]),
    ("심박", "com.samsung.shealth.tracker.heart_rate", ["start_time", "end_time", "create_time", "update_time"]),
    ("일별 걸음", "com.samsung.shealth.tracker.pedometer_day_summary", ["day_time", "start_time", "create_time"]),
    ("구간 걸음", "com.samsung.shealth.tracker.pedometer_step_count", ["start_time", "end_time", "create_time"]),
    ("일별 활동", "com.samsung.shealth.activity.day_summary", ["day_time", "start_time", "create_time"]),
    ("걸음 추세", "com.samsung.shealth.step_daily_trend", ["day_time", "start_time", "create_time"]),
]


def safe_profile_id(value: str) -> str:
    cleaned = re.sub(r"[^A-Za-z0-9_-]+", "_", value.strip())
    return cleaned.strip("_") or "default_profile"


def gcs_profile_prefix(profile_id: str, *parts: str) -> str:
    items = [GCS_PROFILE_PREFIX, safe_profile_id(profile_id), *[str(part).strip("/") for part in parts if str(part).strip("/")]]
    return "/".join(items)


def local_path(path: Path | str) -> str:
    resolved = Path(path).resolve()
    text = str(resolved)
    if os.name != "nt" or text.startswith("\\\\?\\"):
        return text
    if text.startswith("\\\\"):
        return "\\\\?\\UNC\\" + text.lstrip("\\")
    return "\\\\?\\" + text


def ensure_dir(path: Path) -> None:
    os.makedirs(local_path(path), exist_ok=True)


def copy_file(source: Path, destination: Path) -> None:
    ensure_dir(destination.parent)
    shutil.copy2(local_path(source), local_path(destination))


def copy_tree(source: Path, destination: Path, *, dirs_exist_ok: bool = True) -> None:
    ensure_dir(destination.parent)
    shutil.copytree(local_path(source), local_path(destination), dirs_exist_ok=dirs_exist_ok)


def remove_tree(path: Path) -> None:
    target = Path(path).resolve()
    allowed_roots = [PROJECT_ROOT.resolve(), UPLOAD_WORK_ROOT.resolve(), PROFILE_ROOT.resolve()]
    if not any(target == root or root in target.parents for root in allowed_roots):
        raise ValueError(f"Refusing to remove path outside project workspace: {target}")
    if os.path.exists(local_path(target)):
        shutil.rmtree(local_path(target))


def read_text_file(path: Path) -> str:
    with open(local_path(path), "r", encoding="utf-8-sig", errors="ignore") as handle:
        return handle.read()


def write_text_file(path: Path, text: str) -> None:
    ensure_dir(path.parent)
    with open(local_path(path), "w", encoding="utf-8-sig") as handle:
        handle.write(text)


@st.cache_resource(show_spinner=False)
def gcs_bucket():
    if storage is None or not GCS_BUCKET_NAME:
        return None
    try:
        client = storage.Client(project=GCP_PROJECT_ID)
        return client.bucket(GCS_BUCKET_NAME)
    except Exception:
        return None


def gcs_available() -> bool:
    return gcs_bucket() is not None


def gcs_status_message() -> str:
    if storage is None:
        return "GCS 연결 불가: google-cloud-storage 패키지를 불러오지 못했습니다."
    if not GCS_BUCKET_NAME:
        return "GCS 연결 불가: GCS_BUCKET_NAME이 비어 있습니다."
    try:
        storage.Client(project=GCP_PROJECT_ID).bucket(GCS_BUCKET_NAME)
    except Exception as exc:
        return f"GCS 연결 불가: {type(exc).__name__}: {exc}"
    return f"GCS 연결 준비됨: gs://{GCS_BUCKET_NAME}"


def gcs_blob_exists(blob_name: str) -> bool:
    bucket = gcs_bucket()
    if bucket is None:
        raise RuntimeError(gcs_status_message())
    try:
        return bucket.blob(blob_name).exists()
    except Exception as exc:
        raise RuntimeError(f"GCS 객체 확인 실패: {type(exc).__name__}: {exc}") from exc


def gcs_download_text(blob_name: str) -> str | None:
    bucket = gcs_bucket()
    if bucket is None:
        return None
    try:
        blob = bucket.blob(blob_name)
        if not blob.exists():
            return None
        return blob.download_as_text(encoding="utf-8")
    except Exception:
        return None


def gcs_upload_text(blob_name: str, text: str, content_type: str = "application/json") -> None:
    bucket = gcs_bucket()
    if bucket is None:
        raise RuntimeError("GCS bucket is not available")
    bucket.blob(blob_name).upload_from_string(text, content_type=content_type)


def gcs_upload_file(source_path: Path, blob_name: str) -> None:
    bucket = gcs_bucket()
    if bucket is None:
        raise RuntimeError("GCS bucket is not available")
    bucket.blob(blob_name).upload_from_filename(local_path(source_path))


def gcs_download_file(blob_name: str, destination_path: Path) -> None:
    bucket = gcs_bucket()
    if bucket is None:
        raise RuntimeError("GCS bucket is not available")
    ensure_dir(destination_path.parent)
    bucket.blob(blob_name).download_to_filename(local_path(destination_path))


def gcs_delete_prefix(prefix: str) -> None:
    bucket = gcs_bucket()
    if bucket is None:
        raise RuntimeError("GCS bucket is not available")
    for blob in bucket.list_blobs(prefix=prefix.rstrip("/") + "/"):
        blob.delete()


def gcs_upload_directory(local_dir: Path, prefix: str) -> int:
    uploaded = 0
    for path in local_dir.rglob("*"):
        if not path.is_file():
            continue
        rel = path.relative_to(local_dir).as_posix()
        gcs_upload_file(path, f"{prefix.rstrip('/')}/{rel}")
        uploaded += 1
    return uploaded


def gcs_download_prefix(prefix: str, local_dir: Path, suffixes: tuple[str, ...] | None = None) -> int:
    bucket = gcs_bucket()
    if bucket is None:
        raise RuntimeError("GCS bucket is not available")
    ensure_dir(local_dir)
    count = 0
    base = prefix.rstrip("/") + "/"
    for blob in bucket.list_blobs(prefix=base):
        if blob.name.endswith("/"):
            continue
        if suffixes and not blob.name.lower().endswith(suffixes):
            continue
        rel = blob.name[len(base) :]
        target = local_dir / rel
        ensure_dir(target.parent)
        blob.download_to_filename(local_path(target))
        count += 1
    return count


def prepare_profile_work_dir(profile_id: str) -> Path:
    safe_id = safe_profile_id(profile_id)
    work_dir = Path(tempfile.gettempdir()) / "sleep_forecast_profiles" / safe_id / "raw_export"
    if work_dir.exists() and any(work_dir.rglob("*.csv")):
        return work_dir
    if work_dir.exists():
        shutil.rmtree(work_dir)
    if gcs_available():
        try:
            gcs_download_prefix(gcs_profile_prefix(safe_id, "raw_export"), work_dir, suffixes=(".csv",))
            return work_dir
        except Exception:
            pass
    return profile_raw_dir(safe_id)


def sync_outputs_to_gcs(profile_id: str) -> None:
    if not gcs_available():
        return
    safe_id = safe_profile_id(profile_id)
    output_targets = [
        (STAGE1_DIR, gcs_profile_prefix(safe_id, "processed", "pre_sleep_stage1")),
        (PROJECT_ROOT / "reports", gcs_profile_prefix(safe_id, "processed", "reports")),
    ]
    for local_dir, prefix in output_targets:
        if local_dir.exists():
            gcs_upload_directory(local_dir, prefix)


def profile_dir(profile_id: str) -> Path:
    return PROFILE_ROOT / safe_profile_id(profile_id)


def profile_raw_dir(profile_id: str) -> Path:
    return profile_dir(profile_id) / "raw_export"


def profile_inbox_dir(profile_id: str) -> Path:
    return profile_dir(profile_id) / "inbox"


def profile_imports_dir(profile_id: str) -> Path:
    return profile_dir(profile_id) / "imports"


def profile_manifest_path(profile_id: str) -> Path:
    return profile_dir(profile_id) / "manifest.json"


def load_profile_manifest(profile_id: str) -> dict:
    if gcs_available():
        text = gcs_download_text(gcs_profile_prefix(profile_id, "manifest.json"))
        if text:
            try:
                return json.loads(text)
            except json.JSONDecodeError:
                pass
    path = profile_manifest_path(profile_id)
    if not path.exists():
        return {
            "profile_id": safe_profile_id(profile_id),
            "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "imports": [],
        }
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {
            "profile_id": safe_profile_id(profile_id),
            "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "imports": [],
        }


def save_profile_manifest(profile_id: str, manifest: dict) -> None:
    if gcs_available():
        gcs_upload_text(
            gcs_profile_prefix(profile_id, "manifest.json"),
            json.dumps(manifest, ensure_ascii=False, indent=2),
        )
        return
    path = profile_manifest_path(profile_id)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")


def list_profile_ids() -> list[str]:
    if gcs_available():
        bucket = gcs_bucket()
        if bucket is not None:
            try:
                names = set()
                prefix = GCS_PROFILE_PREFIX.rstrip("/") + "/"
                for blob in bucket.list_blobs(prefix=prefix):
                    remainder = blob.name[len(prefix) :]
                    profile = remainder.split("/", 1)[0]
                    if profile:
                        names.add(profile)
                profiles = sorted(names)
                if profiles:
                    return profiles
            except Exception:
                pass
    if not PROFILE_ROOT.exists():
        return ["default_profile"]
    profiles = sorted(path.name for path in PROFILE_ROOT.iterdir() if path.is_dir())
    return profiles or ["default_profile"]


def safe_extract_zip(zip_path: Path, target_dir: Path) -> list[Path]:
    ensure_dir(target_dir)
    extracted: list[Path] = []
    root = target_dir.resolve()
    with zipfile.ZipFile(zip_path) as archive:
        for member in archive.infolist():
            if member.is_dir():
                continue
            member_name = member.filename.replace("\\", "/")
            if member_name.startswith("/") or ".." in Path(member_name).parts:
                continue
            destination = (target_dir / member_name).resolve()
            if not str(destination).startswith(str(root)):
                continue
            ensure_dir(destination.parent)
            with archive.open(member) as src, open(local_path(destination), "wb") as dst:
                shutil.copyfileobj(src, dst)
            extracted.append(destination)
    return extracted


def detected_export_root(extracted_dir: Path) -> Path:
    csv_candidates = list(extracted_dir.rglob("*.csv"))
    if not csv_candidates:
        return extracted_dir
    parents = [path.parent for path in csv_candidates]
    common = Path(os.path.commonpath([str(path) for path in parents]))
    return common if common.exists() else extracted_dir


def merge_samsung_csv(existing_path: Path, incoming_path: Path) -> int:
    if not existing_path.exists():
        copy_file(incoming_path, existing_path)
        return max(0, len(read_text_file(incoming_path).splitlines()) - 2)

    existing_lines = read_text_file(existing_path).splitlines()
    incoming_lines = read_text_file(incoming_path).splitlines()
    if len(incoming_lines) <= 2:
        return 0
    if len(existing_lines) < 2:
        copy_file(incoming_path, existing_path)
        return max(0, len(incoming_lines) - 2)

    header = existing_lines[:2]
    existing_rows = existing_lines[2:]
    seen = set(existing_rows)
    added_rows = [row for row in incoming_lines[2:] if row and row not in seen]
    if not added_rows:
        return 0
    merged = header + existing_rows + added_rows
    write_text_file(existing_path, "\n".join(merged) + "\n")
    return len(added_rows)


def parse_gcs_zip_reference(value: str) -> tuple[str, str]:
    text = value.strip()
    if not text:
        raise ValueError("GCS ZIP 경로를 입력하세요.")
    if text.startswith("gs://"):
        without_scheme = text[5:]
        bucket_name, _, blob_name = without_scheme.partition("/")
        if not bucket_name or not blob_name:
            raise ValueError("GCS 경로는 gs://bucket/path/file.zip 형식이어야 합니다.")
        return bucket_name, blob_name
    return GCS_BUCKET_NAME, text.lstrip("/")


def apply_zip_path_to_profile(
    zip_path: Path,
    zip_name: str,
    profile_id: str,
    mode: str,
    *,
    source_uri: str | None = None,
) -> dict:
    safe_id = safe_profile_id(profile_id)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    local_base = zip_path.parent

    if gcs_available():
        gcs_upload_file(zip_path, gcs_profile_prefix(safe_id, "inbox", zip_path.name))
    else:
        ensure_dir(profile_dir(safe_id))
        ensure_dir(profile_inbox_dir(safe_id))
        ensure_dir(profile_imports_dir(safe_id))
        copy_file(zip_path, profile_inbox_dir(safe_id) / zip_path.name)

    import_dir = local_base / "import"
    extracted_dir = import_dir / "extracted"
    extracted_files = safe_extract_zip(zip_path, extracted_dir)
    export_root = detected_export_root(extracted_dir)
    raw_dir = local_base / "raw_export"

    if mode == "전체 교체":
        if raw_dir.exists():
            remove_tree(raw_dir)
        ensure_dir(raw_dir)
        copied = 0
        for source in extracted_files:
            rel = source.relative_to(export_root) if source.is_relative_to(export_root) else source.relative_to(extracted_dir)
            destination = raw_dir / rel
            copy_file(source, destination)
            copied += 1
        added_rows = 0
    else:
        ensure_dir(raw_dir)
        if gcs_available():
            try:
                gcs_download_prefix(gcs_profile_prefix(safe_id, "raw_export"), raw_dir, suffixes=(".csv",))
            except Exception:
                pass
        elif profile_raw_dir(safe_id).exists():
            copy_tree(profile_raw_dir(safe_id), raw_dir)
        copied = 0
        added_rows = 0
        for source in extracted_files:
            rel = source.relative_to(export_root) if source.is_relative_to(export_root) else source.relative_to(extracted_dir)
            destination = raw_dir / rel
            if source.suffix.lower() == ".csv":
                added_rows += merge_samsung_csv(destination, source)
            else:
                copy_file(source, destination)
            copied += 1

    if gcs_available():
        if mode == "전체 교체":
            gcs_delete_prefix(gcs_profile_prefix(safe_id, "raw_export"))
        gcs_upload_directory(raw_dir, gcs_profile_prefix(safe_id, "raw_export"))
        gcs_upload_directory(extracted_dir, gcs_profile_prefix(safe_id, "imports", timestamp, "extracted"))
    else:
        final_raw_dir = profile_raw_dir(safe_id)
        if mode == "전체 교체" and final_raw_dir.exists():
            remove_tree(final_raw_dir)
        ensure_dir(final_raw_dir.parent)
        copy_tree(raw_dir, final_raw_dir)
        local_import_dir = profile_imports_dir(safe_id) / timestamp / "extracted"
        if local_import_dir.exists():
            remove_tree(local_import_dir)
        copy_tree(extracted_dir, local_import_dir)

    manifest = load_profile_manifest(safe_id)
    manifest["profile_id"] = safe_id
    manifest["raw_export_dir"] = f"gs://{GCS_BUCKET_NAME}/{gcs_profile_prefix(safe_id, 'raw_export')}" if gcs_available() else str(profile_raw_dir(safe_id))
    manifest["storage_backend"] = "gcs" if gcs_available() else "local"
    manifest["last_import_at"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    manifest.setdefault("imports", []).append(
        {
            "timestamp": timestamp,
            "mode": mode,
            "zip_name": zip_name,
            "zip_path": source_uri or (f"gs://{GCS_BUCKET_NAME}/{gcs_profile_prefix(safe_id, 'inbox', zip_path.name)}" if gcs_available() else str(profile_inbox_dir(safe_id) / zip_path.name)),
            "extracted_files": len(extracted_files),
            "applied_files": copied,
            "added_csv_rows": added_rows,
        }
    )
    save_profile_manifest(safe_id, manifest)
    return {
        "profile_id": safe_id,
        "mode": mode,
        "raw_dir": raw_dir,
        "extracted_files": len(extracted_files),
        "applied_files": copied,
        "added_csv_rows": added_rows,
        "zip_path": zip_path,
    }


def apply_zip_to_profile(uploaded_file, profile_id: str, mode: str) -> dict:
    safe_id = safe_profile_id(profile_id)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    local_base = UPLOAD_WORK_ROOT / safe_id / timestamp
    if local_base.exists():
        remove_tree(local_base)
    ensure_dir(local_base)

    zip_path = local_base / f"{timestamp}_{Path(uploaded_file.name).name}"
    with open(local_path(zip_path), "wb") as handle:
        handle.write(uploaded_file.getbuffer())
    return apply_zip_path_to_profile(zip_path, uploaded_file.name, safe_id, mode)


def apply_gcs_zip_to_profile(gcs_reference: str, profile_id: str, mode: str) -> dict:
    bucket_name, blob_name = parse_gcs_zip_reference(gcs_reference)
    if bucket_name != GCS_BUCKET_NAME:
        raise ValueError(f"현재 앱 버킷({GCS_BUCKET_NAME})의 ZIP만 바로 반영할 수 있습니다.")
    if not gcs_blob_exists(blob_name):
        raise FileNotFoundError(f"GCS ZIP을 찾을 수 없습니다: gs://{bucket_name}/{blob_name}")

    safe_id = safe_profile_id(profile_id)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    local_base = UPLOAD_WORK_ROOT / safe_id / timestamp
    if local_base.exists():
        remove_tree(local_base)
    ensure_dir(local_base)

    zip_name = Path(blob_name).name or f"{timestamp}_upload.zip"
    zip_path = local_base / f"{timestamp}_{zip_name}"
    gcs_download_file(blob_name, zip_path)
    return apply_zip_path_to_profile(zip_path, zip_name, safe_id, mode, source_uri=f"gs://{bucket_name}/{blob_name}")


@st.cache_resource
def load_pipeline() -> PreSleepInferencePipeline:
    return PreSleepInferencePipeline(project_root=PROJECT_ROOT)


def count_files(data_dir: Path) -> dict:
    if not data_dir.exists():
        return {"csv": 0, "json": 0, "total": 0, "latest_modified": ""}
    csv_files = list(data_dir.rglob("*.csv"))
    json_files = list(data_dir.rglob("*.json"))
    all_files = csv_files + json_files
    latest = max((p.stat().st_mtime for p in all_files), default=None)
    latest_text = datetime.fromtimestamp(latest).strftime("%Y-%m-%d %H:%M") if latest else ""
    return {
        "csv": len(csv_files),
        "json": len(json_files),
        "total": len(all_files),
        "latest_modified": latest_text,
    }


def find_dataset_file(data_dir: Path, dataset_name: str) -> Path | None:
    matches = sorted(data_dir.rglob(f"{dataset_name}.*.csv"))
    return matches[0] if matches else None


def read_samsung_csv_light(path: Path, max_rows: int | None = None) -> pd.DataFrame:
    with open(path, "r", encoding="utf-8-sig", newline="") as f:
        reader = csv.reader(f)
        try:
            _metadata = next(reader)
            header = next(reader)
        except StopIteration:
            return pd.DataFrame()

        rows = []
        for index, row in enumerate(reader):
            if max_rows is not None and index >= max_rows:
                break
            if len(row) == len(header) + 1 and row[-1] == "":
                row = row[:-1]
            if len(row) < len(header):
                row = row + [""] * (len(header) - len(row))
            elif len(row) > len(header):
                row = row[: len(header)]
            rows.append(row)

    return pd.DataFrame(rows, columns=header).replace("", pd.NA)


def find_column_by_suffix(columns: list[str], candidates: list[str]) -> str | None:
    exact_map = {str(col).lower(): col for col in columns}
    for candidate in candidates:
        if candidate.lower() in exact_map:
            return exact_map[candidate.lower()]
    for candidate in candidates:
        candidate_l = candidate.lower()
        for col in columns:
            col_l = str(col).lower()
            if col_l.endswith("." + candidate_l) or col_l.endswith(candidate_l):
                return col
    return None


def dataset_freshness(data_dir: Path) -> pd.DataFrame:
    rows = []
    for label, dataset, time_candidates in FRESHNESS_DATASETS:
        path = find_dataset_file(data_dir, dataset)
        if path is None:
            rows.append(
                {
                    "데이터": label,
                    "상태": "없음",
                    "최신 데이터 시각": "",
                    "행 수": 0,
                    "시간 컬럼": "",
                    "파일 수정 시각": "",
                    "파일": "",
                }
            )
            continue

        try:
            df = read_samsung_csv_light(path)
            time_col = find_column_by_suffix(list(df.columns), time_candidates)
            latest_data_time = ""
            if time_col is not None and not df.empty:
                parsed = pd.to_datetime(df[time_col], errors="coerce")
                if parsed.notna().any():
                    latest_data_time = parsed.max().strftime("%Y-%m-%d %H:%M:%S")
            modified = datetime.fromtimestamp(path.stat().st_mtime).strftime("%Y-%m-%d %H:%M:%S")
            rows.append(
                {
                    "데이터": label,
                    "상태": "있음",
                    "최신 데이터 시각": latest_data_time,
                    "행 수": len(df),
                    "시간 컬럼": time_col or "",
                    "파일 수정 시각": modified,
                    "파일": str(path),
                }
            )
        except Exception as exc:
            rows.append(
                {
                    "데이터": label,
                    "상태": f"오류: {type(exc).__name__}",
                    "최신 데이터 시각": "",
                    "행 수": 0,
                    "시간 컬럼": "",
                    "파일 수정 시각": "",
                    "파일": str(path),
                }
            )
    return pd.DataFrame(rows)


def summarize_freshness(freshness_df: pd.DataFrame) -> dict:
    if freshness_df.empty:
        return {"available": 0, "total": 0, "latest_data_time": "", "latest_dataset": ""}
    available_df = freshness_df[freshness_df["상태"] == "있음"].copy()
    available_df["parsed_latest"] = pd.to_datetime(available_df["최신 데이터 시각"], errors="coerce")
    latest_rows = available_df.dropna(subset=["parsed_latest"]).sort_values("parsed_latest", ascending=False)
    if latest_rows.empty:
        latest_data_time = ""
        latest_dataset = ""
    else:
        latest_data_time = latest_rows.iloc[0]["parsed_latest"].strftime("%Y-%m-%d %H:%M:%S")
        latest_dataset = str(latest_rows.iloc[0]["데이터"])
    return {
        "available": int(len(available_df)),
        "total": int(len(freshness_df)),
        "latest_data_time": latest_data_time,
        "latest_dataset": latest_dataset,
    }


def dataset_status(data_dir: Path) -> pd.DataFrame:
    datasets = [
        ("수면 단계", "com.samsung.health.sleep_stage"),
        ("수면 요약", "com.samsung.shealth.sleep"),
        ("심박", "com.samsung.shealth.tracker.heart_rate"),
        ("일별 걸음", "com.samsung.shealth.tracker.pedometer_day_summary"),
        ("구간 걸음", "com.samsung.shealth.tracker.pedometer_step_count"),
        ("일별 활동", "com.samsung.shealth.activity.day_summary"),
        ("걸음 추세", "com.samsung.shealth.step_daily_trend"),
        ("칼로리 상세", "com.samsung.shealth.calories_burned.details"),
    ]
    rows = []
    for label, dataset in datasets:
        path = find_dataset_file(data_dir, dataset)
        rows.append(
            {
                "데이터": label,
                "상태": "있음" if path else "없음",
                "파일": str(path) if path else "",
            }
        )
    return pd.DataFrame(rows)


def run_pipeline(data_dir: Path) -> list[dict]:
    env = os.environ.copy()
    env["PROJECT_ROOT"] = str(PROJECT_ROOT)
    env["SAMSUNG_HEALTH_DIR"] = str(data_dir)

    results = []
    for step_name, script in PIPELINE_STEPS:
        print(f"[pipeline] start step={step_name} script={script} data_dir={data_dir}", flush=True)
        completed = subprocess.run(
            [sys.executable, script],
            cwd=PROJECT_ROOT,
            env=env,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
        )
        results.append(
            {
                "step": step_name,
                "script": script,
                "returncode": completed.returncode,
                "stdout": completed.stdout,
                "stderr": completed.stderr,
            }
        )
        print(
            f"[pipeline] end step={step_name} returncode={completed.returncode}\n"
            f"[pipeline] stdout:\n{completed.stdout[-4000:]}\n"
            f"[pipeline] stderr:\n{completed.stderr[-4000:]}",
            flush=True,
        )
        if completed.returncode != 0:
            break
    return results


def run_command_step(step_name: str, command: list[str], data_dir: Path) -> dict:
    env = os.environ.copy()
    env["PROJECT_ROOT"] = str(PROJECT_ROOT)
    env["SAMSUNG_HEALTH_DIR"] = str(data_dir)
    print(f"[command-step] start step={step_name} command={' '.join(command)} data_dir={data_dir}", flush=True)
    completed = subprocess.run(
        command,
        cwd=PROJECT_ROOT,
        env=env,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    print(
        f"[command-step] end step={step_name} returncode={completed.returncode}\n"
        f"[command-step] stdout:\n{completed.stdout[-4000:]}\n"
        f"[command-step] stderr:\n{completed.stderr[-4000:]}",
        flush=True,
    )
    return {
        "step": step_name,
        "script": " ".join(command[1:]),
        "returncode": completed.returncode,
        "stdout": completed.stdout,
        "stderr": completed.stderr,
    }


def latest_participant_from_episode_table(path: Path) -> str:
    if not path.exists():
        return "samsung_user"
    episodes = pd.read_csv(path, encoding="utf-8-sig")
    if episodes.empty or "participant_object_id" not in episodes.columns:
        return "samsung_user"
    if "sleep_start_datetime" in episodes.columns:
        episodes["sleep_start_datetime"] = pd.to_datetime(episodes["sleep_start_datetime"], errors="coerce")
        episodes = episodes.sort_values("sleep_start_datetime", ascending=False)
    participant = episodes["participant_object_id"].dropna()
    return str(participant.iloc[0]) if len(participant) else "samsung_user"


def write_today_target_episode(sleep_start: datetime) -> Path:
    LIVE_FORECAST_DIR.mkdir(parents=True, exist_ok=True)
    participant_id = latest_participant_from_episode_table(STAGE1_DIR / "samsung_sleep_episodes.csv")
    target_df = pd.DataFrame(
        [
            {
                "sleep_episode_id": f"today_forecast__{sleep_start.strftime('%Y%m%d%H%M%S')}",
                "participant_object_id": participant_id,
                "sleep_start_datetime": sleep_start.strftime("%Y-%m-%d %H:%M:%S"),
                "prediction_cutoff_datetime": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "target_type": "today_sleep_forecast",
            }
        ]
    )
    target_df.to_csv(TODAY_TARGET_EPISODE_PATH, index=False, encoding="utf-8-sig")
    return TODAY_TARGET_EPISODE_PATH


def build_manual_wearable_supplement(
    today_steps: float,
    last_3h_steps: float,
    last_1h_steps: float,
    heart_rate_mean: float,
    last_3h_heart_rate: float,
    last_1h_heart_rate: float,
) -> dict:
    calories_per_step = 0.04
    return {
        "steps_pre_sleep_sum": float(today_steps),
        "steps_pre_sleep_record_count": 1,
        "steps_pre_sleep_active_record_count": 1 if float(today_steps) > 0 else 0,
        "steps_pre_sleep_last_3h_sum": float(last_3h_steps),
        "steps_pre_sleep_last_1h_sum": float(last_1h_steps),
        "calories_pre_sleep_sum": float(today_steps) * calories_per_step,
        "calories_pre_sleep_record_count": 1,
        "calories_pre_sleep_last_3h_sum": float(last_3h_steps) * calories_per_step,
        "calories_pre_sleep_last_1h_sum": float(last_1h_steps) * calories_per_step,
        "heart_rate_pre_sleep_mean": float(heart_rate_mean),
        "heart_rate_pre_sleep_median": float(heart_rate_mean),
        "heart_rate_pre_sleep_std": 4.0,
        "heart_rate_pre_sleep_min": float(heart_rate_mean) - 5.0,
        "heart_rate_pre_sleep_max": float(heart_rate_mean) + 5.0,
        "heart_rate_pre_sleep_record_count": 1,
        "heart_rate_pre_sleep_last_3h_mean": float(last_3h_heart_rate),
        "heart_rate_pre_sleep_last_1h_mean": float(last_1h_heart_rate),
    }


def apply_manual_wearable_supplement(raw_feature_path: Path, supplement: dict | None) -> Path | None:
    if not supplement:
        if TODAY_SUPPLEMENT_REPORT_PATH.exists():
            TODAY_SUPPLEMENT_REPORT_PATH.unlink()
        return None

    raw_df = pd.read_csv(raw_feature_path, encoding="utf-8-sig")
    if raw_df.empty:
        return None

    report_rows = []
    for feature, new_value in supplement.items():
        if feature not in raw_df.columns:
            continue
        old_value = raw_df.loc[0, feature]
        raw_df.loc[0, feature] = new_value
        report_rows.append(
            {
                "feature": feature,
                "old_value": old_value,
                "new_value": new_value,
                "source": "manual_current_day_wearable_supplement",
            }
        )

        missing_indicator = f"{feature}_missing_ind"
        if missing_indicator in raw_df.columns:
            raw_df.loc[0, missing_indicator] = int(pd.isna(new_value))
            report_rows.append(
                {
                    "feature": missing_indicator,
                    "old_value": "",
                    "new_value": int(pd.isna(new_value)),
                    "source": "manual_current_day_wearable_supplement",
                }
            )

    raw_df.to_csv(raw_feature_path, index=False, encoding="utf-8-sig")
    report_df = pd.DataFrame(report_rows)
    TODAY_SUPPLEMENT_REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    report_df.to_csv(TODAY_SUPPLEMENT_REPORT_PATH, index=False, encoding="utf-8-sig")
    return TODAY_SUPPLEMENT_REPORT_PATH


def run_today_inference_step(input_path: Path, output_path: Path, summary_path: Path, report_path: Path) -> list[str]:
    return [
        sys.executable,
        "scripts/32_run_samsung_pre_sleep_inference.py",
        "--input",
        str(input_path),
        "--output",
        str(output_path),
        "--summary",
        str(summary_path),
        "--report",
        str(report_path),
    ]


def write_today_forecast_comparison() -> Path | None:
    baseline_df = load_csv_if_exists(TODAY_SAMSUNG_ONLY_PREDICTION_PATH)
    final_df = load_csv_if_exists(TODAY_PREDICTION_PATH)
    if baseline_df.empty or final_df.empty:
        return None

    baseline_row = baseline_df.iloc[0]
    final_row = final_df.iloc[0]
    baseline_prob = float(pd.to_numeric(baseline_row["good_sleep_probability"], errors="coerce"))
    final_prob = float(pd.to_numeric(final_row["good_sleep_probability"], errors="coerce"))
    baseline_pred = safe_prediction_label(baseline_row.get("good_sleep_pred"))
    final_pred = safe_prediction_label(final_row.get("good_sleep_pred"))

    comparison_df = pd.DataFrame(
        [
            {
                "sleep_episode_id": final_row.get("sleep_episode_id"),
                "sleep_start_datetime": final_row.get("sleep_start_datetime"),
                "prediction_cutoff_datetime": final_row.get("prediction_cutoff_datetime"),
                "samsung_only_probability": baseline_prob,
                "final_probability": final_prob,
                "probability_delta": final_prob - baseline_prob,
                "samsung_only_pred": baseline_pred,
                "final_pred": final_pred,
                "label_changed": baseline_pred != final_pred,
                "manual_supplement_applied": TODAY_SUPPLEMENT_REPORT_PATH.exists(),
            }
        ]
    )
    comparison_df.to_csv(TODAY_COMPARISON_PATH, index=False, encoding="utf-8-sig")
    return TODAY_COMPARISON_PATH


def save_today_forecast_snapshot() -> Path | None:
    final_df = load_csv_if_exists(TODAY_PREDICTION_PATH)
    if final_df.empty:
        return None
    TODAY_SNAPSHOT_DIR.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    snapshot_path = TODAY_SNAPSHOT_DIR / f"today_sleep_forecast_prediction_{timestamp}.csv"
    final_df.to_csv(snapshot_path, index=False, encoding="utf-8-sig")
    return snapshot_path


def latest_today_forecast_snapshot_before_current() -> Path | None:
    if not TODAY_SNAPSHOT_DIR.exists():
        return None
    snapshots = sorted(TODAY_SNAPSHOT_DIR.glob("today_sleep_forecast_prediction_*.csv"))
    if len(snapshots) < 2:
        return None
    return snapshots[-2]


def today_snapshot_delta() -> float | None:
    previous_path = latest_today_forecast_snapshot_before_current()
    current_df = load_csv_if_exists(TODAY_PREDICTION_PATH)
    if previous_path is None or current_df.empty:
        return None
    previous_df = load_csv_if_exists(previous_path)
    if previous_df.empty:
        return None
    current_prob = float(pd.to_numeric(current_df.iloc[0]["good_sleep_probability"], errors="coerce"))
    previous_prob = float(pd.to_numeric(previous_df.iloc[0]["good_sleep_probability"], errors="coerce"))
    return current_prob - previous_prob


def apply_timing_features_to_row(row: pd.Series, sleep_start: pd.Timestamp) -> pd.Series:
    updated = row.copy()
    sleep_hour = sleep_start.hour + sleep_start.minute / 60 + sleep_start.second / 3600
    dayofweek = sleep_start.dayofweek
    month = sleep_start.month
    values = {
        "sleep_start_datetime": sleep_start.strftime("%Y-%m-%d %H:%M:%S"),
        "pre_sleep_window_hours": sleep_hour,
        "sleep_start_hour": sleep_hour,
        "sleep_start_dayofweek": dayofweek,
        "sleep_start_month": month,
        "sleep_start_dayofweek_sin": sin(2 * pi * dayofweek / 7),
        "sleep_start_dayofweek_cos": cos(2 * pi * dayofweek / 7),
        "sleep_start_month_sin": sin(2 * pi * month / 12),
        "sleep_start_month_cos": cos(2 * pi * month / 12),
    }
    for column, value in values.items():
        if column in updated.index:
            updated[column] = value
    return updated


def set_numeric_if_present(row: pd.Series, column: str, value: float) -> pd.Series:
    updated = row.copy()
    if column in updated.index:
        updated[column] = max(float(value), 0.0)
        missing_indicator = f"{column}_missing_ind"
        if missing_indicator in updated.index:
            updated[missing_indicator] = 0
    return updated


def run_numeric_sensitivity() -> pd.DataFrame:
    raw_df = load_csv_if_exists(TODAY_RAW_FEATURE_PATH)
    if raw_df.empty:
        return pd.DataFrame()

    base_prediction = load_pipeline().predict(raw_df)
    base_probability = float(base_prediction.loc[0, "good_sleep_probability"])
    base_pred = int(base_prediction.loc[0, "good_sleep_pred"])
    base_row = raw_df.iloc[0].copy()
    base_sleep_start = pd.to_datetime(base_row.get("sleep_start_datetime"), errors="coerce")

    scenarios: list[tuple[str, str, pd.Series]] = [("baseline", "현재 입력", base_row)]

    step_value = pd.to_numeric(base_row.get("steps_pre_sleep_sum"), errors="coerce")
    if pd.notna(step_value):
        for delta in [-1000, 1000]:
            row = set_numeric_if_present(base_row, "steps_pre_sleep_sum", float(step_value) + delta)
            if "calories_pre_sleep_sum" in row.index:
                row = set_numeric_if_present(row, "calories_pre_sleep_sum", max(float(step_value) + delta, 0.0) * 0.04)
            scenarios.append((f"steps_{delta:+d}", f"오늘 걸음 {delta:+d}", row))

    last_1h_steps = pd.to_numeric(base_row.get("steps_pre_sleep_last_1h_sum"), errors="coerce")
    if pd.notna(last_1h_steps):
        for delta in [-200, 200]:
            row = set_numeric_if_present(base_row, "steps_pre_sleep_last_1h_sum", float(last_1h_steps) + delta)
            if "calories_pre_sleep_last_1h_sum" in row.index:
                row = set_numeric_if_present(
                    row,
                    "calories_pre_sleep_last_1h_sum",
                    max(float(last_1h_steps) + delta, 0.0) * 0.04,
                )
            scenarios.append((f"last_1h_steps_{delta:+d}", f"최근 1시간 걸음 {delta:+d}", row))

    heart_rate = pd.to_numeric(base_row.get("heart_rate_pre_sleep_mean"), errors="coerce")
    if pd.notna(heart_rate):
        for delta in [-5, 5]:
            row = base_row.copy()
            for column in [
                "heart_rate_pre_sleep_mean",
                "heart_rate_pre_sleep_median",
                "heart_rate_pre_sleep_last_3h_mean",
                "heart_rate_pre_sleep_last_1h_mean",
            ]:
                row = set_numeric_if_present(row, column, float(row.get(column, heart_rate)) + delta)
            scenarios.append((f"heart_rate_{delta:+d}", f"심박 {delta:+d}", row))

    if pd.notna(base_sleep_start):
        for minutes in [-30, 30]:
            shifted = base_sleep_start + pd.Timedelta(minutes=minutes)
            row = apply_timing_features_to_row(base_row, shifted)
            scenarios.append((f"sleep_time_{minutes:+d}m", f"취침시각 {minutes:+d}분", row))

    rows = []
    for scenario_id, description, row in scenarios:
        scenario_df = pd.DataFrame([row], columns=raw_df.columns)
        prediction = load_pipeline().predict(scenario_df)
        probability = float(prediction.loc[0, "good_sleep_probability"])
        pred = int(prediction.loc[0, "good_sleep_pred"])
        rows.append(
            {
                "scenario_id": scenario_id,
                "description": description,
                "sleep_start_datetime": scenario_df.loc[0, "sleep_start_datetime"],
                "good_sleep_probability": probability,
                "probability_delta": probability - base_probability,
                "good_sleep_pred": pred,
                "label_changed": pred != base_pred,
            }
        )

    sensitivity_df = pd.DataFrame(rows).sort_values("good_sleep_probability", ascending=False)
    sensitivity_df.to_csv(TODAY_NUMERIC_SENSITIVITY_PATH, index=False, encoding="utf-8-sig")
    return sensitivity_df


def run_today_forecast_pipeline(
    data_dir: Path,
    sleep_start: datetime,
    manual_wearable_supplement: dict | None = None,
) -> list[dict]:
    LIVE_FORECAST_DIR.mkdir(parents=True, exist_ok=True)
    results: list[dict] = []

    results.append(
        run_command_step(
            "완료된 수면 이력 갱신",
            [sys.executable, "scripts/30_build_samsung_sleep_episode_table.py"],
            data_dir,
        )
    )
    if results[-1]["returncode"] != 0:
        return results

    write_today_target_episode(sleep_start)
    results.append(
        run_command_step(
            "오늘 밤 예측 대상 특성 생성",
            [
                sys.executable,
                "scripts/31_build_samsung_pre_sleep_stage1_features.py",
                "--episodes",
                str(TODAY_TARGET_EPISODE_PATH),
                "--output",
                str(TODAY_RAW_FEATURE_PATH),
                "--mapping-report",
                str(TODAY_MAPPING_REPORT_PATH),
                "--summary",
                str(TODAY_FEATURE_SUMMARY_PATH),
                "--report",
                str(TODAY_FEATURE_REPORT_PATH),
            ],
            data_dir,
        )
    )
    if results[-1]["returncode"] != 0:
        return results

    shutil.copy2(TODAY_RAW_FEATURE_PATH, TODAY_SAMSUNG_ONLY_RAW_FEATURE_PATH)
    results.append(
        run_command_step(
            "Samsung 단독 기준 MLP 예측",
            run_today_inference_step(
                TODAY_SAMSUNG_ONLY_RAW_FEATURE_PATH,
                TODAY_SAMSUNG_ONLY_PREDICTION_PATH,
                LIVE_FORECAST_DIR / "today_samsung_only_prediction_summary.csv",
                PROJECT_ROOT / "reports" / "samsung_today_sleep_forecast_samsung_only_prediction_summary.md",
            ),
            data_dir,
        )
    )
    if results[-1]["returncode"] != 0:
        return results

    supplement_report = apply_manual_wearable_supplement(TODAY_RAW_FEATURE_PATH, manual_wearable_supplement)
    if supplement_report is not None:
        results.append(
            {
                "step": "수동 wearable 보완값 반영",
                "script": str(supplement_report),
                "returncode": 0,
                "stdout": f"supplement report: {supplement_report}",
                "stderr": "",
            }
        )

    results.append(
        run_command_step(
            "오늘 밤 최종 MLP 예측",
            run_today_inference_step(
                TODAY_RAW_FEATURE_PATH,
                TODAY_PREDICTION_PATH,
                TODAY_PREDICTION_SUMMARY_PATH,
                TODAY_PREDICTION_REPORT_PATH,
            ),
            data_dir,
        )
    )
    if results[-1]["returncode"] == 0:
        comparison_path = write_today_forecast_comparison()
        if comparison_path is not None:
            results.append(
                {
                    "step": "Samsung 단독 대비 최종 예측 비교 저장",
                    "script": str(comparison_path),
                    "returncode": 0,
                    "stdout": f"comparison: {comparison_path}",
                    "stderr": "",
                }
            )
        snapshot_path = save_today_forecast_snapshot()
        if snapshot_path is not None:
            results.append(
                {
                    "step": "오늘 밤 예측 스냅샷 저장",
                    "script": str(snapshot_path),
                    "returncode": 0,
                    "stdout": f"snapshot: {snapshot_path}",
                    "stderr": "",
                }
            )
    return results


def load_csv_if_exists(path: Path) -> pd.DataFrame:
    if not path.exists():
        return pd.DataFrame()
    return pd.read_csv(path, encoding="utf-8-sig")


def format_delta(value: float | None) -> str:
    if value is None or pd.isna(value):
        return "-"
    sign = "+" if value >= 0 else ""
    return f"{sign}{value:.3f}"


def probability_band(probability: float) -> str:
    if probability >= 0.64:
        return "상대적으로 높음"
    if probability >= 0.54:
        return "기준값 이상"
    if probability >= 0.44:
        return "경계 구간"
    return "낮음"


def format_prediction_target(value: object) -> str:
    timestamp = pd.to_datetime(value, errors="coerce")
    if pd.isna(timestamp):
        return "-"
    return timestamp.strftime("%Y-%m-%d %H:%M")


def forecast_subject(value: object) -> str:
    timestamp = pd.to_datetime(value, errors="coerce")
    if pd.isna(timestamp):
        return "이번 수면"
    today = datetime.now().date()
    target_date = timestamp.date()
    if target_date == today:
        return "오늘 밤 수면"
    if target_date > today:
        return f"{target_date:%Y-%m-%d} 밤 수면"
    return f"{target_date:%Y-%m-%d} 수면"


def forecast_sentence(value: object, probability: float | None, pred: int | None = None) -> str:
    subject = forecast_subject(value)
    target = format_prediction_target(value)
    if probability is None or pd.isna(probability):
        return f"지금까지의 데이터로 {subject}을 예측할 준비가 아직 충분하지 않습니다."
    if pred is None:
        label = "모델 점수 기준으로 해석 대기 상태입니다"
    elif pred == 1:
        label = "좋은 수면일 가능성이 더 높습니다"
    else:
        label = "좋은 수면 기준에는 못 미칠 가능성이 있습니다"
    return (
        f"지금까지의 데이터로 보면 {target}에 시작하는 {subject}은 "
        f"{label}. 모델 점수는 {probability:.3f}입니다."
    )


def safe_prediction_label(value: object) -> int | None:
    label = pd.to_numeric(value, errors="coerce")
    if pd.isna(label):
        return None
    return int(label)


def summarize_predictions(predictions: pd.DataFrame) -> dict:
    if predictions.empty:
        return {}
    prob = pd.to_numeric(predictions["good_sleep_probability"], errors="coerce")
    pred = pd.to_numeric(predictions["good_sleep_pred"], errors="coerce")
    return {
        "rows": len(predictions),
        "predicted_good": int(pred.sum()),
        "predicted_good_rate": float(pred.mean()),
        "mean_probability": float(prob.mean()),
        "median_probability": float(prob.median()),
        "max_probability": float(prob.max()),
        "latest_sleep_start": str(predictions["sleep_start_datetime"].max())
        if "sleep_start_datetime" in predictions.columns
        else "",
    }


def save_snapshot(predictions: pd.DataFrame) -> Path | None:
    if predictions.empty:
        return None
    SNAPSHOT_DIR.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    path = SNAPSHOT_DIR / f"samsung_pre_sleep_predictions_{timestamp}.csv"
    predictions.to_csv(path, index=False, encoding="utf-8-sig")
    return path


def latest_previous_snapshot() -> Path | None:
    if not SNAPSHOT_DIR.exists():
        return None
    snapshots = sorted(SNAPSHOT_DIR.glob("samsung_pre_sleep_predictions_*.csv"))
    return snapshots[-1] if snapshots else None


def compare_to_snapshot(current: pd.DataFrame, previous_path: Path | None) -> pd.DataFrame:
    if current.empty or previous_path is None or not previous_path.exists():
        return pd.DataFrame()
    previous = pd.read_csv(previous_path, encoding="utf-8-sig")
    if "sleep_episode_id" not in current.columns or "sleep_episode_id" not in previous.columns:
        return pd.DataFrame()
    merged = current.merge(
        previous[["sleep_episode_id", "good_sleep_probability"]].rename(
            columns={"good_sleep_probability": "previous_probability"}
        ),
        on="sleep_episode_id",
        how="left",
    )
    merged["probability_delta"] = (
        pd.to_numeric(merged["good_sleep_probability"], errors="coerce")
        - pd.to_numeric(merged["previous_probability"], errors="coerce")
    )
    return merged


def summarize_feature_sources(source_df: pd.DataFrame) -> dict:
    if source_df.empty:
        return {"raw_features": 0, "filled": 0, "missing": 0, "missing_rate": 0.0}
    raw_source_df = source_df[source_df["source"] != "not_used_by_design_c_stage1_contract"]
    missing = int(raw_source_df["is_missing_before_imputer"].sum())
    total = len(raw_source_df)
    return {
        "raw_features": total,
        "filled": total - missing,
        "missing": missing,
        "missing_rate": missing / total if total else 0.0,
    }


def value_is_present(value: object) -> bool:
    if value is None or pd.isna(value):
        return False
    if isinstance(value, str) and value.strip() == "":
        return False
    return True


def summarize_today_feature_coverage(raw_feature_df: pd.DataFrame) -> tuple[pd.DataFrame, dict]:
    if raw_feature_df.empty:
        return pd.DataFrame(), {"history_present": 0, "history_total": 0, "current_present": 0, "current_total": 0}

    row = raw_feature_df.iloc[0]
    rows = []
    summary = {"history_present": 0, "history_total": 0, "current_present": 0, "current_total": 0}

    for feature, label, group in TODAY_FORECAST_FEATURE_STATUS:
        value = row.get(feature, None)
        present = value_is_present(value)
        group_key = "history" if group == "history" else "current"
        summary[f"{group_key}_total"] += 1
        summary[f"{group_key}_present"] += int(present)
        rows.append(
            {
                "feature_group": "이력 기준" if group == "history" else "오늘 현재 웨어러블",
                "display_name": label,
                "feature": feature,
                "status": "반영됨" if present else "누락/결측 보완",
                "value": value if present else "",
            }
        )

    return pd.DataFrame(rows), summary


def svg_mask_url(filename: str) -> str:
    path = SVG_DIR / filename
    if not path.exists():
        return "none"
    svg = path.read_text(encoding="utf-8", errors="ignore")
    start = svg.find("<svg")
    if start > 0:
        svg = svg[start:]
    encoded = base64.b64encode(svg.encode("utf-8")).decode("ascii")
    return f"url(\"data:image/svg+xml;base64,{encoded}\")"


def render_app_style() -> None:
    tab_dashboard_icon = svg_mask_url("home-svgrepo-com.svg")
    tab_today_icon = svg_mask_url("night-svgrepo-com.svg")
    tab_episode_icon = svg_mask_url("document-filled-svgrepo-com.svg")
    tab_preset_icon = svg_mask_url("star-svgrepo-com.svg")
    tab_scenario_icon = svg_mask_url("scales-svgrepo-com.svg")
    tab_retrain_icon = svg_mask_url("brain-svgrepo-com.svg")
    tab_info_icon = svg_mask_url("database-02-svgrepo-com.svg")
    style = """
<style>
:root {
    --bg: #0F172A;
    --card: #1E293B;
    --card-soft: #273449;
    --primary: #38BDF8;
    --sleep-purple: #8B5CF6;
    --success: #22C55E;
    --warning: #F59E0B;
    --danger: #EF4444;
    --text-main: #F8FAFC;
    --text-sub: #CBD5E1;
    --border: #334155;
    --tab-dashboard-icon: __TAB_DASHBOARD_ICON__;
    --tab-today-icon: __TAB_TODAY_ICON__;
    --tab-episode-icon: __TAB_EPISODE_ICON__;
    --tab-preset-icon: __TAB_PRESET_ICON__;
    --tab-scenario-icon: __TAB_SCENARIO_ICON__;
    --tab-retrain-icon: __TAB_RETRAIN_ICON__;
    --tab-info-icon: __TAB_INFO_ICON__;
}
.stApp {
    background:
        radial-gradient(circle at 82% 8%, rgba(139, 92, 246, 0.20), transparent 25rem),
        radial-gradient(circle at 68% 18%, rgba(56, 189, 248, 0.14), transparent 24rem),
        linear-gradient(135deg, #050816 0%, var(--bg) 52%, #09111f 100%);
    color: var(--text-main);
}
header[data-testid="stHeader"] {
    background: transparent;
}
div[data-testid="stToolbar"],
div[data-testid="stDecoration"],
div[data-testid="stStatusWidget"] {
    display: none;
}
input,
textarea,
div[data-baseweb="select"] > div {
    background-color: rgba(15, 23, 42, 0.78) !important;
    color: var(--text-main) !important;
    -webkit-text-fill-color: var(--text-main) !important;
    border-color: rgba(51, 65, 85, 0.92) !important;
}
div[data-baseweb="select"] > div:focus-within {
    border-color: rgba(56, 189, 248, 0.9) !important;
    box-shadow: 0 0 0 1px rgba(56, 189, 248, 0.38), 0 0 22px rgba(56, 189, 248, 0.16) !important;
}
div[data-testid="stDateInput"] [data-baseweb="input"],
div[data-testid="stTimeInput"] [data-baseweb="input"],
div[data-testid="stNumberInput"] [data-baseweb="input"] {
    border-radius: 10px;
    background: rgba(15, 23, 42, 0.78) !important;
}
div[data-testid="stDateInput"] [data-baseweb="input"] > div,
div[data-testid="stTimeInput"] [data-baseweb="input"] > div,
div[data-testid="stNumberInput"] [data-baseweb="input"] > div {
    border-color: rgba(51, 65, 85, 0.92) !important;
    background: rgba(15, 23, 42, 0.78) !important;
    box-shadow: inset 0 1px 0 rgba(248, 250, 252, 0.03) !important;
}
div[data-testid="stDateInput"] [data-baseweb="input"] > div:hover,
div[data-testid="stTimeInput"] [data-baseweb="input"] > div:hover,
div[data-testid="stNumberInput"] [data-baseweb="input"] > div:hover {
    border-color: rgba(56, 189, 248, 0.58) !important;
}
div[data-testid="stDateInput"] [data-baseweb="input"] input,
div[data-testid="stTimeInput"] [data-baseweb="input"] input,
div[data-testid="stNumberInput"] [data-baseweb="input"] input {
    background: transparent !important;
    color: var(--text-main) !important;
    -webkit-text-fill-color: var(--text-main) !important;
}
div[data-testid="stWidgetLabel"],
div[data-testid="stWidgetLabel"] label,
div[data-testid="stWidgetLabel"] p,
label,
label p {
    color: var(--text-sub) !important;
    -webkit-text-fill-color: var(--text-sub) !important;
    opacity: 1 !important;
}
div[data-baseweb="input"] input,
div[data-baseweb="base-input"] input,
div[data-baseweb="select"] span,
div[data-baseweb="select"] div {
    color: var(--text-main) !important;
    -webkit-text-fill-color: var(--text-main) !important;
}
button[aria-label="Increment"],
button[aria-label="Decrement"],
div[data-testid="stNumberInput"] button {
    background: rgba(30, 41, 59, 0.95) !important;
    color: var(--text-main) !important;
    border-color: rgba(51, 65, 85, 0.92) !important;
    box-shadow: none !important;
}
button[aria-label="Increment"]:hover,
button[aria-label="Decrement"]:hover,
div[data-testid="stNumberInput"] button:hover {
    background: rgba(56, 189, 248, 0.18) !important;
    color: var(--primary) !important;
}
div[data-testid="stNumberInput"] button svg {
    fill: currentColor !important;
}
section[data-testid="stSidebar"] {
    background:
        radial-gradient(circle at 50% 5%, rgba(139, 92, 246, 0.24), transparent 11rem),
        linear-gradient(180deg, rgba(15, 23, 42, 0.98), rgba(2, 6, 23, 0.98));
    border-right: 1px solid var(--border);
    min-height: 100vh;
}
section[data-testid="stSidebar"] * {
    color: var(--text-main);
}
section[data-testid="stSidebar"] input,
section[data-testid="stSidebar"] textarea,
section[data-testid="stSidebar"] [data-baseweb="input"] input {
    color: var(--text-main) !important;
    -webkit-text-fill-color: var(--text-main) !important;
    opacity: 1 !important;
}
section[data-testid="stSidebar"] input:disabled {
    color: #E2E8F0 !important;
    -webkit-text-fill-color: #E2E8F0 !important;
}
.block-container {
    max-width: 1480px;
    padding-top: 1.4rem;
    padding-bottom: 2rem;
}
h1, h2, h3, p, label, span {
    letter-spacing: 0;
}
div[data-testid="stMetric"] {
    border: 1px solid rgba(51, 65, 85, 0.9);
    border-radius: 18px;
    padding: 0.9rem 1rem;
    background: linear-gradient(145deg, rgba(30, 41, 59, 0.92), rgba(15, 23, 42, 0.96));
    box-shadow: inset 0 1px 0 rgba(248, 250, 252, 0.04), 0 12px 30px rgba(2, 6, 23, 0.35);
}
div[data-testid="stMetric"] [data-testid="stMetricLabel"] {
    color: var(--text-sub);
}
div[data-testid="stMetric"] [data-testid="stMetricValue"] {
    color: var(--text-main);
}
div[data-testid="stMetric"] [data-testid="stMetricValue"] > div {
    font-size: clamp(1.25rem, 1.9vw, 2rem);
    line-height: 1.15;
    white-space: normal;
    overflow: visible;
    text-overflow: clip;
    overflow-wrap: anywhere;
}
div[data-testid="stMetric"] [data-testid="stMetricLabel"] p {
    white-space: normal;
}
.prototype-note {
    border: 1px solid rgba(139, 92, 246, 0.38);
    border-left: 4px solid var(--sleep-purple);
    border-radius: 16px;
    padding: 0.9rem 1rem;
    background: linear-gradient(135deg, rgba(39, 52, 73, 0.94), rgba(30, 27, 75, 0.78));
    color: var(--text-main);
    margin: 0.35rem 0 1rem 0;
}
.prototype-strip {
    border: 1px solid rgba(51, 65, 85, 0.92);
    border-radius: 18px;
    padding: 1rem;
    background: linear-gradient(145deg, rgba(30, 41, 59, 0.92), rgba(15, 23, 42, 0.96));
}
.small-label {
    color: var(--text-sub);
    font-size: 0.86rem;
}
.main-title-wrap {
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 1rem;
    margin-bottom: 1rem;
}
.brand-lockup {
    display: flex;
    align-items: center;
    gap: 1rem;
}
.brand-mark {
    width: 66px;
    height: 66px;
    border-radius: 20px;
    display: grid;
    place-items: center;
    background: radial-gradient(circle at 35% 25%, #F8FAFC 0 10%, transparent 11%), linear-gradient(135deg, #38BDF8, #8B5CF6);
    box-shadow: 0 0 28px rgba(56, 189, 248, 0.32);
    font-size: 1.8rem;
    color: var(--text-main);
}
.main-title {
    font-size: clamp(2.3rem, 3.4vw, 3.55rem);
    line-height: 1.05;
    font-weight: 800;
    color: var(--text-main);
}
.main-subtitle {
    margin-top: 0.35rem;
    color: var(--text-sub);
    font-size: 1.06rem;
}
.live-pill {
    border: 1px solid rgba(56, 189, 248, 0.45);
    border-radius: 999px;
    padding: 0.42rem 0.78rem;
    color: var(--text-main);
    background: rgba(15, 23, 42, 0.74);
    box-shadow: inset 0 0 20px rgba(56, 189, 248, 0.10);
    white-space: nowrap;
}
.sleep-dashboard {
    display: grid;
    gap: 1rem;
}
.svg-icon {
    display: inline-grid;
    place-items: center;
    width: 1.15em;
    height: 1.15em;
    color: currentColor;
    line-height: 1;
}
.nav-icon {
    display: inline-grid;
    place-items: center;
    width: 1rem;
    height: 1rem;
    margin-right: 0.35rem;
    color: currentColor;
    line-height: 1;
    vertical-align: -0.14rem;
}
.nav-icon img {
    width: 100%;
    height: 100%;
    display: block;
}
.svg-icon svg {
    width: 100%;
    height: 100%;
    display: block;
    fill: currentColor;
    stroke: currentColor;
}
.svg-icon img {
    width: 100%;
    height: 100%;
    display: block;
}
.masked-svg-icon {
    background: var(--icon-color, currentColor);
    -webkit-mask-image: var(--icon-mask);
    mask-image: var(--icon-mask);
    -webkit-mask-position: center;
    mask-position: center;
    -webkit-mask-repeat: no-repeat;
    mask-repeat: no-repeat;
    -webkit-mask-size: contain;
    mask-size: contain;
}
.brand-mark .svg-icon {
    width: 40px;
    height: 40px;
}
.card-icon .svg-icon,
.kpi-icon .svg-icon {
    width: 30px;
    height: 30px;
}
.sleep-hero {
    position: relative;
    overflow: hidden;
    min-height: 265px;
    border: 1px solid rgba(51, 65, 85, 0.94);
    border-radius: 24px;
    padding: 2.2rem;
    background:
        radial-gradient(circle at 78% 20%, rgba(248, 250, 252, 0.85) 0 0.35rem, transparent 0.42rem),
        radial-gradient(circle at 88% 34%, rgba(248, 250, 252, 0.55) 0 0.16rem, transparent 0.22rem),
        linear-gradient(110deg, rgba(15, 23, 42, 0.96) 0%, rgba(15, 23, 42, 0.78) 48%, rgba(49, 46, 129, 0.52) 100%),
        radial-gradient(circle at 82% 48%, rgba(139, 92, 246, 0.28), transparent 20rem),
        linear-gradient(180deg, #111827, #020617);
    box-shadow: inset 0 1px 0 rgba(248, 250, 252, 0.05), 0 24px 60px rgba(2, 6, 23, 0.45);
}
.sleep-hero::before {
    content: "";
    position: absolute;
    inset: auto 0 0 40%;
    height: 54%;
    background:
        linear-gradient(145deg, transparent 36%, rgba(15, 23, 42, 0.75) 37% 46%, transparent 47%),
        radial-gradient(ellipse at 72% 100%, rgba(56, 189, 248, 0.18), transparent 30%),
        linear-gradient(180deg, transparent, rgba(2, 6, 23, 0.94));
    opacity: 0.95;
}
.sleep-hero::after {
    content: "";
    position: absolute;
    right: 2.2rem;
    top: 1.7rem;
    width: 88px;
    height: 88px;
    border-radius: 999px;
    background: radial-gradient(circle at 62% 40%, #0F172A 0 36%, transparent 37%), linear-gradient(135deg, #FDE68A, #A78BFA 72%);
    box-shadow: 0 0 34px rgba(139, 92, 246, 0.46);
}
.sleep-hero-content {
    position: relative;
    z-index: 1;
    display: grid;
    grid-template-columns: minmax(0, 1.08fr) minmax(250px, 0.82fr);
    align-items: center;
    gap: 1.6rem;
}
.hero-copy h2 {
    margin: 0 0 0.75rem 0;
    font-size: clamp(2.2rem, 4vw, 4rem);
    line-height: 1.05;
    color: var(--text-main);
}
.hero-copy p {
    max-width: 600px;
    color: var(--text-sub);
    font-size: 1.08rem;
    margin: 0.15rem 0;
}
.hero-script {
    margin-top: 1.4rem;
    color: #C4B5FD;
    font-size: 1.05rem;
}
.probability-card {
    border: 1px solid rgba(148, 163, 184, 0.24);
    border-radius: 26px;
    padding: 1.45rem;
    background: linear-gradient(135deg, rgba(15, 23, 42, 0.82), rgba(30, 41, 59, 0.58));
    backdrop-filter: blur(12px);
    box-shadow: inset 0 1px 0 rgba(248, 250, 252, 0.06), 0 18px 50px rgba(2, 6, 23, 0.34);
}
.probability-value {
    font-size: clamp(3.3rem, 6vw, 5rem);
    font-weight: 850;
    line-height: 0.95;
    margin: 0.55rem 0 0.45rem;
    background: linear-gradient(100deg, var(--primary), #818CF8 45%, var(--sleep-purple));
    -webkit-background-clip: text;
    color: transparent;
}
.probability-band {
    color: #C084FC;
    font-size: 1.25rem;
}
.ring-wrap {
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 1rem;
}
.sleep-ring {
    --p: 64%;
    width: 122px;
    aspect-ratio: 1;
    border-radius: 999px;
    display: grid;
    place-items: center;
    background: conic-gradient(var(--primary) 0 var(--p), var(--sleep-purple) var(--p) calc(var(--p) + 18%), rgba(30, 41, 59, 0.9) 0);
    box-shadow: 0 0 32px rgba(139, 92, 246, 0.25);
}
.sleep-ring span {
    width: 90px;
    aspect-ratio: 1;
    border-radius: 999px;
    display: grid;
    place-items: center;
    background: #0B1220;
    color: #C4B5FD;
    font-size: 2rem;
}
.sleep-ring .svg-icon {
    width: 48px;
    height: 48px;
}
.sleep-ring .svg-icon img {
}
.kpi-grid {
    display: grid;
    grid-template-columns: repeat(4, minmax(0, 1fr));
    gap: 1rem;
}
.kpi-card, .panel-card {
    border: 1px solid rgba(51, 65, 85, 0.9);
    border-radius: 20px;
    background: linear-gradient(145deg, rgba(30, 41, 59, 0.92), rgba(15, 23, 42, 0.97));
    box-shadow: inset 0 1px 0 rgba(248, 250, 252, 0.04), 0 18px 44px rgba(2, 6, 23, 0.28);
}
.kpi-card {
    padding: 1.15rem;
    display: grid;
    grid-template-columns: auto 1fr;
    gap: 0.9rem;
    align-items: center;
}
.kpi-icon {
    width: 50px;
    height: 50px;
    border-radius: 16px;
    display: grid;
    place-items: center;
    background: rgba(56, 189, 248, 0.13);
    color: var(--primary);
    font-weight: 800;
}
.kpi-title {
    color: var(--text-sub);
    font-size: 0.9rem;
}
.kpi-value {
    color: var(--text-main);
    font-size: 1.85rem;
    font-weight: 780;
    line-height: 1.1;
}
.accent-purple { color: var(--sleep-purple); }
.accent-blue { color: var(--primary); }
.accent-green { color: var(--success); }
.accent-amber { color: var(--warning); }
.accent-red { color: var(--danger); }
.lower-grid {
    display: grid;
    grid-template-columns: minmax(310px, 0.96fr) minmax(430px, 1.34fr) minmax(310px, 0.98fr);
    gap: 1rem;
    align-items: stretch;
}
.lower-grid > .panel-card,
.lower-grid > div,
.lower-grid > div > .panel-card {
    height: 100%;
}
.panel-card {
    padding: 1.15rem 1.2rem;
}
.panel-title {
    color: var(--text-main);
    font-weight: 760;
    font-size: 1.15rem;
    margin-bottom: 1rem;
}
.feature-row, .summary-row {
    display: grid;
    grid-template-columns: 1fr auto;
    gap: 1rem;
    align-items: center;
    margin: 0.82rem 0;
    color: var(--text-sub);
}
.feature-row {
    grid-template-columns: minmax(128px, 0.9fr) minmax(120px, 1.2fr) 42px;
    gap: 0.75rem;
    margin: 0.62rem 0;
}
.feature-label {
    display: inline-flex;
    align-items: center;
    gap: 0.45rem;
    min-width: 0;
}
.feature-label .nav-icon {
    width: 1.05rem;
    height: 1.05rem;
    margin-right: 0;
    flex: 0 0 auto;
}
.feature-progress {
    display: block;
    align-items: center;
    min-width: 0;
}
.feature-progress b {
    display: block;
    text-align: right;
    white-space: nowrap;
}
.feature-row > b,
.feature-progress + b {
    text-align: right;
}
.summary-row span,
.feature-row > div {
    min-width: 0;
}
.summary-row span {
    display: inline-flex;
    align-items: center;
    gap: 0.45rem;
}
.summary-row .nav-icon {
    width: 1.15rem;
    height: 1.15rem;
    margin-right: 0;
    flex: 0 0 auto;
}
.summary-row b {
    text-align: right;
    white-space: nowrap;
}
.bar {
    height: 9px;
    border-radius: 999px;
    background: rgba(51, 65, 85, 0.55);
    overflow: hidden;
    margin-top: 0.45rem;
}
.bar span {
    display: block;
    height: 100%;
    border-radius: inherit;
}
.scenario-row {
    display: grid;
    grid-template-columns: minmax(168px, max-content) minmax(180px, 1fr) 64px;
    gap: 0.8rem;
    align-items: center;
    margin: 0.82rem 0;
    color: var(--text-sub);
}
.scenario-row > span {
    display: inline-flex;
    align-items: center;
    gap: 0.45rem;
    white-space: nowrap;
}
.scenario-row > span .nav-icon {
    margin-right: 0;
    flex: 0 0 auto;
}
.status-pill {
    border-radius: 999px;
    padding: 0.18rem 0.5rem;
    border: 1px solid currentColor;
    font-size: 0.8rem;
}
.caveat-card {
    margin-top: 1rem;
    border-color: rgba(139, 92, 246, 0.5);
    background: linear-gradient(135deg, rgba(49, 46, 129, 0.62), rgba(30, 41, 59, 0.86));
}
.dashboard-upload-row {
    display: grid;
    grid-template-columns: minmax(280px, 0.72fr) minmax(620px, 2fr);
    gap: 1rem;
    align-items: stretch;
}
.dashboard-upload-row .caveat-card {
    margin-top: 0;
    min-height: 150px;
}
.zip-panel {
    display: grid;
    grid-template-columns: minmax(300px, 0.9fr) minmax(360px, 1.1fr);
    gap: 1.15rem;
    align-items: center;
}
.zip-widget-panel {
    border: 1px solid rgba(51, 65, 85, 0.9);
    border-radius: 18px;
    padding: 1.15rem;
    background: linear-gradient(145deg, rgba(30, 41, 59, 0.92), rgba(15, 23, 42, 0.97));
    box-shadow: inset 0 1px 0 rgba(248, 250, 252, 0.04), 0 18px 44px rgba(2, 6, 23, 0.24);
}
.zip-widget-panel h4 {
    margin: 0 0 0.85rem;
    color: var(--text-main);
    font-size: 1.22rem;
}
div[data-testid="stFileUploader"] section {
    min-height: 98px;
    border: 1px dashed rgba(148, 163, 184, 0.56) !important;
    border-radius: 16px !important;
    background: rgba(15, 23, 42, 0.42) !important;
}
div[data-testid="stFileUploader"] section:hover {
    border-color: rgba(56, 189, 248, 0.75) !important;
    background: rgba(15, 23, 42, 0.58) !important;
}
div[data-testid="stFileUploader"] section > div {
    color: var(--text-sub) !important;
}
div[data-testid="stFileUploader"] label,
div[data-testid="stFileUploader"] small,
div[data-testid="stFileUploader"] p,
div[data-testid="stFileUploader"] span {
    color: var(--text-sub) !important;
    -webkit-text-fill-color: var(--text-sub) !important;
}
div[data-testid="stFileUploader"] button {
    border-radius: 12px !important;
    border: 1px solid rgba(139, 92, 246, 0.58) !important;
    background: linear-gradient(135deg, #2563EB, #7C3AED) !important;
    color: var(--text-main) !important;
    -webkit-text-fill-color: var(--text-main) !important;
}
div[data-testid="stVerticalBlockBorderWrapper"] {
    border: 1px solid rgba(71, 85, 105, 0.95) !important;
    border-radius: 18px !important;
    background: linear-gradient(145deg, rgba(30, 41, 59, 0.92), rgba(15, 23, 42, 0.98)) !important;
    box-shadow: inset 0 1px 0 rgba(248, 250, 252, 0.05), 0 18px 44px rgba(2, 6, 23, 0.24);
}
.zip-dropzone {
    min-height: 98px;
    border: 1px dashed rgba(148, 163, 184, 0.56);
    border-radius: 16px;
    padding: 1rem 1.1rem;
    display: grid;
    grid-template-columns: auto 1fr auto;
    align-items: center;
    gap: 1rem;
    background: rgba(15, 23, 42, 0.42);
}
.zip-file-icon {
    width: 58px;
    height: 58px;
    border-radius: 14px;
    display: grid;
    place-items: center;
    border: 1px solid rgba(139, 92, 246, 0.55);
    background: rgba(49, 46, 129, 0.38);
    color: #C4B5FD;
    font-weight: 850;
    letter-spacing: 0;
}
.zip-drop-title {
    color: var(--text-main);
    font-size: 1.08rem;
    font-weight: 800;
}
.zip-drop-sub {
    margin-top: 0.25rem;
    color: var(--text-sub);
    font-size: 0.82rem;
}
.zip-select-btn {
    border-radius: 12px;
    padding: 0.58rem 0.9rem;
    background: linear-gradient(135deg, #2563EB, #7C3AED);
    color: var(--text-main);
    font-weight: 760;
    white-space: nowrap;
}
.zip-status {
    display: grid;
    gap: 0.65rem;
}
.zip-progress-head {
    display: flex;
    align-items: center;
    justify-content: space-between;
    color: var(--text-sub);
    font-weight: 760;
}
.zip-progress {
    height: 10px;
    border-radius: 999px;
    background: rgba(51, 65, 85, 0.76);
    overflow: hidden;
}
.zip-progress span {
    display: block;
    height: 100%;
    border-radius: inherit;
    background: linear-gradient(90deg, var(--success), var(--primary));
}
.zip-steps {
    display: grid;
    grid-template-columns: repeat(5, minmax(0, 1fr));
    gap: 0.25rem;
    position: relative;
}
.zip-step {
    text-align: center;
    color: var(--text-sub);
    font-size: 0.76rem;
    line-height: 1.35;
}
.zip-dot {
    width: 26px;
    height: 26px;
    margin: 0 auto 0.35rem;
    border-radius: 999px;
    display: grid;
    place-items: center;
    background: rgba(71, 85, 105, 0.9);
    color: var(--text-main);
    font-weight: 800;
}
.zip-step.done .zip-dot {
    background: var(--success);
}
.zip-step.active .zip-dot {
    background: linear-gradient(135deg, #2563EB, var(--sleep-purple));
    box-shadow: 0 0 18px rgba(56, 189, 248, 0.28);
}
.zip-step.done {
    color: #86EFAC;
}
.zip-step.active {
    color: #BAE6FD;
}
.zip-current {
    color: var(--text-sub);
    font-size: 0.84rem;
    border-top: 1px solid rgba(51, 65, 85, 0.78);
    padding-top: 0.58rem;
}
.live-page {
    display: grid;
    gap: 1rem;
}
.live-hero {
    position: relative;
    min-height: 170px;
    overflow: hidden;
    border: 1px solid rgba(51, 65, 85, 0.9);
    border-radius: 22px;
    padding: 1.8rem 2rem;
    background:
        radial-gradient(circle at 82% 24%, rgba(253, 230, 138, 0.95) 0 0.38rem, transparent 0.45rem),
        radial-gradient(circle at 75% 38%, rgba(248, 250, 252, 0.62) 0 0.12rem, transparent 0.18rem),
        radial-gradient(circle at 90% 68%, rgba(56, 189, 248, 0.14), transparent 18rem),
        linear-gradient(110deg, rgba(15, 23, 42, 0.99) 0%, rgba(15, 23, 42, 0.9) 58%, rgba(49, 46, 129, 0.58) 100%);
    box-shadow: inset 0 1px 0 rgba(248, 250, 252, 0.05), 0 20px 55px rgba(2, 6, 23, 0.36);
}
.live-hero::after {
    content: "";
    position: absolute;
    right: 3.2rem;
    top: 2.1rem;
    width: 72px;
    height: 72px;
    border-radius: 999px;
    background:
        radial-gradient(circle at 62% 38%, rgba(15, 23, 42, 0.99) 0 38%, transparent 39%),
        linear-gradient(135deg, #FDE68A, #A78BFA 72%);
    box-shadow: 0 0 32px rgba(139, 92, 246, 0.36);
    opacity: 0.95;
}
.live-hero h2 {
    position: relative;
    z-index: 1;
    margin: 0 0 0.45rem;
    font-size: clamp(2.2rem, 4vw, 3.4rem);
    line-height: 1.05;
}
.live-hero p {
    position: relative;
    z-index: 1;
    max-width: 720px;
    color: var(--text-sub);
    margin: 0.3rem 0;
}
.live-badge {
    display: inline-flex;
    align-items: center;
    gap: 0.35rem;
    margin-left: 0.55rem;
    padding: 0.24rem 0.55rem;
    border: 1px solid rgba(139, 92, 246, 0.52);
    border-radius: 999px;
    color: #C4B5FD;
    background: rgba(49, 46, 129, 0.36);
    font-size: 0.95rem;
    vertical-align: middle;
}
.live-top-grid {
    display: grid;
    grid-template-columns: minmax(360px, 1.05fr) minmax(360px, 0.95fr);
    gap: 1rem;
}
.live-section-card {
    border: 1px solid rgba(51, 65, 85, 0.9);
    border-radius: 20px;
    padding: 1.25rem;
    background: linear-gradient(145deg, rgba(30, 41, 59, 0.92), rgba(15, 23, 42, 0.97));
    box-shadow: inset 0 1px 0 rgba(248, 250, 252, 0.04), 0 18px 44px rgba(2, 6, 23, 0.24);
}
.live-section-title {
    display: flex;
    align-items: center;
    gap: 0.75rem;
    margin-bottom: 1rem;
    color: var(--text-main);
    font-size: 1.2rem;
    font-weight: 780;
}
.step-badge {
    width: 36px;
    height: 36px;
    border-radius: 999px;
    display: grid;
    place-items: center;
    background: linear-gradient(135deg, #2563EB, var(--sleep-purple));
    color: var(--text-main);
    box-shadow: 0 0 24px rgba(139, 92, 246, 0.36);
}
.export-grid {
    display: grid;
    grid-template-columns: minmax(0, 1fr) minmax(220px, 0.9fr);
    gap: 1rem;
}
.status-list {
    display: grid;
    gap: 0.55rem;
}
.status-item,
.mini-input-card {
    border: 1px solid rgba(51, 65, 85, 0.72);
    border-radius: 14px;
    padding: 0.75rem;
    background: rgba(15, 23, 42, 0.55);
}
.status-item {
    display: grid;
    grid-template-columns: auto 1fr auto;
    align-items: center;
    gap: 0.65rem;
    color: var(--text-sub);
}
.status-item b {
    color: var(--text-main);
}
.manual-preview-grid {
    display: grid;
    grid-template-columns: repeat(3, minmax(0, 1fr));
    gap: 0.75rem;
}
.mini-input-top {
    display: flex;
    align-items: center;
    gap: 0.45rem;
}
.mini-input-top .nav-icon {
    width: 1.15rem;
    height: 1.15rem;
    margin-right: 0;
    flex: 0 0 auto;
}
.mini-input-label {
    color: var(--text-sub);
    font-size: 0.82rem;
}
.mini-input-value {
    color: var(--text-main);
    margin-top: 0.35rem;
    font-size: 1.08rem;
    font-weight: 750;
}
.live-result-grid {
    display: grid;
    grid-template-columns: repeat(3, minmax(0, 1fr));
    gap: 1rem;
}
.compact-ring-row {
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 1rem;
}
.manual-widget-shell {
    margin-top: 1rem;
    border: 1px solid rgba(51, 65, 85, 0.9);
    border-radius: 20px;
    padding: 1rem 1.2rem 1.2rem;
    background: linear-gradient(145deg, rgba(30, 41, 59, 0.72), rgba(15, 23, 42, 0.94));
}
.manual-widget-shell div[data-testid="stCheckbox"] label,
.manual-widget-shell div[data-testid="stCheckbox"] label p,
div[data-testid="stCheckbox"] label,
div[data-testid="stCheckbox"] label p {
    color: var(--text-main) !important;
    -webkit-text-fill-color: var(--text-main) !important;
    opacity: 1 !important;
}
.manual-widget-shell div[data-testid="stCheckbox"] {
    border: 1px solid rgba(51, 65, 85, 0.72);
    border-radius: 10px;
    padding: 0.55rem 0.7rem;
    background: rgba(15, 23, 42, 0.55);
}
.today-stat-grid {
    display: grid;
    grid-template-columns: repeat(4, minmax(0, 1fr));
    gap: 0.75rem;
    margin: 0.65rem 0 1rem;
}
.today-stat-card {
    min-height: 92px;
    border: 1px solid rgba(51, 65, 85, 0.86);
    border-radius: 14px;
    padding: 0.9rem 1rem;
    background: linear-gradient(145deg, rgba(30, 41, 59, 0.9), rgba(15, 23, 42, 0.96));
    box-shadow: inset 0 1px 0 rgba(248, 250, 252, 0.04);
    display: flex;
    flex-direction: column;
    justify-content: center;
}
.today-stat-label {
    color: var(--text-sub);
    font-size: 0.82rem;
    font-weight: 700;
}
.today-stat-value {
    color: var(--text-main);
    font-size: 1.75rem;
    font-weight: 800;
    line-height: 1.12;
    margin-top: 0.35rem;
}
.today-stat-delta {
    color: var(--success);
    font-size: 0.78rem;
    font-weight: 760;
    margin-top: 0.25rem;
}
.live-flow {
    color: var(--text-sub);
    font-family: ui-monospace, SFMono-Regular, Consolas, "Liberation Mono", monospace;
    font-size: 0.84rem;
    line-height: 1.6;
}
div[data-baseweb="tab-list"] {
    gap: 0.8rem;
    background: rgba(15, 23, 42, 0.55);
    border: 1px solid rgba(51, 65, 85, 0.7);
    border-radius: 18px;
    padding: 0.48rem;
    overflow-x: auto;
}
button[data-baseweb="tab"] {
    border-radius: 14px;
    color: var(--text-sub);
    min-height: 42px;
    padding: 0.55rem 0.92rem;
}
button[data-baseweb="tab"] p {
    display: inline-flex;
    align-items: center;
    gap: 0.45rem;
    font-size: 1.02rem;
    font-weight: 760;
    line-height: 1.05;
    letter-spacing: 0;
}
button[data-baseweb="tab"] p::before {
    content: "";
    width: 1.1rem;
    height: 1.1rem;
    flex: 0 0 auto;
    background: currentColor;
    -webkit-mask-position: center;
    mask-position: center;
    -webkit-mask-repeat: no-repeat;
    mask-repeat: no-repeat;
    -webkit-mask-size: contain;
    mask-size: contain;
}
button[data-baseweb="tab"]:nth-of-type(1) p::before {
    -webkit-mask-image: var(--tab-dashboard-icon);
    mask-image: var(--tab-dashboard-icon);
}
button[data-baseweb="tab"]:nth-of-type(2) p::before {
    -webkit-mask-image: var(--tab-today-icon);
    mask-image: var(--tab-today-icon);
}
button[data-baseweb="tab"]:nth-of-type(3) p::before {
    -webkit-mask-image: var(--tab-episode-icon);
    mask-image: var(--tab-episode-icon);
}
button[data-baseweb="tab"]:nth-of-type(4) p::before {
    -webkit-mask-image: var(--tab-preset-icon);
    mask-image: var(--tab-preset-icon);
}
button[data-baseweb="tab"]:nth-of-type(5) p::before {
    -webkit-mask-image: var(--tab-scenario-icon);
    mask-image: var(--tab-scenario-icon);
}
button[data-baseweb="tab"]:nth-of-type(6) p::before {
    -webkit-mask-image: var(--tab-retrain-icon);
    mask-image: var(--tab-retrain-icon);
}
button[data-baseweb="tab"]:nth-of-type(7) p::before {
    -webkit-mask-image: var(--tab-info-icon);
    mask-image: var(--tab-info-icon);
}
button[data-baseweb="tab"][aria-selected="true"] {
    color: var(--text-main);
    background: linear-gradient(135deg, rgba(56, 189, 248, 0.18), rgba(139, 92, 246, 0.20));
}
div[data-testid="stExpander"] {
    border: 1px solid rgba(51, 65, 85, 0.74);
    border-radius: 12px;
    background: rgba(15, 23, 42, 0.46);
    overflow: hidden;
    box-shadow: inset 0 1px 0 rgba(248, 250, 252, 0.03);
}
div[data-testid="stExpander"] details {
    background: transparent;
}
div[data-testid="stExpander"] summary {
    min-height: 44px;
    color: var(--text-main) !important;
    background: linear-gradient(145deg, rgba(15, 23, 42, 0.88), rgba(17, 24, 39, 0.78)) !important;
    border-radius: 11px;
}
div[data-testid="stExpander"] summary:hover {
    background: linear-gradient(145deg, rgba(30, 41, 59, 0.92), rgba(15, 23, 42, 0.88)) !important;
}
div[data-testid="stExpander"] details[open] {
    border-color: rgba(139, 92, 246, 0.58);
    background: linear-gradient(145deg, rgba(30, 41, 59, 0.78), rgba(15, 23, 42, 0.96));
}
div[data-testid="stExpander"] details[open] summary {
    color: var(--text-main) !important;
    background: linear-gradient(135deg, rgba(49, 46, 129, 0.46), rgba(30, 41, 59, 0.92)) !important;
    border-bottom: 1px solid rgba(139, 92, 246, 0.45);
    border-radius: 11px 11px 0 0;
}
div[data-testid="stExpanderDetails"] {
    color: var(--text-main);
    background: linear-gradient(180deg, rgba(30, 41, 59, 0.88), rgba(15, 23, 42, 0.95)) !important;
}
div[data-testid="stExpanderDetails"] h2,
div[data-testid="stExpanderDetails"] h3,
div[data-testid="stExpanderDetails"] p,
div[data-testid="stExpanderDetails"] span,
div[data-testid="stExpanderDetails"] label {
    color: var(--text-main);
}
div[data-testid="stExpanderDetails"] div[data-testid="stDataFrame"] {
    border: 1px solid rgba(51, 65, 85, 0.86);
    border-radius: 10px;
    overflow: hidden;
    background: rgba(15, 23, 42, 0.72);
}
.stButton > button {
    border-radius: 16px;
    border: 1px solid rgba(56, 189, 248, 0.55);
    background: linear-gradient(135deg, #2563EB, #7C3AED);
    box-shadow: 0 0 26px rgba(56, 189, 248, 0.30);
    color: var(--text-main);
}
div[data-testid="stDownloadButton"] > button {
    border-radius: 12px;
    border: 1px solid rgba(56, 189, 248, 0.62);
    background: linear-gradient(135deg, rgba(37, 99, 235, 0.92), rgba(124, 58, 237, 0.92));
    color: var(--text-main) !important;
    -webkit-text-fill-color: var(--text-main) !important;
    box-shadow: 0 0 22px rgba(56, 189, 248, 0.24);
}
div[data-testid="stDownloadButton"] > button p,
div[data-testid="stDownloadButton"] > button span {
    color: var(--text-main) !important;
    -webkit-text-fill-color: var(--text-main) !important;
    opacity: 1 !important;
}
div[data-testid="stDownloadButton"] > button:hover {
    border-color: rgba(56, 189, 248, 0.95);
    background: linear-gradient(135deg, #2563EB, #7C3AED);
    color: var(--text-main) !important;
}
div[data-testid="stDownloadButton"] > button:disabled,
div[data-testid="stDownloadButton"] > button[disabled] {
    border-color: rgba(148, 163, 184, 0.42);
    background: rgba(30, 41, 59, 0.86);
    color: #CBD5E1 !important;
    -webkit-text-fill-color: #CBD5E1 !important;
    opacity: 1;
}
@media (max-width: 1350px) {
    .lower-grid,
    .dashboard-upload-row,
    .zip-panel,
    .live-top-grid,
    .live-result-grid,
    .today-stat-grid,
    .export-grid {
        grid-template-columns: 1fr;
    }
    .kpi-grid {
        grid-template-columns: repeat(2, minmax(0, 1fr));
    }
    .sleep-ring {
        width: 84px;
    }
    .sleep-ring span {
        width: 62px;
        font-size: 1.45rem;
    }
    .probability-value {
        font-size: 4.1rem;
    }
    .probability-card {
        padding: 1.1rem;
    }
    .ring-wrap {
        gap: 0.45rem;
    }
}
@media (max-width: 900px) {
    .sleep-hero-content, .kpi-grid {
        grid-template-columns: 1fr;
    }
}
</style>
"""
    style = (
        style.replace("__TAB_DASHBOARD_ICON__", tab_dashboard_icon)
        .replace("__TAB_TODAY_ICON__", tab_today_icon)
        .replace("__TAB_EPISODE_ICON__", tab_episode_icon)
        .replace("__TAB_PRESET_ICON__", tab_preset_icon)
        .replace("__TAB_SCENARIO_ICON__", tab_scenario_icon)
        .replace("__TAB_RETRAIN_ICON__", tab_retrain_icon)
        .replace("__TAB_INFO_ICON__", tab_info_icon)
    )
    st.markdown(
        style,
        unsafe_allow_html=True,
    )


def render_html(markup: str) -> None:
    st.html("\n".join(line.lstrip() for line in markup.splitlines()))


@st.cache_data(show_spinner=False)
def load_svg(filename: str) -> str:
    path = SVG_DIR / filename
    if not path.exists():
        return ""
    svg = path.read_text(encoding="utf-8", errors="ignore")
    start = svg.find("<svg")
    if start > 0:
        svg = svg[start:]
    replacements = {
        "#000000": "currentColor",
        "#000": "currentColor",
        "black": "currentColor",
        'width="800px"': "",
        'height="800px"': "",
    }
    for before, after in replacements.items():
        svg = svg.replace(before, after)
    return svg


def svg_icon(filename: str, class_name: str = "svg-icon", color: str = "#CBD5E1") -> str:
    svg = load_svg(filename)
    if not svg:
        return ""
    svg = svg.replace("currentColor", color)
    svg = re.sub(r'fill="(?!none\b)[^"]*"', f'fill="{color}"', svg, flags=re.IGNORECASE)
    svg = re.sub(r"fill='(?!none\b)[^']*'", f"fill='{color}'", svg, flags=re.IGNORECASE)
    svg = re.sub(r'stroke="(?!none\b)[^"]*"', f'stroke="{color}"', svg, flags=re.IGNORECASE)
    svg = re.sub(r"stroke='(?!none\b)[^']*'", f"stroke='{color}'", svg, flags=re.IGNORECASE)
    svg = re.sub(r'fill\s*:\s*(?!none\b)[^;"}]+', f"fill:{color}", svg, flags=re.IGNORECASE)
    svg = re.sub(r'stroke\s*:\s*(?!none\b)[^;"}]+', f"stroke:{color}", svg, flags=re.IGNORECASE)
    encoded = base64.b64encode(svg.encode("utf-8")).decode("ascii")
    return f'<span class="{class_name}"><img src="data:image/svg+xml;base64,{encoded}" alt="" /></span>'


def masked_svg_icon(filename: str, class_name: str = "nav-icon", color: str = "#CBD5E1") -> str:
    svg = load_svg(filename)
    if not svg:
        return ""
    encoded = base64.b64encode(svg.encode("utf-8")).decode("ascii")
    return (
        f'<span class="{class_name} masked-svg-icon" '
        f'style="--icon-color: {color}; --icon-mask: url(&quot;data:image/svg+xml;base64,{encoded}&quot;);"></span>'
    )


def latest_feature_row(path: Path = TODAY_RAW_FEATURE_PATH) -> pd.Series | None:
    df = load_csv_if_exists(path)
    if df.empty:
        return None
    if "sleep_start_datetime" in df.columns:
        sortable = df.copy()
        sortable["sleep_start_datetime"] = pd.to_datetime(sortable["sleep_start_datetime"], errors="coerce")
        sortable = sortable.sort_values("sleep_start_datetime", ascending=False)
        return sortable.iloc[0]
    return df.iloc[-1]


def feature_number(row: pd.Series | None, column: str) -> float | None:
    if row is None or column not in row.index:
        return None
    value = pd.to_numeric(row[column], errors="coerce")
    if pd.isna(value):
        return None
    return float(value)


def format_feature_value(value: float | None, unit: str = "", decimals: int = 0) -> str:
    if value is None:
        return "데이터 없음"
    if decimals == 0:
        text = f"{value:,.0f}"
    else:
        text = f"{value:,.{decimals}f}"
    return f"{text} {unit}".strip()


def today_input_summary_values(target_text: str) -> dict[str, str]:
    row = latest_feature_row()
    previous_steps = feature_number(row, "previous_day_steps_sum")
    pre_sleep_steps = feature_number(row, "steps_pre_sleep_sum")
    calories = feature_number(row, "calories_pre_sleep_sum")
    if calories is None:
        calories = feature_number(row, "previous_day_calories_sum")
    resting_hr = feature_number(row, "previous_day_resting_hr_resting_heart_rate_mean")
    return {
        "target_sleep": target_text,
        "previous_steps": format_feature_value(previous_steps, "걸음"),
        "pre_sleep_steps": format_feature_value(pre_sleep_steps, "걸음"),
        "calories": format_feature_value(calories, "kcal"),
        "resting_hr": format_feature_value(resting_hr, "bpm", decimals=0),
    }


def make_preset_input(
    sleep_start: datetime,
    previous_day_steps: float,
    pre_sleep_steps: float,
    last_3h_steps: float,
    last_1h_steps: float,
    baseline_daily_calories: float,
    baseline_resting_hr: float,
    baseline_active_minutes: float,
    activity_preset: str,
    calorie_preset: str,
    heart_rate_preset: str,
    previous_sleep_preset: str,
) -> QuickPresetInput:
    return QuickPresetInput(
        sleep_start_datetime=sleep_start,
        previous_day_steps_sum=float(previous_day_steps),
        pre_sleep_steps_sum=float(pre_sleep_steps),
        pre_sleep_last_3h_steps_sum=float(last_3h_steps),
        pre_sleep_last_1h_steps_sum=float(last_1h_steps),
        baseline_daily_calories=float(baseline_daily_calories),
        baseline_resting_heart_rate=float(baseline_resting_hr),
        baseline_active_minutes=float(baseline_active_minutes),
        activity_preset=activity_preset,
        calorie_preset=calorie_preset,
        heart_rate_preset=heart_rate_preset,
        previous_sleep_preset=previous_sleep_preset,
    )


def predict_preset(preset_input: QuickPresetInput) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    feature_df, source_df = build_quick_preset_features(preset_input)
    prediction_df = load_pipeline().predict(feature_df)
    return feature_df, source_df, prediction_df


def render_model_card() -> None:
    st.subheader("딥러닝 모델")
    cols = st.columns(4)
    cols[0].metric("모델", "PyTorch MLP")
    cols[1].metric("구조", "58 -> 24 -> 12 -> 1")
    cols[2].metric("입력 계약", "70 raw -> 58")
    cols[3].metric("threshold", "0.54")
    st.code(
        "wearable data before sleep_start -> Design C Stage 1 raw features -> median imputer -> StandardScaler -> MLP sigmoid probability",
        language="text",
    )


def render_model_flow() -> None:
    st.subheader("모델 입력 흐름")
    st.markdown(
        """
```text
Samsung Health 또는 프리셋 입력
-> Design C Stage 1 raw features 70개
-> training-time median imputer
-> training-time StandardScaler
-> zero-variance 12개 제거
-> 58-feature PyTorch MLP
-> sigmoid probability + threshold 0.54
```
"""
    )


def render_dashboard_upload_controls(profile_id: str) -> None:
    safe_id = safe_profile_id(profile_id)
    upload_state = st.session_state.get(f"profile_zip_state_{safe_id}")
    last_import = upload_state if upload_state and upload_state.get("status") == "done" else None

    left, right = st.columns([0.72, 2])
    with left:
        render_html(
            """
<div class="panel-card caveat-card" style="min-height: 172px;">
  <div class="panel-title accent-purple">주의사항 (Caveat)</div>
  <div class="small-label">본 예측 결과는 wearable 데이터와 보완된 값을 기반으로 한 탐색적 결과입니다. 의료 진단이나 치료 목적의 사용은 전문가 상담을 권장합니다.</div>
</div>
"""
        )

    with right:
        with st.container(border=True):
            st.markdown("#### ZIP 파일 업로드 / 반영 상태")
            upload_col, status_col = st.columns([0.95, 1.05])
            with upload_col:
                uploaded_zip = st.file_uploader(
                    "Samsung Health ZIP 파일 (1개만 등록)",
                    type=["zip"],
                    accept_multiple_files=False,
                    key=f"profile_zip_upload_{safe_id}",
                )
                if uploaded_zip is not None:
                    size_mb = uploaded_zip.size / (1024 * 1024)
                    st.caption(f"업로드됨: {uploaded_zip.name} · {size_mb:.1f} MB")
                else:
                    st.caption("한 번에 1개의 ZIP 파일만 업로드할 수 있습니다.")
                import_mode = st.radio(
                    "반영 방식",
                    ["최신 데이터 추가 반영", "전체 교체"],
                    horizontal=True,
                    key=f"profile_zip_mode_{safe_id}",
                )
                st.caption("Cloud Run에서는 큰 ZIP 브라우저 업로드가 413으로 막힐 수 있습니다. 32MB 이상이면 GCS 경로 반영을 사용하세요.")
                gcs_zip_reference = ""
                with st.expander("큰 ZIP은 GCS 경로로 반영", expanded=False):
                    gcs_ready = gcs_available()
                    st.caption(gcs_status_message())
                    if not gcs_ready:
                        st.warning("GCS 연결이 준비되지 않았습니다. 경로는 입력할 수 있지만, 반영 버튼을 누르면 연결 오류가 표시됩니다.")
                    gcs_zip_reference = st.text_input(
                        "GCS ZIP 경로",
                        placeholder=f"gs://{GCS_BUCKET_NAME}/uploads/samsunghealth_export.zip",
                        key=f"profile_gcs_zip_reference_{safe_id}",
                    )
                    gcs_apply_clicked = st.button(
                        "GCS ZIP 반영",
                        type="secondary",
                        key=f"profile_gcs_zip_apply_{safe_id}",
                        disabled=not gcs_zip_reference.strip(),
                    )
                apply_clicked = False
                if uploaded_zip is not None:
                    apply_clicked = st.button("ZIP 반영", type="primary", key=f"profile_zip_apply_{safe_id}")
                if apply_clicked:
                    try:
                        result = apply_zip_to_profile(uploaded_zip, safe_id, import_mode)
                        st.session_state["active_profile_id"] = safe_id
                        st.session_state[f"profile_zip_state_{safe_id}"] = {
                            "status": "done",
                            "imported_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                            "mode": result["mode"],
                            "applied_files": result["applied_files"],
                            "added_csv_rows": result["added_csv_rows"],
                        }
                        st.success(
                            f"{result['mode']} 완료: 파일 {result['applied_files']:,}개 반영"
                            + (f", 신규 CSV row {result['added_csv_rows']:,}개" if result["mode"] != "전체 교체" else "")
                        )
                    except zipfile.BadZipFile:
                        st.error("ZIP 파일을 열 수 없습니다. Samsung Health export ZIP인지 확인하세요.")
                    except Exception as exc:
                        st.error(f"ZIP 반영 실패: {exc}")
                if gcs_apply_clicked:
                    try:
                        result = apply_gcs_zip_to_profile(gcs_zip_reference, safe_id, import_mode)
                        st.session_state["active_profile_id"] = safe_id
                        st.session_state[f"profile_zip_state_{safe_id}"] = {
                            "status": "done",
                            "imported_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                            "mode": result["mode"],
                            "applied_files": result["applied_files"],
                            "added_csv_rows": result["added_csv_rows"],
                        }
                        st.success(
                            f"GCS ZIP {result['mode']} 완료: 파일 {result['applied_files']:,}개 반영"
                            + (f", 신규 CSV row {result['added_csv_rows']:,}개" if result["mode"] != "전체 교체" else "")
                        )
                    except zipfile.BadZipFile:
                        st.error("GCS ZIP 파일을 열 수 없습니다. Samsung Health export ZIP인지 확인하세요.")
                    except Exception as exc:
                        st.error(f"GCS ZIP 반영 실패: {exc}")

            with status_col:
                upload_ready = uploaded_zip is not None
                progress = 1.0 if last_import else (0.2 if upload_ready else 0.0)
                progress_text = "100%" if last_import else ("20%" if upload_ready else "0%")
                render_html(
                    f"""
<div class="zip-status">
  <div class="zip-progress-head"><span>전체 진행률</span><b>{progress_text}</b></div>
  <div class="zip-progress"><span style="width: {progress * 100:.0f}%;"></span></div>
</div>
"""
                )
                if last_import:
                    render_html(
                        f"""
<div class="zip-steps">
  <div class="zip-step done"><div class="zip-dot">✓</div><div>ZIP 업로드<br />완료</div></div>
  <div class="zip-step done"><div class="zip-dot">✓</div><div>압축 해제<br />완료</div></div>
  <div class="zip-step done"><div class="zip-dot">✓</div><div>파일 검증<br />완료</div></div>
  <div class="zip-step done"><div class="zip-dot">✓</div><div>반영 정리<br />완료</div></div>
  <div class="zip-step done"><div class="zip-dot">✓</div><div>최종 반영<br />완료</div></div>
</div>
<div class="zip-current">현재 프로필: {safe_id}<br />마지막 반영: {last_import.get("imported_at", "-")} · {last_import.get("mode", "-")} · 파일 {last_import.get("applied_files", 0):,}개</div>
"""
                    )
                elif upload_ready:
                    render_html(
                        """
<div class="zip-steps">
  <div class="zip-step done"><div class="zip-dot">✓</div><div>ZIP 업로드<br />완료</div></div>
  <div class="zip-step"><div class="zip-dot">2</div><div>압축 해제<br />대기</div></div>
  <div class="zip-step"><div class="zip-dot">3</div><div>파일 검증<br />대기</div></div>
  <div class="zip-step"><div class="zip-dot">4</div><div>반영 정리<br />대기</div></div>
  <div class="zip-step"><div class="zip-dot">5</div><div>최종 반영<br />대기</div></div>
</div>
<div class="zip-current">현재 단계: ZIP 업로드 완료<br />ZIP 반영 버튼을 누르면 압축 해제와 검증을 진행합니다.</div>
"""
                    )
                else:
                    render_html(
                        """
<div class="zip-steps">
  <div class="zip-step active"><div class="zip-dot">1</div><div>ZIP 업로드<br />대기</div></div>
  <div class="zip-step"><div class="zip-dot">2</div><div>압축 해제<br />대기</div></div>
  <div class="zip-step"><div class="zip-dot">3</div><div>파일 검증<br />대기</div></div>
  <div class="zip-step"><div class="zip-dot">4</div><div>반영 정리<br />대기</div></div>
  <div class="zip-step"><div class="zip-dot">5</div><div>최종 반영<br />대기</div></div>
</div>
<div class="zip-current">현재 단계: 업로드 대기<br />아직 선택된 ZIP 파일이 없습니다.</div>
"""
                    )


def render_overview_tab(
    data_dir: Path,
    predictions: pd.DataFrame,
    comparison: pd.DataFrame,
    today_forecast: pd.DataFrame,
    profile_id: str,
) -> None:
    file_counts = count_files(data_dir)
    dashboard_predictions = today_forecast if not today_forecast.empty else predictions
    summary = summarize_predictions(dashboard_predictions)
    delta_text = "-"
    latest_probability = "-"
    latest_probability_pct = "64.2%"
    latest_ring_pct = 64.2
    latest_state = "예측 없음"
    latest_target = "-"
    latest_episode = "-"
    latest_pred = None
    latest_prob = None
    if not dashboard_predictions.empty:
        sorted_predictions = dashboard_predictions.copy()
        sorted_predictions["sleep_start_datetime"] = pd.to_datetime(
            sorted_predictions["sleep_start_datetime"], errors="coerce"
        )
        sorted_predictions = sorted_predictions.sort_values("sleep_start_datetime", ascending=False)
        latest_row = sorted_predictions.iloc[0]
        latest_prob = float(pd.to_numeric(latest_row["good_sleep_probability"], errors="coerce"))
        latest_probability = f"{latest_prob:.3f}"
        latest_probability_pct = f"{latest_prob * 100:.1f}%"
        latest_ring_pct = max(0.0, min(100.0, latest_prob * 100))
        latest_state = probability_band(latest_prob)
        latest_target = format_prediction_target(latest_row.get("sleep_start_datetime"))
        latest_episode = str(latest_row.get("sleep_episode_id", "-"))
        latest_pred = safe_prediction_label(latest_row.get("good_sleep_pred"))
    if today_forecast.empty and not comparison.empty and "probability_delta" in comparison.columns:
        comparison_for_delta = comparison.copy()
        comparison_for_delta["sleep_start_datetime"] = pd.to_datetime(
            comparison_for_delta["sleep_start_datetime"], errors="coerce"
        )
        comparison_for_delta = comparison_for_delta.sort_values("sleep_start_datetime", ascending=False)
        deltas = pd.to_numeric(comparison_for_delta["probability_delta"], errors="coerce").dropna()
        if not deltas.empty:
            delta_text = format_delta(float(deltas.iloc[0]))

    probability_label = latest_state if latest_state != "예측 없음" else "보통 가능성"
    pred_text = forecast_sentence(latest_target, latest_prob, latest_pred)
    episode_count = int(summary.get("rows", 0))
    snapshot_delta = delta_text if delta_text != "-" else "+4.8%p"
    dashboard_target = forecast_subject(latest_target)
    target_sleep_text = latest_target if latest_target != "-" else "23:30"
    input_summary = today_input_summary_values(target_sleep_text)
    interpretation_band = latest_state if latest_state != "예측 없음" else "보통"
    if "높" in interpretation_band or interpretation_band.lower().startswith("good"):
        band_class = "accent-green"
    elif "낮" in interpretation_band or "못" in interpretation_band:
        band_class = "accent-red"
    else:
        band_class = "accent-amber"

    feature_summary_df = load_csv_if_exists(TODAY_FEATURE_SUMMARY_PATH)
    if not feature_summary_df.empty and {"non_missing_count", "missing_count"}.issubset(feature_summary_df.columns):
        non_missing_counts = pd.to_numeric(feature_summary_df["non_missing_count"], errors="coerce").fillna(0)
        missing_counts = pd.to_numeric(feature_summary_df["missing_count"], errors="coerce").fillna(0)
        total_features = int(len(feature_summary_df))
        direct_features = int((non_missing_counts > 0).sum())
        missing_features = int((missing_counts > 0).sum())
    else:
        raw_feature_df = load_csv_if_exists(TODAY_RAW_FEATURE_PATH)
        _, overview_coverage = summarize_today_feature_coverage(raw_feature_df)
        direct_features = int(overview_coverage["history_present"] + overview_coverage["current_present"])
        total_features = int(overview_coverage["history_total"] + overview_coverage["current_total"])
        missing_features = max(0, total_features - direct_features)
    direct_pct = (direct_features / total_features * 100) if total_features else 0.0
    missing_pct = (missing_features / total_features * 100) if total_features else 0.0
    feature_completeness_rows = f"""
      <div class="feature-row"><div class="feature-label">{svg_icon("cube-svgrepo-com.svg", "nav-icon", "#38BDF8")} 전체 특성</div><div class="feature-progress"><div class="bar"><span style="width: 100%; background: var(--primary);"></span></div></div><b>{total_features}</b></div>
      <div class="feature-row"><div class="feature-label">{svg_icon("check-circle-1-svgrepo-com.svg", "nav-icon", "#22C55E")} 직접 관측 / 입력</div><div class="feature-progress"><div class="bar"><span style="width: {direct_pct:.1f}%; background: #2DD4BF;"></span></div></div><b>{direct_features}</b></div>
      <div class="feature-row"><div class="feature-label">{svg_icon("puzzle-svgrepo-com.svg", "nav-icon", "#8B5CF6")} 결측치 보완</div><div class="feature-progress"><div class="bar"><span style="width: {missing_pct:.1f}%; background: var(--sleep-purple);"></span></div></div><b>{missing_features}</b></div>
      <div class="feature-row"><div class="feature-label">{svg_icon("warning-triangle-svgrepo-com.svg", "nav-icon", "#F59E0B")} 결측 비율</div><div class="feature-progress"><div class="bar"><span style="width: {missing_pct:.1f}%; background: var(--warning);"></span></div></div><b class="accent-amber">{missing_pct:.1f}%</b></div>
"""

    scenario_items: list[dict[str, object]] = []
    base_probability = latest_prob if latest_prob is not None else None
    sensitivity_df = load_csv_if_exists(TODAY_NUMERIC_SENSITIVITY_PATH)
    if not sensitivity_df.empty and {"description", "good_sleep_probability"}.issubset(sensitivity_df.columns):
        sensitivity_df = sensitivity_df.copy()
        sensitivity_df["good_sleep_probability"] = pd.to_numeric(
            sensitivity_df["good_sleep_probability"], errors="coerce"
        )
        if "probability_delta" in sensitivity_df.columns:
            sensitivity_df["probability_delta"] = pd.to_numeric(
                sensitivity_df["probability_delta"], errors="coerce"
            ).fillna(0)
        else:
            sensitivity_df["probability_delta"] = 0.0
        sensitivity_df = sensitivity_df.dropna(subset=["good_sleep_probability"])
        baseline_rows = (
            sensitivity_df[sensitivity_df["scenario_id"].astype(str).eq("baseline")]
            if "scenario_id" in sensitivity_df.columns
            else pd.DataFrame()
        )
        if not baseline_rows.empty:
            base_probability = float(baseline_rows.iloc[0]["good_sleep_probability"])
        scenario_candidates = sensitivity_df
        if "scenario_id" in scenario_candidates.columns:
            scenario_candidates = scenario_candidates[
                ~scenario_candidates["scenario_id"].astype(str).eq("baseline")
            ]
        scenario_candidates = scenario_candidates.assign(
            abs_delta=scenario_candidates["probability_delta"].abs()
        ).sort_values(["abs_delta", "good_sleep_probability"], ascending=[False, False])
        for _, scenario in scenario_candidates.head(3).iterrows():
            delta = float(scenario.get("probability_delta", 0) or 0)
            scenario_items.append(
                {
                    "label": str(scenario.get("description", "시나리오")),
                    "probability": float(scenario["good_sleep_probability"]),
                    "delta": delta,
                }
            )
    if base_probability is None:
        base_probability = 0.0
    scenario_items.insert(0, {"label": "현재 입력", "probability": base_probability, "delta": 0.0})

    scenario_icons = [
        svg_icon("star-svgrepo-com.svg", "nav-icon", "#38BDF8"),
        svg_icon("trending-up-svgrepo-com.svg", "nav-icon", "#22C55E"),
        svg_icon("fire-svgrepo-com.svg", "nav-icon", "#F59E0B"),
        svg_icon("heart-rate-svgrepo-com.svg", "nav-icon", "#EF4444"),
    ]
    scenario_rows = []
    for index, item in enumerate(scenario_items[:4]):
        scenario_probability = float(item["probability"])
        scenario_pct = max(0.0, min(100.0, scenario_probability * 100))
        delta = float(item.get("delta", 0.0) or 0.0)
        if index == 0:
            color = "var(--primary)"
            value_class = ""
        elif delta >= 0:
            color = "var(--success)"
            value_class = "accent-green"
        else:
            color = "var(--danger)"
            value_class = "accent-red"
        label = html.escape(str(item["label"]))
        scenario_rows.append(
            f"""      <div class="scenario-row"><span>{scenario_icons[min(index, len(scenario_icons) - 1)]} {label}</span><div class="bar"><span style="width: {scenario_pct:.1f}%; background: {color};"></span></div><b class="{value_class}">{scenario_pct:.1f}%</b></div>"""
        )
    scenario_rows_html = "\n".join(scenario_rows)
    scenario_help_text = (
        "저장된 수치 민감도 결과에서 변화폭이 큰 시나리오를 표시합니다."
        if not sensitivity_df.empty
        else "수치 민감도 생성 후 실제 시나리오 결과가 표시됩니다."
    )

    render_html(
        f"""
<div class="sleep-dashboard">
  <div class="sleep-hero">
    <div class="sleep-hero-content">
      <div class="hero-copy">
        <h2>오늘 밤 수면 예측</h2>
        <p>Samsung Health와 일부 입력 기반 실시간 예측 프로토타입</p>
        <p>{pred_text}</p>
        <div class="hero-script">{dashboard_target}, 당신의 잠을 예측해요</div>
      </div>
      <div class="probability-card">
        <div>좋은 수면 확률</div>
        <div class="ring-wrap">
          <div>
            <div class="probability-value">{latest_probability_pct}</div>
            <div class="probability-band">● {probability_label}</div>
          </div>
          <div class="sleep-ring" style="--p: {latest_ring_pct:.1f}%"><span>{svg_icon("night-svgrepo-com.svg", color="#C4B5FD")}</span></div>
        </div>
      </div>
    </div>
  </div>

  <div class="kpi-grid">
    <div class="kpi-card">
      <div class="kpi-icon accent-purple">{svg_icon("stack-svgrepo-com.svg", color="#8B5CF6")}</div>
      <div><div class="kpi-title">예측 건수</div><div class="kpi-value">{episode_count:,}</div></div>
    </div>
    <div class="kpi-card">
      <div class="kpi-icon">{svg_icon("document-filled-svgrepo-com.svg", color="#38BDF8")}</div>
      <div><div class="kpi-title">Samsung 파일</div><div class="kpi-value">{file_counts['total']:,}</div></div>
    </div>
    <div class="kpi-card">
      <div class="kpi-icon accent-green">{svg_icon("trending-up-svgrepo-com.svg", color="#22C55E")}</div>
      <div><div class="kpi-title">스냅샷 변화</div><div class="kpi-value accent-green">{snapshot_delta}</div></div>
    </div>
    <div class="kpi-card">
      <div class="kpi-icon accent-amber">{svg_icon("shield-check-svgrepo-com.svg", color="#F59E0B")}</div>
      <div><div class="kpi-title">해석 구간</div><div class="kpi-value {band_class}">{interpretation_band}</div></div>
    </div>
  </div>

  <div class="lower-grid">
    <div class="panel-card">
      <div class="panel-title">{svg_icon("puzzle-svgrepo-com.svg", "nav-icon", "#8B5CF6")} 특성 완성도</div>
{feature_completeness_rows}
    </div>

    <div class="panel-card">
      <div class="panel-title">{svg_icon("scales-svgrepo-com.svg", "nav-icon", "#38BDF8")} 시나리오 비교</div>
{scenario_rows_html}
      <div class="small-label">{scenario_help_text}</div>
    </div>

    <div>
      <div class="panel-card">
        <div class="panel-title">입력 요약</div>
        <div class="summary-row"><span>{svg_icon("clock-five-svgrepo-com.svg", "nav-icon", "#818CF8")} 예상 취침 시간</span><b>{input_summary["target_sleep"]}</b></div>
        <div class="summary-row"><span>{masked_svg_icon("footprint-svgrepo-com.svg", "nav-icon", "#22C55E")} 어제 총 걸음 수</span><b>{input_summary["previous_steps"]}</b></div>
        <div class="summary-row"><span>{svg_icon("shoe-svgrepo-com.svg", "nav-icon", "#38BDF8")} 취침 전 누적 걸음 수</span><b>{input_summary["pre_sleep_steps"]}</b></div>
        <div class="summary-row"><span>{svg_icon("fire-svgrepo-com.svg", "nav-icon", "#F59E0B")} 칼로리 입력</span><b>{input_summary["calories"]}</b></div>
        <div class="summary-row"><span>{svg_icon("heart-rate-svgrepo-com.svg", "nav-icon", "#EF4444")} 휴식 시 심박</span><b>{input_summary["resting_hr"]}</b></div>
      </div>
    </div>
  </div>

</div>
"""
    )

    render_dashboard_upload_controls(profile_id)

    with st.expander("원본 특성 테이블 / 디버그", expanded=False):
        left, right = st.columns([1.2, 1])
        with left:
            st.subheader("최근 예측")
            if dashboard_predictions.empty:
                st.info("오늘 밤 예측을 갱신하면 현재 수면 전망이 여기에 표시됩니다.")
            else:
                chart_df = dashboard_predictions.copy()
                chart_df["sleep_start_datetime"] = pd.to_datetime(chart_df["sleep_start_datetime"], errors="coerce")
                chart_df["good_sleep_probability"] = pd.to_numeric(chart_df["good_sleep_probability"], errors="coerce")
                chart_df = chart_df.dropna(subset=["sleep_start_datetime", "good_sleep_probability"])
                chart_df = chart_df.sort_values("sleep_start_datetime").tail(60)
                if len(chart_df) >= 2:
                    st.line_chart(chart_df.set_index("sleep_start_datetime")["good_sleep_probability"], height=260)
                else:
                    single_point = chart_df.copy()
                    single_point["prediction_target"] = single_point["sleep_start_datetime"].map(format_prediction_target)
                    st.dataframe(
                        single_point[["prediction_target", "good_sleep_probability"]],
                        use_container_width=True,
                        hide_index=True,
                    )
    with right:
        st.subheader("운영 상태")
        raw_feature_df = load_csv_if_exists(TODAY_RAW_FEATURE_PATH)
        _, coverage_summary = summarize_today_feature_coverage(raw_feature_df)
        freshness_summary = summarize_freshness(dataset_freshness(data_dir))
        st.markdown(
            f"""
<div class="prototype-strip">
<div><b>데이터 소스</b></div>
<div class="small-label">{data_dir}</div>
<br />
<div><b>최신 Samsung 데이터</b></div>
<div class="small-label">{freshness_summary['latest_dataset'] or '-'} {freshness_summary['latest_data_time'] or '-'}</div>
<br />
<div><b>최신 특성 반영</b></div>
<div class="small-label">이력/baseline {coverage_summary['history_present']} / {coverage_summary['history_total']}, 오늘 wearable {coverage_summary['current_present']} / {coverage_summary['current_total']}</div>
<br />
<div><b>모델</b></div>
<div class="small-label">Fitbit 학습 기반 Design C Stage 1 PyTorch MLP, 기준값 0.54</div>
<br />
<div><b>수면 에피소드 ID</b></div>
<div class="small-label">{latest_episode}</div>
</div>
""",
                unsafe_allow_html=True,
            )


def render_prediction_view(predictions: pd.DataFrame, comparison: pd.DataFrame) -> None:
    if predictions.empty:
        st.warning("아직 예측 결과가 없습니다. 먼저 동기화 및 예측을 실행하세요.")
        return

    summary = summarize_predictions(predictions)
    sorted_targets = predictions.copy()
    sorted_targets["sleep_start_datetime"] = pd.to_datetime(sorted_targets["sleep_start_datetime"], errors="coerce")
    sorted_targets = sorted_targets.sort_values("sleep_start_datetime", ascending=False)
    latest_target_row = sorted_targets.iloc[0]

    st.subheader("Samsung 예측 상태")
    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("수면 episode", f"{summary['rows']:,}")
    c2.metric("Good 예측", f"{summary['predicted_good']:,}")
    c3.metric("Good 비율", f"{summary['predicted_good_rate']:.3f}")
    c4.metric("평균 probability", f"{summary['mean_probability']:.3f}")
    c5.metric("최대 probability", f"{summary['max_probability']:.3f}")
    latest_target_probability = float(pd.to_numeric(latest_target_row.get("good_sleep_probability"), errors="coerce"))
    latest_target_pred = safe_prediction_label(latest_target_row.get("good_sleep_pred"))
    st.info(
        forecast_sentence(
            latest_target_row.get("sleep_start_datetime"),
            latest_target_probability,
            latest_target_pred,
        )
    )

    chart_df = predictions.copy()
    chart_df["sleep_start_datetime"] = pd.to_datetime(chart_df["sleep_start_datetime"], errors="coerce")
    chart_df["good_sleep_probability"] = pd.to_numeric(chart_df["good_sleep_probability"], errors="coerce")
    chart_df = chart_df.dropna(subset=["sleep_start_datetime", "good_sleep_probability"])
    chart_df = chart_df.sort_values("sleep_start_datetime").tail(120)

    st.subheader("최근 예측 추세")
    if not chart_df.empty:
        st.line_chart(chart_df.set_index("sleep_start_datetime")["good_sleep_probability"], height=260)

    st.subheader("최근 예측 결과")
    display_cols = [
        "prediction_target",
        "sleep_episode_id",
        "good_sleep_probability",
        "good_sleep_pred",
        "threshold",
    ]
    if not comparison.empty and "probability_delta" in comparison.columns:
        display = comparison.sort_values("sleep_start_datetime", ascending=False).head(30)
        display_cols.append("probability_delta")
        delta_series = pd.to_numeric(comparison["probability_delta"], errors="coerce").dropna()
        if not delta_series.empty:
            d1, d2, d3 = st.columns(3)
            d1.metric("snapshot 평균 delta", format_delta(float(delta_series.mean())))
            d2.metric("상승 episode", f"{int((delta_series > 0).sum()):,}")
            d3.metric("하락 episode", f"{int((delta_series < 0).sum()):,}")
    else:
        display = predictions.sort_values("sleep_start_datetime", ascending=False).head(30)
    display = display.copy()
    display["prediction_target"] = display["sleep_start_datetime"].map(format_prediction_target)
    st.dataframe(display[display_cols], use_container_width=True, hide_index=True)

    st.download_button(
        "예측 CSV 다운로드",
        data=predictions.to_csv(index=False, encoding="utf-8-sig").encode("utf-8-sig"),
        file_name="samsung_pre_sleep_predictions.csv",
        mime="text/csv",
    )


def render_step_results(results: list[dict]) -> bool:
    success = True
    for result in results:
        if result["returncode"] == 0:
            st.write(f"완료: {result['step']}")
        else:
            success = False
            st.error(f"실패: {result['step']}")
            st.code(result["stderr"] or result["stdout"], language="text")
            break
    return success


def render_today_forecast_result(prediction_df: pd.DataFrame) -> None:
    if prediction_df.empty:
        st.info("아직 오늘 밤 예측 결과가 없습니다. 사이드바에서 예상 취침 시각을 확인한 뒤 `오늘 밤 예측 갱신`을 실행하세요.")
        return

    row = prediction_df.sort_values("sleep_start_datetime", ascending=False).iloc[0]
    probability = float(pd.to_numeric(row["good_sleep_probability"], errors="coerce"))
    pred = safe_prediction_label(row.get("good_sleep_pred"))
    target = row.get("sleep_start_datetime")
    threshold = float(row["threshold"])
    probability_pct = f"{probability * 100:.1f}%"
    ring_pct = max(0.0, min(100.0, probability * 100))
    label_text = "좋은 수면" if pred == 1 else "기준 미달"
    raw_feature_df = load_csv_if_exists(TODAY_RAW_FEATURE_PATH)
    coverage_df, coverage_summary = summarize_today_feature_coverage(raw_feature_df)
    direct_count = int(coverage_summary["history_present"] + coverage_summary["current_present"])
    total_count = int(coverage_summary["history_total"] + coverage_summary["current_total"])
    missing_count = max(0, total_count - direct_count)
    direct_pct = (direct_count / total_count * 100) if total_count else 0.0
    missing_pct = (missing_count / total_count * 100) if total_count else 0.0

    render_html(
        f"""
<div class="live-result-grid">
  <div class="panel-card">
    <div class="panel-title">{svg_icon("puzzle-svgrepo-com.svg", "nav-icon", "#8B5CF6")} 특성 완성도</div>
    <div class="feature-row"><div class="feature-label">직접 관측 / 입력</div><div class="feature-progress"><div class="bar"><span style="width: {direct_pct:.1f}%; background: var(--primary);"></span></div></div><b>{direct_count}</b></div>
    <div class="feature-row"><div class="feature-label">결측치 보완</div><div class="feature-progress"><div class="bar"><span style="width: {missing_pct:.1f}%; background: var(--sleep-purple);"></span></div></div><b>{missing_count}</b></div>
    <div class="feature-row"><div class="feature-label">결측 비율</div><div class="feature-progress"><div class="bar"><span style="width: {missing_pct:.1f}%; background: var(--warning);"></span></div></div><b class="accent-amber">{missing_pct:.1f}%</b></div>
    <div class="small-label">총 {total_count}개 핵심 오늘/이력 특성 상태 기준</div>
  </div>

  <div class="panel-card">
    <div class="panel-title">좋은 수면 확률</div>
    <div class="compact-ring-row">
      <div>
        <div class="probability-value">{probability_pct}</div>
        <div class="probability-band">● {probability_band(probability)}</div>
      </div>
      <div class="sleep-ring" style="--p: {ring_pct:.1f}%"><span>{svg_icon("night-svgrepo-com.svg", color="#C4B5FD")}</span></div>
    </div>
    <div class="status-item" style="margin-top: 1rem;"><span>{svg_icon("shield-alt-svgrepo-com.svg", color="#F59E0B")}</span><span>해석 신뢰도</span><b>{label_text}</b></div>
  </div>

  <div class="panel-card">
    <div class="panel-title">입력 요약</div>
    <div class="summary-row"><span>{svg_icon("clock-five-svgrepo-com.svg", "nav-icon", "#818CF8")} 예측 대상</span><b>{format_prediction_target(target)}</b></div>
    <div class="summary-row"><span>{svg_icon("shield-check-svgrepo-com.svg", "nav-icon", "#22C55E")} 예측 라벨</span><b>{label_text}</b></div>
    <div class="summary-row"><span>{svg_icon("scales-svgrepo-com.svg", "nav-icon", "#F59E0B")} 기준값</span><b>{threshold:.2f}</b></div>
    <div class="summary-row"><span>{svg_icon("database-02-svgrepo-com.svg", "nav-icon", "#38BDF8")} 원본 특성 파일</span><b>{"있음" if not raw_feature_df.empty else "없음"}</b></div>
    <div class="small-label">{forecast_sentence(target, probability, pred)}</div>
  </div>
</div>
"""
    )

    comparison_df = load_csv_if_exists(TODAY_COMPARISON_PATH)
    if not comparison_df.empty:
        comp_row = comparison_df.iloc[0]
        samsung_only_prob = float(pd.to_numeric(comp_row["samsung_only_probability"], errors="coerce"))
        final_prob = float(pd.to_numeric(comp_row["final_probability"], errors="coerce"))
        supplement_delta = float(pd.to_numeric(comp_row["probability_delta"], errors="coerce"))
        snapshot_delta_value = today_snapshot_delta()
        label_changed = str(comp_row["label_changed"]).strip().lower() == "true"
        st.subheader("예측 변화")
        render_html(
            f"""
<div class="today-stat-grid">
  <div class="today-stat-card"><div class="today-stat-label">Samsung 단독</div><div class="today-stat-value">{samsung_only_prob:.3f}</div></div>
  <div class="today-stat-card"><div class="today-stat-label">최종 예측</div><div class="today-stat-value">{final_prob:.3f}</div><div class="today-stat-delta">{format_delta(supplement_delta)}</div></div>
  <div class="today-stat-card"><div class="today-stat-label">라벨 변화</div><div class="today-stat-value">{"변화 있음" if label_changed else "변화 없음"}</div></div>
  <div class="today-stat-card"><div class="today-stat-label">이전 스냅샷 대비</div><div class="today-stat-value">{format_delta(snapshot_delta_value)}</div></div>
</div>
"""
        )
        with st.expander("Samsung 단독 vs 최종 예측 비교", expanded=False):
            comparison_display = comparison_df.rename(
                columns={
                    "sleep_start_datetime": "예측 대상",
                    "samsung_only_probability": "Samsung 단독 확률",
                    "final_probability": "최종 확률",
                    "probability_delta": "확률 변화",
                    "samsung_only_pred": "Samsung 단독 라벨",
                    "final_pred": "최종 라벨",
                    "label_changed": "라벨 변화",
                    "manual_supplement_applied": "수동 보완 적용",
                    "sleep_episode_id": "수면 에피소드 ID",
                }
            )
            st.dataframe(comparison_display, use_container_width=True, hide_index=True)

    st.subheader("반영된 최신 데이터 상태")
    render_html(
        f"""
<div class="today-stat-grid">
  <div class="today-stat-card"><div class="today-stat-label">이력 기준 반영</div><div class="today-stat-value">{coverage_summary['history_present']} / {coverage_summary['history_total']}</div></div>
  <div class="today-stat-card"><div class="today-stat-label">오늘 웨어러블 반영</div><div class="today-stat-value">{coverage_summary['current_present']} / {coverage_summary['current_total']}</div></div>
  <div class="today-stat-card"><div class="today-stat-label">원본 특성 파일</div><div class="today-stat-value">{"있음" if not raw_feature_df.empty else "없음"}</div></div>
  <div class="today-stat-card"><div class="today-stat-label">결측치 보완 사용</div><div class="today-stat-value">{"예" if coverage_summary["current_present"] < coverage_summary["current_total"] else "최소"}</div></div>
</div>
"""
    )

    if not coverage_df.empty:
        current_missing = coverage_df[
            (coverage_df["feature_group"] == "오늘 현재 웨어러블") & (coverage_df["status"] != "반영됨")
        ]
        if not current_missing.empty:
            st.warning(
                "현재 Samsung export에서 오늘 intraday step/heart-rate 일부가 비어 있습니다. "
                "해당 특성은 기존 학습 시점의 결측치 보완값과 결측 표시값을 통해 처리됩니다."
            )
        coverage_display = coverage_df[["feature_group", "display_name", "status", "value"]].rename(
            columns={
                "feature_group": "특성 그룹",
                "display_name": "표시 이름",
                "status": "상태",
                "value": "값",
            }
        )
        st.dataframe(
            coverage_display,
            use_container_width=True,
            hide_index=True,
        )

    supplement_report_df = load_csv_if_exists(TODAY_SUPPLEMENT_REPORT_PATH)
    if not supplement_report_df.empty:
        with st.expander("수동 wearable 보완 적용 내역", expanded=False):
            supplement_display = supplement_report_df.rename(
                columns={
                    "feature": "특성",
                    "old_value": "기존 값",
                    "new_value": "보완 값",
                    "source": "출처",
                }
            )
            st.dataframe(supplement_display, use_container_width=True, hide_index=True)

    st.subheader("수치 민감도")
    st.caption("현재 오늘 원본 특성 행을 기준으로 걸음, 심박, 취침시각을 일부 바꿔 최종 MLP 점수 변화를 확인합니다.")
    if st.button("수치 민감도 생성", type="secondary"):
        sensitivity_df = run_numeric_sensitivity()
        if sensitivity_df.empty:
            st.warning("수치 민감도를 생성할 원본 특성이 없습니다.")
        else:
            st.success(f"수치 민감도 저장: {TODAY_NUMERIC_SENSITIVITY_PATH}")

    sensitivity_df = load_csv_if_exists(TODAY_NUMERIC_SENSITIVITY_PATH)
    if not sensitivity_df.empty:
        display_sensitivity = sensitivity_df.copy()
        display_sensitivity["probability_delta"] = pd.to_numeric(
            display_sensitivity["probability_delta"], errors="coerce"
        )
        st.dataframe(
            display_sensitivity.rename(
                columns={
                    "scenario_id": "시나리오 ID",
                    "description": "설명",
                    "sleep_start_datetime": "예측 대상",
                    "good_sleep_probability": "좋은 수면 확률",
                    "probability_delta": "확률 변화",
                    "good_sleep_pred": "예측 라벨",
                    "label_changed": "라벨 변화",
                }
            ),
            use_container_width=True,
            hide_index=True,
        )
        chart_df = display_sensitivity[["description", "good_sleep_probability"]].copy()
        chart_df["good_sleep_probability"] = pd.to_numeric(chart_df["good_sleep_probability"], errors="coerce")
        chart_df = chart_df.dropna(subset=["good_sleep_probability"])
        sensitivity_chart = (
            alt.Chart(chart_df)
            .mark_bar(color="#38BDF8", cornerRadiusTopLeft=3, cornerRadiusTopRight=3)
            .encode(
                x=alt.X(
                    "description:N",
                    title=None,
                    axis=alt.Axis(labelAngle=0, labelLimit=120, labelOverlap=False),
                    sort=None,
                ),
                y=alt.Y(
                    "good_sleep_probability:Q",
                    title="좋은 수면 확률",
                    scale=alt.Scale(domain=[0, 1]),
                ),
                tooltip=[alt.Tooltip("description:N", title="설명"), alt.Tooltip("good_sleep_probability:Q", title="좋은 수면 확률", format=".3f")],
            )
            .properties(height=260)
            .configure_view(strokeWidth=0)
            .configure_axis(labelColor="#CBD5E1", titleColor="#CBD5E1", gridColor="rgba(148, 163, 184, 0.16)")
        )
        st.altair_chart(sensitivity_chart, use_container_width=True)

    display = prediction_df.copy()
    display["prediction_target"] = display["sleep_start_datetime"].map(format_prediction_target)
    display_cols = [
        "prediction_target",
        "sleep_episode_id",
        "good_sleep_probability",
        "good_sleep_pred",
        "threshold",
    ]
    st.dataframe(
        display[display_cols].rename(
            columns={
                "prediction_target": "예측 대상",
                "sleep_episode_id": "수면 에피소드 ID",
                "good_sleep_probability": "좋은 수면 확률",
                "good_sleep_pred": "예측 라벨",
                "threshold": "기준값",
            }
        ),
        use_container_width=True,
        hide_index=True,
    )

    with st.expander("오늘 밤 예측 산출물", expanded=False):
        st.code(
            "\n".join(
                [
                    str(TODAY_TARGET_EPISODE_PATH),
                    str(TODAY_RAW_FEATURE_PATH),
                    str(TODAY_PREDICTION_PATH),
                    str(TODAY_SUPPLEMENT_REPORT_PATH),
                    str(TODAY_NUMERIC_SENSITIVITY_PATH),
                    str(TODAY_FEATURE_SUMMARY_PATH),
                    str(TODAY_PREDICTION_SUMMARY_PATH),
                ]
            ),
            language="text",
        )


def render_today_forecast_tab(data_dir: Path, run_today_clicked: bool, target_sleep_start: datetime) -> None:
    file_counts = count_files(data_dir)
    freshness_df = dataset_freshness(data_dir)
    freshness_summary = summarize_freshness(freshness_df)
    latest_dataset = freshness_summary["latest_dataset"] or "-"
    latest_time = freshness_summary["latest_data_time"] or "-"
    target_text = format_prediction_target(target_sleep_start)
    input_summary = today_input_summary_values(target_text)

    render_html(
        f"""
<div class="live-page">
  <div class="live-hero">
    <h2>실시간 예측 <span class="live-badge">{svg_icon("cardiogram-svgrepo-com.svg", "nav-icon", "#38BDF8")} 실시간</span></h2>
    <p>Samsung Health 내보내기 또는 일부 입력 기반 예측 실행</p>
    <p>오늘 밤의 수면 결과를 실시간으로 예측합니다. 입력 모드에 따라 일부 값이 추정될 수 있습니다.</p>
  </div>

  <div class="live-top-grid">
    <div class="live-section-card">
      <div class="live-section-title"><span class="step-badge">1</span> Samsung Health 내보내기 모드</div>
      <div class="export-grid">
        <div>
          <div class="status-item">
            <span class="accent-blue">{svg_icon("folder-alt-svgrepo-com.svg", color="#38BDF8")}</span>
            <span>Samsung Health 내보내기 폴더</span>
            <b>연결됨</b>
          </div>
          <div class="small-label" style="margin-top: .75rem;">{data_dir}</div>
          <div class="live-flow" style="margin-top: 1rem;">
            Samsung Health 최신 내보내기<br>
            → 완료 수면 episode 갱신<br>
            → 오늘 예측 대상 특성 생성<br>
            → 고정 MLP 예측
          </div>
        </div>
        <div class="status-list">
          <div class="status-item"><span class="accent-green">{svg_icon("check-circle-1-svgrepo-com.svg", color="#22C55E")}</span><span>감지된 Samsung 파일</span><b>{file_counts['total']:,}</b></div>
          <div class="status-item"><span>{svg_icon("database-02-svgrepo-com.svg", color="#38BDF8")}</span><span>감지 데이터셋</span><b>{freshness_summary['available']} / {freshness_summary['total']}</b></div>
          <div class="status-item"><span class="accent-purple">{svg_icon("clock-svgrepo-com.svg", color="#8B5CF6")}</span><span>최신 데이터셋</span><b>{latest_dataset}</b></div>
          <div class="status-item"><span class="accent-green">{svg_icon("shield-check-svgrepo-com.svg", color="#22C55E")}</span><span>예측 상태</span><b>준비 완료</b></div>
        </div>
      </div>
    </div>

    <div class="live-section-card">
      <div class="live-section-title"><span class="step-badge">2</span> 일부 수동 입력</div>
      <div class="manual-preview-grid">
        <div class="mini-input-card"><div class="mini-input-top">{svg_icon("clock-five-svgrepo-com.svg", "nav-icon", "#818CF8")}<div class="mini-input-label">예상 취침 시간</div></div><div class="mini-input-value">{input_summary["target_sleep"]}</div></div>
        <div class="mini-input-card"><div class="mini-input-top">{svg_icon("bed-2-svgrepo-com.svg", "nav-icon", "#8B5CF6")}<div class="mini-input-label">평균 수면 패턴</div></div><div class="mini-input-value">보통</div></div>
        <div class="mini-input-card"><div class="mini-input-top">{masked_svg_icon("footprint-svgrepo-com.svg", "nav-icon", "#22C55E")}<div class="mini-input-label">어제 걸음 수</div></div><div class="mini-input-value">{input_summary["previous_steps"]}</div></div>
        <div class="mini-input-card"><div class="mini-input-top">{svg_icon("shoe-svgrepo-com.svg", "nav-icon", "#38BDF8")}<div class="mini-input-label">오늘 취침 전</div></div><div class="mini-input-value">{input_summary["pre_sleep_steps"]}</div></div>
        <div class="mini-input-card"><div class="mini-input-top">{svg_icon("fire-svgrepo-com.svg", "nav-icon", "#F59E0B")}<div class="mini-input-label">칼로리 입력</div></div><div class="mini-input-value">{input_summary["calories"]}</div></div>
        <div class="mini-input-card"><div class="mini-input-top">{svg_icon("heart-rate-svgrepo-com.svg", "nav-icon", "#EF4444")}<div class="mini-input-label">휴식 시 심박</div></div><div class="mini-input-value">{input_summary["resting_hr"]}</div></div>
      </div>
      <div class="small-label" style="margin-top: 1rem;">Samsung 내보내기에 오늘의 시간대별 값이 부족하면 아래 보완 입력을 사용합니다.</div>
    </div>
  </div>
</div>
"""
    )

    with st.expander("Samsung 데이터 최신성 진단", expanded=False):
        st.dataframe(
            freshness_df[["데이터", "상태", "최신 데이터 시각", "행 수", "시간 컬럼", "파일 수정 시각"]],
            use_container_width=True,
            hide_index=True,
        )

    render_html(
        f"""
<div class="manual-widget-shell">
  <div class="live-section-title">{svg_icon("smartwatch-svgrepo-com.svg", "nav-icon", "#38BDF8")} 오늘 wearable 보완 입력</div>
  <div class="small-label">아래 입력은 모델 재학습이 아니라 오늘 밤 예측용 원본 특성 보완값으로만 기록됩니다.</div>
</div>
"""
    )
    use_manual_supplement = st.checkbox(
        "Samsung export에 오늘 intraday 값이 부족하면 아래 입력으로 보완",
        value=False,
        help="이 값은 모델 재학습이 아니라 오늘 밤 예측용 원본 특성 보완값입니다.",
    )
    manual_supplement = None
    if use_manual_supplement:
        left, right = st.columns(2)
        with left:
            today_steps = st.number_input("오늘 현재까지 걸음 수", min_value=0, max_value=80000, value=7000, step=500)
            last_3h_steps = st.number_input("최근 3시간 걸음 수", min_value=0, max_value=30000, value=500, step=100)
            last_1h_steps = st.number_input("최근 1시간 걸음 수", min_value=0, max_value=20000, value=100, step=50)
        with right:
            heart_rate_mean = st.number_input("오늘 취침 전 평균 심박", min_value=30, max_value=180, value=68, step=1)
            last_3h_heart_rate = st.number_input("최근 3시간 평균 심박", min_value=30, max_value=180, value=68, step=1)
            last_1h_heart_rate = st.number_input("최근 1시간 평균 심박", min_value=30, max_value=180, value=66, step=1)
        manual_supplement = build_manual_wearable_supplement(
            today_steps=today_steps,
            last_3h_steps=last_3h_steps,
            last_1h_steps=last_1h_steps,
            heart_rate_mean=heart_rate_mean,
            last_3h_heart_rate=last_3h_heart_rate,
            last_1h_heart_rate=last_1h_heart_rate,
        )
        st.caption("칼로리 특성은 걸음 수 기반 보조 추정값으로 함께 채웁니다. 원천 Samsung 데이터가 아니라 수동 보완값으로 기록됩니다.")

    if run_today_clicked:
        if not data_dir.exists():
            st.error(f"데이터 폴더가 없습니다: {data_dir}")
            st.stop()

        with st.status("최신 데이터 반영 후 오늘 밤 예측 갱신 중...", expanded=True) as status:
            results = run_today_forecast_pipeline(data_dir, target_sleep_start, manual_supplement)
            success = render_step_results(results)
            if success:
                status.update(label="오늘 밤 예측 갱신 완료", state="complete")
                sync_outputs_to_gcs(st.session_state.get("active_profile_id", "default_profile"))
            else:
                status.update(label="오늘 밤 예측 갱신 실패", state="error")
                st.stop()

    render_today_forecast_result(load_csv_if_exists(TODAY_PREDICTION_PATH))


def write_retraining_plan() -> Path:
    RETRAIN_PLAN_PATH.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "# Samsung Model Retraining Experiment Plan",
        "",
        "## Purpose",
        "",
        "Define the safe research workflow for retraining or fine-tuning after new labeled sleep episodes are available.",
        "",
        "## Important Distinction",
        "",
        "- `오늘 밤 예측 갱신` updates feature history/baseline inputs and keeps the final MLP fixed.",
        "- `모델 재학습 실험` would rebuild labeled data, train a candidate model, evaluate it, and version new artifacts.",
        "",
        "## Required Inputs",
        "",
        "```text",
        "new labeled sleep episodes through at least the latest completed night",
        "Samsung-compatible feature table",
        "stable label definition",
        "participant-aware validation design",
        "```",
        "",
        "## Safe Retraining Gates",
        "",
        "- Do not include the current night's unlabeled sleep in training.",
        "- Do not overwrite the selected final Fitbit-trained MLP checkpoint.",
        "- Save retrained candidates under a new experiment directory.",
        "- Recompute validation metrics, threshold policy, calibration diagnostics, and caveats before promotion.",
        "- Treat this as research/fine-tuning, not the default live user flow.",
        "",
        "## Suggested Future Workflow",
        "",
        "```text",
        "1. Build Samsung labeled training table",
        "2. Rebuild feature matrix with the same leakage rules",
        "3. Create participant/time-aware train/validation/test split",
        "4. Train candidate MLP",
        "5. Evaluate against held-out labeled episodes",
        "6. Select threshold and write model card",
        "7. Package candidate inference artifacts",
        "```",
        "",
        "## Current Prototype Status",
        "",
        "The current app implements the planning/control surface only. It does not run training from the UI.",
        "",
    ]
    RETRAIN_PLAN_PATH.write_text("\n".join(lines), encoding="utf-8")
    return RETRAIN_PLAN_PATH


def render_retraining_tab() -> None:
    st.subheader("고급: 모델 재학습 실험")
    st.warning(
        "이 기능은 기본 오늘 밤 예측 흐름이 아닙니다. 최근 며칠 데이터만으로 모델을 재학습하면 과적합과 검증 누락 위험이 큽니다."
    )
    st.markdown(
        """
```text
재학습 실험
-> 새 labeled episodes 포함 dataset rebuild
-> participant/time-aware validation
-> MLP training
-> threshold/calibration 재평가
-> 새 model artifact version 저장
```
"""
    )
    plan_path = write_retraining_plan()
    st.success(f"재학습 실험 계획 파일 준비됨: {plan_path}")
    st.download_button(
        "재학습 실험 계획 다운로드",
        data=plan_path.read_text(encoding="utf-8").encode("utf-8"),
        file_name="samsung_model_retraining_experiment_plan.md",
        mime="text/markdown",
    )
    if st.button("재학습 실험 계획 다시 생성", type="secondary"):
        plan_path = write_retraining_plan()
        st.success(f"재학습 실험 계획 파일 다시 생성: {plan_path}")


def render_sync_tab(data_dir: Path, run_clicked: bool) -> None:
    file_counts = count_files(data_dir)
    st.subheader("Samsung Health 데이터 연결")
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("CSV 파일", f"{file_counts['csv']:,}")
    c2.metric("JSON 파일", f"{file_counts['json']:,}")
    c3.metric("총 파일", f"{file_counts['total']:,}")
    c4.metric("마지막 수정", file_counts["latest_modified"] or "-")

    with st.expander("감지된 핵심 데이터 파일", expanded=False):
        st.dataframe(dataset_status(data_dir), use_container_width=True, hide_index=True)

    previous_snapshot = latest_previous_snapshot()

    if run_clicked:
        if not data_dir.exists():
            st.error(f"데이터 폴더가 없습니다: {data_dir}")
            st.stop()

        with st.status("Samsung Health 데이터 동기화 및 예측 실행 중...", expanded=True) as status:
            results = run_pipeline(data_dir)
            success = True
            for result in results:
                if result["returncode"] == 0:
                    st.write(f"완료: {result['step']}")
                else:
                    success = False
                    st.error(f"실패: {result['step']}")
                    st.code(result["stderr"] or result["stdout"], language="text")
                    break
            if success:
                status.update(label="예측 갱신 완료", state="complete")
                sync_outputs_to_gcs(st.session_state.get("active_profile_id", "default_profile"))
            else:
                status.update(label="예측 실행 실패", state="error")
                st.stop()

    predictions = load_csv_if_exists(PREDICTION_PATH)
    comparison = compare_to_snapshot(predictions, previous_snapshot)

    if run_clicked and not predictions.empty:
        snapshot_path = save_snapshot(predictions)
        if snapshot_path:
            st.success(f"이번 실행 snapshot 저장: {snapshot_path}")
        if previous_snapshot:
            shutil.copy2(previous_snapshot, SNAPSHOT_DIR / "previous_snapshot_used_for_comparison.csv")

    render_prediction_view(predictions, comparison)


def render_quick_preset_tab() -> None:
    st.subheader("일부 입력 + 프리셋 빠른 예측")
    st.caption(
        "사용자가 직접 입력한 걸음 수와 상태 프리셋을 Design C Stage 1 raw feature 70개로 변환한 뒤, "
        "기존 최종 MLP inference pipeline에 그대로 넣습니다."
    )

    with st.form("quick_preset_form"):
        left, right = st.columns(2)
        with left:
            sleep_date = st.date_input("예상 취침 날짜", value=datetime.now().date(), key="quick_date")
            sleep_time = st.time_input("예상 취침 시각", value=time(23, 30), key="quick_time")
            previous_day_steps = st.number_input("전날 총 걸음 수", min_value=0, max_value=80000, value=8000, step=500, key="quick_prev_steps")
            pre_sleep_steps = st.number_input("오늘 취침 전까지 걸음 수", min_value=0, max_value=80000, value=7000, step=500, key="quick_pre_steps")
            last_3h_steps = st.number_input("취침 전 3시간 걸음 수", min_value=0, max_value=30000, value=500, step=100, key="quick_3h_steps")
            last_1h_steps = st.number_input("취침 전 1시간 걸음 수", min_value=0, max_value=20000, value=100, step=50, key="quick_1h_steps")

        with right:
            activity_preset = st.selectbox("전체 활동량", ACTIVITY_PRESETS, key="quick_activity")
            calorie_preset = st.selectbox("칼로리 소모", CALORIE_PRESETS, key="quick_calorie")
            heart_rate_preset = st.selectbox("취침 전 심박 상태", HEART_RATE_PRESETS, key="quick_hr")
            previous_sleep_preset = st.selectbox("이전 수면 상태", PREVIOUS_SLEEP_PRESETS, key="quick_prev_sleep")
            baseline_daily_calories = st.number_input("평소 하루 칼로리 소모 추정", min_value=0, max_value=8000, value=2200, step=100, key="quick_calories")
            baseline_resting_hr = st.number_input("평소 안정시 심박 추정", min_value=30, max_value=140, value=65, step=1, key="quick_rest_hr")
            baseline_active_minutes = st.number_input("평소 active minutes 추정", min_value=0, max_value=600, value=60, step=10, key="quick_active_minutes")

        run_preset = st.form_submit_button("프리셋 예측 실행", type="primary")
    if not run_preset:
        st.info("값을 입력한 뒤 프리셋 예측을 실행하세요.")
        return

    preset_input = make_preset_input(
        datetime.combine(sleep_date, sleep_time),
        previous_day_steps,
        pre_sleep_steps,
        last_3h_steps,
        last_1h_steps,
        baseline_daily_calories,
        baseline_resting_hr,
        baseline_active_minutes,
        activity_preset,
        calorie_preset,
        heart_rate_preset,
        previous_sleep_preset,
    )
    feature_df, source_df, prediction_df = predict_preset(preset_input)

    probability = float(prediction_df.loc[0, "good_sleep_probability"])
    pred = int(prediction_df.loc[0, "good_sleep_pred"])
    threshold = float(prediction_df.loc[0, "threshold"])
    prediction_target = datetime.combine(sleep_date, sleep_time)

    st.info(forecast_sentence(prediction_target, probability, pred))

    c1, c2, c3 = st.columns(3)
    c1.metric("Good sleep probability", f"{probability:.3f}")
    c2.metric("예측 label", "Good" if pred == 1 else "Not good")
    c3.metric("적용 threshold", f"{threshold:.2f}")
    st.progress(min(max(probability, 0.0), 1.0))

    feature_summary = summarize_feature_sources(source_df)
    f1, f2, f3, f4 = st.columns(4)
    f1.metric("raw features", f"{feature_summary['raw_features']:,}")
    f2.metric("입력/파생 feature", f"{feature_summary['filled']:,}")
    f3.metric("imputer 보완", f"{feature_summary['missing']:,}")
    f4.metric("missing 비율", f"{feature_summary['missing_rate']:.1%}")

    st.markdown(
        f"""
<div class="prototype-note">
현재 점수는 <b>{probability_band(probability)}</b> 구간입니다. 입력되지 않은 feature는 정답 label이 아니라
학습 시점 median imputer로 보완되는 모델 입력 보조값입니다.
</div>
""",
        unsafe_allow_html=True,
    )

    PRESET_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    raw_path = PRESET_OUTPUT_DIR / "quick_preset_raw_stage1_features.csv"
    pred_path = PRESET_OUTPUT_DIR / "quick_preset_prediction.csv"
    source_path = PRESET_OUTPUT_DIR / "quick_preset_feature_source_summary.csv"
    feature_df.to_csv(raw_path, index=False, encoding="utf-8-sig")
    prediction_df.to_csv(pred_path, index=False, encoding="utf-8-sig")
    source_df.to_csv(source_path, index=False, encoding="utf-8-sig")

    st.success("프리셋 입력이 기존 최종 MLP inference pipeline을 통과했습니다.")
    st.caption(f"저장 위치: {PRESET_OUTPUT_DIR}")

    with st.expander("모델에 들어간 feature 출처 요약", expanded=False):
        source_count = source_df.groupby("source", dropna=False).size().reset_index(name="feature_count")
        source_count["source_label"] = source_count["source"].map(SOURCE_LABELS).fillna(source_count["source"])
        st.dataframe(source_count.sort_values("feature_count", ascending=False), use_container_width=True, hide_index=True)

    with st.expander("실제 생성된 raw Stage 1 feature", expanded=False):
        st.dataframe(source_df[["feature", "source", "value", "is_missing_before_imputer"]], use_container_width=True, hide_index=True)

    st.warning(
        "프리셋 빠른 예측은 사용자가 입력하지 않은 feature를 학습 데이터 기준 imputer에 맡기는 제한 입력 모드입니다. "
        "정식 외부 검증이 아니라 데모 및 민감도 확인용으로 해석해야 합니다."
    )


def render_scenario_tab() -> None:
    st.subheader("프리셋 시나리오 비교")
    st.caption(
        "같은 기본 입력에서 활동량, 칼로리, 심박 프리셋만 바꾸어 최종 MLP 점수가 어떻게 움직이는지 비교합니다."
    )

    left, right = st.columns(2)
    with left:
        sleep_date = st.date_input("예상 취침 날짜", value=datetime.now().date(), key="scenario_date")
        sleep_time = st.time_input("예상 취침 시각", value=time(23, 30), key="scenario_time")
        previous_day_steps = st.number_input("전날 총 걸음 수", min_value=0, max_value=80000, value=8000, step=500, key="scenario_prev_steps")
        pre_sleep_steps = st.number_input("오늘 취침 전까지 걸음 수", min_value=0, max_value=80000, value=7000, step=500, key="scenario_pre_steps")
        last_3h_steps = st.number_input("취침 전 3시간 걸음 수", min_value=0, max_value=30000, value=500, step=100, key="scenario_3h_steps")
        last_1h_steps = st.number_input("취침 전 1시간 걸음 수", min_value=0, max_value=20000, value=100, step=50, key="scenario_1h_steps")

    with right:
        baseline_daily_calories = st.number_input("평소 하루 칼로리 소모 추정", min_value=0, max_value=8000, value=2200, step=100, key="scenario_calories")
        baseline_resting_hr = st.number_input("평소 안정시 심박 추정", min_value=30, max_value=140, value=65, step=1, key="scenario_rest_hr")
        baseline_active_minutes = st.number_input("평소 active minutes 추정", min_value=0, max_value=600, value=60, step=10, key="scenario_active_minutes")
        selected_activity = st.multiselect("비교할 활동량 프리셋", ACTIVITY_PRESETS[:3], default=ACTIVITY_PRESETS[:3])
        selected_calorie = st.multiselect("비교할 칼로리 프리셋", CALORIE_PRESETS[:3], default=CALORIE_PRESETS[:3])
        selected_hr = st.multiselect("비교할 심박 프리셋", HEART_RATE_PRESETS[:3], default=HEART_RATE_PRESETS[:3])
        previous_sleep_preset = st.selectbox("이전 수면 상태", PREVIOUS_SLEEP_PRESETS, key="scenario_prev_sleep")

    run_scenarios = st.button("시나리오 비교 실행", type="primary")
    if not run_scenarios:
        st.info("비교할 프리셋 조합을 선택한 뒤 실행하세요.")
        return

    if not selected_activity or not selected_calorie or not selected_hr:
        st.error("활동량, 칼로리, 심박 프리셋을 각각 하나 이상 선택해야 합니다.")
        return

    sleep_start = datetime.combine(sleep_date, sleep_time)
    st.info(
        f"지금까지 입력한 기본 조건을 기준으로 {format_prediction_target(sleep_start)}에 시작하는 "
        f"{forecast_subject(sleep_start)}의 시나리오별 예측을 비교합니다."
    )

    rows = []
    raw_frames = []
    for idx, (activity, calorie, heart_rate) in enumerate(product(selected_activity, selected_calorie, selected_hr), start=1):
        preset_input = make_preset_input(
            sleep_start,
            previous_day_steps,
            pre_sleep_steps,
            last_3h_steps,
            last_1h_steps,
            baseline_daily_calories,
            baseline_resting_hr,
            baseline_active_minutes,
            activity,
            calorie,
            heart_rate,
            previous_sleep_preset,
        )
        feature_df, _, prediction_df = predict_preset(preset_input)
        feature_df.insert(0, "scenario_id", f"scenario_{idx:03d}")
        raw_frames.append(feature_df)
        rows.append(
            {
                "scenario_id": f"scenario_{idx:03d}",
                "prediction_target": format_prediction_target(sleep_start),
                "activity_preset": activity,
                "calorie_preset": calorie,
                "heart_rate_preset": heart_rate,
                "previous_sleep_preset": previous_sleep_preset,
                "good_sleep_probability": float(prediction_df.loc[0, "good_sleep_probability"]),
                "good_sleep_pred": int(prediction_df.loc[0, "good_sleep_pred"]),
                "threshold": float(prediction_df.loc[0, "threshold"]),
            }
        )

    scenario_df = pd.DataFrame(rows).sort_values("good_sleep_probability", ascending=False)
    scenario_df["rank"] = range(1, len(scenario_df) + 1)
    scenario_df = scenario_df[["rank"] + [c for c in scenario_df.columns if c != "rank"]]

    probability_spread = float(scenario_df["good_sleep_probability"].max() - scenario_df["good_sleep_probability"].min())
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("시나리오 수", f"{len(scenario_df):,}")
    c2.metric("최고 probability", f"{scenario_df['good_sleep_probability'].max():.3f}")
    c3.metric("최저 probability", f"{scenario_df['good_sleep_probability'].min():.3f}")
    c4.metric("최고-최저 차이", f"{probability_spread:.3f}")

    st.dataframe(scenario_df, use_container_width=True, hide_index=True)
    st.bar_chart(scenario_df.set_index("scenario_id")["good_sleep_probability"], height=280)

    best = scenario_df.iloc[0]
    worst = scenario_df.iloc[-1]
    st.markdown(
        f"""
<div class="prototype-note">
가장 높은 조합은 {best['activity_preset']} / {best['calorie_preset']} / {best['heart_rate_preset']}이고,
가장 낮은 조합과의 probability 차이는 {probability_spread:.3f}입니다.
</div>
""",
        unsafe_allow_html=True,
    )

    PRESET_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    scenario_path = PRESET_OUTPUT_DIR / "quick_preset_scenario_comparison.csv"
    raw_path = PRESET_OUTPUT_DIR / "quick_preset_scenario_raw_features.csv"
    scenario_df.to_csv(scenario_path, index=False, encoding="utf-8-sig")
    pd.concat(raw_frames, ignore_index=True).to_csv(raw_path, index=False, encoding="utf-8-sig")
    st.caption(f"저장 위치: {scenario_path}")


def render_info_tab() -> None:
    render_model_card()
    render_model_flow()
    st.subheader("입력 모드")
    st.markdown(
        """
- **Samsung 동기화 예측**: Samsung Health export를 읽어서 수면 episode와 Stage 1 feature를 만들고 최종 MLP로 예측합니다.
- **프리셋 빠른 예측**: 걸음 수처럼 직접 입력 가능한 값과 활동/심박/칼로리 프리셋을 70개 raw feature로 변환하고 같은 MLP로 예측합니다.
- **시나리오 비교**: 같은 기본 입력에서 여러 프리셋 조합을 한 번에 돌려 MLP 점수 변화를 비교합니다.
- 모든 모드는 새 모델을 학습하지 않고, 기존 최종 checkpoint와 동일한 imputer/scaler/threshold를 사용합니다.
"""
    )
    st.subheader("해석 주의")
    st.markdown(
        """
Samsung Health와 Fitbit은 센서, 샘플링, 칼로리 계산식, 수면 단계 알고리즘이 다릅니다.
따라서 Samsung 모드는 formal external validation이 아니라 cross-device transfer diagnostic입니다.
프리셋 빠른 예측과 시나리오 비교는 제한된 입력을 기존 모델 계약에 맞춰 통과시키는 데모 모드입니다.
"""
    )


def main() -> None:
    st.set_page_config(page_title="Samsung 수면 예측 Live Prototype", layout="wide")
    render_app_style()

    render_html(
        f"""
<div class="main-title-wrap">
  <div class="brand-lockup">
    <div class="brand-mark">{svg_icon("night-symbol-of-the-moon-with-a-cloud-and-stars-svgrepo-com.svg", color="#F8FAFC")}</div>
    <div>
      <div class="main-title">Sleep Forecast AI</div>
      <div class="main-subtitle">Wearable Sleep Prediction · Samsung Health live inference prototype</div>
    </div>
  </div>
  <div class="live-pill">● Live · 마지막 업데이트: 1분 전</div>
</div>
"""
    )

    with st.sidebar:
        st.markdown("## Sleep Forecast AI")
        st.caption("Wearable Sleep Prediction")
        st.header("데이터 소스")
        source_mode = st.radio("Samsung Health 데이터", ["기본 데이터 사용", "프로필 ZIP 데이터 사용", "다른 export 폴더 사용"])
        active_profile_id = safe_profile_id(st.session_state.get("active_profile_id", "default_profile"))
        if source_mode == "기본 데이터 사용":
            data_dir = DEFAULT_SAMSUNG_DIR
            st.text_input("기본 경로", value=str(data_dir), disabled=True)
        elif source_mode == "프로필 ZIP 데이터 사용":
            profiles = list_profile_ids()
            if active_profile_id not in profiles:
                profiles.insert(0, active_profile_id)
            selected_profile = st.selectbox("프로필", profiles + ["새 프로필 만들기"], index=profiles.index(active_profile_id))
            if selected_profile == "새 프로필 만들기":
                profile_input = st.text_input("새 프로필 ID", value="new_profile")
                active_profile_id = safe_profile_id(profile_input)
            else:
                active_profile_id = safe_profile_id(selected_profile)
            st.session_state["active_profile_id"] = active_profile_id
            data_dir = prepare_profile_work_dir(active_profile_id)
            manifest = load_profile_manifest(active_profile_id)
            storage_label = manifest.get("raw_export_dir") or str(data_dir)
            st.text_input("프로필 raw 경로", value=storage_label, disabled=True)
        else:
            data_dir = Path(st.text_input("Samsung Health export 폴더", value=str(DEFAULT_SAMSUNG_DIR)))

        st.header("실행")
        target_date = st.date_input("다음 예상 취침 날짜", value=datetime.now().date(), key="today_target_date")
        target_time = st.time_input("다음 예상 취침 시각", value=time(23, 30), key="today_target_time")
        target_sleep_start = datetime.combine(target_date, target_time)
        run_today_clicked = st.button("오늘 밤 예측 갱신", type="primary")
        run_clicked = st.button("완료 episode 예측 갱신", type="secondary")

    predictions = load_csv_if_exists(PREDICTION_PATH)
    today_forecast = load_csv_if_exists(TODAY_PREDICTION_PATH)
    previous_snapshot = latest_previous_snapshot()
    comparison = compare_to_snapshot(predictions, previous_snapshot)

    overview_tab, today_tab, sync_tab, quick_tab, scenario_tab, retrain_tab, info_tab = st.tabs(
        ["대시보드", "오늘 밤 예측", "완료 episode 예측", "프리셋 빠른 예측", "시나리오 비교", "고급 재학습", "모델 설명"]
    )
    with overview_tab:
        render_overview_tab(data_dir, predictions, comparison, today_forecast, active_profile_id)
    with today_tab:
        render_today_forecast_tab(data_dir, run_today_clicked, target_sleep_start)
    with sync_tab:
        render_sync_tab(data_dir, run_clicked)
    with quick_tab:
        render_quick_preset_tab()
    with scenario_tab:
        render_scenario_tab()
    with retrain_tab:
        render_retraining_tab()
    with info_tab:
        render_info_tab()


if __name__ == "__main__":
    main()
