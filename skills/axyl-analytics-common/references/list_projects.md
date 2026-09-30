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
| `company_cd` | N | Company code. If omitted, returns projects from **every company** the user can access |
| `org_idx` | N | Organization idx (the idx from `list_organizations`). Specify it together with `company_cd`; returns only the projects that organization controls |

- You may call it with no arguments when the goal is to identify the company, but do not make the final project selection from that result.
- In tasks where the organization controls projects, specify `company_cd` + `org_idx` together regardless of administrator status.

## Return Value

Returns one row per project with the company code, the project ID (`appid_group`), the game name and its
per-language names, and the list of member AppIDs.

- `company_cd`: the company number in the Hive console. Required for every subsequent tool call.
- `appid_group`: the Hive Analytics project ID (`gameId`). Use it as is for the `project` parameter of `preview_chart` and similar tools.
- Display `game_name` first; if it is empty, fall back to the `ko`/`en`/`ja`/`zn` value matching the user's language.
- `app_id_list[]`: the list of **appIds** belonging to the project. An `appId` is issued per OS and per market, so one project can have several.
  - `app_id_list` is an **array nested inside the project row**. Rows do not multiply per appId, so PROJECT_ID_GATE's project-candidate selection logic works unchanged.

## Decision Rules

- For tasks that need organization scope, the order is `confirm company → list_organizations(company_cd) → select organization →
  list_projects(company_cd, org_idx) → select project`.
- Use a result fetched without organization scope (because `company_cd` was unknown) only to identify the company and narrow
  candidates. Even if the same project appears, do not confirm it before rechecking it in the scoped query after organization selection.
- The result can be large. Narrow the candidates with a keyword search over `game_name`/`ko`/`en` and then confirm with the user.
- If the name is ambiguous or there are several candidates, show the list and let the user choose.
- Note the confirmed `appid_group` together with `company_cd`. Subsequent tool calls need `company_cd`.
- Do not guess or invent `appid_group`.

## On Failure

- Empty result: check the account's permissions or authentication state. If you specified `org_idx`, that organization may have no project access, filtering everything out — query again without `org_idx` and compare.

## Recommended Chain

```
[Ordinary metric]  list_projects → list_metrics → (ORG_WORKSPACE_GATE) → preview_chart
[Revenue metric]   list_projects → list_metrics + list_currencies → (ORG_WORKSPACE_GATE) → preview_chart
[Event mode]       list_projects → list_events → list_dimensions → (ORG_WORKSPACE_GATE) → preview_chart
```

`preview_*` (including `preview_chart_rank`), content and dashboard `create_*`/`update_*`, `get_content`, and `get_dashboard` need `org_idx`/`workspace_idx` in addition to `project` (appid_group). See ORG_WORKSPACE_GATE, which starts with `check_analytics_admin`.
