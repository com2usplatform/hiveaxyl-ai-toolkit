# list_organizations (List Organizations)

> **Prerequisite:** Follow the common rules in [`../SKILL.md`](../SKILL.md). In ORG_WORKSPACE_GATE, this is the step after `check_analytics_admin`
> (or before it, when PROJECT_ID_GATE already ran it).

## When to Use

- To obtain the `org_idx` needed by `preview_chart` and similar tools (after `check_analytics_admin` in ORG_WORKSPACE_GATE, or before it when
  PROJECT_ID_GATE already ran it).
- To obtain `org_idx` before querying the list of projects an organization controls.
- **Do not call it** if the same conversation already has an `org_idx` verified for the same company and, when a project is
  involved, the same `appid_group`.

## Parameters

| Parameter | Required | Description |
|---------|------|------|
| `company_cd` | Y | Company code (the `company_cd` from `list_projects`) |
| `appid_group` | N | Project ID whose access you want to check (the `appid_group` from `list_projects`). Specify it when the task targets a specific project |

- **The filter applies to Analytics administrators as well.** It answers "which organizations can use this project",
  and that answer does not depend on administrator status. An organization that is not linked to the project is
  rejected by `preview_*`/`create_*` even for an administrator, so pass `appid_group` whenever the project is known.
- Omit `appid_group` only when no project is involved. A candidate `appid_group` from `list_projects` counts as known.

## Return Value

Returns the `idx` to use in calls, the name and description for display, and whether the organization was last accessed.

The result is the intersection of ordinary organization access and MCP access for that organization. Even an
Analytics administrator cannot see or use an organization where MCP access is not allowed.

- The organization with `last_org_flag="Y"` is the **most recently accessed organization** for that company. When showing it to the user, **only label** it — for example, `(last accessed)` — and do not use it as a basis for a default selection.
- If you specified `appid_group` and the result is empty, no organization that you can use through MCP is linked to that
  project: either none is linked to it at all, or you have no MCP access in the ones that are. The result cannot tell which.

## Decision Rules

- **If there is exactly one organization**, use it (no confirmation question needed).
- **If there are two or more, present every candidate and have the user choose** (Analytics configuration tools are the
  exception: see SETTING_ACCESS_GATE step 5). Do not auto-select even when
  `last_org_flag='Y'` is present — just label that entry `(last accessed)`. Organization selection changes both the result scope and where content is created, so "last accessed" is not evidence that it is the target of this request.
- Show the user only `org_name`, plus `org_desc` when needed. Use `idx` only for subsequent tool calls.
  Do not proceed with queries or creation before the user chooses (except Analytics configuration tools, SETTING_ACCESS_GATE
  step 5).
- Do not guess or invent `idx` (for example, `0`).
- Use the confirmed `org_idx` as is for `list_workspaces`, `preview_chart`, and similar tools.

## On Failure

- Permission denial: you lack company permission or have MCP access in no organization of the company. Do not sign in again
  or retry; follow MCP_ACCESS_GATE. This is also why a query without `appid_group` never returns an empty list.
- Empty result (with `appid_group` specified): no organization that you can use through MCP is linked to that project. Ask an
  Analytics administrator either to link the project to one of your MCP-enabled organizations or to grant you MCP access in an
  organization already linked to it. A query without `appid_group` cannot tell which applies.

## Recommended Chain

```
list_projects (candidate) → check_analytics_admin → list_organizations(company_cd, appid_group) → select organization → list_projects(company_cd, org_idx)
```
