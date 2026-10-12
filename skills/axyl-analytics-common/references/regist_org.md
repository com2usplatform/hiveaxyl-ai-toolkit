# regist_org (Create an Organization)

Creates a new organization. The caller joins it as a member when `all_members=False`. Only an Analytics administrator can use it.

> **Prerequisite:** Follow SETTING_ADMIN_GATE and WRITE_APPROVAL in [`../SKILL.md`](../SKILL.md).

## When to Use

- When a new organization is needed to manage project access separately
- Before calling, ask the user whether an organization for the same purpose already exists. `list_organizations` shows only
  organizations where the user has MCP access, so it cannot rule out an existing organization with MCP disabled; the console's
  organization settings show them all

## Parameters

| Parameter | Required | Description |
|---------|------|------|
| `org_name` | Y | Organization name |
| `company_cd` | Y | Company code confirmed from `list_projects` |
| `org_desc` | N | Description. Empty if omitted |
| `appid_groups` | N | The project IDs to connect, confirmed with the user from `list_projects(company_cd)`. Required when `all_projects=False`. Every project must belong to `company_cd`; if any does not, the call is rejected before saving |
| `all_projects` | N | `True` creates an organization that accesses every project in the company; `appid_groups` is then ignored |
| `all_members` | N | `True` creates an organization open to everyone in the company. `False` leaves the caller as the only member |
| `allow_duplicate` | N | Default `False`. Pass `True` only after the user confirms that a second organization with the same name is intended (see Decision Rules) |

## Return Value

Returns `org_idx`, the name, the sharing scope that was applied, and the list of connected projects.

A new organization is created with MCP disabled. Regular organization membership and MCP access are separate.
When `all_members=False`, the creator becomes a regular organization member but does not automatically receive MCP access.
Setting `all_members=True` only broadens regular organization access; it does not enable MCP. After creation, allow MCP
access for all members or selected users in the console's organization settings. The result has no separate `mcp_enabled` field.

## Decision Rules

- **Creation cannot be undone through MCP.** No organization deletion tool is provided. Always confirm the name and the
  projects to connect before calling.
- **Do not add members with this tool.** Adding someone else requires a roster of internal accounts, which is personal
  information and is not handled here. Point the user to the organization settings screen in the console after creation.
- **The new organization cannot be used through MCP immediately.** Enable all or selected users in the console's
  organization settings before it appears in `list_organizations` or can be used by organization-scoped tools.
- If the caller has MCP access in no organization of the company, COMPANY scope blocks `regist_org` itself. Grant the
  caller MCP access in an organization first, in the console's organization settings.
- **The server prevents accidental duplicates.** Same-name organizations are allowed, as in the console, but if the caller
  created an organization with the same name in the last 10 minutes, the call is rejected with that organization's
  `org_idx` and creation time. Do not assume it is the organization the user wants: its linked projects cannot be checked
  through MCP while its MCP access is off. Ask the user to check it in the console's organization settings. If it is the
  right one, set members and MCP access there. The only call that may follow is one call with `allow_duplicate=True`, and
  only after the user confirms a second same-name organization is really intended.
- If `all_projects=False` and `appid_groups` is empty, the call fails. This prevents creating an organization with no projects.
- An organization is the unit that defines data access scope. Access to every project (`all_projects=True`) and open sharing
  (`all_members=True`) are broad, so confirm they are really needed before using them.

## On Failure

- Administrator privilege error: do not create. Prepare the request details to send to an Analytics administrator.
- Company-level permission denial (for example, no MCP access in any organization of the company): do not sign in again or
  retry. Grant access first in the console's organization settings.
- Duplicate rejection (an organization with the same name was created by you in the last 10 minutes): the organization
  already exists with the returned `org_idx`. Have the user check it in the console's organization settings; if it is the
  right one, set members and MCP access there. Call again only once,
  with `allow_duplicate=True`, if the user confirms a second same-name organization is really intended, after fresh
  WRITE_APPROVAL.
- Input rejected before saving (missing `appid_groups` or a project of another company): nothing
  was created. Fix the input, obtain WRITE_APPROVAL again, and call once more.
- API error (any other error): do not call again, with or without `allow_duplicate`. When the save response fails but the
  organization was created, the server itself returns success with `org_idx` and a `note`; such an error therefore means
  creation was not confirmed. Do not use
  `list_organizations` to check — a new organization never appears there until MCP access is granted. Ask the user to
  check the console's organization settings before deciding to create it again.

## Recommended Chain

```text
check_analytics_admin → confirm with the user that no organization serves the same purpose (console organization settings)
→ WRITE_APPROVAL → regist_org → point to the console to configure members and MCP access
```
