# regist_workspace (Create a Workspace)

Creates a new workspace in an organization. The caller becomes its OWNER.

> **Prerequisite:** Follow WRITE_APPROVAL in [`../SKILL.md`](../SKILL.md).

## When to Use

- When a new space is needed to store content
- Always check with `list_workspaces` whether a workspace for the same purpose already exists before calling

## Parameters

| Parameter | Required | Description |
|---------|------|------|
| `workspace_name` | Y | Workspace name |
| `company_cd` | Y | Company code confirmed from `list_projects` |
| `org_idx` | Y | Organization idx confirmed from `list_organizations` |
| `workspace_desc` | N | Description. Empty if omitted |

## Return Value

Returns `workspace_idx`, the name, and `org_idx`, along with `console_url` (the screen for adding and editing members).

## Decision Rules

- **Creation cannot be undone through MCP.** Analytics has no workspace deletion API, and hiding is not provided either.
  A mistake has to be cleaned up in the console, so always confirm the name before calling.
- **Do not add members with this tool.** Adding someone else requires a roster of internal accounts, which is personal
  information and is not handled here. Point the user to `console_url` after creation.
- A newly created workspace has no content. Creating content is a separate write that needs its own approval.

## On Failure

- Organization access error: recheck the accessible organizations with `list_organizations`.
- API error: do not retry automatically. First check with `list_workspaces` whether the workspace was actually created —
  a retry can create two workspaces with the same name, and they cannot be deleted.

## Recommended Chain

```text
list_organizations → list_workspaces → no workspace for the same purpose
→ WRITE_APPROVAL → regist_workspace → point to console_url to add members
```
