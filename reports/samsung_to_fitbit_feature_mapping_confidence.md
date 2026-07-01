# Samsung-to-Fitbit Feature Mapping Confidence

## Purpose

Document how Samsung Health features were adapted to the existing Fitbit-trained Design C Stage 1 inference contract.

This is a feature-schema compatibility mapping, not a claim that Samsung Health raw data are equivalent to Fitbit raw data.

## Mapping Summary

| Fitbit-compatible feature group | Samsung source | Current method | Confidence | Main caveat |
|---|---|---|---|---|
| sleep episode start/end | `sleep_stage` | group by Samsung sleep episode id; use min stage start and max stage end after UTC offset correction | high | sleep table and sleep_stage table are not always directly linked |
| pre-sleep heart-rate mean/std/min/max/median | `tracker.heart_rate` | aggregate heart-rate rows before `sleep_start_datetime` | high | Samsung sampling differs from Fitbit |
| pre-sleep heart-rate last 3h/1h | `tracker.heart_rate` | aggregate rows in fixed trailing windows before sleep start | high | depends on heart-rate row density |
| pre-sleep heart-rate record count | `tracker.heart_rate` | count heart-rate rows before sleep start | high | count reflects Samsung sampling pattern |
| previous-day steps | `pedometer_day_summary`, `activity.day_summary` | previous calendar-day daily step total | high | Samsung day boundary may differ from Fitbit behavioral day |
| previous-day calories | `pedometer_day_summary`, `activity.day_summary`, `step_daily_trend` | previous calendar-day calorie total | medium | calorie algorithms differ by platform |
| previous-day active minutes | `pedometer_day_summary.active_time`, `activity.day_summary.active_time` | active time converted from milliseconds to minutes | medium | not equivalent to Fitbit lightly/moderately/very active buckets |
| pre-sleep steps | `pedometer_step_count` | sum interval step count before sleep start | low-current | current export has sparse interval coverage in pre-sleep windows |
| pre-sleep calories | `pedometer_step_count.calorie` | sum interval calories before sleep start | low-current | current export has sparse interval coverage and calorie definitions differ |
| resting heart rate | none direct in current adapter | left missing and handled by existing imputer | low | possible future proxy from stable overnight/daytime HR but not Fitbit-equivalent |
| Fitbit active-intensity buckets | Samsung active/exercise summaries | only lightly active is approximated from total active time; other buckets left missing | low-medium | Samsung does not expose Fitbit-equivalent intensity bins |
| sleep score proxy label | `sleep.sleep_score` | diagnostic proxy only, `sleep_score >= 80` | low for validation | small matched subset and vendor-specific score |
| stage proxy label | `sleep_stage` | duration/efficiency/awake-ratio proxy | medium for diagnostics | proxy label is strict and not original `good_sleep_label` |

## Current High-Confidence Coverage

- Heart-rate pre-sleep features are usable.
- Previous-day steps/calories/activity are usable with platform caveats.
- Sleep episode construction is usable after UTC offset correction.

## Current Low-Confidence Areas

- Pre-sleep step/calorie interval coverage is too sparse in the current adapter output.
- The interval `pedometer_step_count` source only covers a short recent range, `2026-05-25` to `2026-06-29`, while sleep episodes span `2021-07-30` to `2026-06-27`.
- Resting-HR has no direct Samsung equivalent in the current export.
- Fitbit-style active intensity buckets should not be treated as one-to-one Samsung equivalents.

## Reporting Language

Use:

> Samsung Health data were transformed into a Fitbit-compatible feature schema for cross-device transfer diagnostics.

Avoid:

> Samsung Health data were converted into Fitbit data.

Avoid:

> Samsung Health externally validated the Fitbit-trained model.
