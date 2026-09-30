# regist_org (Create an Organization)

Creates a new organization. The caller joins it as a member. Only an Analytics administrator can use it.

> **Prerequisite:** Follow SETTING_ADMIN_GATE and WRITE_APPROVAL in [`../SKILL.md`](../SKILL.md).

## When to Use

- When a new organization is needed to manage project access separately
- Always check with `list_organizations` whether an organization for the same purpose already exists before calling

## Parameters

| Parameter | Required | Description |
|---------|------|------|
| `org_name` | Y | Organization name |
| `company_cd` | Y | Company code confirmed from `list_projects` |
| `org_desc` | N | Description. Empty if omitted |
| `appid_groups` | N | The project IDs to connect. Required when `all_projects=False` |
| `all_projects` | N | `True` creates an organization that accesses every project in the company; `appid_groups` is then ignored |
| `all_members` | N | `True` creates an organization open to everyone in the company. `False` leaves the caller as the only member |

## Return Value

Returns `org_idx`, the name, the sharing scope that was applied, and the list of connected projects.

## Decision Rules

- **Creation cannot be undone through MCP.** No organization deletion tool is provided. Always confirm the name and the
  projects to connect before calling.
- **Do not add members with this tool.** Adding someone else requires a roster of internal accounts, which is personal
  information and is not handled here. Point the user to the organization settings screen in the console after creation.
- If `all_projects=False` and `appid_groups` is empty, the call fails. This prevents creating an organization with no projects.
- An organization is the unit that defines data access scope. Access to every project (`all_projects=True`) and open sharing
  (`all_members=True`) are broad, so confirm they are really needed before using them.

## On Failure

- Administrator privilege error: do not create. Prepare the request details to send to an Analytics administrator.
- API error: do not retry automatically. First check with `list_organizations` whether the organization was actually created —
  a retry can create two organizations with the same name, and they cannot be deleted.

## Recommended Chain

```text
check_analytics_admin → list_organizations → no organization for the same purpose
→ WRITE_APPROVAL → regist_org → point to the console to add members
```
