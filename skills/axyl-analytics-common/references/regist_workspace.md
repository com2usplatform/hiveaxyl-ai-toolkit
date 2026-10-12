# regist_workspace (Create a Workspace)

Creates a new workspace in an organization. The caller becomes its OWNER.

> **Prerequisite:** Follow WRITE_APPROVAL in [`../SKILL.md`](../SKILL.md).

## When to Use

- When a new space is needed to store content
- Before calling, check with `list_workspaces` and ask the user whether a workspace for the same purpose already exists.
  `list_workspaces` shows non-administrators only the workspaces they belong to, so it cannot rule out an existing
  workspace with the same name; the console's workspace settings show them all

## Parameters

| Parameter | Required | Description |
|---------|------|------|
| `workspace_name` | Y | Workspace name |
| `company_cd` | Y | Company code confirmed from `list_projects` |
| `org_idx` | Y | Organization idx confirmed from `list_organizations` |
| `workspace_desc` | N | Description. Empty if omitted |

## Return Value

Returns `workspace_idx`, the name, and `org_idx`, along with `console_url` (the screen for adding and editing members).
`workspace_idx` can be null when the new workspace could not be identified; `console_url` then opens the workspace
settings list. Have the user find the new workspace there, and confirm it with `list_workspaces` before using it.

## Decision Rules

- **Creation cannot be undone through MCP.** Analytics has no workspace deletion API, and hiding is not provided either.
  A mistake has to be cleaned up in the console, so always confirm the name before calling.
- **Do not add members with this tool.** Adding someone else requires a roster of internal accounts, which is personal
  information and is not handled here. Point the user to `console_url` after creation.
- A newly created workspace has no content. Creating content is a separate write that needs its own approval.

## On Failure

- Organization or project authorization denial: do not retry the same call unchanged or with a guessed identifier; follow
  MCP_ACCESS_GATE (denied call with `org_idx`).
- API error, or the session expired during the call: do not retry automatically. First check with `list_workspaces` whether the workspace was actually created —
  a retry can create two workspaces with the same name, and they cannot be deleted. A same-name workspace that existed
  before the call does not count.

## Recommended Chain

```text
list_organizations → list_workspaces + ask the user (console workspace settings) → no workspace for the same purpose
→ WRITE_APPROVAL → regist_workspace → point to console_url to add members
```
