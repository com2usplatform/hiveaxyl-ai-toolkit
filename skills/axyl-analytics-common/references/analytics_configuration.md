# Analytics Configuration Gates

> **Prerequisite:** Read [`../SKILL.md`](../SKILL.md) first and follow its routing table for access and project context.

### SETTING_ACCESS_GATE

Before querying users excluded from metrics, metric start dates, or metric filters:

1. If an accessible `org_idx` has already been confirmed for the same `company_cd` and `appid_group` in the current
   conversation, reuse it.
2. Find the company and a candidate `appid_group` with `list_projects` (PROJECT_ID_GATE); do not confirm the project from
   it. It returns only companies where the user has MCP access in at least one organization, so a missing company may lack
   MCP access rather than not exist; follow MCP_ACCESS_GATE.
3. Call `list_organizations(company_cd, appid_group)` with the candidate. Omit `appid_group` only when no project is known
   yet. With the filter, an empty result follows PROJECT_ID_GATE's "No organization for the project".
4. Without a filter this call never returns an empty list. If it is denied, do not guess `org_idx`; report that the
   configuration cannot be queried and follow MCP_ACCESS_GATE. Until MCP access is granted in an organization of that
   company, even an Analytics administrator cannot call `regist_org`.
5. If there is exactly one organization, use it. If there are two or more, any of them authorizes the same per-project
   setting: use one and tell the user which (in the WRITE_APPROVAL summary for a write). This does not apply to
   `get_org_details`, which reads one specific organization. An `org_idx` chosen this way is verified only for Analytics
   configuration tools; for other tools apply the candidate rule again. `last_org_flag='Y'` is a display label
   ("last accessed") only, never a default.
6. Query the selected organization's projects with `list_projects(company_cd, org_idx)`, and confirm `appid_group`
   only from this result. If the target project is not in it, return to step 5. With several projects, confirm that each
   one is in this result.
7. Query the current configuration with the confirmed `org_idx`. Listing does not require Analytics administrator privileges.

- For configuration tools, use `list_projects.appid_group`, not AppID, as `project_id`.
- Use a `list_projects` result without `org_idx` only to find candidates, not as the basis for confirming the project.
- Excluded users, metric start dates, and metric filters apply **per project**: a registration made through any organization linked to the
  project affects that project, and listing shows registrations made through other organizations too. State this in the
  WRITE_APPROVAL summary. The `org_idx` is used for authorization, so even if one was used in another step, verify that it
  can access the target project.
- Configuration tools do not require `workspace_idx`; do not substitute ORG_WORKSPACE_GATE.

### SETTING_ADMIN_GATE

Before calling `regist_except_users`, `regist_start_dates`, `regist_metric_filter`, `regist_currency`, `get_org_details`,
or `regist_org`:

1. Reuse the `company_cd`, `org_idx`, and `appid_group` confirmed through SETTING_ACCESS_GATE, passing only the
   identifiers each tool takes:
   - `regist_except_users`, `regist_start_dates`, `regist_metric_filter`: `company_cd`, `org_idx`, and the confirmed
     `appid_group` passed as `project_id` (a list for except users and metric filters, a string for start dates).
   - `get_org_details`: `company_cd` and the `org_idx`, returned by `list_organizations`, of the organization the user
     asked about (with several candidates, have the user choose); no `appid_group`.
   - `regist_currency`: only `company_cd`.
   - `regist_org`: `company_cd`, plus `appid_groups` confirmed with the user from `list_projects(company_cd)`. It needs no
     existing `org_idx`, so skip organization selection (PROJECT_ID_GATE, company-level).
2. Verify that `check_analytics_admin(company_cd)` returns `true`.
3. If the user is not an administrator, do not call these tools. Provide the current configuration query result
   and the request details to send to an Analytics administrator.
4. If the user is an administrator and the tool writes (every tool above except `get_org_details`), present the current
   value, the new value, and the scope of impact, then obtain WRITE_APPROVAL. `get_org_details` is a read and needs no
   WRITE_APPROVAL.

These six are the only tools the server rejects for non-administrators. Other writes — `create_metric`/`update_metric`,
`regist_event`/`regist_event_dimension`/`update_event`, content, dashboards, and segments — do not require administrator
status, but they must still pass their ordinary company or organization permission and MCP_ACCESS_GATE.

Administrator status determines only whether configuration can be written. Do not skip `list_except_users` or
`list_start_dates` queries merely because the user is not an administrator.
