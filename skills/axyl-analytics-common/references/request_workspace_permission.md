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
| `workspace_idx` | Y | The workspace to request access to. A non-administrator's `list_workspaces` does not show workspaces they do not belong to, so take it from a denied call, from the workspace of a `list_contents` row, or (for an Analytics administrator) from `list_workspaces`. If none has it, ask the user to request access in the console — never guess it |

## Return Value

Returns `request_idx`, `workspace_idx`, `workspace_name`, `org_idx`, `approval_status` (`PENDING`), and `console_url`
(the screen for checking how the request is being handled). `request_idx` can be null when the request could not be
identified in the response; the request may still have been filed.

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
- Pending request exists: report that a request is already pending; do not file again.
- Not an active workspace of this organization: it may be hidden or deleted, or it may **belong to another organization**.
  Call `get_workspace_details(company_cd, org_idx, workspace_idx)` (it needs only organization access, not membership): a
  not-found error means it is deleted; an ownership error names the owning organization, so confirm that organization
  through ORG_WORKSPACE_GATE and request again there. Do not use `list_workspaces` for this — it lists only workspaces you
  already belong to.
- Organization or project authorization denial: do not retry the same call unchanged or with a guessed identifier; follow
  MCP_ACCESS_GATE (denied call with `org_idx`).
- API error, or the session expired during the call: the request may have been filed. Do not retry automatically; with
  fresh WRITE_APPROVAL (say that nothing changed), calling again cannot file a duplicate — the server blocks it while a request is pending, and that
  block confirms the first request went through.

## Recommended Chain

```text
list_organizations → list_workspaces → no access to the target workspace
→ WRITE_APPROVAL → request_workspace_permission
→ report that it awaits approval + console_url
```
