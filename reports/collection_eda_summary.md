# Collection EDA Summary

- Mongo URI: `mongodb://localhost:27017`
- Database: `rais_anonymized`
- Generated at: `2026-06-27T01:54:21`

## Scope

- This report completes the collection-level EDA step.
- It documents what each MongoDB collection contains before variable extraction.
- It does not perform date-level aggregation, merging, imputation, encoding, scaling, or PCA.

## Fitbit Candidate Types

| type | documents | useful date fields | top data keys |
| --- | ---: | --- | --- |
| `sleep` | 4,141 | `data.dateOfSleep` (4,141)<br>`data.startTime` (4,141) | `dateOfSleep`, `duration`, `efficiency`, `endTime`, `infoCode`, `levels`, `logId`, `mainSleep`, `minutesAfterWakeup`, `minutesAsleep`, `minutesAwake`, `minutesToFallAsleep`, `startTime`, `timeInBed` |
| `Stress Score` | 1,911 | `data.DATE` (1,911) | `CALCULATION_FAILED`, `DATE`, `EXERTION_POINTS`, `MAX_EXERTION_POINTS`, `MAX_RESPONSIVENESS_POINTS`, `MAX_SLEEP_POINTS`, `RESPONSIVENESS_POINTS`, `SLEEP_POINTS`, `STATUS`, `STRESS_SCORE`, `UPDATED_AT` |
| `Daily Heart Rate Variability Summary` | 2,475 | `data.timestamp` (2,475) | `entropy`, `nremhr`, `rmssd`, `timestamp` |
| `Heart Rate Variability Details` | 220,512 | `data.timestamp` (220,512) | `coverage`, `high_frequency`, `low_frequency`, `rmssd`, `timestamp` |
| `resting_heart_rate` | 12,362 | `data.dateTime` (12,362) | `dateTime`, `value` |
| `steps` | 3,010,529 | `data.dateTime` (3,010,529) | `dateTime`, `value` |
| `calories` | 9,675,782 | `data.dateTime` (9,675,782) | `dateTime`, `value` |
| `sedentary_minutes` | 7,203 | `data.dateTime` (7,203) | `dateTime`, `value` |
| `lightly_active_minutes` | 7,203 | `data.dateTime` (7,203) | `dateTime`, `value` |
| `moderately_active_minutes` | 7,203 | `data.dateTime` (7,203) | `dateTime`, `value` |
| `very_active_minutes` | 7,203 | `data.dateTime` (7,203) | `dateTime`, `value` |
| `Daily SpO2` | 1,274 | `data.timestamp` (1,274) | `average_value`, `lower_bound`, `timestamp`, `upper_bound` |
| `Respiratory Rate Summary` | 3,000 | `data.timestamp` (3,000) | `deep_sleep_breathing_rate`, `deep_sleep_signal_to_noise`, `deep_sleep_standard_deviation`, `full_sleep_breathing_rate`, `full_sleep_signal_to_noise`, `full_sleep_standard_deviation`, `light_sleep_breathing_rate`, `light_sleep_signal_to_noise`, `light_sleep_standard_deviation`, `rem_sleep_breathing_rate`, `rem_sleep_signal_to_noise`, `rem_sleep_standard_deviation`, `timestamp` |
| `Wrist Temperature` | 4,372,238 | `data.recorded_time` (4,372,238) | `recorded_time`, `temperature` |

### Fitbit Sample Shapes

#### sleep

Date fields:

- `data.dateOfSleep`: 4,141 docs, min=`2021-05-24`, max=`2022-01-22`
- `data.startTime`: 4,141 docs, min=`2021-05-24T00:08:30.000`, max=`2022-01-21T23:04:00.000`

```text
{'_id': ObjectId('62cc2021b41dcd4b1bfe938c'),
 'id': ObjectId('621e2e8e67b776a24055b564'),
 'type': 'sleep',
 'data': {'logId': 32294959626,
          'dateOfSleep': '2021-05-24',
          'startTime': '2021-05-24T00:40:00.000',
          'endTime': '2021-05-24T09:21:00.000',
          'duration': 31260000,
          'minutesToFallAsleep': 0,
          'minutesAsleep': 445,
          'minutesAwake': 76,
          'minutesAfterWakeup': 0,
          'timeInBed': 521,
          'efficiency': 93,
          'type': 'stages',
          'infoCode': 0,
          'levels': {'summary': 'dict', 'data': 'list', 'shortData': 'list'},
          'mainSleep': True}}
```

#### Stress Score

Date fields:

- `data.DATE`: 1,911 docs, min=`2021-05-24T00:00:00`, max=`2022-01-22T00:00:00`

```text
{'_id': ObjectId('62cc2029b41dcd4b1b0029d6'),
 'id': ObjectId('621e2e8e67b776a24055b564'),
 'type': 'Stress Score',
 'data': {'DATE': '2021-05-26T00:00:00',
          'UPDATED_AT': '2021-05-26T07:08:02.443',
          'STRESS_SCORE': 84,
          'SLEEP_POINTS': 29,
          'MAX_SLEEP_POINTS': 30,
          'RESPONSIVENESS_POINTS': 26,
          'MAX_RESPONSIVENESS_POINTS': 30,
          'EXERTION_POINTS': 29,
          'MAX_EXERTION_POINTS': 40,
          'STATUS': 'READY',
          'CALCULATION_FAILED': False}}
```

#### Daily Heart Rate Variability Summary

Date fields:

- `data.timestamp`: 2,475 docs, min=`2021-05-24T00:00:00`, max=`2022-01-22T00:00:00`

```text
{'_id': ObjectId('62cc2021b41dcd4b1bfe7950'),
 'id': ObjectId('621e2e8e67b776a24055b564'),
 'type': 'Daily Heart Rate Variability Summary',
 'data': {'timestamp': '2021-05-29T00:00:00', 'rmssd': 89.941, 'nremhr': 57.314, 'entropy': 3.143}}
```

#### Heart Rate Variability Details

Date fields:

- `data.timestamp`: 220,512 docs, min=`2021-05-24T00:00:00`, max=`2022-01-22T00:00:00`

```text
{'_id': ObjectId('62cc2021b41dcd4b1bfe79e5'),
 'id': ObjectId('621e2e8e67b776a24055b564'),
 'type': 'Heart Rate Variability Details',
 'data': {'timestamp': '2021-05-24T00:40:00',
          'rmssd': 118.288,
          'coverage': 0.88,
          'low_frequency': 6000.846,
          'high_frequency': 2975.152}}
```

#### resting_heart_rate

Date fields:

- `data.dateTime`: 12,362 docs, min=`01/01/22 00:00:00`, max=`12/31/21 00:00:00`

```text
{'_id': ObjectId('62cc2021b41dcd4b1bfd9bde'),
 'id': ObjectId('621e2e8e67b776a24055b564'),
 'type': 'resting_heart_rate',
 'data': {'dateTime': '05/25/21 00:00:00', 'value': {'date': 'str', 'value': 'float', 'error': 'float'}}}
```

#### steps

Date fields:

- `data.dateTime`: 3,010,529 docs, min=`2021-05-24T00:00:00`, max=`2022-01-22T00:00:00`

```text
{'_id': ObjectId('62cc2021b41dcd4b1bfdc4a1'),
 'id': ObjectId('621e2e8e67b776a24055b564'),
 'type': 'steps',
 'data': {'dateTime': '2021-05-24T00:15:00', 'value': '0'}}
```

#### calories

Date fields:

- `data.dateTime`: 9,675,782 docs, min=`01/01/22 00:00:00`, max=`12/31/21 23:59:00`

```text
{'_id': ObjectId('62cc1f9ab41dcd4b1bebf727'),
 'id': ObjectId('621e2e8e67b776a24055b564'),
 'type': 'calories',
 'data': {'dateTime': '05/24/21 00:00:00', 'value': '2.62'}}
```

#### sedentary_minutes

Date fields:

- `data.dateTime`: 7,203 docs, min=`01/01/22 00:00:00`, max=`12/31/21 00:00:00`

```text
{'_id': ObjectId('62cc2021b41dcd4b1bfd9d50'),
 'id': ObjectId('621e2e8e67b776a24055b564'),
 'type': 'sedentary_minutes',
 'data': {'dateTime': '05/30/21 00:00:00', 'value': '763'}}
```

#### lightly_active_minutes

Date fields:

- `data.dateTime`: 7,203 docs, min=`01/01/22 00:00:00`, max=`12/31/21 00:00:00`

```text
{'_id': ObjectId('62cc2021b41dcd4b1bfd9b31'),
 'id': ObjectId('621e2e8e67b776a24055b564'),
 'type': 'lightly_active_minutes',
 'data': {'dateTime': '06/01/21 00:00:00', 'value': '106'}}
```

#### moderately_active_minutes

Date fields:

- `data.dateTime`: 7,203 docs, min=`01/01/22 00:00:00`, max=`12/31/21 00:00:00`

```text
{'_id': ObjectId('62cc2021b41dcd4b1bfd9b85'),
 'id': ObjectId('621e2e8e67b776a24055b564'),
 'type': 'moderately_active_minutes',
 'data': {'dateTime': '05/26/21 00:00:00', 'value': '27'}}
```

#### very_active_minutes

Date fields:

- `data.dateTime`: 7,203 docs, min=`01/01/22 00:00:00`, max=`12/31/21 00:00:00`

```text
{'_id': ObjectId('62cc2021b41dcd4b1bfe78b5'),
 'id': ObjectId('621e2e8e67b776a24055b564'),
 'type': 'very_active_minutes',
 'data': {'dateTime': '05/26/21 00:00:00', 'value': '31'}}
```

#### Daily SpO2

Date fields:

- `data.timestamp`: 1,274 docs, min=`2021-05-24T00:00:00Z`, max=`2022-01-22T00:00:00Z`

```text
{'_id': ObjectId('62cc2179b41dcd4b1b32e71c'),
 'id': ObjectId('621e2ef567b776a24099f889'),
 'type': 'Daily SpO2',
 'data': {'timestamp': '2021-10-19T00:00:00Z',
          'average_value': 97.7,
          'lower_bound': 94.4,
          'upper_bound': 99.6}}
```

#### Respiratory Rate Summary

Date fields:

- `data.timestamp`: 3,000 docs, min=`2021-05-24T06:42:00`, max=`2022-01-21T12:43:00`

```text
{'_id': ObjectId('62cc2021b41dcd4b1bfe9344'),
 'id': ObjectId('621e2e8e67b776a24055b564'),
 'type': 'Respiratory Rate Summary',
 'data': {'timestamp': '2021-05-30T09:45:30',
          'full_sleep_breathing_rate': 15.2,
          'full_sleep_standard_deviation': 0.9,
          'full_sleep_signal_to_noise': 7.606,
          'deep_sleep_breathing_rate': 13.8,
          'deep_sleep_standard_deviation': 1.5,
          'deep_sleep_signal_to_noise': 10.003,
          'light_sleep_breathing_rate': None,
          'light_sleep_standard_deviation': None,
          'light_sleep_signal_to_noise': None,
          'rem_sleep_breathing_rate': 15.2,
          'rem_sleep_standard_deviation': 1.0,
          'rem_sleep_signal_to_noise': 3.369}}
```

#### Wrist Temperature

Date fields:

- `data.recorded_time`: 4,372,238 docs, min=`2021-05-24T00:00`, max=`2022-01-22T00:00`

```text
{'_id': ObjectId('62cc2027b41dcd4b1bfed1e0'),
 'id': ObjectId('621e2e8e67b776a24055b564'),
 'type': 'Wrist Temperature',
 'data': {'recorded_time': '2021-05-24T00:00', 'temperature': -1.1897946612}}
```

## SEMA Collection

- Documents: `15,380`
- Participants: `63`
- CREATED_TS range: `2021-04-07T11:59:00` to `2022-01-17T11:09:00`

### Survey Names

| survey name | documents |
| --- | ---: |
| `Context and Mood Survey` | 11,526 |
| `Step Goal Survey` | 3,852 |
| `None` | 2 |

### Top SEMA Data Keys

| key | documents |
| --- | ---: |
| `PARTICIPANT_ID` | 15,380 |
| `STUDY_ID` | 15,380 |
| `STUDY_NAME` | 15,380 |
| `STUDY_VERSION` | 15,380 |
| `SURVEY_ID` | 15,380 |
| `SURVEY_NAME` | 15,380 |
| `TRIGGER` | 15,380 |
| `START_END` | 15,380 |
| `CREATED_TS` | 15,380 |
| `SCHEDULED_TS` | 15,380 |
| `STARTED_TS` | 15,380 |
| `COMPLETED_TS` | 15,380 |
| `EXPIRED_TS` | 15,380 |
| `UPLOADED_TS` | 15,380 |
| `TOTAL_RT` | 15,380 |
| `RAND_PROB` | 15,380 |
| `PLACE` | 15,380 |
| `PLACE_RT` | 15,380 |
| `OTHER` | 15,380 |
| `OTHER_RT` | 15,380 |
| `MOOD` | 15,380 |
| `MOOD_RT` | 15,380 |
| `STEPS` | 15,380 |
| `STEPS_RT` | 15,380 |

### SEMA Sample Shape

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
          'COMPLETED_TS': '2021-12-15T15:26:00',
          'EXPIRED_TS': None,
          'UPLOADED_TS': '2021-12-15T15:26:00',
          'TOTAL_RT': '10030',
          'RAND_PROB': '<no-response>',
          'PLACE': 'HOME',
          'PLACE_RT': '2440'}}
```

## Surveys Collection

- Documents: `935`
- Participants: `67`

### Survey Type Counts

| survey type | documents |
| --- | ---: |
| `stai` | 314 |
| `panas` | 302 |
| `ttmspbf` | 102 |
| `breq` | 99 |
| `dq` | 66 |
| `bfpt` | 52 |

### Top Survey Data Keys By Type

#### bfpt

| key | documents |
| --- | ---: |
| `id` | 52 |
| `submitdate` | 52 |
| `startdate` | 52 |
| `datestamp` | 52 |
| `ipip[SQ001]` | 52 |
| `ipip[SQ002]` | 52 |
| `ipip[SQ003]` | 52 |
| `ipip[SQ004]` | 52 |
| `ipip[SQ005]` | 52 |
| `ipip[SQ006]` | 52 |
| `ipip[SQ007]` | 52 |
| `ipip[SQ008]` | 52 |
| `ipip[SQ009]` | 52 |
| `ipip[SQ010]` | 52 |
| `ipip[SQ011]` | 52 |
| `ipip[SQ012]` | 52 |
| `ipip[SQ013]` | 52 |
| `ipip[SQ014]` | 52 |
| `ipip[SQ015]` | 52 |
| `ipip[SQ016]` | 52 |
| `ipip[SQ017]` | 52 |
| `ipip[SQ018]` | 52 |
| `ipip[SQ019]` | 52 |
| `ipip[SQ020]` | 52 |
| `ipip[SQ021]` | 52 |
| `ipip[SQ022]` | 52 |
| `ipip[SQ023]` | 52 |
| `ipip[SQ024]` | 52 |
| `ipip[SQ025]` | 52 |
| `ipip[SQ026]` | 52 |
| `ipip[SQ027]` | 52 |
| `ipip[SQ028]` | 52 |
| `ipip[SQ029]` | 52 |
| `ipip[SQ030]` | 52 |
| `ipip[SQ031]` | 52 |
| `ipip[SQ032]` | 52 |
| `ipip[SQ033]` | 52 |
| `ipip[SQ034]` | 52 |
| `ipip[SQ035]` | 52 |
| `ipip[SQ036]` | 52 |
| `ipip[SQ037]` | 52 |
| `ipip[SQ038]` | 52 |
| `ipip[SQ039]` | 52 |
| `ipip[SQ040]` | 52 |
| `ipip[SQ041]` | 52 |
| `ipip[SQ042]` | 52 |
| `ipip[SQ043]` | 52 |
| `ipip[SQ044]` | 52 |
| `ipip[SQ045]` | 52 |
| `ipip[SQ046]` | 52 |
| `ipip[SQ047]` | 52 |
| `ipip[SQ048]` | 52 |
| `ipip[SQ049]` | 52 |
| `ipip[SQ050]` | 52 |
| `interviewtime` | 52 |
| `groupTime748` | 52 |
| `ipipTime` | 52 |
| `emailTime` | 52 |

#### breq

| key | documents |
| --- | ---: |
| `id` | 99 |
| `submitdate` | 99 |
| `startdate` | 99 |
| `datestamp` | 99 |
| `engage[SQ001]` | 99 |
| `engage[SQ002]` | 99 |
| `engage[SQ003]` | 99 |
| `engage[SQ004]` | 99 |
| `engage[SQ005]` | 99 |
| `engage[SQ006]` | 99 |
| `engage[SQ007]` | 99 |
| `engage[SQ008]` | 99 |
| `engage[SQ009]` | 99 |
| `engage[SQ010]` | 99 |
| `engage[SQ011]` | 99 |
| `engage[SQ012]` | 99 |
| `engage[SQ013]` | 99 |
| `engage[SQ014]` | 99 |
| `engage[SQ015]` | 99 |
| `engage[SQ016]` | 99 |
| `engage[SQ017]` | 99 |
| `engage[SQ018]` | 99 |
| `engage[SQ019]` | 99 |
| `interviewtime` | 99 |
| `groupTime778` | 99 |
| `engageTime` | 99 |
| `emailTime` | 99 |

#### dq

| key | documents |
| --- | ---: |
| `id` | 66 |
| `submitdate` | 66 |
| `usage` | 66 |
| `noUsage[SQ002]` | 66 |
| `noUsage[SQ003]` | 66 |
| `noUsage[SQ004]` | 66 |
| `noUsage[SQ005]` | 66 |
| `noUsage[SQ006]` | 66 |
| `noUsage[SQ007]` | 66 |
| `noUsage[other]` | 66 |
| `manufacturer[SQ002]` | 66 |
| `manufacturer[SQ003]` | 66 |
| `manufacturer[SQ004]` | 66 |
| `manufacturer[SQ005]` | 66 |
| `manufacturer[SQ006]` | 66 |
| `manufacturer[SQ007]` | 66 |
| `manufacturer[SQ008]` | 66 |
| `manufacturer[SQ009]` | 66 |
| `manufacturer[SQ010]` | 66 |
| `manufacturer[other]` | 66 |
| `why[SQ002]` | 66 |
| `why[SQ003]` | 66 |
| `why[SQ004]` | 66 |
| `why[SQ005]` | 66 |
| `why[SQ006]` | 66 |
| `why[SQ007]` | 66 |
| `why[SQ008]` | 66 |
| `why[SQ009]` | 66 |
| `why[other]` | 66 |
| `indicators[SQ001]` | 66 |
| `indicators[SQ002]` | 66 |
| `indicators[SQ003]` | 66 |
| `indicators[SQ004]` | 66 |
| `indicators[SQ005]` | 66 |
| `indicators[SQ006]` | 66 |
| `indicators[SQ007]` | 66 |
| `indicators[SQ008]` | 66 |
| `indicators[SQ009]` | 66 |
| `indicators[SQ010]` | 66 |
| `indicators[SQ011]` | 66 |
| `indicators[other]` | 66 |
| `accuracy` | 66 |
| `privacy` | 66 |
| `sharing[SQ001]` | 66 |
| `sharing[SQ002]` | 66 |
| `sharing[SQ003]` | 66 |
| `sharing[SQ004]` | 66 |
| `sharing[SQ005]` | 66 |
| `sharing[SQ006]` | 66 |
| `sharing[SQ007]` | 66 |
| `sharing[SQ008]` | 66 |
| `sharing[SQ009]` | 66 |
| `sharing[other]` | 66 |

#### panas

| key | documents |
| --- | ---: |
| `id` | 302 |
| `submitdate` | 302 |
| `startdate` | 302 |
| `datestamp` | 302 |
| `P1[SQ001]` | 302 |
| `P1[SQ002]` | 302 |
| `P1[SQ003]` | 302 |
| `P1[SQ004]` | 302 |
| `P1[SQ005]` | 302 |
| `P1[SQ006]` | 302 |
| `P1[SQ007]` | 302 |
| `P1[SQ008]` | 302 |
| `P1[SQ009]` | 302 |
| `P1[SQ010]` | 302 |
| `P1[SQ011]` | 302 |
| `P1[SQ012]` | 302 |
| `P1[SQ013]` | 302 |
| `P1[SQ014]` | 302 |
| `P1[SQ015]` | 302 |
| `P1[SQ016]` | 302 |
| `P1[SQ017]` | 302 |
| `P1[SQ018]` | 302 |
| `P1[SQ019]` | 302 |
| `P1[SQ020]` | 302 |
| `interviewtime` | 302 |
| `groupTime770` | 302 |
| `P1Time` | 302 |
| `emailTime` | 302 |

#### stai

| key | documents |
| --- | ---: |
| `id` | 314 |
| `submitdate` | 314 |
| `startdate` | 314 |
| `datestamp` | 314 |
| `STAI[SQ001]` | 314 |
| `STAI[SQ002]` | 314 |
| `STAI[SQ003]` | 314 |
| `STAI[SQ004]` | 314 |
| `STAI[SQ005]` | 314 |
| `STAI[SQ006]` | 314 |
| `STAI[SQ007]` | 314 |
| `STAI[SQ008]` | 314 |
| `STAI[SQ009]` | 314 |
| `STAI[SQ010]` | 314 |
| `STAI[SQ011]` | 314 |
| `STAI[SQ012]` | 314 |
| `STAI[SQ013]` | 314 |
| `STAI[SQ014]` | 314 |
| `STAI[SQ015]` | 314 |
| `STAI[SQ016]` | 314 |
| `STAI[SQ017]` | 314 |
| `STAI[SQ018]` | 314 |
| `STAI[SQ019]` | 314 |
| `STAI[SQ020]` | 314 |
| `interviewtime` | 314 |
| `groupTime782` | 314 |
| `STAITime` | 314 |
| `emailTime` | 314 |

#### ttmspbf

| key | documents |
| --- | ---: |
| `id` | 102 |
| `submitdate` | 102 |
| `startdate` | 102 |
| `datestamp` | 102 |
| `stage` | 102 |
| `processes[SQ002]` | 102 |
| `processes[SQ003]` | 102 |
| `processes[SQ004]` | 102 |
| `processes[SQ005]` | 102 |
| `processes[SQ006]` | 102 |
| `processes[SQ007]` | 102 |
| `processes[SQ008]` | 102 |
| `processes[SQ009]` | 102 |
| `processes[SQ010]` | 102 |
| `processes[SQ011]` | 102 |
| `processes[SQ012]` | 102 |
| `processes[SQ013]` | 102 |
| `processes[SQ014]` | 102 |
| `processes[SQ015]` | 102 |
| `processes[SQ016]` | 102 |
| `processes[SQ017]` | 102 |
| `processes[SQ018]` | 102 |
| `processes[SQ019]` | 102 |
| `processes[SQ020]` | 102 |
| `processes[SQ021]` | 102 |
| `processes[SQ022]` | 102 |
| `processes[SQ023]` | 102 |
| `processes[SQ024]` | 102 |
| `processes[SQ025]` | 102 |
| `processes[SQ026]` | 102 |
| `processes[SQ027]` | 102 |
| `processes[SQ028]` | 102 |
| `processes[SQ029]` | 102 |
| `processes[SQ030]` | 102 |
| `processes[SQ031]` | 102 |
| `interviewtime` | 102 |
| `groupTime749` | 102 |
| `stageTime` | 102 |
| `emailTime` | 102 |
| `groupTime750` | 102 |
| `processesTime` | 102 |

### Survey Sample Shapes

#### bfpt

```text
{'_id': ObjectId('6241bd11a59be121689b2b3b'),
 'user_id': ObjectId('621e32af67b776a24045b4cf'),
 'type': 'bfpt',
 'data': {'id': 6.0,
          'submitdate': '31/5/2021 13:28',
          'startdate': '31/5/2021 13:24',
          'datestamp': '31/5/2021 13:28',
          'ipip[SQ001]': 1.0,
          'ipip[SQ002]': 4.0,
          'ipip[SQ003]': 4.0,
          'ipip[SQ004]': 4.0,
          'ipip[SQ005]': 3.0,
          'ipip[SQ006]': 5.0,
          'ipip[SQ007]': 1.0,
          'ipip[SQ008]': 1.0,
          'ipip[SQ009]': 1.0,
          'ipip[SQ010]': 1.0,
          'ipip[SQ011]': 5.0,
          'ipip[SQ012]': 2.0,
          'ipip[SQ013]': 5.0,
          'ipip[SQ014]': 5.0}}
```

#### breq

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
          'engage[SQ008]': 4,
          'engage[SQ009]': 1,
          'engage[SQ010]': 3,
          'engage[SQ011]': 2,
          'engage[SQ012]': 1,
          'engage[SQ013]': 4,
          'engage[SQ014]': 5}}
```

#### dq

```text
{'_id': ObjectId('6241bd12a59be121689b2b5b'),
 'user_id': ObjectId('621e32d967b776a240627414'),
 'type': 'dq',
 'data': {'id': 3,
          'submitdate': '1/1/1980 0:00',
          'usage': 'No',
          'noUsage[SQ002]': 'No',
          'noUsage[SQ003]': 'No',
          'noUsage[SQ004]': 'No',
          'noUsage[SQ005]': 'No',
          'noUsage[SQ006]': 'No',
          'noUsage[SQ007]': 'Yes',
          'noUsage[other]': None,
          'manufacturer[SQ002]': None,
          'manufacturer[SQ003]': None,
          'manufacturer[SQ004]': None,
          'manufacturer[SQ005]': None,
          'manufacturer[SQ006]': None,
          'manufacturer[SQ007]': None,
          'manufacturer[SQ008]': None,
          'manufacturer[SQ009]': None}}
```

#### panas

```text
{'_id': ObjectId('6241bd12a59be121689b2b9f'),
 'user_id': ObjectId('621e36f967b776a240e5e7c9'),
 'type': 'panas',
 'data': {'id': 1,
          'submitdate': '31/5/2021 12:39',
          'startdate': '31/5/2021 12:38',
          'datestamp': '31/5/2021 12:39',
          'P1[SQ001]': 3,
          'P1[SQ002]': 4,
          'P1[SQ003]': 3,
          'P1[SQ004]': 3,
          'P1[SQ005]': 4,
          'P1[SQ006]': 1,
          'P1[SQ007]': 1,
          'P1[SQ008]': 4,
          'P1[SQ009]': 3,
          'P1[SQ010]': 2,
          'P1[SQ011]': 4,
          'P1[SQ012]': 3,
          'P1[SQ013]': 2,
          'P1[SQ014]': 3}}
```

#### stai

```text
{'_id': ObjectId('6241bd12a59be121689b2c5c'),
 'user_id': ObjectId('621e2e8e67b776a24055b564'),
 'type': 'stai',
 'data': {'id': 2,
          'submitdate': '31/5/2021 13:32',
          'startdate': '31/5/2021 13:17',
          'datestamp': '31/5/2021 13:32',
          'STAI[SQ001]': 4,
          'STAI[SQ002]': 5,
          'STAI[SQ003]': 1,
          'STAI[SQ004]': 1,
          'STAI[SQ005]': 4,
          'STAI[SQ006]': 1,
          'STAI[SQ007]': 1,
          'STAI[SQ008]': 5,
          'STAI[SQ009]': 1,
          'STAI[SQ010]': 4,
          'STAI[SQ011]': 5,
          'STAI[SQ012]': 1,
          'STAI[SQ013]': 1,
          'STAI[SQ014]': 1}}
```

#### ttmspbf

```text
{'_id': ObjectId('6241bd12a59be121689b2d1b'),
 'user_id': ObjectId('621e36f967b776a240e5e7c9'),
 'type': 'ttmspbf',
 'data': {'id': 2,
          'submitdate': '31/5/2021 12:56',
          'startdate': '31/5/2021 12:54',
          'datestamp': '31/5/2021 12:56',
          'stage': 'Yes, I have been doing physical activity regularly, but for less than 6 months.',
          'processes[SQ002]': 2,
          'processes[SQ003]': 4,
          'processes[SQ004]': 4,
          'processes[SQ005]': 5,
          'processes[SQ006]': 3,
          'processes[SQ007]': 3,
          'processes[SQ008]': 1,
          'processes[SQ009]': 4,
          'processes[SQ010]': 4,
          'processes[SQ011]': 1,
          'processes[SQ012]': 2,
          'processes[SQ013]': 5,
          'processes[SQ014]': 2}}
```

## Variable Extraction Plan

Recommended next extraction targets:

- `fitbit.sleep`: sleep target and sleep-stage variables.
- `fitbit.Stress Score`: stress explanatory variable.
- `fitbit.Daily Heart Rate Variability Summary`: daily HRV features.
- `fitbit.resting_heart_rate`: daily resting heart rate.
- `fitbit.steps`, `fitbit.calories`, activity-minute types: daily activity features.
- `sema`: EMA mood/context variables, joined by participant and response date.
- `surveys`: participant-level survey features, joined by participant.

Next pipeline stage:

```text
필요한 변수 추출 -> 날짜 단위 집계 -> fitbit/sema/surveys 병합
```
