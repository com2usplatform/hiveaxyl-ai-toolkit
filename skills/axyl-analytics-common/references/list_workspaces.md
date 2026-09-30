# list_workspaces (List Workspaces)

> **Prerequisite:** Follow the common rules in [`../SKILL.md`](../SKILL.md). This is the step after `list_organizations` and the final query step of ORG_WORKSPACE_GATE.

## When to Use

- After obtaining `org_idx`, to obtain the `workspace_idx` needed by `preview_chart` and similar tools.
- **Do not call it** if a `workspace_idx` has already been verified in the same conversation.

## Parameters

| Parameter | Required | Description |
|---------|------|------|
| `company_cd` | Y | Company code (the `company_cd` from `list_projects`) |
| `org_idx` | Y | Organization idx (the `idx` from `list_organizations`) |

- `org_idx` is required. If you know only the project and not the organization, obtain the candidates first with `list_organizations(company_cd, appid_group)`; when two or more organizations come back, present them to the user and confirm one before calling.
- `workspace_idx` is where content gets saved, so never pick an organization arbitrarily to query with.

## Return Value

Returns the `workspace_idx` for subsequent calls, the name and description for display, the member type, the display order, and whether it was last accessed.

- `member_type`: with `OWNER`/`ADMIN` you can also edit and delete content created by others; with `MEMBER` you cannot. `null` for a non-member when called by an administrator.

## Decision Rules

- **If there is exactly one workspace**, use it (no confirmation question needed).
- **If there are two or more, present every candidate and have the user choose.** The list comes back with `last_flag='Y'` first and then in `order_num` order, but **do not use the ordering as a basis for selection** — just label the `last_flag='Y'` entry `(last accessed)`. There may be no `last_flag='Y'` at all (when the last accessed workspace does not belong to this organization).
- When presenting candidates, show `workspace_name` together with `member_type` — for a request that will end in a save, permissions affect the choice (`MEMBER` cannot edit or delete someone else's content).
- Do not guess or invent `workspace_idx` (for example, `0`).
- Use the confirmed `workspace_idx` as is for `preview_chart` and similar tools.

## On Failure

- Empty result: this organization grants no accessible workspaces. Check other organization candidates with `list_organizations`.

## Recommended Chain

```
check_analytics_admin → list_organizations → list_workspaces → list_projects → preview_chart, etc.
```
