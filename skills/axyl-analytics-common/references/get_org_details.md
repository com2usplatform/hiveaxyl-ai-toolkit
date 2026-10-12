# get_org_details (Get Organization Details)

Gets the configuration of a single organization: which projects it is connected to and how widely it is shared.
Only an Analytics administrator can use it.

> **Prerequisite:** Follow SETTING_ADMIN_GATE in [`../SKILL.md`](../SKILL.md). It is a read, but administrator verification is still required.

## When to Use

- To check which projects this organization can access
- To see whether it is open to everyone in the company or restricted to named members
- When you need more than `list_organizations` returns, since that tool provides only the name and description

## Parameters

| Parameter | Required | Description |
|---------|------|------|
| `company_cd` | Y | Company code confirmed from `list_projects` |
| `org_idx` | Y | `idx` from `list_organizations` |

## Return Value

Returns the name and description along with `all_type`, `member_all_type`, `mcp_member_all_type`, `display`,
`appid_groups`, `member_count`, and `mcp_member_count`.

| Value | Meaning |
|---|---|
| `all_type='Y'` | The organization accesses **every project** in the company. `appid_groups` does not decide access and may be empty |
| `all_type='N'` | It accesses only the projects connected through `appid_groups` |
| `member_all_type='Y'` | An **openly shared** organization that anyone in the company uses. There is no regular member roster; `member_count` counts only users registered individually, such as users individually allowed to use MCP |
| `member_all_type='N'` | Only named members use it, and `member_count` is how many |
| `mcp_member_all_type='Y'` | Every member who can use this organization is allowed to use MCP |
| `mcp_member_all_type='N'` | Only individually enabled users may use MCP (possible in openly shared organizations too); `mcp_member_count` is how many |

## Decision Rules

- **Member identities are not returned.** If a roster is needed, point the user to the organization settings screen in the console.
- MCP-enabled member identities are also not returned; only `mcp_member_count` is provided.
- In `appid_groups`, `exclude='Y'` marks an entry that is left out of the connection.

## On Failure

- Administrator privilege error: do not query. Ask an Analytics administrator to check instead.
- Ownership error: the specified `org_idx` is not an organization of that company. Recheck with `list_organizations`.
- Organization permission denial: administrators also need MCP access in that organization, so a newly created
  organization cannot be queried until MCP access is granted. Do not sign in again; follow MCP_ACCESS_GATE.

## Recommended Chain

```text
check_analytics_admin → list_organizations → get_org_details
```
