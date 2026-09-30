# Activity History Investigation (Summary → Detail)

The procedure for **narrowing the range with a summary and then looking at the detail** for one user.

> **Prerequisite:** Follow the rules in [`../SKILL.md`](../SKILL.md) and [`../../axyl-analytics-common/SKILL.md`](../../axyl-analytics-common/SKILL.md). This is the step after USER_ID_GATE passes.

## Order

```text
get_user_activity_summary   Activity counts for the whole period and per date
  ↓ pick the dates where activity is concentrated
list_user_activities        Narrow to those dates and check the chronological activity flow
  ↓ when needed
get_user_recent_info        Check the current state from the per-date snapshot data (classification type, cumulative purchases, server, country, and so on)
```

Do not open the activity list first.
There are many entries and `properties` differs per event, so without a summary it can be hard to interpret.

## Reading the Summary

```text
get_user_activity_summary(company_cd, org_idx, appid_group, user_id,
                          start_date="2026-09-15", end_date="2026-09-17")
  → summary: [{"type": "period", "data": [...]},
              {"type": "2026-09-17", "data": [...]},
              {"type": "2026-09-16", "data": [...]}]
```

| `type` | Meaning |
|---|---|
| `period` | The total for the whole specified period |
| A date string | The activity on that date |

Each item is `{category, categoryLabel, name, nameLabel, cnt}`.

- **`cnt` is a string** (`"1"`). Take care that comparisons do not fall back to string ordering.
- Find the **day that stands out** among the per-date items. Use that date as the period for `list_user_activities`.

**Do not set a long period.** The summary grows with event types × dates — even a few days can return dozens
of event types. Beyond one or two weeks, even the summary becomes a burden.

## Reading the Detail

```text
list_user_activities(company_cd, org_idx, appid_group, user_id,
                     start_date="2026-09-17", end_date="2026-09-17",
                     page=0, size=100)
  → {"count", "has_more", "activities": [...]}
```

| Field | Content |
|---|---|
| `activity_date_time` | Activity time (with the user's timezone applied) |
| `category` · `category_label` | Event category (`gamePlay`, `purchase`, `login`, and so on) |
| `name` · `name_label` | Event name (`useablePurchase`, `tutorialAccept`, and so on) |
| `properties` | Per-event detail. **Free-form, so the properties differ per activity** |

`page` starts at **0**. The server does not return a total count, so the only signal for whether a
next page exists is `has_more` (`count >= size`).

**Do not page through everything.**
When there are many entries, narrow the range using the per-date items in the summary and call again,
or ask the user which range to look at.

### properties

Size and structure differ greatly by event type.

```text
Game events:  {dateTime, country, serverId, modeTypeName, userLevel, characterLv, ...}
Airbridge:    {..., deviceAttributes:{...}, touchpointAttributes:{...}, fraudAttributes:{...}}
```

Airbridge events carry nested objects, so one entry is the size of five or six game events.
Unless it is genuinely required, **quote only the needed keys** and do not spread the raw content.

## Querying the Current Snapshot Data

```text
get_user_recent_info(company_cd, org_idx, appid_group, user_id, last_date="2026-09-17")
  → properties: [{"property_category", "property_name", "property_value",
                  "property_name_label", "property_value_label", ...}]
```

- **Items that were not collected come back with `property_value` of `'-'`.** Missing is not the same
  as zero — do not describe `'-'` as "0 times" or "none"
- `property_value` returns numbers as strings too (`"21080.44"`)
- `property_value_label` is the display name of a coded value (`dolphin` → dolphin, `AP` → App Store)
- `userType` (user classification type) is included here. That value can lead into an investigation
  based on the classification criteria

## Checking Group Membership

If the user knows the group number, check membership in the same call.

```text
check_user_exists(company_cd, org_idx, appid_group, user_id, user_group_id=<user_group_id>)
  → exists: true  → the user is a member of that user group
```

## When Answering

- **State the time basis.** `activity_date_time` has the user's timezone applied and
  `properties.dateTime` is UTC, so a time difference can occur. Unless the case calls for otherwise,
  use `activity_date_time` as the basis.
- Do not state counts from the activity history as metric figures — the aggregation basis differs.
  When they disagree with a metric, continue into the configuration cross-check step of the
  investigation procedure in the main document.
- Do not list the entire history. Answer **what was being verified**, and quote only the items that
  support it.
