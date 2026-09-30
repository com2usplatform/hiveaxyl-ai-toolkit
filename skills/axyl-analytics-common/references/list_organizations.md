# list_organizations (List Organizations)

> **Prerequisite:** Follow the common rules in [`../SKILL.md`](../SKILL.md). This is the step after `check_analytics_admin`.

## When to Use

- After `check_analytics_admin`, to obtain the `org_idx` needed by `preview_chart` and similar tools.
- To obtain `org_idx` before querying the list of projects an organization controls.
- **Do not call it** if the same conversation already has an `org_idx` verified for the same company.

## Parameters

| Parameter | Required | Description |
|---------|------|------|
| `company_cd` | Y | Company code (the `company_cd` from `list_projects`) |
| `appid_group` | N | Project ID whose access you want to check (the `appid_group` from `list_projects`). Specify it when the task targets a specific project |

- **The filter applies to Analytics administrators as well.** It answers "which organizations can use this project",
  and that answer does not depend on administrator status. An organization that is not linked to the project is
  rejected by `preview_*`/`create_*` even for an administrator, so pass `appid_group` whenever the project is known.
- In a flow that selects the organization first, the project is not yet confirmed, so omit `appid_group`.

## Return Value

Returns the `idx` to use in calls, the name and description for display, and whether the organization was last accessed.

- The organization with `last_org_flag="Y"` is the **most recently accessed organization** for that company. When showing it to the user, **only label** it — for example, `(last accessed)` — and do not use it as a basis for a default selection.
- If you specified `appid_group` and the result is empty, no organization can access that project.

## Decision Rules

- **If there is exactly one organization**, use it (no confirmation question needed).
- **If there are two or more, present every candidate and have the user choose.** Do not auto-select even when
  `last_org_flag='Y'` is present — just label that entry `(last accessed)`. Organization selection changes both the result scope and where content is created, so "last accessed" is not evidence that it is the target of this request.
- Show the user only `org_name`, plus `org_desc` when needed. Use `idx` only for subsequent tool calls.
  Do not proceed with queries or creation before the user chooses.
- Do not guess or invent `idx` (for example, `0`).
- Use the confirmed `org_idx` as is for `list_workspaces`, `preview_chart`, and similar tools.

## On Failure

- Empty result (with `appid_group` omitted): no organization in that company is accessible. Recheck company permissions.
- Empty result (with `appid_group` specified): no organization can access that project. Query again without `appid_group` and compare.

## Recommended Chain

```
check_analytics_admin → list_organizations → select organization → list_projects(company_cd, org_idx)
```
