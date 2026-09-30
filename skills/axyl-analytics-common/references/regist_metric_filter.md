# regist_metric_filter (Register a Metric Filter)

Registers targets to exclude from metric calculation by server ID or app ID. Once registered, logs from those servers
or apps are left out of all later metric calculation.

> **Prerequisite:** Follow SETTING_ADMIN_GATE and WRITE_APPROVAL in [`../SKILL.md`](../SKILL.md).

## When to Use

- To keep logs from QA servers or test apps from polluting real metrics
- Always check the current registrations with `list_metric_filters` before calling

## Parameters

| Parameter | Required | Description |
|---------|------|------|
| `title` | Y | A name identifying the purpose of the registration, for example `QA server exclusion` |
| `project_id` | Y | A list of `list_projects.appid_group` values, not AppIDs |
| `filter_type` | Y | `appId` (by app ID) or `serverId` (by server ID) |
| `filter_value` | Y | The values to exclude. Use values matching `filter_type` |
| `company_cd` | Y | Company code confirmed from `list_projects` |
| `org_idx` | Y | Organization idx confirmed through SETTING_ACCESS_GATE and cleared for writes by SETTING_ADMIN_GATE |

## Return Value

Returns the registration name, the project/type/value lists, and `expected_rows` (the number of rows this call creates).
Storage is one row per project and per value, so two projects with three values register six rows.

## Decision Rules

- `filter_value` is validated against the candidate list from the meta API. A value that cannot be selected in the console
  would filter nothing, so if it is not in the list the tool raises an error with the candidates instead of registering.
- If the same combination (project + type + value) already exists, the call is blocked before registration. The server does
  not prevent duplicates, so the same value would otherwise pile up as extra rows.
- **Editing and deletion are not provided.** The console has no edit function either. To remove a mistaken registration, delete it in the console.
- A registration affects every metric calculation. Present the target organization, projects, type, and values along with the
  impact, and obtain approval first.

## On Failure

- Value not in candidates: pick a correct value from the candidate list in the error message. Nothing was registered.
- Duplicate combination: it is already registered. No further registration is needed.
- Project access error: that project does not belong to the organization. Perform SETTING_ACCESS_GATE again.
- Administrator privilege error: do not register. Prepare the request details to send to an Analytics administrator.

## Recommended Chain

```text
SETTING_ACCESS_GATE → list_metric_filters → no duplicate
→ SETTING_ADMIN_GATE → WRITE_APPROVAL → regist_metric_filter
→ confirm it took effect with list_metric_filters
```
