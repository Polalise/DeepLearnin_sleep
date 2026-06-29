from pathlib import Path
import argparse
import json

import numpy as np
import pandas as pd
from bson import ObjectId
from pymongo import MongoClient


ID_COL = "participant_object_id"


def resolve_mongo_participant_id(participant_id):
    if isinstance(participant_id, ObjectId):
        return participant_id
    return ObjectId(str(participant_id))


def format_mongo_datetime_for_type(timestamp, fitbit_type):
    if fitbit_type == "calories":
        return timestamp.strftime("%m/%d/%y %H:%M:%S")
    return timestamp.strftime("%Y-%m-%dT%H:%M:%S")


def aggregate_steps(collection, participant_id, start_dt, end_dt, sleep_start_datetime):
    mongo_id = resolve_mongo_participant_id(participant_id)
    start_str = format_mongo_datetime_for_type(start_dt, "steps")
    end_str = format_mongo_datetime_for_type(end_dt, "steps")
    last_3h_str = format_mongo_datetime_for_type(sleep_start_datetime - pd.Timedelta(hours=3), "steps")
    last_1h_str = format_mongo_datetime_for_type(sleep_start_datetime - pd.Timedelta(hours=1), "steps")

    pipeline = [
        {"$match": {"id": mongo_id, "type": "steps", "data.dateTime": {"$gte": start_str, "$lt": end_str}}},
        {"$project": {"_id": 0, "dateTime": "$data.dateTime", "value": {"$toDouble": "$data.value"}}},
        {
            "$group": {
                "_id": None,
                "steps_pre_sleep_sum": {"$sum": "$value"},
                "steps_pre_sleep_record_count": {"$sum": 1},
                "steps_pre_sleep_active_record_count": {"$sum": {"$cond": [{"$gt": ["$value", 0]}, 1, 0]}},
                "steps_pre_sleep_last_3h_sum": {"$sum": {"$cond": [{"$gte": ["$dateTime", last_3h_str]}, "$value", 0]}},
                "steps_pre_sleep_last_1h_sum": {"$sum": {"$cond": [{"$gte": ["$dateTime", last_1h_str]}, "$value", 0]}},
            }
        },
    ]

    result = list(collection.aggregate(pipeline, allowDiskUse=False))
    if not result:
        return {
            "steps_pre_sleep_sum": np.nan,
            "steps_pre_sleep_record_count": 0,
            "steps_pre_sleep_active_record_count": 0,
            "steps_pre_sleep_last_3h_sum": np.nan,
            "steps_pre_sleep_last_1h_sum": np.nan,
        }

    row = result[0]
    row.pop("_id", None)
    return row


def aggregate_calories(collection, participant_id, start_dt, end_dt, sleep_start_datetime):
    mongo_id = resolve_mongo_participant_id(participant_id)
    start_str = format_mongo_datetime_for_type(start_dt, "calories")
    end_str = format_mongo_datetime_for_type(end_dt, "calories")
    last_3h_str = format_mongo_datetime_for_type(sleep_start_datetime - pd.Timedelta(hours=3), "calories")
    last_1h_str = format_mongo_datetime_for_type(sleep_start_datetime - pd.Timedelta(hours=1), "calories")

    pipeline = [
        {"$match": {"id": mongo_id, "type": "calories", "data.dateTime": {"$gte": start_str, "$lt": end_str}}},
        {"$project": {"_id": 0, "dateTime": "$data.dateTime", "value": {"$toDouble": "$data.value"}}},
        {
            "$group": {
                "_id": None,
                "calories_pre_sleep_sum": {"$sum": "$value"},
                "calories_pre_sleep_record_count": {"$sum": 1},
                "calories_pre_sleep_last_3h_sum": {"$sum": {"$cond": [{"$gte": ["$dateTime", last_3h_str]}, "$value", 0]}},
                "calories_pre_sleep_last_1h_sum": {"$sum": {"$cond": [{"$gte": ["$dateTime", last_1h_str]}, "$value", 0]}},
            }
        },
    ]

    result = list(collection.aggregate(pipeline, allowDiskUse=False))
    if not result:
        return {
            "calories_pre_sleep_sum": np.nan,
            "calories_pre_sleep_record_count": 0,
            "calories_pre_sleep_last_3h_sum": np.nan,
            "calories_pre_sleep_last_1h_sum": np.nan,
        }

    row = result[0]
    row.pop("_id", None)
    return row


def aggregate_heart_rate(collection, participant_id, start_dt, end_dt, sleep_start_datetime):
    mongo_id = resolve_mongo_participant_id(participant_id)
    start_str = format_mongo_datetime_for_type(start_dt, "heart_rate")
    end_str = format_mongo_datetime_for_type(end_dt, "heart_rate")
    last_3h_str = format_mongo_datetime_for_type(sleep_start_datetime - pd.Timedelta(hours=3), "heart_rate")
    last_1h_str = format_mongo_datetime_for_type(sleep_start_datetime - pd.Timedelta(hours=1), "heart_rate")

    pipeline = [
        {"$match": {"id": mongo_id, "type": "heart_rate", "data.dateTime": {"$gte": start_str, "$lt": end_str}}},
        {
            "$project": {
                "_id": 0,
                "dateTime": "$data.dateTime",
                "bpm": {"$toDouble": "$data.value.bpm"},
                "confidence": {"$toDouble": "$data.value.confidence"},
            }
        },
        {
            "$group": {
                "_id": None,
                "heart_rate_pre_sleep_mean": {"$avg": "$bpm"},
                "heart_rate_pre_sleep_std": {"$stdDevPop": "$bpm"},
                "heart_rate_pre_sleep_min": {"$min": "$bpm"},
                "heart_rate_pre_sleep_max": {"$max": "$bpm"},
                "heart_rate_pre_sleep_record_count": {"$sum": 1},
                "heart_rate_pre_sleep_mean_confidence": {"$avg": "$confidence"},
                "heart_rate_pre_sleep_last_3h_mean": {
                    "$avg": {"$cond": [{"$gte": ["$dateTime", last_3h_str]}, "$bpm", "$$REMOVE"]}
                },
                "heart_rate_pre_sleep_last_1h_mean": {
                    "$avg": {"$cond": [{"$gte": ["$dateTime", last_1h_str]}, "$bpm", "$$REMOVE"]}
                },
                "heart_rate_values": {"$push": "$bpm"},
            }
        },
        {
            "$project": {
                "_id": 0,
                "heart_rate_pre_sleep_mean": 1,
                "heart_rate_pre_sleep_std": 1,
                "heart_rate_pre_sleep_min": 1,
                "heart_rate_pre_sleep_max": 1,
                "heart_rate_pre_sleep_record_count": 1,
                "heart_rate_pre_sleep_mean_confidence": 1,
                "heart_rate_pre_sleep_last_3h_mean": 1,
                "heart_rate_pre_sleep_last_1h_mean": 1,
                "heart_rate_pre_sleep_median": {
                    "$arrayElemAt": [
                        {"$sortArray": {"input": "$heart_rate_values", "sortBy": 1}},
                        {"$floor": {"$divide": [{"$size": "$heart_rate_values"}, 2]}},
                    ]
                },
            }
        },
    ]

    result = list(collection.aggregate(pipeline, allowDiskUse=False))
    if not result:
        return {
            "heart_rate_pre_sleep_mean": np.nan,
            "heart_rate_pre_sleep_std": np.nan,
            "heart_rate_pre_sleep_min": np.nan,
            "heart_rate_pre_sleep_max": np.nan,
            "heart_rate_pre_sleep_record_count": 0,
            "heart_rate_pre_sleep_mean_confidence": np.nan,
            "heart_rate_pre_sleep_last_3h_mean": np.nan,
            "heart_rate_pre_sleep_last_1h_mean": np.nan,
            "heart_rate_pre_sleep_median": np.nan,
        }

    return result[0]


def build_timing_features(sleep_start_datetime):
    sleep_start_date = sleep_start_datetime.normalize()
    pre_sleep_window_hours = (sleep_start_datetime - sleep_start_date).total_seconds() / 3600

    sleep_start_hour = (
        sleep_start_datetime.hour
        + sleep_start_datetime.minute / 60
        + sleep_start_datetime.second / 3600
    )

    dayofweek = sleep_start_datetime.dayofweek
    month = sleep_start_datetime.month

    return {
        "pre_sleep_window_hours": pre_sleep_window_hours,
        "sleep_start_hour": sleep_start_hour,
        "sleep_start_dayofweek_sin": np.sin(2 * np.pi * dayofweek / 7),
        "sleep_start_dayofweek_cos": np.cos(2 * np.pi * dayofweek / 7),
        "sleep_start_month_sin": np.sin(2 * np.pi * month / 12),
        "sleep_start_month_cos": np.cos(2 * np.pi * month / 12),
    }


def build_previous_day_features(daily_df, participant_id, sleep_start_datetime, previous_day_feature_names):
    previous_day_date = sleep_start_datetime.normalize() - pd.Timedelta(days=1)

    match = daily_df[
        (daily_df[ID_COL].astype(str) == str(participant_id))
        & (daily_df["calendar_date"] == previous_day_date)
    ]

    output = {}

    if len(match) == 0:
        for feature in previous_day_feature_names:
            output[feature] = np.nan
        return output

    row = match.iloc[0]

    for feature in previous_day_feature_names:
        source_feature = feature.replace("previous_day_", "", 1)
        output[feature] = row[source_feature] if source_feature in row.index else np.nan

    return output


def build_feature_row(episode_row, collection, daily_df, raw_features):
    participant_id = str(episode_row[ID_COL])
    sleep_start_datetime = pd.to_datetime(episode_row["sleep_start_datetime"])
    sleep_start_date = sleep_start_datetime.normalize()

    output = {
        ID_COL: participant_id,
        "sleep_start_datetime": sleep_start_datetime,
        "prediction_cutoff_datetime": sleep_start_datetime,
    }

    if "sleep_episode_id" in episode_row and pd.notna(episode_row["sleep_episode_id"]):
        output["sleep_episode_id"] = episode_row["sleep_episode_id"]
    else:
        output["sleep_episode_id"] = (
            participant_id + "__" + sleep_start_datetime.strftime("%Y%m%d%H%M%S")
        )

    output.update(
        aggregate_steps(
            collection=collection,
            participant_id=participant_id,
            start_dt=sleep_start_date,
            end_dt=sleep_start_datetime,
            sleep_start_datetime=sleep_start_datetime,
        )
    )
    output.update(
        aggregate_calories(
            collection=collection,
            participant_id=participant_id,
            start_dt=sleep_start_date,
            end_dt=sleep_start_datetime,
            sleep_start_datetime=sleep_start_datetime,
        )
    )
    output.update(
        aggregate_heart_rate(
            collection=collection,
            participant_id=participant_id,
            start_dt=sleep_start_date,
            end_dt=sleep_start_datetime,
            sleep_start_datetime=sleep_start_datetime,
        )
    )
    output.update(build_timing_features(sleep_start_datetime))

    previous_day_feature_names = [
        feature for feature in raw_features
        if feature.startswith("previous_day_") and not feature.endswith("_missing_ind")
    ]
    output.update(
        build_previous_day_features(
            daily_df=daily_df,
            participant_id=participant_id,
            sleep_start_datetime=sleep_start_datetime,
            previous_day_feature_names=previous_day_feature_names,
        )
    )

    for feature in raw_features:
        if feature.endswith("_missing_ind"):
            base_feature = feature.replace("_missing_ind", "")
            output[feature] = int(pd.isna(output.get(base_feature, np.nan)))

    for feature in raw_features:
        if feature not in output:
            output[feature] = np.nan

    return output


def build_features(episodes_df, project_root, manifest_path, mongo_uri, mongo_db, mongo_collection):
    manifest = json.loads(Path(manifest_path).read_text(encoding="utf-8"))
    raw_features = manifest["raw_feature_order"]

    daily_path = project_root / "data" / "processed" / "modeling_dataset_daily.csv"
    daily_df = pd.read_csv(daily_path, encoding="utf-8-sig")
    daily_df["calendar_date"] = pd.to_datetime(daily_df["calendar_date"]).dt.normalize()

    client = MongoClient(mongo_uri)
    collection = client[mongo_db][mongo_collection]

    rows = []
    total = len(episodes_df)

    for index, (_, episode_row) in enumerate(episodes_df.iterrows(), start=1):
        rows.append(
            build_feature_row(
                episode_row=episode_row,
                collection=collection,
                daily_df=daily_df,
                raw_features=raw_features,
            )
        )

        if index == 1 or index % 25 == 0 or index == total:
            print(f"{index}/{total} episodes processed")

    output_df = pd.DataFrame(rows)

    passthrough_columns = [
        "sleep_episode_id",
        ID_COL,
        "sleep_start_datetime",
        "prediction_cutoff_datetime",
    ]

    return output_df[passthrough_columns + raw_features]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--episodes", required=True, help="CSV with participant_object_id and sleep_start_datetime.")
    parser.add_argument("--output", required=True, help="Output CSV for 70 raw Stage 1 features.")
    parser.add_argument("--project-root", default=r"C:\workSpace\DeepLearnin_sleep")
    parser.add_argument(
        "--manifest",
        default=None,
        help="Inference manifest path. Defaults to selected model manifest.",
    )
    parser.add_argument("--mongo-uri", default="mongodb://localhost:27017")
    parser.add_argument("--mongo-db", default="rais_anonymized")
    parser.add_argument("--mongo-collection", default="fitbit")
    args = parser.parse_args()

    project_root = Path(args.project_root)

    manifest_path = args.manifest
    if manifest_path is None:
        manifest_path = (
            project_root
            / "data"
            / "processed"
            / "pre_sleep_forecasting"
            / "design_c_stage1"
            / "inference_package"
            / "pre_sleep_inference_manifest.json"
        )

    episodes_df = pd.read_csv(args.episodes, encoding="utf-8-sig")

    required_columns = [ID_COL, "sleep_start_datetime"]
    missing_columns = [col for col in required_columns if col not in episodes_df.columns]
    if missing_columns:
        raise ValueError(f"Missing required episode columns: {missing_columns}")

    output_df = build_features(
        episodes_df=episodes_df,
        project_root=project_root,
        manifest_path=manifest_path,
        mongo_uri=args.mongo_uri,
        mongo_db=args.mongo_db,
        mongo_collection=args.mongo_collection,
    )

    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_df.to_csv(output_path, index=False, encoding="utf-8-sig")

    print("raw Stage 1 features written:", output_path)
    print("rows:", len(output_df))
    print("features:", len(output_df.columns))


if __name__ == "__main__":
    main()