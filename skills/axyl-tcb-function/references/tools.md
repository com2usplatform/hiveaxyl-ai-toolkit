# TCB Tools — Parameters, Responses, Errors

> **Prerequisite:** Follow the rules in [`../SKILL.md`](../SKILL.md) and, for every Console tool, the gates in [axyl-console-access](../../axyl-console-access/SKILL.md). The tool descriptions returned by the `hive-axyl` MCP server are authoritative; if they differ from this file, follow the server.

## Availability

- `start_tcb_workflow` and the document tools need no Console-login (OAuth bridge) session, company selection, or menu permission. The authentication of the MCP connection itself is enough.
- The four Console TCB settings tools need a Console-login (OAuth bridge) session. In both cases below, function development can still proceed:
  - The tools are missing from the tool list: this server runs without Console control. Tell the user that the Console TCB settings cannot be reached through this server.
  - A call returns `console control requires a console-login (OAuth) session`: follow its `guidance`. Ask the user to reconnect the MCP server with the browser Console login (LOGIN_GATE in axyl-console-access), then retry.
- No MCP tool builds, deploys, or invokes a function. Those steps run in the user's local project with the commands from the documents.

## `start_tcb_workflow`

| Argument | Required | Notes |
|---|---|---|
| `goal` | yes | What the user wants to build, in their words. Echoed back. |
| `stage` | no | `bootstrap`, `develop`, `deploy`, `test`, or `wrap-up`. Case-insensitive. Omit for the overview. |

- Response: `goal`, `stages` (stage → document id), `documentId`, `title`, `lastUpdated`, `content` (full markdown). With `stage`, the response also carries `stage` and a `note` that points back to the overview.
- Unknown stage: `error` with `validStages`. Call again with a valid stage.
- Document not loaded: `error` with a `hint` naming the `list_docs` and `get_*` calls that find it instead. Follow the hint; it is a server-side issue, not a request problem.
- Read-only and idempotent, so call it again freely when entering each stage.

## Console prerequisites

Follow the gate order of axyl-console-access: company first, then menu. The menu check is evaluated for the selected company; until one is selected, the first company is used by default and may carry no permissions.

| Step | Tool | Notes |
|---|---|---|
| 1. Company | `list_my_companies`, then `select_company(companyName)` | Required when the account belongs to several companies. Ask the user which one. |
| 2. Menu and action check | `check_console_menu_access(menu='tcb-settings')` | Returns `accessible` and `actionPermission`. `Edit` is needed for reveal and update. An empty list means view-only. |
| 3. Project key | `list_axyl_projects(menu='tcb-settings')` | Scopes the list by the TCB settings permission, which can differ from project-settings. Use `projectIndex` only in tool calls; show the user `projectId`. |

## Console TCB settings tools

All four require the `tcb-settings` menu. All four take `projectIndex` (a positive number, required); a missing or non-positive value is rejected with a hint to call `list_axyl_projects` first.

| Tool | Extra arguments | Permission | Result |
|---|---|---|---|
| `get_axyl_tcb_credential` | none | menu | `registered`, `secretId` (plain), `secretKey` (always masked), `note`. Nothing stored: `registered=false`. This is a normal state, not an error. |
| `list_axyl_tcb_console_logs` | `page` (1-based, default 1), `size` (1-100, default 20) | menu | `list` of `{seq, logType, log[{column, beforeData, afterData}], createdAt}`, newest first, plus `count`, `page`, `size`, and totals when known. Secret Key values are masked and operator identifiers are omitted. An empty list carries a `note`; it is a normal result. |
| `get_axyl_tcb_secret_key_suffix` | none | menu + `Edit` | `secretKey` shows only the last 4 characters (shorter keys show the mask only). The full value is never returned. Nothing stored: `registered=false`. Call only when the user explicitly asks to identify the key. |
| `update_axyl_tcb_secret_id` | `secretId` (required, the API ID, never the Secret Key) | menu + `Edit` | Write. Updates only the API ID and leaves the Secret Key unchanged. Returns the masked credential with `updated: true`. |

### `update_axyl_tcb_secret_id` sequence

1. Read the current value with `get_axyl_tcb_credential`. If `registered=false`, stop: the first registration needs the Secret Key and happens on the Console TCB settings screen. Ask before directing the user there.
2. WRITE_CONFIRM: show the project (`projectId`) and the API ID change (current → new), then get explicit approval.
3. Call the tool.
4. POST_WRITE_VERIFY: read again with `get_axyl_tcb_credential` and report the resulting API ID.

Never place a Secret Key in `secretId`. If the user offers a value that looks like a key, do not send it. Ask whether they meant the API ID, and keep the Secret Key on the Console screen.

## TCB-specific errors

Errors carry a top-level `error` (`isError: true`) plus `hint` or `guidance`. Generic cases (session, company, menu, `action_denied`, `reason` codes such as `downstream_unavailable` and `outcome_unknown`) follow the table in [axyl-console-access](../../axyl-console-access/SKILL.md).

| Response | Meaning | Action |
|---|---|---|
| `... denied — the account lacks the required action permission` | The Console API refused the action (`no_action_permission`). | Do not retry. Ask the user to request the permission from a Console owner. |
| `... rejected — unknown or unauthorized projectIndex` | Wrong project, or the project is outside the permitted scope or company. | Re-list with `list_axyl_projects(menu='tcb-settings')` or switch company with `select_company`. |
| `... rejected — no TCB credential stored for this project yet` | Update attempted before the first registration (`not_found`). | The Secret Key must be registered on the Console TCB settings screen first. Ask permission before directing the user there, then use the update tool. |
| `secretId is required` | Empty API ID. | Ask the user for the API ID, never the Secret Key. |
| `... failed (<status>)` | Other TCB Console API error. | Retry later. If it persists, report it without guessing the cause. |
| `reason: outcome_unknown` after the update | The change may already be applied. | Re-read with `get_axyl_tcb_credential`. Retry only if the new API ID is absent, after WRITE_CONFIRM again. |

## Console screen name

The tools name the screen with its Console menu label, for example `TCB Connector > TCB 설정` in the Korean Console. Repeat the label exactly as the tool returns it.
