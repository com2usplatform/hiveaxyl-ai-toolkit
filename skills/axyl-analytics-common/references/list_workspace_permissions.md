# list_workspace_permissions (List Workspace Access Requests)

Returns an aggregate view of workspace access requests for an organization. Workspace permissions are not granted
directly; they follow a "request → approval" flow.

> **Prerequisite:** Follow the common rules in [`../SKILL.md`](../SKILL.md).

## When to Use

- To check whether any requests are awaiting approval
- To see which workspaces the access requests are concentrated on

## Parameters

| Parameter | Required | Description |
|---------|------|------|
| `company_cd` | Y | Company code confirmed from `list_projects` |
| `org_idx` | Y | Organization idx confirmed from `list_organizations` |

## Return Value

Returns the organization-wide `total`, `pending`, `approved`, and `rejected` counts, a per-workspace breakdown
(`by_workspace`), and `console_url`. `by_workspace` is sorted by the number of pending requests, highest first.

## Decision Rules

- **Requester identities are not returned.** The internal account IDs of requesters and approvers are personal information,
  so only aggregates are provided. If they need to be checked, point the user to `console_url`.
- **Approval and rejection are not provided.** They grant another person access, so they are handled in the console. Use
  `request_workspace_permission` to file a request.
- Requests for hidden or deleted workspaces are excluded. Approving them would lead nowhere, and long-standing pending
  requests are usually of this kind.

## On Failure

- Organization access error: recheck the accessible organizations with `list_organizations`.
- A `pending` of `0` means there is nothing to process.

## Recommended Chain

```text
list_organizations → list_workspace_permissions → (if needed) point to console_url
```
