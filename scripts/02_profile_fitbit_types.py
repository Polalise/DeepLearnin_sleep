from __future__ import annotations

from datetime import datetime
from pathlib import Path
from pprint import pformat
from typing import Any

from pymongo import MongoClient


# Fitbit 원본 로그는 하나의 컬렉션 안에 여러 종류의 record가 섞여 있습니다.
# 예: heart_rate, sleep, steps, Stress Score 등이 모두 fitbit 컬렉션에 들어 있습니다.
MONGO_URI = "mongodb://localhost:27017"
DB_NAME = "rais_anonymized"
COLLECTION = "fitbit"
REPORT_PATH = Path(__file__).resolve().parents[1] / "reports" / "fitbit_type_profile.md"


def compact(value: Any, depth: int = 0) -> Any:
    """각 type의 샘플 문서를 사람이 읽기 쉬운 짧은 형태로 줄입니다."""

    # 샘플 문서에는 긴 리스트가 들어갈 수 있으므로 깊이 제한을 둡니다.
    if depth >= 3:
        return type(value).__name__
    if isinstance(value, dict):
        # dict는 앞쪽 key 일부만 보여줍니다.
        return {key: compact(item, depth + 1) for key, item in list(value.items())[:16]}
    if isinstance(value, list):
        # 리스트 전체를 출력하지 않고 첫 원소의 구조와 길이만 확인합니다.
        if not value:
            return []
        return [compact(value[0], depth + 1), f"... {len(value)} item(s)"]
    if isinstance(value, str):
        return value if len(value) <= 100 else value[:97] + "..."
    return value


def main() -> None:
    # 로컬 MongoDB에 연결합니다. mongod가 실행 중이어야 합니다.
    client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=5000)
    client.admin.command("ping")
    collection = client[DB_NAME][COLLECTION]

    # fitbit 컬렉션에서 type별 문서 수를 집계합니다.
    # 이 결과를 보면 어떤 원본 데이터를 먼저 사용할지 정할 수 있습니다.
    # allowDiskUse=True는 큰 컬렉션 집계에서 MongoDB가 임시 디스크 사용을 허용하게 합니다.
    pipeline = [
        {"$group": {"_id": "$type", "count": {"$sum": 1}}},
        {"$sort": {"count": -1}},
    ]
    type_counts = list(
        collection.aggregate(pipeline, allowDiskUse=True, maxTimeMS=120_000)
    )

    lines = [
        "# Fitbit Raw Type Profile",
        "",
        f"- Mongo URI: `{MONGO_URI}`",
        f"- Database: `{DB_NAME}`",
        f"- Collection: `{COLLECTION}`",
        f"- Generated at: `{datetime.now().isoformat(timespec='seconds')}`",
        "",
        "## Type Counts",
        "",
        "| type | documents |",
        "| --- | ---: |",
    ]

    for row in type_counts:
        lines.append(f"| `{row['_id']}` | {row['count']} |")

    lines.extend(["", "## Sample Shapes", ""])

    for row in type_counts:
        type_name = row["_id"]

        # 각 type마다 대표 문서 1개만 가져옵니다.
        # 구조 확인용이므로 전체 문서를 DataFrame으로 읽지 않습니다.
        sample = collection.find_one({"type": type_name})
        lines.extend(
            [
                f"### {type_name}",
                "",
                "```text",
                pformat(compact(sample), width=110, sort_dicts=False),
                "```",
                "",
            ]
        )

    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    REPORT_PATH.write_text("\n".join(lines), encoding="utf-8")

    print("Fitbit types:")
    for row in type_counts:
        print(f"- {row['_id']}: {row['count']}")
    print(f"\nWrote report: {REPORT_PATH}")


if __name__ == "__main__":
    main()
