# list_projects (List Accessible Projects)

> **Prerequisite:** Follow the common rules in [`../SKILL.md`](../SKILL.md). This is the entry point for PROJECT_ID_GATE.

## When to Use

- When you do not know `project_id` (`appid_group`) and are identifying the project for the first time.
- When the user mentioned a game name but `appid_group` is unclear.
- To query the selected organization's projects in tasks where the organization controls project access scope.
- **Do not call it** if the same conversation already has an `appid_group` verified for the same company and organization.

## Parameters

| Parameter | Required | Description |
|---------|------|------|
| `company_cd` | N | Company code. If omitted, returns projects only from companies where the user has at least one MCP-enabled organization |
| `org_idx` | N | Organization idx (the idx from `list_organizations`). Specify it together with `company_cd`; returns only the projects that organization controls. Passing it without `company_cd` is rejected with an error |
| `name_keyword` | N | Case-insensitive partial match over `game_name`, the per-language names (`ko`/`en`/`ja`/`zn`), and `appid_group`. No filtering if omitted |

- You may call it with no arguments when the goal is to identify the company, but do not make the final project selection from that result.
- In tasks where the organization controls projects, specify `company_cd` + `org_idx` together regardless of administrator status.

## Return Value

Returns one row per project with the company code, the project ID (`appid_group`), the game name and its
per-language names, and the list of member AppIDs.

- `company_cd`: the company number in the Hive console. Required for most later tool calls.
- `appid_group`: the Hive Analytics project ID (`gameId`). Use it as is for the `project` parameter of `preview_chart` and similar tools.
- Display `game_name` first; if it is empty, fall back to the `ko`/`en`/`ja`/`zn` value matching the user's language.
- `app_id_list[]`: the list of **appIds** belonging to the project. An `appId` is issued per OS and per market, so one project can have several.
  - `app_id_list` is an **array nested inside the project row**. Rows do not multiply per appId, so PROJECT_ID_GATE's project-candidate selection logic works unchanged.

## Decision Rules

- For tasks that need organization scope, the order is `find candidates → list_organizations(company_cd, appid_group) →
  select organization → list_projects(company_cd, org_idx) → confirm project`.
- A result fetched without `org_idx` (with or without `company_cd`) is not organization-scoped. Use it only to identify the
  company and narrow candidates; do not confirm a project before rechecking it in the scoped query.
- Pass `name_keyword` on the first call when the user named the game.
- The result can be large. If there are more than 5 candidates, show the first 5 and ask the user for part of the game name,
  then call again with that text as `name_keyword` to narrow the candidates. The result is sorted by name only; do not use
  the order as a basis for selection.
- If a `name_keyword` query returns nothing, change or drop the keyword and query again.
- If the name is ambiguous or there are several candidates, show the list and let the user choose.
- Note the confirmed `appid_group` together with `company_cd`. Most later tool calls need `company_cd`.
- Do not guess or invent `appid_group`.

## On Failure

- Permission denial: do not ask the user to sign in again or retry. Follow MCP_ACCESS_GATE: denied call with `org_idx` if one
  was passed, otherwise denied call without `org_idx`.
- Empty result: no project matches the current conditions.
  - Without `org_idx`: a company appears only if the user has MCP access in one of its organizations, so a missing game can
    also mean no MCP access. Present that cause alongside "not found" (MCP_ACCESS_GATE).
  - With `org_idx`: this organization cannot use the project. Rerun `list_organizations(company_cd, appid_group)` and follow
    PROJECT_ID_GATE ("No organization for the project" when none is returned); do not fall back to the unscoped list.

## Recommended Chain

```
[Ordinary metric]  list_projects → list_metrics → (ORG_WORKSPACE_GATE) → preview_chart
[Revenue metric]   list_projects → list_metrics + list_currencies → (ORG_WORKSPACE_GATE) → preview_chart
[Event mode]       list_projects → list_events → list_dimensions → (ORG_WORKSPACE_GATE) → preview_chart
```

`preview_*` (including `preview_chart_rank`), content and dashboard `create_*`/`update_*`, `get_content`, and `get_dashboard` need `org_idx`/`workspace_idx` in addition to `project` (appid_group). See ORG_WORKSPACE_GATE.
