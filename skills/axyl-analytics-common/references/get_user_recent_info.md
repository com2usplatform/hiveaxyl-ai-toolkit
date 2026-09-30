# get_user_recent_info (Get a User's Latest Properties)

Returns one user's latest properties from the per-date snapshot data — classification type,
cumulative purchases, server, country, and so on.

> **Prerequisite:** Follow the common rules in [`../SKILL.md`](../SKILL.md). Call after `check_user_exists`.

## When to Use

- To check what state a user is in now, where the activity history shows what they did in the past
- To check why a user is or is not included in a segment condition
- To read the user classification type (`userType`) of a specific user

## Parameters

| Parameter | Required | Description |
|---------|------|------|
| `company_cd` | Y | Company code confirmed from `list_projects` |
| `org_idx` | Y | Organization idx confirmed from `list_organizations` |
| `appid_group` | Y | Project ID (`list_projects.appid_group`) |
| `user_id` | Y | The user ID to query |
| `last_date` | N | Base date `YYYY-MM-DD`. Omit for the server default |
| `lang` | N | Label language. Default `ko` |

## Return Value

Returns `{"user_id", "appid_group", "last_date", "count", "properties"}`.
`properties` is the server response as is.

| Field | Content |
|---|---|
| `property_category` · `property_category_label` | Property group (login info, purchase info, user info, session info, play info) |
| `property_name` · `property_name_label` | Property name and its display name |
| `property_value` · `property_value_label` | Value and its display name |

## Decision Rules

- **Items that were not collected come back with `property_value` of `'-'`.** Missing is not the same
  as zero — do not describe `'-'` as "0 times" or "none".
- `property_value` returns numbers as strings too (`"21080.44"`).
- `property_value_label` is the display name of a coded value (`dolphin` → dolphin, `AP` → App Store,
  `HI` → Hive). For plain numbers it is the same as the value.
- `userType` holds the user classification type. Use it to continue into a classification-based
  investigation.
- This is a raw value; metric settings are not applied. Cumulative figures such as `accKrw` and
  `accPurchaseCnt` can differ from metric queries.

## On Failure

- Organization or project access error: recheck the organization and project relationship.
- All values `'-'`: the user exists but nothing has been collected. Do not read it as zero.

## Recommended Chain

```text
check_user_exists → get_user_activity_summary → list_user_activities → get_user_recent_info
```
