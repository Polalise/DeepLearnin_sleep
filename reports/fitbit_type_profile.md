# Fitbit Raw Type Profile

- Mongo URI: `mongodb://localhost:27017`
- Database: `rais_anonymized`
- Collection: `fitbit`
- Generated at: `2026-06-26T19:17:29`

## Type Counts

| type | documents |
| --- | ---: |
| `heart_rate` | 48720040 |
| `calories` | 9675782 |
| `Wrist Temperature` | 4372238 |
| `distance` | 3010529 |
| `steps` | 3010529 |
| `estimated_oxygen_variation` | 2009637 |
| `Heart Rate Variability Details` | 220512 |
| `Device Temperature` | 92121 |
| `altitude` | 81022 |
| `mindfulness_eda_data_sessions` | 16070 |
| `resting_heart_rate` | 12362 |
| `very_active_minutes` | 7203 |
| `sedentary_minutes` | 7203 |
| `moderately_active_minutes` | 7203 |
| `lightly_active_minutes` | 7203 |
| `time_in_heart_rate_zones` | 4876 |
| `demographic_vo2_max` | 4854 |
| `sleep` | 4141 |
| `exercise` | 4051 |
| `Computed Temperature` | 3568 |
| `Respiratory Rate Summary` | 3000 |
| `Heart Rate Variability Histogram` | 3000 |
| `Daily Heart Rate Variability Summary` | 2475 |
| `Stress Score` | 1911 |
| `Daily SpO2` | 1274 |
| `badge` | 902 |
| `water_logs` | 207 |
| `mindfulness_sessions` | 143 |
| `journal_entries` | 118 |
| `Afib ECG Readings` | 73 |
| `Profile` | 69 |
| `mindfulness_goals` | 30 |

## Sample Shapes

### heart_rate

```text
{'_id': ObjectId('62cc1fb7b41dcd4b1bf0e2ac'),
 'id': ObjectId('621e2e8e67b776a24055b564'),
 'type': 'heart_rate',
 'data': {'dateTime': '2021-05-24T00:00:16', 'value': {'bpm': 'int', 'confidence': 'int'}}}
```

### calories

```text
{'_id': ObjectId('62cc1f9ab41dcd4b1bebf727'),
 'id': ObjectId('621e2e8e67b776a24055b564'),
 'type': 'calories',
 'data': {'dateTime': '05/24/21 00:00:00', 'value': '2.62'}}
```

### Wrist Temperature

```text
{'_id': ObjectId('62cc2027b41dcd4b1bfed1e0'),
 'id': ObjectId('621e2e8e67b776a24055b564'),
 'type': 'Wrist Temperature',
 'data': {'recorded_time': '2021-05-24T00:00', 'temperature': -1.1897946612}}
```

### distance

```text
{'_id': ObjectId('62cc1fa0b41dcd4b1beda764'),
 'id': ObjectId('621e2e8e67b776a24055b564'),
 'type': 'distance',
 'data': {'dateTime': '2021-05-24T00:17:00', 'value': '880'}}
```

### steps

```text
{'_id': ObjectId('62cc2021b41dcd4b1bfdc4a1'),
 'id': ObjectId('621e2e8e67b776a24055b564'),
 'type': 'steps',
 'data': {'dateTime': '2021-05-24T00:15:00', 'value': '0'}}
```

### estimated_oxygen_variation

```text
{'_id': ObjectId('62cc1f9ab41dcd4b1beae820'),
 'id': ObjectId('621e2e8e67b776a24055b564'),
 'type': 'estimated_oxygen_variation',
 'data': {'timestamp': '05/24/21 01:03:30', 'Infrared to Red Signal Ratio': -4}}
```

### Heart Rate Variability Details

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

### Device Temperature

```text
{'_id': ObjectId('62cc400ab41dcd4b1ba16e12'),
 'id': ObjectId('621e356967b776a24027bd9f'),
 'type': 'Device Temperature',
 'data': {'recorded_time': '2021-11-15T00:01', 'temperature': -0.4811632526, 'sensor_type': 'UNKNOWN'}}
```

### altitude

```text
{'_id': ObjectId('62cc1f9ab41dcd4b1beb875e'),
 'id': ObjectId('621e2e8e67b776a24055b564'),
 'type': 'altitude',
 'data': {'dateTime': '05/24/21 10:45:00', 'value': '10'}}
```

### mindfulness_eda_data_sessions

```text
{'_id': ObjectId('62cc227cb41dcd4b1b5b6274'),
 'id': ObjectId('621e2f1b67b776a240b3d87c'),
 'type': 'mindfulness_eda_data_sessions',
 'data': {'session_id': '6ca4b730-6e3c-11ec-8080-808080808080',
          'timestamp': '2022-01-05T15:30:39+00:00',
          'valid_data': False,
          'activation': False,
          'scl_avg': 0.0}}
```

### resting_heart_rate

```text
{'_id': ObjectId('62cc2021b41dcd4b1bfd9bde'),
 'id': ObjectId('621e2e8e67b776a24055b564'),
 'type': 'resting_heart_rate',
 'data': {'dateTime': '05/25/21 00:00:00', 'value': {'date': 'str', 'value': 'float', 'error': 'float'}}}
```

### very_active_minutes

```text
{'_id': ObjectId('62cc2021b41dcd4b1bfe78b5'),
 'id': ObjectId('621e2e8e67b776a24055b564'),
 'type': 'very_active_minutes',
 'data': {'dateTime': '05/26/21 00:00:00', 'value': '31'}}
```

### sedentary_minutes

```text
{'_id': ObjectId('62cc2021b41dcd4b1bfd9d50'),
 'id': ObjectId('621e2e8e67b776a24055b564'),
 'type': 'sedentary_minutes',
 'data': {'dateTime': '05/30/21 00:00:00', 'value': '763'}}
```

### moderately_active_minutes

```text
{'_id': ObjectId('62cc2021b41dcd4b1bfd9b85'),
 'id': ObjectId('621e2e8e67b776a24055b564'),
 'type': 'moderately_active_minutes',
 'data': {'dateTime': '05/26/21 00:00:00', 'value': '27'}}
```

### lightly_active_minutes

```text
{'_id': ObjectId('62cc2021b41dcd4b1bfd9b31'),
 'id': ObjectId('621e2e8e67b776a24055b564'),
 'type': 'lightly_active_minutes',
 'data': {'dateTime': '06/01/21 00:00:00', 'value': '106'}}
```

### time_in_heart_rate_zones

```text
{'_id': ObjectId('62cc2021b41dcd4b1bfe7865'),
 'id': ObjectId('621e2e8e67b776a24055b564'),
 'type': 'time_in_heart_rate_zones',
 'data': {'dateTime': '06/03/21 00:00:00', 'value': {'valuesInZones': 'dict'}}}
```

### demographic_vo2_max

```text
{'_id': ObjectId('62cc1fa0b41dcd4b1bed8011'),
 'id': ObjectId('621e2e8e67b776a24055b564'),
 'type': 'demographic_vo2_max',
 'data': {'dateTime': '05/28/21 00:00:00',
          'value': {'demographicVO2Max': 'float',
                    'demographicVO2MaxError': 'float',
                    'filteredDemographicVO2Max': 'float',
                    'filteredDemographicVO2MaxError': 'float'}}}
```

### sleep

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

### exercise

```text
{'_id': ObjectId('62cc1fabb41dcd4b1bee599a'),
 'id': ObjectId('621e2e8e67b776a24055b564'),
 'type': 'exercise',
 'data': {'logId': 40052199029,
          'activityName': 'Walk',
          'activityTypeId': 90013,
          'activityLevel': ['dict', '... 4 item(s)'],
          'averageHeartRate': 102,
          'calories': 180,
          'duration': 1638000,
          'activeDuration': 1638000,
          'steps': 2693,
          'logType': 'auto_detected',
          'manualValuesSpecified': {'calories': 'bool', 'distance': 'bool', 'steps': 'bool'},
          'heartRateZones': ['dict', '... 4 item(s)'],
          'activeZoneMinutes': {'totalMinutes': 'int', 'minutesInHeartRateZones': 'list'},
          'lastModified': '2021-05-26T17:38:38',
          'startTime': '2021-05-26T09:46:21',
          'originalStartTime': '2021-05-26T09:46:21'}}
```

### Computed Temperature

```text
{'_id': ObjectId('62cc2021b41dcd4b1bfe7909'),
 'id': ObjectId('621e2e8e67b776a24055b564'),
 'type': 'Computed Temperature',
 'data': {'type': 'SKIN',
          'sleep_start': '2021-05-24T23:48:30',
          'sleep_end': '2021-05-25T08:56:30',
          'temperature_samples': 548,
          'nightly_temperature': 33.7945437956,
          'baseline_relative_sample_sum': -349.428125352,
          'baseline_relative_sample_sum_of_squares': 838.7141319106,
          'baseline_relative_nightly_standard_deviation': 0.2334325643,
          'baseline_relative_sample_standard_deviation': 0.9058124551}}
```

### Respiratory Rate Summary

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

### Heart Rate Variability Histogram

```text
{'_id': ObjectId('62cc2021b41dcd4b1bfe92fc'),
 'id': ObjectId('621e2e8e67b776a24055b564'),
 'type': 'Heart Rate Variability Histogram',
 'data': {'timestamp': '2021-05-26T09:06:30',
          'bucket_values': '[0.0, 0.0, 0.0, 0.0, 0.0, 0.002, 0.003, 0.005, 0.016, 0.026, 0.037, 0.061, '
                           '0.094, 0.117, 0.129, 0...'}}
```

### Daily Heart Rate Variability Summary

```text
{'_id': ObjectId('62cc2021b41dcd4b1bfe7950'),
 'id': ObjectId('621e2e8e67b776a24055b564'),
 'type': 'Daily Heart Rate Variability Summary',
 'data': {'timestamp': '2021-05-29T00:00:00', 'rmssd': 89.941, 'nremhr': 57.314, 'entropy': 3.143}}
```

### Stress Score

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

### Daily SpO2

```text
{'_id': ObjectId('62cc2179b41dcd4b1b32e71c'),
 'id': ObjectId('621e2ef567b776a24099f889'),
 'type': 'Daily SpO2',
 'data': {'timestamp': '2021-10-19T00:00:00Z',
          'average_value': 97.7,
          'lower_bound': 94.4,
          'upper_bound': 99.6}}
```

### badge

```text
{'_id': ObjectId('62cc2029b41dcd4b1b0028a6'),
 'id': ObjectId('621e2e8e67b776a24055b564'),
 'type': 'badge',
 'data': {'badgeType': 'DAILY_FLOORS', 'value': 75, 'dateTime': '2021-05-29'}}
```

### water_logs

```text
{'_id': ObjectId('62cc202db41dcd4b1b002a13'),
 'id': ObjectId('621e2eaf67b776a2406b14ac'),
 'type': 'water_logs',
 'data': {'id': 8795217682, 'date': '01/07/22', 'waterAmount': 250.0, 'measurementUnit': 'MILLILITER'}}
```

### mindfulness_sessions

```text
{'_id': ObjectId('62cc227cb41dcd4b1b5b69e9'),
 'id': ObjectId('621e2f1b67b776a240b3d87c'),
 'type': 'mindfulness_sessions',
 'data': {'session_id': '5c5b2590-5e73-11ec-8080-808080808080',
          'activity_name': 'Quick scan',
          'average_heart_rate': None,
          'start_heart_rate': 77,
          'end_heart_rate': 73,
          'duration': 120000,
          'start_date_time': '2021-12-16T15:23:30',
          'end_date_time': '2021-12-16T15:25:39',
          'session_type': 'quick-scan',
          'stress_metrics': '{meanScore=-1  derivScore=-1  peakScore=-1  hrvBaseline=26.914756774902344  '
                            'hrvSessionRsmmd=-1  S...',
          'pause_times': '[[9]]'}}
```

### journal_entries

```text
{'_id': ObjectId('62cc202db41dcd4b1b010813'),
 'id': ObjectId('621e2eaf67b776a2406b14ac'),
 'type': 'journal_entries',
 'data': {'entry_id': '3e920e50-40cf-11ec-a34e-811659e91d8a',
          'log_time': '2021-11-08T21:05:16',
          'log_type': 'MOOD',
          'value': '4',
          'meta': '{platform=mobile, source=stress}',
          'entry_category': 'MOOD'}}
```

### Afib ECG Readings

```text
{'_id': ObjectId('62cc25b6b41dcd4b1bd3cc92'),
 'id': ObjectId('621e2ff067b776a2403eb737'),
 'type': 'Afib ECG Readings',
 'data': {'reading_id': '00706d90-6359-11ec-8080-808080808080',
          'reading_time': '2021-12-22T19:57:25+00:00',
          'wire_id': '89485863582c',
          'result_classification': 'NSR',
          'heart_rate': 83,
          'heart_rate_alert': 'NONE',
          'firmware_version': '128.6.12',
          'device_app_version': '2.9.0',
          'hardware_version': 'Sense',
          'waveform_samples': '[-32768  -32768  -32768  -32768  -32768  -32768  -32768  -32768  -32768  '
                              '-32768  -32768  -32768  ...'}}
```

### Profile

```text
{'_id': ObjectId('62cc1f9ab41dcd4b1beb86a9'),
 'id': ObjectId('621e2e8e67b776a24055b564'),
 'type': 'Profile',
 'data': {'child': False,
          'start_of_week': 'SUNDAY',
          'sleep_tracking': 'Normal',
          'time_display_format': '12hour',
          'gender': 'MALE',
          'weight_unit': 'METRIC',
          'distance_unit': 'METRIC',
          'height_unit': 'METRIC',
          'water_unit': 'en_US',
          'glucose_unit': 'en_US',
          'swim_unit': 'METRIC',
          'bmi': '<19',
          'age': '<30'}}
```

### mindfulness_goals

```text
{'_id': ObjectId('62cc20deb41dcd4b1b1aedd2'),
 'id': ObjectId('621e2eaf67b776a2406b14ac'),
 'type': 'mindfulness_goals',
 'data': {'date': 'Fri Oct 29 00:00:00 UTC 2021', 'days': 7, 'default_goal': False}}
```
