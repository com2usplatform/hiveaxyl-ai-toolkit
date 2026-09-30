# Organization and Project Context

This document defines the procedure for confirming the company, organization, project, and AppID needed for actual-ingestion
duplicate checks, sample sends, or Analytics configuration queries. It does not apply to requests that need no analytics data
access, such as a static code review.

## 1. Confirm the company and administrator status

1. If the same conversation has no verified `company_cd`, call `list_projects()` for the purpose of identifying the company.
2. Narrow to the company by the row whose `app_id_list[]` matches the AppID confirmed in the repository. Do not finalize the
   project from this query result.
3. If more than one company remains, do not proceed until the user confirms.
4. Call `check_analytics_admin(company_cd)`.

Administrator status does not change how organizations are queried — everyone passes the `appid_group` filter, since an
organization not linked to the project is rejected even for an administrator.
Registering or changing configuration additionally requires `SETTING_ADMIN_GATE` and approval.

## 2. Confirm the organization and project

1. Call `list_organizations(company_cd, appid_group)` using the `appid_group` confirmed in the
   company-identification query. **Pass the filter for administrators too** — an organization that is not linked
   to the project is rejected regardless of administrator status.
2. If there is no organization, do not guess `org_idx` — stop.
3. If there is exactly one organization, use it. If there are several, show the organization names and `last_org_flag` and have
   the user choose. Do not auto-select the most recently accessed organization.
4. Call `list_projects(company_cd, org_idx)` again with the selected organization.
5. Finalize `appid_group` and `app_id_list[]` only from this org-scoped result.
6. If the repository's AppID is not in the selected organization's projects, check the other organizations. Do not keep going on
   the basis of the initial query made without organization scope.

Reuse the confirmed `company_cd`, `org_idx`, `appid_group`, AppID list, and administrator status in the later steps for as long as
the target does not change.

## 3. Duplicate checks per AppID

- Always pass the confirmed `org_idx` and `appid_groups`, and for a single AppID use `query_adhoc`'s
  `filters={"appId":"<app-id>"}`.
- For several AppIDs, pass the confirmed list as `app_ids=["<app-id-1>", "<app-id-2>"]` and query them in one call.
  That mode returns one latest row per AppID, so do not repeat individual calls per AppID.
- Group the results by AppID. If it is collected on only some AppIDs, mark it as partially collected.
- If an AppID is not in the org-scoped projects, or the query fails, do not estimate the value — report the status as `unconfirmed`.

## 4. Configuration access

When querying users excluded from metrics or metric start dates, recheck that the organization and project confirmed above are the
same as the configuration target. Anyone can list them, even without administrator privileges. Perform registration or changes only
after rechecking administrator status and obtaining separate approval.
