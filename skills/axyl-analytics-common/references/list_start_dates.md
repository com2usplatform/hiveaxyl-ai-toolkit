# list_start_dates (List Metric Start Dates by Project)

Lists the registered metric start dates for an organization's projects. Data from before the metric start date is
excluded from metric calculation.

> **Prerequisite:** Follow PROJECT_ID_GATE and SETTING_ACCESS_GATE in [`../SKILL.md`](../SKILL.md).

## When to Use

- To check the existing start date before calling `regist_start_dates`
- To confirm the applied value after a registration or change
- To judge whether a pre-launch project's ETL sample data can be separated out as pre-start-date data

## Parameters

| Parameter | Required | Description |
|---------|------|------|
| `company_cd` | Y | Company code confirmed from `list_projects` |
| `org_idx` | Y | Accessible organization idx confirmed through SETTING_ACCESS_GATE |

Anyone with access to that organization can call this, even without Analytics administrator privileges. Only an administrator can register or change.

## Return Value

Returns the registration ID, the company and project scope, and the start date in the organization's time zone.

- `project_id` is `list_projects.appid_group`, not an AppID.
- `start_date` uses the `YYYY-MM-DDTHH:mm:ss` format in the organization's time zone.
- A project with no registered start date does not appear in the list.

## Decision Rules

- No start date means a new registration; an existing one means changing the current value.
- Show both the current value and the proposed value, then ask for approval of the change.
- The response does not include the organization's time zone name, so tell the user that the time entered is in the organization's
  time zone, and do not guess the time zone.

## On Failure

- Organization access error: recheck the company, organization, and project relationship through SETTING_ACCESS_GATE.
- No `start_date` array in the response: treat it as a query failure, not as an empty configuration.
- API error: report the server message and do not guess the existing configuration.

## Recommended Chain

```text
SETTING_ACCESS_GATE → list_start_dates
→ if a change is needed, SETTING_ADMIN_GATE → WRITE_APPROVAL → regist_start_dates
→ confirm it took effect with list_start_dates
```
