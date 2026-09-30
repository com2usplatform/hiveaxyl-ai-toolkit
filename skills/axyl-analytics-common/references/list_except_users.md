# list_except_users (List Users Excluded from Metrics)

Lists the users registered as excluded from metrics for an organization. Both past and current data for a registered
identifier are excluded retroactively from metric calculation; the raw logs are not deleted.

> **Prerequisite:** Follow PROJECT_ID_GATE and SETTING_ACCESS_GATE in [`../SKILL.md`](../SKILL.md).

## When to Use

- To check whether the same identifier is already registered before calling `regist_except_users`
- To confirm that the configuration took effect after registration
- To check a test identifier's metric-exclusion status before sending an ETL sample

## Parameters

| Parameter | Required | Description |
|---------|------|------|
| `company_cd` | Y | Company code confirmed from `list_projects` |
| `org_idx` | Y | Accessible organization idx confirmed through SETTING_ACCESS_GATE |

Anyone with access to that organization can call this, even without Analytics administrator privileges. Only an administrator can register.

## Return Value

Returns the registration ID, the name, the company and project scope, and the identifier type and value.

- `project_id` is `list_projects.appid_group`, not an AppID.
- Deleted registrations are not returned.
- A registration covering several projects at once is returned as one row per project.

## Decision Rules

- For duplicates, check whether the target `project_id`, `user_type`, and `user_id` all match.
- Registering either `userId` or `deviceId` as excluded excludes that user from every metric, so there is no need to register both identifiers from the same ETL sample.
- If the same test identifier is already registered, do not call `regist_except_users` again.
- Listing is not a write and does not require administrator privileges.

## On Failure

- Organization access error: recheck the company, organization, and project relationship through SETTING_ACCESS_GATE.
- Empty result: read it as "no excluded users are registered," but distinguish it from a query failure.
- API error: report the server message and do not guess whether the registration exists.

## Recommended Chain

```text
SETTING_ACCESS_GATE
→ list_except_users
→ no duplicate
→ SETTING_ADMIN_GATE
→ present the change and obtain WRITE_APPROVAL
→ regist_except_users
→ confirm it took effect with list_except_users
```
