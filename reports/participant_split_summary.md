# Participant-Aware Split Summary

- Generated at: `2026-06-28T21:01:02`
- Input file: `C:\workSpace\DeepLearnin_sleep\data\processed\modeling_dataset_encoded.csv`
- Train output: `C:\workSpace\DeepLearnin_sleep\data\processed\splits\train_participant_split.csv`
- Test output: `C:\workSpace\DeepLearnin_sleep\data\processed\splits\test_participant_split.csv`
- Participant assignments: `C:\workSpace\DeepLearnin_sleep\data\processed\splits\participant_split_assignments.csv`

## Scope

- This step creates a participant-aware train/test split.
- Every participant belongs to exactly one split.
- The split is selected from stratified grouped folds to keep the target distribution reasonably balanced.
- This split supports both traditional ML reference baselines and deep learning sequence datasets.
- For deep learning, validation participants are split from the training participants during tensor creation.

## Split Summary

| split | rows | participants | good_sleep_label mean | class 0 rows | class 1 rows |
| --- | ---: | ---: | ---: | ---: | ---: |
| train | 2,944 | 55 | 0.3988 | 1,770 | 1,174 |
| test | 607 | 14 | 0.3690 | 383 | 224 |
| all | 3,551 | 69 | 0.3937 | 2,153 | 1,398 |

## Leakage Checks

- Participant overlap between train and test: `0`
- Train duplicate participant-date rows: `0`
- Test duplicate participant-date rows: `0`
- Train participants: `55`
- Test participants: `14`

## Candidate Fold Diagnostics

| fold | train rows | test rows | train participants | test participants | test row share | train target rate | test target rate | score |
| ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 1 | 2,676 | 875 | 52 | 17 | 0.2464 | 0.4043 | 0.3611 | 0.0790 |
| 2 | 2,911 | 640 | 57 | 12 | 0.1802 | 0.3683 | 0.5094 | 0.1355 |
| 3 | 2,704 | 847 | 55 | 14 | 0.2385 | 0.3839 | 0.4250 | 0.0699 |
| 4 | 2,969 | 582 | 57 | 12 | 0.1639 | 0.4129 | 0.2955 | 0.1343 |
| 5 | 2,944 | 607 | 55 | 14 | 0.1709 | 0.3988 | 0.3690 | 0.0537 |

## Participant Assignment Preview

| participant_object_id | split | rows | target mean | first date | last date |
| --- | --- | ---: | ---: | --- | --- |
| `621e2eaf67b776a2406b14ac` | test | 83 | 0.5181 | 2021-10-29 | 2022-01-22 |
| `621e2efa67b776a2409dd1c3` | test | 66 | 0.4697 | 2021-05-25 | 2021-09-29 |
| `621e2f1b67b776a240b3d87c` | test | 76 | 0.5658 | 2021-11-07 | 2022-01-21 |
| `621e2f6167b776a240e082a9` | test | 45 | 0.2889 | 2021-05-26 | 2021-07-29 |
| `621e309267b776a240ae1cdb` | test | 17 | 0.2353 | 2021-11-09 | 2021-11-26 |
| `621e309b67b776a240b532b0` | test | 54 | 0.1667 | 2021-10-12 | 2022-01-19 |
| `621e324e67b776a2400191cb` | test | 68 | 0.1029 | 2021-11-10 | 2022-01-17 |
| `621e32af67b776a24045b4cf` | test | 58 | 0.1724 | 2021-05-25 | 2021-07-26 |
| `621e332267b776a24092a584` | test | 21 | 0.7619 | 2021-05-25 | 2021-06-20 |
| `621e34f767b776a240de4e1a` | test | 2 | 0.5000 | 2021-06-10 | 2021-07-07 |
| `621e356967b776a24027bd9f` | test | 68 | 0.5882 | 2021-11-15 | 2022-01-21 |
| `621e36bb67b776a240b40d64` | test | 2 | 0.0000 | 2021-06-11 | 2021-06-12 |
| `621e36c267b776a240ba2756` | test | 44 | 0.1591 | 2021-05-24 | 2021-07-25 |
| `621e36dd67b776a240ce9a45` | test | 3 | 0.0000 | 2021-08-11 | 2021-09-01 |
| `621e2e8e67b776a24055b564` | train | 63 | 0.8889 | 2021-05-24 | 2021-08-01 |
| `621e2ed667b776a24085d8d1` | train | 76 | 0.5263 | 2021-05-25 | 2021-08-17 |
| `621e2ef567b776a24099f889` | train | 1 | 1.0000 | 2021-10-19 | 2021-10-19 |
| `621e2f3967b776a240c654db` | train | 62 | 0.6129 | 2021-05-25 | 2021-08-01 |
| `621e2f5767b776a240d8f9d6` | train | 22 | 0.5000 | 2021-11-15 | 2021-12-07 |
| `621e2f7a67b776a240f14425` | train | 53 | 0.3208 | 2021-05-24 | 2021-07-29 |

## Next Step

```text
deep learning sequence dataset creation, with traditional ML baseline modeling kept as reference only
```
