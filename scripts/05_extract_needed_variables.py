from __future__ import annotations

import csv
from datetime import datetime
from pathlib import Path
from typing import Any, Iterable

import pandas as pd
from pymongo import MongoClient


# This script performs the "needed variable extraction" step after collection EDA.
# It extracts model candidate variables from MongoDB into small, reusable raw tables.
#
# Important boundary:
# - This script does not merge fitbit/sema/surveys.
# - This script does not impute missing values, encode categories, scale, or run PCA.
# - Very large minute-level sources such as steps/calories are documented here, but
#   they should be aggregated directly from MongoDB in the next date-level aggregation step.
MONGO_URI = "mongodb://localhost:27017"
DB_NAME = "rais_anonymized"

PROJECT_ROOT = Path(__file__).resolve().parents[1]
OUTPUT_DIR = PROJECT_ROOT / "data" / "raw" / "extracted_variables"
REPORT_PATH = PROJECT_ROOT / "reports" / "variable_extraction_summary.md"


def get_nested(document: dict[str, Any], dotted_path: str) -> Any:
    """Read a dotted path from a nested dict and return None when missing."""

    current: Any = document
    for part in dotted_path.split("."):
        if not isinstance(current, dict) or part not in current:
            return None
        current = current[part]
    return current


def stringify(value: Any) -> Any:
    """Convert MongoDB-specific objects to CSV-friendly values."""

    if value is None:
        return None
    if isinstance(value, datetime):
        return value.isoformat()
    return str(value) if value.__class__.__name__ == "ObjectId" else value


def write_csv(path: Path, fieldnames: list[str], rows: Iterable[dict[str, Any]]) -> int:
    """Write rows to CSV without requiring the whole table in memory."""

    path.parent.mkdir(parents=True, exist_ok=True)
    count = 0
    with path.open("w", newline="", encoding="utf-8-sig") as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow({key: stringify(row.get(key)) for key in fieldnames})
            count += 1
    return count


def fitbit_rows(
    collection: Any,
    type_name: str,
    field_map: dict[str, str],
    batch_size: int = 1000,
) -> Iterable[dict[str, Any]]:
    """Yield flattened rows for one Fitbit type."""

    projection = {"_id": 1, "id": 1, "type": 1}
    for source_path in field_map.values():
        projection[source_path] = 1

    cursor = collection.find(
        {"type": type_name},
        projection,
        batch_size=batch_size,
    )

    for document in cursor:
        row: dict[str, Any] = {
            "mongo_doc_id": document.get("_id"),
            "participant_object_id": document.get("id"),
            "fitbit_type": document.get("type"),
        }
        for output_name, source_path in field_map.items():
            row[output_name] = get_nested(document, source_path)
        yield row


def export_fitbit_type(
    collection: Any,
    type_name: str,
    output_name: str,
    field_map: dict[str, str],
) -> dict[str, Any]:
    """Export one selected Fitbit type to a raw variable CSV."""

    path = OUTPUT_DIR / f"{output_name}.csv"
    fieldnames = ["mongo_doc_id", "participant_object_id", "fitbit_type", *field_map.keys()]
    count = write_csv(path, fieldnames, fitbit_rows(collection, type_name, field_map))
    return {
        "name": output_name,
        "source": f"fitbit.{type_name}",
        "path": path,
        "rows": count,
        "columns": len(fieldnames),
    }


def export_activity_minutes(collection: Any) -> dict[str, Any]:
    """Export daily Fitbit activity-minute types into one long table."""

    activity_types = [
        "sedentary_minutes",
        "lightly_active_minutes",
        "moderately_active_minutes",
        "very_active_minutes",
    ]
    path = OUTPUT_DIR / "fitbit_activity_minutes.csv"
    fieldnames = [
        "mongo_doc_id",
        "participant_object_id",
        "fitbit_type",
        "date_time",
        "value",
    ]

    def rows() -> Iterable[dict[str, Any]]:
        for type_name in activity_types:
            yield from fitbit_rows(
                collection,
                type_name,
                {
                    "date_time": "data.dateTime",
                    "value": "data.value",
                },
            )

    count = write_csv(path, fieldnames, rows())
    return {
        "name": "fitbit_activity_minutes",
        "source": "fitbit activity-minute types",
        "path": path,
        "rows": count,
        "columns": len(fieldnames),
    }


def export_sema(db: Any) -> dict[str, Any]:
    """Flatten SEMA mood/context responses into one raw table."""

    documents = list(db.sema.find({}, {"_id": 1, "user_id": 1, "data": 1}))
    records: list[dict[str, Any]] = []
    for document in documents:
        data = document.get("data", {})
        row = {
            "mongo_doc_id": str(document.get("_id")),
            "participant_object_id": str(document.get("user_id")),
        }
        row.update(data)
        records.append(row)

    df = pd.DataFrame(records)
    path = OUTPUT_DIR / "sema_responses.csv"
    path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(path, index=False, encoding="utf-8-sig")

    return {
        "name": "sema_responses",
        "source": "sema",
        "path": path,
        "rows": len(df),
        "columns": len(df.columns),
    }


def export_surveys(db: Any) -> dict[str, Any]:
    """Flatten participant-level survey responses into one raw table."""

    documents = list(db.surveys.find({}, {"_id": 1, "user_id": 1, "type": 1, "data": 1}))
    records: list[dict[str, Any]] = []
    for document in documents:
        data = document.get("data", {})
        row = {
            "mongo_doc_id": str(document.get("_id")),
            "participant_object_id": str(document.get("user_id")),
            "survey_type": document.get("type"),
        }
        row.update(data)
        records.append(row)

    df = pd.DataFrame(records)
    path = OUTPUT_DIR / "surveys_responses.csv"
    path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(path, index=False, encoding="utf-8-sig")

    return {
        "name": "surveys_responses",
        "source": "surveys",
        "path": path,
        "rows": len(df),
        "columns": len(df.columns),
    }


def write_report(exports: list[dict[str, Any]]) -> None:
    """Write a summary of extracted variable tables and next steps."""

    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "# Variable Extraction Summary",
        "",
        f"- Mongo URI: `{MONGO_URI}`",
        f"- Database: `{DB_NAME}`",
        f"- Generated at: `{datetime.now().isoformat(timespec='seconds')}`",
        "",
        "## Scope",
        "",
        "- This report covers the needed-variable extraction step.",
        "- Output tables are first-extract/raw tables saved under `data/raw/extracted_variables/`.",
        "- No cross-source merge, imputation, categorical encoding, scaling, or PCA was performed.",
        "",
        "## Extracted Tables",
        "",
        "| table | source | rows | columns | path |",
        "| --- | --- | ---: | ---: | --- |",
    ]

    for item in exports:
        columns = item.get("columns", "")
        lines.append(
            f"| `{item['name']}` | `{item['source']}` | {item['rows']:,} | {columns} | `{item['path']}` |"
        )

    lines.extend(
        [
            "",
            "## Large Sources Reserved For Date-Level Aggregation",
            "",
            "The following Fitbit sources are useful but very large. They should be aggregated",
            "directly from MongoDB in the next step instead of exporting full raw CSV files now.",
            "",
            "| source | count from EDA | aggregation idea |",
            "| --- | ---: | --- |",
            "| `fitbit.steps` | 3,010,529 | daily sum by participant/date |",
            "| `fitbit.calories` | 9,675,782 | daily sum by participant/date |",
            "| `fitbit.Wrist Temperature` | 4,372,238 | daily mean/min/max by participant/date |",
            "",
            "## Next Step",
            "",
            "```text",
            "date-level aggregation -> merge fitbit/sema/surveys -> final dataset EDA",
            "```",
            "",
        ]
    )

    REPORT_PATH.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=5000)
    client.admin.command("ping")
    db = client[DB_NAME]
    fitbit = db.fitbit

    exports: list[dict[str, Any]] = []

    exports.append(
        export_fitbit_type(
            fitbit,
            "Stress Score",
            "fitbit_stress_score",
            {
                "date_time": "data.DATE",
                "updated_at": "data.UPDATED_AT",
                "stress_score": "data.STRESS_SCORE",
                "sleep_points": "data.SLEEP_POINTS",
                "max_sleep_points": "data.MAX_SLEEP_POINTS",
                "responsiveness_points": "data.RESPONSIVENESS_POINTS",
                "max_responsiveness_points": "data.MAX_RESPONSIVENESS_POINTS",
                "exertion_points": "data.EXERTION_POINTS",
                "max_exertion_points": "data.MAX_EXERTION_POINTS",
                "status": "data.STATUS",
                "calculation_failed": "data.CALCULATION_FAILED",
            },
        )
    )

    exports.append(
        export_fitbit_type(
            fitbit,
            "Daily Heart Rate Variability Summary",
            "fitbit_daily_hrv_summary",
            {
                "timestamp": "data.timestamp",
                "rmssd": "data.rmssd",
                "nremhr": "data.nremhr",
                "entropy": "data.entropy",
            },
        )
    )

    exports.append(
        export_fitbit_type(
            fitbit,
            "Heart Rate Variability Details",
            "fitbit_hrv_details",
            {
                "timestamp": "data.timestamp",
                "rmssd": "data.rmssd",
                "coverage": "data.coverage",
                "low_frequency": "data.low_frequency",
                "high_frequency": "data.high_frequency",
            },
        )
    )

    exports.append(
        export_fitbit_type(
            fitbit,
            "resting_heart_rate",
            "fitbit_resting_heart_rate",
            {
                "date_time": "data.dateTime",
                "value_date": "data.value.date",
                "resting_heart_rate": "data.value.value",
                "error": "data.value.error",
            },
        )
    )

    exports.append(export_activity_minutes(fitbit))

    exports.append(
        export_fitbit_type(
            fitbit,
            "Daily SpO2",
            "fitbit_daily_spo2",
            {
                "timestamp": "data.timestamp",
                "average_value": "data.average_value",
                "lower_bound": "data.lower_bound",
                "upper_bound": "data.upper_bound",
            },
        )
    )

    exports.append(
        export_fitbit_type(
            fitbit,
            "Respiratory Rate Summary",
            "fitbit_respiratory_rate_summary",
            {
                "timestamp": "data.timestamp",
                "full_sleep_breathing_rate": "data.full_sleep_breathing_rate",
                "full_sleep_signal_to_noise": "data.full_sleep_signal_to_noise",
                "full_sleep_standard_deviation": "data.full_sleep_standard_deviation",
                "deep_sleep_breathing_rate": "data.deep_sleep_breathing_rate",
                "light_sleep_breathing_rate": "data.light_sleep_breathing_rate",
                "rem_sleep_breathing_rate": "data.rem_sleep_breathing_rate",
            },
        )
    )

    exports.append(export_sema(db))
    exports.append(export_surveys(db))

    write_report(exports)

    print("Extracted variable tables:")
    for item in exports:
        columns = f", {item['columns']} cols" if "columns" in item else ""
        print(f"- {item['name']}: {item['rows']} rows{columns}")
    print(f"\nWrote report: {REPORT_PATH}")


if __name__ == "__main__":
    main()
