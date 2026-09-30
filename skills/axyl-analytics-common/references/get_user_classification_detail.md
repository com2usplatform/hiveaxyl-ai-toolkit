# get_user_classification_detail (Get Per-Type Metric)

Returns the average of one metric per user classification type. Use it for questions like "how many
minutes a day do whales play".

> **Prerequisite:** Follow the common rules in [`../SKILL.md`](../SKILL.md).

## When to Use

- To compare behavior or spending across types (when the question is about **behavior**, not counts)
- After looking at the type distribution, to move on to "so how do these users actually play"

## Parameters

| Parameter | Required | Description |
|---------|------|------|
| `company_cd` | Y | Company code confirmed from `list_projects` |
| `org_idx` | Y | Organization idx confirmed from `list_organizations` |
| `appid_group` | Y | Project ID (`list_projects.appid_group`) |
| `start_date` | Y | Start date `YYYY-MM-DD` |
| `end_date` | Y | End date `YYYY-MM-DD` |
| `metric` | Y | One code below. **Only one per call** |

## Metrics

| Code | Content |
|---|---|
| `playTime` | Play time on the last active day (minutes, average) |
| `loginDay` | Login days over the 3 days up to and including the last active day (average) |
| `loginCnt` | Login count over the 3 days up to and including the last active day (average) |
| `loginHit` | Average daily login count up to and including the last active day |
| `pushRate` | Push response rate over the 3 days up to and including the last active day (average) |
| `adCnt` | Rewarded ad views over the 3 days up to and including the last active day (average) |
| `firstDiff` | Time from first entry to first purchase |
| `accKrw` | Cumulative purchase amount (KRW) |
| `arppu` | Average purchase amount per paying user (KRW) |
| `lifeTime` | Lifetime (days, average) |
| `accUsd` | Cumulative purchase amount (USD) |
| `arppuUsd` | Purchase amount per paying user (USD) |

To compare several metrics, call repeatedly with a different `metric`. The server aggregates on every
call, so pick only the metrics you need.

## Return Value

Returns `{"appid_group", "start_date", "end_date", "metric", "metric_desc", "values"}`.
`values` is `[{"name", "y"}]` where `name` is the type and `y` is that type's average.
`metric_desc` carries the metric description — **use it to state the unit when reporting numbers.**

## Decision Rules

- **Do not read `y=0` as "users whose value is 0".** Zero arises two ways:
  - The type has no users at all → confirm counts via `user_type` in `get_user_classification`
  - The server floors the value → an actual average of 0.9 becomes 0
  Only `pushRate`, `lifeTime`, `accUsd` and `arppuUsd` are rounded to two decimals.
- All 6 types always appear, even with no users. Presence in the list does not mean users exist.
- **Report alongside counts.** The average for a type with one user is just that one user's value and
  carries no weight.
- Do not guess units. State only what `metric_desc` says.

## On Failure

- A `metric` outside the list fails with the allowed values. Use the codes from the table verbatim.
- Organization or project access error: recheck the organization and project relationship.

## Recommended Chain

```text
get_user_classification (confirm users per type)
→ get_user_classification_detail (query the metric) → report together with counts
```
