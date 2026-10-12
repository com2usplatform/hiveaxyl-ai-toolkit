# Organization and Project Context

This document defines the procedure for confirming the company, organization, project, and AppID needed for actual-ingestion
duplicate checks, sample sends, or Analytics configuration queries. It does not apply to requests that need no analytics data
access, such as a static code review.

## 1. Confirm the company and administrator status

1. If the same conversation has no verified `company_cd` or candidate `appid_group`, call `list_projects()` for the purpose of identifying the company.
2. Narrow to the company by the row whose `app_id_list[]` matches the AppID confirmed in the repository. Do not finalize the
   project from this query result. `list_projects()` returns only companies where the user has an MCP-enabled organization,
   so if no row matches, do not conclude that the project does not exist and do not pick a single cause. Show the possible
   causes and ask the user which applies: the user has no MCP access in an organization of that company (ask an Analytics
   administrator to allow it in the organization settings), the user lacks permission for that Hive company (obtain company
   permission first), or the AppID is not registered in the Hive console yet (register the AppID in the Hive console first).
   If the user confirms the AppID is not registered yet, do not stop the integration:
   - Confirm `company_cd` with the user (when `list_projects()` shows a single company, confirm that one).
   - Continue with the SDK, event recommendation, and code steps that need only `company_cd`.
   - Tell the user that ingestion checks and the sample send cannot be done until the AppID is registered in the Hive
     console; record them as `not performed` with that reason.
3. If more than one company remains, do not proceed until the user confirms.
4. Call `check_analytics_admin(company_cd)`.

Administrator status does not change how organizations are queried — everyone passes the `appid_group` filter, since an
organization not linked to the project is rejected even for an administrator.
Registering or changing configuration additionally requires `SETTING_ADMIN_GATE` and approval.

## 2. Confirm the organization and project

1. Call `list_organizations(company_cd, appid_group)` using the candidate `appid_group` from the
   company-identification query. **Pass the filter for administrators too** — an organization that is not linked
   to the project is rejected regardless of administrator status.
2. If there is no organization, do not guess `org_idx`. Stop the organization-scoped steps (ingestion checks, sample send,
   configuration) and continue the steps that need only `company_cd`, recording the others as `not performed`. No organization the user can use through MCP is linked to
   this project. Ask the user to request from an Analytics administrator either a link from the project to one of their
   MCP-enabled organizations or MCP access in an organization already linked to it; a query without `appid_group` cannot
   tell which applies.
3. If there is exactly one organization, use it. If there are several, show the organization names, mark the last-accessed
   one as "last accessed", and have the user choose (configuration only: SETTING_ACCESS_GATE step 5). Do not auto-select it.
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
same as the configuration target. Non-administrators can list them too, though organization access and MCP access still apply. Perform registration or changes only
after rechecking administrator status and obtaining separate approval.
