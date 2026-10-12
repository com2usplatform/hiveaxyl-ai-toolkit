# Project and Workspace Context

> **Prerequisite:** Read [`../SKILL.md`](../SKILL.md) first and follow its routing table for access control.

### PROJECT_ID_GATE

```
Before every tool call that requires project_id:

Step 1. Does the current conversation contain a project_id verified for the current company and organization scope?
  └─ YES → Reuse it. Do not call list_projects again.
  └─ NO  → Find candidates with list_projects (pass company_cd if known, and name_keyword when the user named the game;
            no org_idx yet)
            → More than 5 candidates → show the first 5, ask for part of the game name, and call again
              with name_keyword (matches game_name, per-language names, and appid_group)
            → Two or more candidates → present them and wait for the user to choose
            → Candidate project_id (appid_group) + company_cd
            → Does the task use organization scope?
               ├─ NO  (company-level: events, metrics, regist_org's appid_groups) → Confirm the candidate with the user
               └─ YES (preview_*, content and dashboards, configuration, segments and users, query_adhoc,
                       run_etl_simulation, axyl-integrate-analytics-log; an AppID not yet registered in the Hive
                       console continues with company_cd only, as that skill says)
                       → list_organizations(company_cd, appid_group) → select organization by the candidate rule
                         (Analytics configuration tools: SETTING_ACCESS_GATE step 5)
                       → list_projects(company_cd, org_idx) → confirm project_id from that organization's results
                       → If the project is not in them, return to organization selection
```

- Do not guess or invent `project_id`.
- Reconfirm it if the project changes or the environment switches within the same conversation.
- In an organization-scope task, a project found by a `list_projects` call without `org_idx` (with or without
  `company_cd`) is only a candidate; confirm it from the `list_projects(company_cd, org_idx)` result after organization
  selection.
- Segment and user-group tools take these identifiers. Obtain `appid_group` and `game_name` from the **same row**
  of `list_projects(company_cd, org_idx)` for the confirmed organization. Do not guess `game_name` either.

  | Tool | `company_cd` | `org_idx` | `appid_group` | `game_name` |
  |---|---|---|---|---|
  | `list_segment_meta`, `list_segment_snapshots` | Y | Y | Y | — |
  | `simulate_segment`, `create_segment`, `regist_user_group` | Y | Y | Y | Y |
  | `create_segment_from_classification` | Y | Y | Y | — |
  | `create_segment_snapshot` | Y | Y | — (takes `segment_idx`) | — |
  | User investigation and classification reads (`check_user_exists`, `get_user_*`, `list_user_*`) | Y | Y | Y | — |

  `org_idx` comes from `list_organizations(company_cd, appid_group)`: use it when there is exactly one candidate,
  and otherwise show them all and let the user choose (`last_org_flag` is a label, never a default). If there is
  none, do not guess `org_idx`; follow **No organization for the project** below.

- **No organization for the project**: no organization the user can use through MCP is linked to this project. Do not guess
  `org_idx`. Ask the user to request from an Analytics administrator either a link from the project to one of their
  MCP-enabled organizations or MCP access in an organization already linked to it; a query without `appid_group`
  cannot tell which applies.

### ORG_WORKSPACE_GATE

```
Before calling a tool that requires org_idx/workspace_idx (preview_chart, preview_chart_rank, preview_funnel,
preview_retention, content and dashboard create_*/update_*, get_content, get_dashboard):

Step 1. Does the current conversation contain verified org_idx/workspace_idx values?
  └─ YES → Reuse them. Do not call the tools again. A workspace used only for preview_* is not confirmed
            for saving — have the user choose before saving.
  └─ Only org_idx is verified (for example, by PROJECT_ID_GATE) → Reuse it; call check_analytics_admin(company_cd) if not
     done yet, then list_workspaces(company_cd, org_idx)
  └─ NO  → Call check_analytics_admin(company_cd)
            → Call list_organizations(company_cd, appid_group) → list_projects(company_cd, org_idx) (confirm the
              project) → list_workspaces(company_cd, org_idx) in that order. **Pass appid_group for administrators too** — the filter answers
              "which organizations can use this project", and the answer does not change with
              administrator status
            → If exactly one candidate exists, use it; if there are two or more, present them ALL and wait
              for the user to choose (workspaces for preview_* only: see the bullet below); if there is none, do not guess — no organization: follow PROJECT_ID_GATE's
              "No organization for the project"; no workspace: follow list_workspaces' empty-result rule
            → last_org_flag='Y' / last_flag='Y' is a display hint only — label that entry "last accessed"
              and never treat it as a default or an automatic selection
            → Record the confirmed org_idx + workspace_idx
```

- Do not guess or invent `org_idx`/`workspace_idx` (for example, `0`).
- For `preview_*` only (nothing is saved), the workspace is used only for authorization: if there are several, use any
  returned workspace and tell the user which. Have the user choose before saving.
- Calls with unverified org_idx/workspace_idx values cause authorization errors for the organization's project access
  or for workspace access.
- Check in this order: `list_projects` (candidate) → `check_analytics_admin` → `list_organizations(company_cd, appid_group)` →
  `list_projects(company_cd, org_idx)` (confirm the project) → `list_workspaces`. When PROJECT_ID_GATE already ran
  `list_organizations`, `check_analytics_admin` may come after it. Steps already done in the same
  conversation, such as an `org_idx` confirmed by PROJECT_ID_GATE, are reused, not repeated.
- Regardless of administrator status, the `list_organizations`/`list_workspaces` calls themselves cannot be skipped,
  because content is created at the org_idx/workspace_idx location where it actually exists.
- **An organization that is not linked to the project is rejected even for administrators.** Administrators
  bypass organization/workspace membership, but not the organization-to-project scope — `preview_*` and
  `create_*` alike verify it. Choosing an organization without the `appid_group` filter can therefore fail
  on the very next call.
