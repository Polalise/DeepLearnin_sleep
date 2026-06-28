from __future__ import annotations

from pathlib import Path
from typing import Any

import pandas as pd
from pymongo import MongoClient


# 로컬 MongoDB 원본에서 sleep 로그만 추출해 분석용 CSV로 저장하는 스크립트입니다.
# fitbit 전체를 pandas로 읽으면 메모리 문제가 생기므로 type == "sleep"만 조회합니다.
MONGO_URI = "mongodb://localhost:27017"
DB_NAME = "rais_anonymized"
COLLECTION = "fitbit"
OUTPUT_PATH = Path(__file__).resolve().parents[1] / "data" / "raw" / "sleep_from_mongodb.csv"


# sleep 문서의 data 안에서 바로 꺼낼 수 있는 기본 수면 지표입니다.
# 모델링 target 후보인 minutesAsleep, minutesAwake, efficiency 등이 여기에 포함됩니다.
BASE_FIELDS = [
    "logId",
    "dateOfSleep",
    "startTime",
    "endTime",
    "duration",
    "minutesToFallAsleep",
    "minutesAsleep",
    "minutesAwake",
    "minutesAfterWakeup",
    "timeInBed",
    "efficiency",
    "type",
    "infoCode",
    "mainSleep",
]


def get_nested(data: dict[str, Any], path: tuple[str, ...]) -> Any:
    """중첩된 dict에서 안전하게 값을 꺼냅니다.

    예:
    get_nested(data, ("levels", "summary", "deep", "minutes"))

    sleep stage 정보는 문서마다 구조가 조금 다를 수 있어서,
    key가 없으면 에러를 내지 않고 None을 반환합니다.
    """

    current: Any = data
    for key in path:
        if not isinstance(current, dict) or key not in current:
            return None
        current = current[key]
    return current


def sleep_row(document: dict[str, Any]) -> dict[str, Any]:
    """MongoDB sleep 문서 1개를 DataFrame 한 행으로 펼칩니다."""

    data = document.get("data", {})

    # MongoDB의 ObjectId는 CSV 저장 시 그대로 쓰기 어렵기 때문에 문자열로 바꿉니다.
    # participant_object_id는 이후 다른 Fitbit type과 병합할 때 사용할 참가자 key입니다.
    row: dict[str, Any] = {
        "mongo_doc_id": str(document.get("_id")),
        "participant_object_id": str(document.get("id")),
    }

    # data 최상위에 있는 sleep 기본 필드를 그대로 복사합니다.
    for field in BASE_FIELDS:
        row[field] = data.get(field)

    # Fitbit sleep 로그에는 두 가지 sleep level 체계가 섞일 수 있습니다.
    # stages: deep/light/rem/wake
    # classic: asleep/restless/awake
    # 둘 다 컬럼으로 만들어두면 나중에 결측 패턴을 보고 선택할 수 있습니다.
    for stage in ("deep", "light", "rem", "wake", "asleep", "restless", "awake"):
        row[f"{stage}_count"] = get_nested(data, ("levels", "summary", stage, "count"))
        row[f"{stage}_minutes"] = get_nested(data, ("levels", "summary", stage, "minutes"))
        row[f"{stage}_30day_avg_minutes"] = get_nested(
            data, ("levels", "summary", stage, "thirtyDayAvgMinutes")
        )

    return row


def main() -> None:
    # 로컬 MongoDB에 연결합니다. 이 스크립트 실행 전 mongod가 켜져 있어야 합니다.
    client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=5000)
    client.admin.command("ping")
    collection = client[DB_NAME][COLLECTION]

    # projection으로 필요한 필드만 가져옵니다.
    # _id, id, data만 있으면 sleep table 생성에 충분합니다.
    # batch_size는 한 번에 너무 많은 문서를 메모리에 올리지 않기 위한 안전장치입니다.
    cursor = collection.find(
        {"type": "sleep"},
        {"_id": 1, "id": 1, "data": 1},
        batch_size=500,
    )
    df = pd.DataFrame(sleep_row(document) for document in cursor)

    if df.empty:
        raise RuntimeError("No sleep documents found in MongoDB.")

    # 날짜/시간 문자열을 pandas datetime으로 변환합니다.
    # errors="coerce"는 파싱 실패 값을 NaT로 두어 이후 결측치 점검이 가능하게 합니다.
    df["dateOfSleep"] = pd.to_datetime(df["dateOfSleep"], errors="coerce")
    df["startTime"] = pd.to_datetime(df["startTime"], errors="coerce")
    df["endTime"] = pd.to_datetime(df["endTime"], errors="coerce")

    # 참가자와 날짜 기준으로 정렬해 같은 사람의 수면 흐름을 보기 쉽게 합니다.
    df = df.sort_values(["participant_object_id", "dateOfSleep", "startTime"])

    # 원본에서 바로 추출한 1차 raw table이므로 data/raw 아래에 저장합니다.
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(OUTPUT_PATH, index=False, encoding="utf-8-sig")

    print(f"Rows: {len(df)}")
    print(f"Columns: {len(df.columns)}")
    print(f"Participants: {df['participant_object_id'].nunique()}")
    print(f"Date range: {df['dateOfSleep'].min().date()} to {df['dateOfSleep'].max().date()}")
    print(f"Main sleep rows: {int(df['mainSleep'].fillna(False).sum())}")
    print(f"Wrote: {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
