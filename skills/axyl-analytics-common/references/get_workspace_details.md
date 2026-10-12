# get_workspace_details (Get Workspace Details)

Gets the configuration of a single workspace: the number of members and how their permissions are distributed, the home
dashboard, and whether the workspace is visible.

> **Prerequisite:** Follow the common rules in [`../SKILL.md`](../SKILL.md). This is the step after `list_workspaces`.

## When to Use

- To check how many people use this workspace and how its permissions are split
- To see whether a home dashboard is set for the workspace landing page
- When you need more than `list_workspaces` returns, since that tool provides only what a list view needs

## Parameters

| Parameter | Required | Description |
|---------|------|------|
| `company_cd` | Y | Company code confirmed from `list_projects` |
| `org_idx` | Y | Organization idx confirmed from `list_organizations` |
| `workspace_idx` | Y | The workspace to look up: from `list_workspaces`, a `list_contents` row, or a denied call |

## Return Value

Returns the name and description, `order_num`, `display_yn`, `indicator_type`, and `dashboard_idx`, together with
`member_count` (the number of members), `member_types` (counts by OWNER/ADMIN/MEMBER), and `console_url`.

## Decision Rules

- **Member identities are not returned.** Internal account IDs are personal information, so only the member count and
  permission distribution are provided. If a roster is needed, point the user to `console_url` — looking for the right person
  to ask for access is exactly that case.
- `dashboard_idx` of `0` means no home dashboard is set.
- `display_yn='N'` means the workspace is not shown in the console list (effectively deleted).
- This detail call is authorized at organization scope, so a caller with organization access can read the workspace even
  when they are not a member. For a non-administrator, `list_workspaces` filters by workspace membership; an Analytics
  administrator instead receives every active workspace in the organization, with `member_type=null` for non-members.

## On Failure

- Ownership error: the workspace belongs to the organization named in the error. Confirm that organization through
  ORG_WORKSPACE_GATE and continue there (for an access request, follow `request_workspace_permission`). Do not recheck with
  `list_workspaces`, which lists only workspaces you belong to.
- Organization or project authorization denial: do not retry the same call unchanged or with a guessed identifier; follow
  MCP_ACCESS_GATE (denied call with `org_idx`).

## Recommended Chain

```text
list_organizations → list_workspaces → get_workspace_details
```
