from __future__ import annotations

from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path
from pprint import pformat
from typing import Any

from pymongo import MongoClient


# This script completes the collection-level EDA step.
# It does not build the final modeling table yet; it only documents what each
# MongoDB collection contains and which variables are promising for extraction.
MONGO_URI = "mongodb://localhost:27017"
DB_NAME = "rais_anonymized"
REPORT_PATH = Path(__file__).resolve().parents[1] / "reports" / "collection_eda_summary.md"


# Fitbit is very large, so we profile only types that are useful for sleep
# prediction or feature engineering. The full type distribution already exists
# in reports/fitbit_type_profile.md.
FITBIT_CANDIDATE_TYPES = [
    "sleep",
    "Stress Score",
    "Daily Heart Rate Variability Summary",
    "Heart Rate Variability Details",
    "resting_heart_rate",
    "steps",
    "calories",
    "sedentary_minutes",
    "lightly_active_minutes",
    "moderately_active_minutes",
    "very_active_minutes",
    "Daily SpO2",
    "Respiratory Rate Summary",
    "Wrist Temperature",
]


# Fitbit documents use different date field names depending on type.
# We check these fields to understand how later date-level aggregation should work.
FITBIT_DATE_FIELDS = [
    "data.DATE",
    "data.dateOfSleep",
    "data.dateTime",
    "data.date",
    "data.timestamp",
    "data.startTime",
    "data.sleep_start",
    "data.reading_time",
    "data.recorded_time",
]


def compact(value: Any, depth: int = 0) -> Any:
    """Return a short structural preview for nested MongoDB documents."""

    if depth >= 3:
        return type(value).__name__
    if isinstance(value, dict):
        return {key: compact(item, depth + 1) for key, item in list(value.items())[:18]}
    if isinstance(value, list):
        if not value:
            return []
        return [compact(value[0], depth + 1), f"... {len(value)} item(s)"]
    if isinstance(value, str):
        return value if len(value) <= 120 else value[:117] + "..."
    return value


def flatten_keys(value: Any, prefix: str = "") -> list[str]:
    """Collect dotted key paths from a nested dict/list sample."""

    if isinstance(value, dict):
        keys: list[str] = []
        for key, item in value.items():
            dotted = f"{prefix}.{key}" if prefix else str(key)
            keys.append(dotted)
            keys.extend(flatten_keys(item, dotted))
        return keys
    if isinstance(value, list) and value:
        return flatten_keys(value[0], f"{prefix}[]")
    return []


def data_key_counter(documents: list[dict[str, Any]]) -> Counter[str]:
    """Count how often each key under data appears across small collections."""

    counter: Counter[str] = Counter()
    for document in documents:
        data = document.get("data", {})
        for key in flatten_keys(data):
            counter[key] += 1
    return counter


def get_nested(document: dict[str, Any], dotted_path: str) -> Any:
    """Read a dotted field path from a nested MongoDB document."""

    current: Any = document
    for part in dotted_path.split("."):
        if not isinstance(current, dict) or part not in current:
            return None
        current = current[part]
    return current


def fitbit_type_profile(db: Any) -> list[dict[str, Any]]:
    """Profile selected Fitbit types without loading the full Fitbit collection."""

    collection = db.fitbit
    rows: list[dict[str, Any]] = []

    for type_name in FITBIT_CANDIDATE_TYPES:
        query = {"type": type_name}
        sample = collection.find_one(query, {"_id": 1, "id": 1, "type": 1, "data": 1})
        count = collection.count_documents(query)

        date_fields: dict[str, dict[str, Any]] = {}
        for field in FITBIT_DATE_FIELDS:
            # Count only documents where the candidate date field exists.
            # This tells us which field should be used for date-level aggregation.
            exists_query = {"type": type_name, field: {"$exists": True, "$ne": None}}
            exists_count = collection.count_documents(exists_query)
            if exists_count == 0:
                continue

            # For large time-series types, min/max helps confirm the period covered.
            pipeline = [
                {"$match": exists_query},
                {"$group": {"_id": None, "min": {"$min": f"${field}"}, "max": {"$max": f"${field}"}}},
            ]
            range_row = next(collection.aggregate(pipeline, allowDiskUse=True), {})
            date_fields[field] = {
                "count": exists_count,
                "min": range_row.get("min"),
                "max": range_row.get("max"),
            }

        rows.append(
            {
                "type": type_name,
                "document_count": count,
                "data_top_keys": sorted(sample.get("data", {}).keys()) if sample else [],
                "date_fields": date_fields,
                "sample_shape": compact(sample) if sample else None,
            }
        )

    return rows


def sema_profile(db: Any) -> dict[str, Any]:
    """Profile SEMA mood/context survey documents."""

    documents = list(db.sema.find({}, {"_id": 1, "user_id": 1, "data": 1}))
    survey_names = Counter(doc.get("data", {}).get("SURVEY_NAME") for doc in documents)
    participants = {str(doc.get("user_id")) for doc in documents if doc.get("user_id") is not None}
    key_counts = data_key_counter(documents)

    created_values = [
        doc.get("data", {}).get("CREATED_TS")
        for doc in documents
        if doc.get("data", {}).get("CREATED_TS") is not None
    ]

    return {
        "document_count": len(documents),
        "participant_count": len(participants),
        "survey_name_counts": survey_names,
        "created_ts_min": min(created_values) if created_values else None,
        "created_ts_max": max(created_values) if created_values else None,
        "top_data_keys": key_counts.most_common(80),
        "sample_shape": compact(documents[0]) if documents else None,
    }


def surveys_profile(db: Any) -> dict[str, Any]:
    """Profile participant-level survey documents by survey type."""

    documents = list(db.surveys.find({}, {"_id": 1, "user_id": 1, "type": 1, "data": 1}))
    type_counts = Counter(doc.get("type") for doc in documents)
    participants = {str(doc.get("user_id")) for doc in documents if doc.get("user_id") is not None}

    keys_by_type: dict[str, Counter[str]] = defaultdict(Counter)
    sample_by_type: dict[str, dict[str, Any]] = {}
    for doc in documents:
        survey_type = str(doc.get("type"))
        sample_by_type.setdefault(survey_type, doc)
        for key in flatten_keys(doc.get("data", {})):
            keys_by_type[survey_type][key] += 1

    return {
        "document_count": len(documents),
        "participant_count": len(participants),
        "type_counts": type_counts,
        "top_data_keys_by_type": {
            survey_type: counter.most_common(60)
            for survey_type, counter in sorted(keys_by_type.items())
        },
        "sample_shape_by_type": {
            survey_type: compact(sample)
            for survey_type, sample in sorted(sample_by_type.items())
        },
    }


def write_report(fitbit_rows: list[dict[str, Any]], sema: dict[str, Any], surveys: dict[str, Any]) -> None:
    """Write the collection-level EDA summary as Markdown."""

    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "# Collection EDA Summary",
        "",
        f"- Mongo URI: `{MONGO_URI}`",
        f"- Database: `{DB_NAME}`",
        f"- Generated at: `{datetime.now().isoformat(timespec='seconds')}`",
        "",
        "## Scope",
        "",
        "- This report completes the collection-level EDA step.",
        "- It documents what each MongoDB collection contains before variable extraction.",
        "- It does not perform date-level aggregation, merging, imputation, encoding, scaling, or PCA.",
        "",
        "## Fitbit Candidate Types",
        "",
        "| type | documents | useful date fields | top data keys |",
        "| --- | ---: | --- | --- |",
    ]

    for row in fitbit_rows:
        date_field_text = "<br>".join(
            f"`{field}` ({info['count']:,})"
            for field, info in row["date_fields"].items()
        )
        key_text = ", ".join(f"`{key}`" for key in row["data_top_keys"][:14])
        lines.append(
            f"| `{row['type']}` | {row['document_count']:,} | {date_field_text or '-'} | {key_text or '-'} |"
        )

    lines.extend(["", "### Fitbit Sample Shapes", ""])
    for row in fitbit_rows:
        lines.extend(
            [
                f"#### {row['type']}",
                "",
                "Date fields:",
                "",
            ]
        )
        if row["date_fields"]:
            for field, info in row["date_fields"].items():
                lines.append(
                    f"- `{field}`: {info['count']:,} docs, min=`{info['min']}`, max=`{info['max']}`"
                )
        else:
            lines.append("- No obvious date field found.")
        lines.extend(
            [
                "",
                "```text",
                pformat(row["sample_shape"], width=110, sort_dicts=False),
                "```",
                "",
            ]
        )

    lines.extend(
        [
            "## SEMA Collection",
            "",
            f"- Documents: `{sema['document_count']:,}`",
            f"- Participants: `{sema['participant_count']:,}`",
            f"- CREATED_TS range: `{sema['created_ts_min']}` to `{sema['created_ts_max']}`",
            "",
            "### Survey Names",
            "",
            "| survey name | documents |",
            "| --- | ---: |",
        ]
    )
    for name, count in sema["survey_name_counts"].most_common():
        lines.append(f"| `{name}` | {count:,} |")

    lines.extend(["", "### Top SEMA Data Keys", "", "| key | documents |", "| --- | ---: |"])
    for key, count in sema["top_data_keys"]:
        lines.append(f"| `{key}` | {count:,} |")

    lines.extend(
        [
            "",
            "### SEMA Sample Shape",
            "",
            "```text",
            pformat(sema["sample_shape"], width=110, sort_dicts=False),
            "```",
            "",
            "## Surveys Collection",
            "",
            f"- Documents: `{surveys['document_count']:,}`",
            f"- Participants: `{surveys['participant_count']:,}`",
            "",
            "### Survey Type Counts",
            "",
            "| survey type | documents |",
            "| --- | ---: |",
        ]
    )
    for survey_type, count in surveys["type_counts"].most_common():
        lines.append(f"| `{survey_type}` | {count:,} |")

    lines.extend(["", "### Top Survey Data Keys By Type", ""])
    for survey_type, keys in surveys["top_data_keys_by_type"].items():
        lines.extend([f"#### {survey_type}", "", "| key | documents |", "| --- | ---: |"])
        for key, count in keys:
            lines.append(f"| `{key}` | {count:,} |")
        lines.append("")

    lines.extend(["### Survey Sample Shapes", ""])
    for survey_type, sample in surveys["sample_shape_by_type"].items():
        lines.extend(
            [
                f"#### {survey_type}",
                "",
                "```text",
                pformat(sample, width=110, sort_dicts=False),
                "```",
                "",
            ]
        )

    lines.extend(
        [
            "## Variable Extraction Plan",
            "",
            "Recommended next extraction targets:",
            "",
            "- `fitbit.sleep`: sleep target and sleep-stage variables.",
            "- `fitbit.Stress Score`: stress explanatory variable.",
            "- `fitbit.Daily Heart Rate Variability Summary`: daily HRV features.",
            "- `fitbit.resting_heart_rate`: daily resting heart rate.",
            "- `fitbit.steps`, `fitbit.calories`, activity-minute types: daily activity features.",
            "- `sema`: EMA mood/context variables, joined by participant and response date.",
            "- `surveys`: participant-level survey features, joined by participant.",
            "",
            "Next pipeline stage:",
            "",
            "```text",
            "필요한 변수 추출 -> 날짜 단위 집계 -> fitbit/sema/surveys 병합",
            "```",
            "",
        ]
    )

    REPORT_PATH.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=5000)
    client.admin.command("ping")
    db = client[DB_NAME]

    print("Profiling selected Fitbit types...")
    fitbit_rows = fitbit_type_profile(db)

    print("Profiling SEMA collection...")
    sema = sema_profile(db)

    print("Profiling surveys collection...")
    surveys = surveys_profile(db)

    write_report(fitbit_rows, sema, surveys)

    print(f"Wrote report: {REPORT_PATH}")
    print("Fitbit candidate types profiled:", len(fitbit_rows))
    print("SEMA documents:", sema["document_count"])
    print("Survey documents:", surveys["document_count"])


if __name__ == "__main__":
    main()
