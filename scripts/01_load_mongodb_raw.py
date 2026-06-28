from __future__ import annotations

from datetime import datetime
from pathlib import Path
from pprint import pformat
from typing import Any

from pymongo import MongoClient


# 로컬 MongoDB에 복원된 LifeSnaps 원본 DB 접속 정보입니다.
# Atlas가 아니라 PC에서 실행 중인 mongod에 붙는 설정입니다.
MONGO_URI = "mongodb://localhost:27017"
DB_NAME = "rais_anonymized"

# 원본 BSON에서 복원한 핵심 컬렉션만 먼저 확인합니다.
# fitbit은 매우 크기 때문에 전체를 읽지 않고 샘플/문서 수만 봅니다.
COLLECTIONS = ("fitbit", "sema", "surveys")
REPORT_PATH = Path(__file__).resolve().parents[1] / "reports" / "mongodb_raw_overview.md"


def summarize_value(value: Any, depth: int = 0) -> Any:
    """큰 원본 문서를 그대로 출력하지 않고, 구조만 짧게 요약합니다."""

    # MongoDB 문서는 중첩 dict/list가 많습니다.
    # 너무 깊게 내려가면 보고서가 길어지므로 3단계까지만 펼칩니다.
    if depth >= 3:
        return type(value).__name__

    if isinstance(value, dict):
        # 상위 key 일부만 남겨 컬렉션의 대략적인 모양을 확인합니다.
        return {
            key: summarize_value(item, depth + 1)
            for key, item in list(value.items())[:12]
        }

    if isinstance(value, list):
        # 리스트는 첫 번째 원소의 구조와 전체 길이만 남깁니다.
        # 예: sleep stage의 상세 리스트 전체를 보고서에 넣지 않기 위함입니다.
        if not value:
            return []
        return [summarize_value(value[0], depth + 1), f"... {len(value)} item(s)"]

    if isinstance(value, datetime):
        return value.isoformat()

    if isinstance(value, str):
        return value if len(value) <= 80 else value[:77] + "..."

    return value


def collection_overview(client: MongoClient) -> list[dict[str, Any]]:
    """각 원본 컬렉션의 존재 여부, 문서 수, 첫 문서 구조를 확인합니다."""

    db = client[DB_NAME]
    available = set(db.list_collection_names())
    overviews: list[dict[str, Any]] = []

    for name in COLLECTIONS:
        if name not in available:
            overviews.append({"collection": name, "status": "missing"})
            continue

        collection = db[name]

        # find_one()은 컬렉션 구조를 빠르게 보기 위한 용도입니다.
        # fitbit 전체는 7천만 건 이상이므로 여기서 절대 전체 로드하지 않습니다.
        sample = collection.find_one()
        overviews.append(
            {
                "collection": name,
                "status": "ok",
                "estimated_document_count": collection.estimated_document_count(),
                "top_level_keys": sorted(sample.keys()) if sample else [],
                "sample_shape": summarize_value(sample) if sample else None,
            }
        )

    return overviews


def write_report(overviews: list[dict[str, Any]]) -> None:
    """MongoDB 연결 점검 결과를 Markdown 보고서로 저장합니다."""

    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "# MongoDB Raw Data Overview",
        "",
        f"- Mongo URI: `{MONGO_URI}`",
        f"- Database: `{DB_NAME}`",
        f"- Generated at: `{datetime.now().isoformat(timespec='seconds')}`",
        "",
    ]

    for item in overviews:
        lines.extend(
            [
                f"## {item['collection']}",
                "",
                f"- Status: `{item['status']}`",
            ]
        )
        if item["status"] == "ok":
            lines.extend(
                [
                    f"- Estimated document count: `{item['estimated_document_count']}`",
                    "- Top-level keys:",
                    "",
                    "```text",
                    "\n".join(item["top_level_keys"]),
                    "```",
                    "",
                    "- Sample shape:",
                    "",
                    "```text",
                    pformat(item["sample_shape"], width=100, sort_dicts=False),
                    "```",
                ]
            )
        lines.append("")

    REPORT_PATH.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    # serverSelectionTimeoutMS를 짧게 둬서 mongod가 꺼져 있을 때 오래 기다리지 않게 합니다.
    client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=5000)

    # 실제 쿼리를 시작하기 전 ping으로 연결 가능 여부를 명확히 확인합니다.
    client.admin.command("ping")

    overviews = collection_overview(client)
    write_report(overviews)

    for item in overviews:
        if item["status"] != "ok":
            print(f"{item['collection']}: {item['status']}")
            continue
        print(
            f"{item['collection']}: "
            f"{item['estimated_document_count']} docs, "
            f"{len(item['top_level_keys'])} top-level keys"
        )
    print(f"\nWrote report: {REPORT_PATH}")


if __name__ == "__main__":
    main()
