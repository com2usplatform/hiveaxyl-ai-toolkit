# get_workspace_details (Get Workspace Details)

Gets the configuration of a single workspace: the number of members and how their permissions are distributed, the home
dashboard, and whether the workspace is visible.

> **Prerequisite:** Follow the common rules in [`../SKILL.md`](../SKILL.md). This is the step after `list_workspaces`.

## When to Use

- To check who is using this workspace and how its permissions are structured
- To see whether a home dashboard is set for the workspace landing page
- When you need more than `list_workspaces` returns, since that tool provides only what a list view needs

## Parameters

| Parameter | Required | Description |
|---------|------|------|
| `company_cd` | Y | Company code confirmed from `list_projects` |
| `org_idx` | Y | Organization idx confirmed from `list_organizations` |
| `workspace_idx` | Y | `workspace_idx` from `list_workspaces` |

## Return Value

Returns the name and description, `order_num`, `display_yn`, `indicator_type`, and `dashboard_idx`, together with
`member_count` (the number of members), `member_types` (counts by OWNER/ADMIN/MEMBER), and `console_url`.

## Decision Rules

- **Member identities are not returned.** Internal account IDs are personal information, so only the member count and
  permission distribution are provided. If a roster is needed, point the user to `console_url` — looking for the right person
  to ask for access is exactly that case.
- `dashboard_idx` of `0` means no home dashboard is set.
- `display_yn='N'` means the workspace is not shown in the console list (effectively deleted).
- The workspace is readable by anyone with access to the organization, even a non-member. This differs from `list_workspaces`,
  which filters by membership, and the difference is intentional.

## On Failure

- Ownership error: the specified `workspace_idx` does not belong to that `org_idx`. Recheck with `list_workspaces`.
- Organization access error: recheck the accessible organizations with `list_organizations`.

## Recommended Chain

```text
list_organizations → list_workspaces → get_workspace_details
```
