# list_metric_filters (List Metric Filters)

Lists the metric filters registered for an organization. A metric filter is a configuration that excludes logs coming
from QA servers or test apps from metric calculation.

> **Prerequisite:** Follow SETTING_ACCESS_GATE in [`../SKILL.md`](../SKILL.md).

## When to Use

- To check the calculation basis together with excluded users and metric start dates when a metric differs from expectations
- To check for duplicates before calling `regist_metric_filter`

## Parameters

| Parameter | Required | Description |
|---------|------|------|
| `company_cd` | Y | Company code confirmed from `list_projects` |
| `org_idx` | Y | Organization idx confirmed through SETTING_ACCESS_GATE |

## Return Value

Returns `idx`, `title`, `project_id`, `filter_type`, and `filter_value` for each registration.
`filter_type` is either `appId` (by app ID) or `serverId` (by server ID).
Deleted registrations are excluded.

## Decision Rules

- A registration is stored as **one row per project and per value**. Even a single registration call appears as several rows.
- Metric filters apply to every metric calculation. When asked about a number, check this configuration first, and if a
  filtered server or app is involved, explain that as part of the answer.
- **The whole organization is returned.** To look at a single project, filter the response by `project_id` yourself
  (the same way you would for `list_except_users` and `list_start_dates`).

## On Failure

- Empty result: no metric filters are registered for this organization.

## Recommended Chain

```text
SETTING_ACCESS_GATE → list_metric_filters → (if needed) SETTING_ADMIN_GATE → regist_metric_filter
```
