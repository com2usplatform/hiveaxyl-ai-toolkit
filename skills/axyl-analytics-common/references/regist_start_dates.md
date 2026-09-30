# regist_start_dates (Register or Change a Project's Metric Start Date)

Registers or changes the metric start date for one project. Data from before the start date, including historical data,
is excluded from metric calculation.

> **Prerequisite:** Follow SETTING_ADMIN_GATE and WRITE_APPROVAL in [`../SKILL.md`](../SKILL.md).

## When to Use

- When the app has not launched yet and the actual metric aggregation start time has been confirmed
- To exclude pre-launch ETL and QA sample data from the metric aggregation scope

Do not use it to exclude a single sample from a released, live project. Use `regist_except_users` for that.

## Parameters

| Parameter | Required | Description |
|---------|------|------|
| `project_id` | Y | One `list_projects.appid_group` value. Not an AppID |
| `start_date` | Y | `YYYY-MM-DDTHH:mm:ss` in the organization's time zone |
| `company_cd` | Y | Company code confirmed from `list_projects` |
| `org_idx` | Y | Organization idx confirmed through SETTING_ACCESS_GATE, with write permission verified through SETTING_ADMIN_GATE |

## Return Value

Returns the project and start date, the operation type, the number of settings applied alongside it, and the save result.
In an actual call, use the launch or aggregation start time confirmed with the user.

- `action`: `created` for a new registration, `updated` for a change to an existing value.
- `sent_count`: the number of projects sent together after merging the existing settings into the full-replacement API.

## Decision Rules

- Query the current value with `list_start_dates` first.
- If the existing start date already matches the value the user confirmed, do not call the registration tool.
- Do not arbitrarily use the current time or the ETL send time as the start date. Confirm with the user the actual
  aggregation start time and that it is in the organization's time zone.
- Changing the start date has a retroactive effect on the project's entire metric aggregation scope. Show the existing value,
  the new value, and the scope of impact, then obtain explicit approval.
- The server API replaces the organization's entire start-date configuration, but this tool reads the existing list,
  updates only the target project, and resends the whole set. If reading the existing list fails, do not proceed with the registration.
- After the call, recheck the target project's value with `list_start_dates`. Do not retry failures automatically.

## On Failure

- Date format error: fix it to `YYYY-MM-DDTHH:mm:ss` in the organization's time zone.
- Administrator or project access error: perform SETTING_ACCESS_GATE and SETTING_ADMIN_GATE again.
- Failure reading the existing list: do not call the full-replacement API.
- API error: do not retry automatically — first check with `list_start_dates` whether it actually took effect.

## Recommended Chain

```text
SETTING_ACCESS_GATE → list_start_dates → confirm the actual start date with the user
→ SETTING_ADMIN_GATE → WRITE_APPROVAL → regist_start_dates
→ confirm it took effect with list_start_dates
```
