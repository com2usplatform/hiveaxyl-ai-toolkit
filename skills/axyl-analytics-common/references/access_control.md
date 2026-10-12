# Access Control

> **Prerequisite:** Read [`../SKILL.md`](../SKILL.md) first.

### MCP_CONNECTION_GATE

Before any Analytics request, confirm that the Analytics tools are available. If they are missing or a call fails because the sign-in session expired, do not query, guess a project, or plan the analysis. Tell the user to sign in to the Hive Axyl MCP server from the host's MCP server list, naming the server as the host shows it, then stop and ask them to repeat the request after signing in. If a write was in progress, run its duplicate check again after sign-in and obtain WRITE_APPROVAL again before writing. An MCP access denial is not a sign-in problem; follow MCP_ACCESS_GATE.

### MCP_ACCESS_GATE

The server applies the following MCP scope to every tool. This is an **additional** gate on top of the existing
company, organization, and workspace permissions; it does not replace them.

| Scope | Access rule |
|---|---|
| `SYSTEM` | Applies only to `check_axyl_mcp_health`, which returns server health and no Analytics data |
| `META` | The user must have MCP access in at least one organization of one of their companies |
| `COMPANY` | The user must belong to the target company and have MCP access in at least one of its organizations |
| `ORG` | MCP use must be allowed for the user in the exact `org_idx` |
| `WORKSPACE` | The ORG rule must pass, followed by the existing workspace permission check |

- Analytics administrators may bypass ordinary organization/workspace membership, but never MCP access nor the
  organization-to-project link.
- Use only organizations returned by `list_organizations`. Do not guess a missing `org_idx` or reuse an old value to bypass the filter.
- A permission denial means the user lacks that permission, not that a call failed or the session expired. A permission
  denial comes back as the tool's error result. An expired session instead fails as an authentication error (401; for
  example, the host reports that the server needs authentication), or the Analytics tools disappear. Recommend signing in again only in that case or when the MCP server is not connected (MCP_CONNECTION_GATE).
- Do not branch on the exact wording of the server's message; it can change. Decide from **which call was denied**, and
  relay the server's guidance (whom to ask, what to obtain first) as it is.
- **Denied call without `org_idx`** (`list_projects` without `org_idx`, `list_organizations`, company-level tools): the user lacks company
  permission or has MCP access in no organization of that company. Do not retry; relay the server's guidance and ask the
  user to request access from an Analytics administrator.
- **Denied call with `org_idx`** (organization- or workspace-level tools): treat the denied `org_idx`/`workspace_idx` as
  no longer verified. Do not retry the same call unchanged or bypass it with a guessed value. Rerun
  `list_organizations(company_cd, appid_group)` (omit `appid_group` only when no project is involved).
  - If that organization is not returned, apply the candidate rule again: one → use it; two or more → present them all
    and wait for the user (Analytics configuration tools: SETTING_ACCESS_GATE step 5); none → PROJECT_ID_GATE's "No organization for the project". If the denied organization
    is required, ask the user to request access from an Analytics administrator.
  - If it is returned, the denial concerns the project or the workspace. Reconfirm the project with
    `list_projects(company_cd, org_idx)` and the workspaces with `list_workspaces(company_cd, org_idx)`, leaving out the
    denied workspace. Apply the candidate rule to the remaining workspaces (`preview_*` only:
    any returned workspace, as in ORG_WORKSPACE_GATE); if none remain, offer the other organizations
    from that `list_organizations` result. Retry once only with a project or workspace that changed this way. If nothing
    changes, stop and relay the server's guidance. Offer `request_workspace_permission` (with WRITE_APPROVAL) only for a
    workspace that `list_workspaces` does not return.
  - Before retrying a write in a different organization, workspace, or project, run its duplicate check again for the new
    target and obtain WRITE_APPROVAL again.
- **Administrator-only tools** are covered by SETTING_ADMIN_GATE.
- Do not apply these rules to wrong inputs (an organization or project of another company). If a read fails with a generic
  check failure that names no missing permission, retry it once before applying these rules; never retry a write
  automatically.
