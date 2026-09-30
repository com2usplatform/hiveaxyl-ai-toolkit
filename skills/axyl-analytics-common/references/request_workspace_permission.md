# request_workspace_permission (Request Workspace Access)

Files a request for access to a workspace the caller has no permission for. The requester is always the caller.

> **Prerequisite:** Follow WRITE_APPROVAL in [`../SKILL.md`](../SKILL.md).

## When to Use

- When content in a workspace that does not appear in `list_workspaces` has to be reached
- When creating or reading content is blocked by workspace permissions, so that the request can be filed on the spot
  instead of ending with "please request it in the console"

## Parameters

| Parameter | Required | Description |
|---------|------|------|
| `company_cd` | Y | Company code confirmed from `list_projects` |
| `org_idx` | Y | Organization idx confirmed from `list_organizations` |
| `workspace_idx` | Y | The idx of the workspace to request access to |

## Return Value

Returns `request_idx`, `workspace_idx`, `workspace_name`, `org_idx`, `approval_status` (`PENDING`), and `console_url`
(the screen for checking how the request is being handled).

## Decision Rules

- **A request does not grant access.** Access begins only once an owner approves, so do not continue into a flow that uses
  that workspace right after requesting. Tell the user the request is awaiting approval and point to `console_url`.
- **It cannot be cancelled.** There is no cancellation API, so a filed request is hard to undo through either MCP or the
  console. Confirm which workspace is being requested, by name, before calling.
- **You cannot request on someone else's behalf.** The requester is fixed to the caller.
- **Approval and rejection are not provided.** They grant another person access to data, and the decision depends on knowing
  who the requester is — which is personal information that is not exposed. Approvals are handled in the console.
- If the caller is already a member, or already has a pending request, the tool blocks the call beforehand. In that case do
  not file again; report the current state.
- A previously rejected request can be filed again, but confirm with the user before repeating the same request.

## On Failure

- Already has access: no request is needed. Proceed with that workspace.
- Pending request exists: report the request `idx` from the error message along with `console_url`.
- Not an active workspace: it is hidden or deleted, and approving would lead nowhere. Recheck the target with `list_workspaces`.
- Organization access error: recheck the accessible organizations with `list_organizations`.

## Recommended Chain

```text
list_organizations → list_workspaces → no access to the target workspace
→ WRITE_APPROVAL → request_workspace_permission
→ report that it awaits approval + console_url
```
