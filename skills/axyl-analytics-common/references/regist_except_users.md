# regist_except_users (Register a User Excluded from Metrics)

Registers one `userId` or `deviceId` to exclude from a project's metric calculation. The exclusion applies
retroactively to data from before the registration as well.

> **Prerequisite:** Follow SETTING_ADMIN_GATE and WRITE_APPROVAL in [`../SKILL.md`](../SKILL.md).

## When to Use

- To keep internal test, QA, and ETL sample identifiers from polluting real metrics
- Always call it after checking for duplicates with `list_except_users`

## Parameters

| Parameter | Required | Description |
|---------|------|------|
| `title` | Y | A name identifying the purpose of the registration. For example, `ETL sample 2026-09-04` |
| `project_id` | Y | A list of `list_projects.appid_group` values. Not a list of AppIDs |
| `user_type` | Y | `userId` or `deviceId` |
| `user_id` | Y | One identifier value matching `user_type` |
| `company_cd` | Y | Company code confirmed from `list_projects` |
| `org_idx` | Y | Organization idx confirmed through SETTING_ACCESS_GATE, with write permission verified through SETTING_ADMIN_GATE |

The parameter is named `user_id`, but pass a device ID value when `user_type="deviceId"`.

## Return Value

Returns the registration name, the project list, the identifier type and value, and the save result. The identifier comes
from the user (for example, QA test accounts); confirm each one. Only when excluding an ETL sample, use the test identifier
returned by `run_etl_simulation(org_idx, dry_run=true)`, called with a confirmed project and a verified `org_idx`.

## Decision Rules

- This tool does not itself prevent duplicate registrations. Use `list_except_users` before and after the call.
- Register only one identifier per call. Several identifiers require a separate call each; you may present them together
  for a **batch approval**.
- Registering either `userId` or `deviceId` excludes that user from every metric. For an ETL sample, register just the
  `userId` by default rather than both.
- Show the target project (the organization is used only for authorization), the identifier, and the retroactive
  exclusion impact, then obtain explicit approval.
- Do not retry a failed registration automatically. Query the current list again to check whether it took effect, then decide.

## On Failure

- Required-value or `user_type` validation error: recheck the correct type (`userId`/`deviceId`) and the single identifier.
- Administrator permission error: do not register; prepare the request information to pass to an Analytics administrator.
- Project access error: treat the `org_idx` as unverified and follow MCP_ACCESS_GATE (denied call with `org_idx`),
  resuming SETTING_ACCESS_GATE at step 3. Before calling again through another organization, recheck with
  `list_except_users` and obtain WRITE_APPROVAL again.
- API error: do not retry automatically — first check with `list_except_users` whether it actually took effect.

## Recommended Chain

```text
SETTING_ACCESS_GATE → list_except_users → no duplicate
→ SETTING_ADMIN_GATE → WRITE_APPROVAL → regist_except_users
→ confirm it took effect with list_except_users
```
