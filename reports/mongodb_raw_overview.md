# MongoDB Raw Data Overview

- Mongo URI: `mongodb://localhost:27017`
- Database: `rais_anonymized`
- Generated at: `2026-06-26T19:15:10`

## fitbit

- Status: `ok`
- Estimated document count: `71284346`
- Top-level keys:

```text
_id
data
id
type
```

- Sample shape:

```text
{'_id': ObjectId('62cc1f9ab41dcd4b1beae820'),
 'id': ObjectId('621e2e8e67b776a24055b564'),
 'type': 'estimated_oxygen_variation',
 'data': {'timestamp': '05/24/21 01:03:30', 'Infrared to Red Signal Ratio': -4}}
```

## sema

- Status: `ok`
- Estimated document count: `15380`
- Top-level keys:

```text
_id
data
user_id
```

- Sample shape:

```text
{'_id': ObjectId('62cc7d568e3d174ffc0fbb47'),
 'user_id': ObjectId('621e2f1b67b776a240b3d87c'),
 'data': {'PARTICIPANT_ID': 's523044002',
          'STUDY_ID': 'uk96OixJ-',
          'STUDY_NAME': 'RAIS Consortium Experiment v2.0',
          'STUDY_VERSION': 5,
          'SURVEY_ID': 'BjTcu3Lg-',
          'SURVEY_NAME': 'Context and Mood Survey',
          'TRIGGER': 'scheduled',
          'START_END': 1,
          'CREATED_TS': '2021-12-15T15:26:00',
          'SCHEDULED_TS': '2021-12-15T15:16:00',
          'STARTED_TS': '2021-12-15T15:26:00',
          'COMPLETED_TS': '2021-12-15T15:26:00'}}
```

## surveys

- Status: `ok`
- Estimated document count: `935`
- Top-level keys:

```text
_id
data
type
user_id
```

- Sample shape:

```text
{'_id': ObjectId('6241bd11a59be121689b2aff'),
 'user_id': ObjectId('621e36f967b776a240e5e7c9'),
 'type': 'breq',
 'data': {'id': 1,
          'submitdate': '31/5/2021 12:42',
          'startdate': '31/5/2021 12:41',
          'datestamp': '31/5/2021 12:42',
          'engage[SQ001]': 3,
          'engage[SQ002]': 5,
          'engage[SQ003]': 5,
          'engage[SQ004]': 3,
          'engage[SQ005]': 1,
          'engage[SQ006]': 1,
          'engage[SQ007]': 5,
          'engage[SQ008]': 4}}
```
