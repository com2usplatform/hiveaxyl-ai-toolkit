# get_user_activity_summary (Get a User's Activity Summary)

Returns a summary of one user's activity for a period. Use it to grasp the overall picture before
reading the detailed history.

> **Prerequisite:** Follow the common rules in [`../SKILL.md`](../SKILL.md). Call after `check_user_exists`.

## When to Use

- To find the dates where activity is concentrated before calling `list_user_activities`
- To see at a glance what kinds of events a user produced during a period

## Parameters

| Parameter | Required | Description |
|---------|------|------|
| `company_cd` | Y | Company code confirmed from `list_projects` |
| `org_idx` | Y | Organization idx confirmed from `list_organizations` |
| `appid_group` | Y | Project ID (`list_projects.appid_group`) |
| `user_id` | Y | The user ID to query |
| `start_date` | N | Start date `YYYY-MM-DD`. Unlike chart tools there is no time component |
| `end_date` | N | End date `YYYY-MM-DD` |
| `lang` | N | Label language. Default `ko` |

## Return Value

Returns `{"user_id", "appid_group", "start_date", "end_date", "summary"}`.
`summary` is the server response as is: `[{"type", "data"}]`.

| `type` | Meaning |
|---|---|
| `period` | The total for the whole specified period |
| A date string (`2026-09-11`) | The activity on that date |

Each item in `data` is `{category, categoryLabel, name, nameLabel, cnt}`.

## Decision Rules

- **`cnt` is a string** (`"1"`). Take care that size comparisons do not fall back to string ordering.
- Use the per-date items to find the day that stands out, then query only that date with
  `list_user_activities`.
- **Do not set a long period.** The summary grows with event types × dates — even a few days can return dozens
  of event types. One or two weeks is a practical upper bound.
- This is a raw log; users excluded from metrics, metric filters, and metric start dates are not
  applied. Figures can differ from metric queries, and that is an aggregation-basis difference,
  not an error.

## On Failure

- Organization or project access error: recheck the organization and project relationship.
- Empty result: there was no activity in that period. Confirm the user exists with `check_user_exists`
  before concluding.

## Recommended Chain

```text
check_user_exists → get_user_activity_summary → list_user_activities (narrowed to a date)
```
