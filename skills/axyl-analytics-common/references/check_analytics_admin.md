# check_analytics_admin (Check Analytics Administrator Status)

> **Prerequisite:** Follow the common rules in [`../SKILL.md`](../SKILL.md). This is the entry point for ORG_WORKSPACE_GATE (it may follow
> `list_organizations` when PROJECT_ID_GATE already ran it).

## When to Use

- A step in obtaining `org_idx`/`workspace_idx` (first in ORG_WORKSPACE_GATE, or after `list_organizations` when
  PROJECT_ID_GATE already ran it) before calling a tool that takes both — `preview_*` (including `preview_chart_rank`), content and dashboard `create_*`/`update_*`, `get_content`, `get_dashboard`.
- SETTING_ADMIN_GATE step 2: verify administrator status before registering or changing Analytics configuration.
- Do not call it again if administrator status has already been verified in the same conversation.

## Parameters

| Parameter | Required | Description |
|---------|------|------|
| `company_cd` | Y | Company code confirmed from `list_projects` |

## Return Value

Returns a boolean indicating whether the user is an Analytics administrator for the company.

## Decision Rules

- **`true` (administrator)**: Organization and workspace membership checks are skipped. MCP access and the
  organization-to-project scope are not.
  - **MCP access is never skipped.** The administrator must still have MCP access in at least one organization of the
    company, and ORG/WORKSPACE tools require MCP access in the exact organization.
  - **The organization-to-project scope is never skipped** — an organization that is not linked to the project is
    rejected even for an administrator.
  - So pass the `appid_group` filter to `list_organizations` whenever the project is known, administrator or not. `list_workspaces` does not accept `appid_group` at all — `org_idx` is required.
  - Even so, for content and dashboard tools (ORG_WORKSPACE_GATE), the `list_organizations`/`list_workspaces` calls
    themselves cannot be skipped, because content is created at the `org_idx`/`workspace_idx` location where it actually exists. Configuration tools do not need a workspace.
- **`false` (non-administrator)**: Call `list_organizations(company_cd, appid_group)` → `list_projects(company_cd, org_idx)` → `list_workspaces(company_cd, org_idx)` in order, and use only values filtered by actual membership.

## On Failure

- Sign-in session expired: sign in again. For any other permission denial, do not sign in again; follow MCP_ACCESS_GATE.
- If a call is denied, first verify the company code, then relay the server's guidance. Do not treat an error as `false`.

## Recommended Chain

```
list_projects (candidate) → check_analytics_admin → list_organizations → list_projects(company_cd, org_idx) → list_workspaces → preview_chart, etc.
```
