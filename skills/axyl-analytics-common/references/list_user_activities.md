# list_user_activities (List a User's Activities)

Returns one user's activity history in chronological order.

> **Prerequisite:** Follow the common rules in [`../SKILL.md`](../SKILL.md). Narrow the range with
> `get_user_activity_summary` first.

## When to Use

- To follow what a user did around a specific time, for a CS inquiry or a report
- To check the sequence of events on a date that stood out in the summary

## Parameters

| Parameter | Required | Description |
|---------|------|------|
| `company_cd` | Y | Company code confirmed from `list_projects` |
| `org_idx` | Y | Organization idx confirmed from `list_organizations` |
| `appid_group` | Y | Project ID (`list_projects.appid_group`) |
| `user_id` | Y | The user ID to query |
| `start_date` | N | Start date `YYYY-MM-DD` |
| `end_date` | N | End date `YYYY-MM-DD` |
| `page` | N | Page number. **Starts at 0.** Default 0 |
| `size` | N | Entries per page. Default 100 |
| `lang` | N | Label language. Default `ko` |

## Return Value

Returns `{"user_id", "appid_group", "start_date", "end_date", "page", "size", "count", "has_more", "activities"}`.

| Field | Content |
|---|---|
| `activity_date_time` | Activity time, with the user's timezone applied |
| `category` · `category_label` | Event category (`gamePlay`, `purchase`, `login`) |
| `name` · `name_label` | Event name (`useablePurchase`, `tutorialAccept`) |
| `properties` | Per-event detail. Free-form, so keys differ per event |

`count` is the number of entries on this page, not the total; the server does not return a total.
`has_more` is `count >= size`.

## Decision Rules

- **Do not exhaust an unrelated broad history.** First narrow the range with the per-date items in the summary.
  After it is narrowed to the smallest supported date range, a targeted question about a specific event or property must
  continue page by page until the evidence is found or `has_more=false`. If the remaining volume is impractical, stop and
  report that the search is incomplete; ask for a narrower date or more identifying detail. Never conclude that the target
  event or property is absent from only the first page.
- `properties` uses camelCase keys (`productId`, `serverId`) while the top-level fields are snake_case.
- `activity_date_time` has the user's timezone applied and `properties.dateTime` is UTC — they differ by the
  user's UTC offset (9 hours for KST), which **can change the date** (for example, `2026-01-01 06:00:00` KST = `2025-12-31 21:00:00` UTC).
  Answer based on `activity_date_time`.
- Airbridge events carry nested objects (`deviceAttributes`, `touchpointAttributes`, and others) and
  are far larger than game events. Quote only the keys you need.
- This is a raw log; metric settings are not applied. When it disagrees with a metric, check
  `list_except_users`, `list_metric_filters`, and `list_start_dates` before concluding.

## On Failure

- Organization or project authorization denial: do not retry the same call unchanged or with a guessed identifier; follow
  MCP_ACCESS_GATE (denied call with `org_idx`).
- Parameter-format validation error: fix the format (required `user_id`; dates as `YYYY-MM-DD`) and call again.
- Empty result: there was no activity in that period. Confirm the user exists with `check_user_exists`.

## Recommended Chain

```text
check_user_exists → get_user_activity_summary → list_user_activities → (if needed) get_user_recent_info
```
