# check_analytics_admin (Check Analytics Administrator Status)

> **Prerequisite:** Follow the common rules in [`../SKILL.md`](../SKILL.md). This is the entry point for ORG_WORKSPACE_GATE.

## When to Use

- The first step in obtaining `org_idx`/`workspace_idx` before calling a tool that takes both — `preview_*` (including `preview_chart_rank`), content and dashboard `create_*`/`update_*`, `get_content`, `get_dashboard`.
- Do not call it again if administrator status has already been verified in the same conversation.

## Parameters

| Parameter | Required | Description |
|---------|------|------|
| `company_cd` | Y | Company code confirmed from `list_projects` |

## Return Value

Returns a boolean indicating whether the user is an Analytics administrator for the company.

## Decision Rules

- **`true` (administrator)**: All detailed organization-, workspace-, and project-level permission checks are skipped.
  - **Organization and workspace membership** is what gets skipped. The organization-to-project scope is not — an organization that is not linked to the project is rejected even for an administrator.
  - So pass the `appid_group` filter to `list_organizations` whenever the project is known, administrator or not. `list_workspaces` does not accept `appid_group` at all — `org_idx` is required.
  - Even so, the `list_organizations`/`list_workspaces` calls themselves cannot be skipped, because content is created at the `org_idx`/`workspace_idx` location where it actually exists.
- **`false` (non-administrator)**: Call `list_organizations(company_cd, appid_group)` → `list_workspaces(company_cd, org_idx)` in order, and use only values filtered by actual membership.

## On Failure

- Authentication or company-access error: reauthenticate or confirm the company; do not treat it as `false`.

## Recommended Chain

```
check_analytics_admin → list_organizations → list_workspaces → list_projects → preview_chart, etc.
```
