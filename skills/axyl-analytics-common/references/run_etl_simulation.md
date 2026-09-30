# run_etl_simulation (Send a Custom Event Sample and Verify Ingestion)

Generates a sample send payload for a custom event and, after approval, sends it over the HTTP receiving path to verify
ingestion into the Analytics system. The implementation approach generated in the game remains SDK sending; this tool's
HTTP call is used for verification only.

> **Prerequisite:** Follow PROJECT_ID_GATE in [`../SKILL.md`](../SKILL.md), confirm an `org_idx` that can access the
> target project, and then finalize the event specification in `axyl-integrate-analytics-log`. `dry_run=false`
> requires a separate **WRITE_APPROVAL**.

## When to Use

- Use it to verify a custom event's flat payload contract and whether it is actually ingested.
- Generate the final payload and the test identifiers first with `dry_run=true`.
- Do not use it to verify compilation or runtime calls in the game client's SDK code.

## Parameters

| Name | Required | Description |
|------|------|------|
| `app_id` | Y | The real AppID confirmed from `list_projects` and the game repository |
| `org_idx` | Y | An organization idx that can access the target project. Confirm it from `list_organizations(company_cd, appid_group)` |
| `event_name` | Y | The real event name confirmed from the event definition or the approved custom design |
| `event_attribute` | Y | A flat dict holding the defined event properties plus the diagnostic `guid` from axyl-integrate-analytics-log. Only string and numeric scalars are allowed |
| `user_id` | Conditional | For an actual send, the test-only userId from the `dry_run` result |
| `device_id` | Conditional | For an actual send, the test-only deviceId from the `dry_run` result |
| `event_time` | Conditional | For an actual send, the RFC 3339 eventTime from the `dry_run` result |
| `dry_run` | N | Default `true`. `false` performs an actual send |
| `max_retries` | N | Number of ingestion-check retries. 1–5, default 3 |
| `retry_interval_sec` | N | Wait between retries, in seconds. 1–30, default 10 |
| `confirmation_token` | Conditional | Required for an actual send. The short-lived, single-use token returned by the identical dry-run |

Do not put required properties or reserved words in `event_attribute`. In axyl-integrate-analytics-log you may add the UUID
string `guid` as a common diagnostic property. Objects, arrays, booleans, and nulls are not allowed.
There may be at most 100 properties, and the final payload must not exceed 64 KiB in UTF-8.

## Return Value

- `dry_run=true`: returns `dry_run`, the confirmed `company_cd`/`appid_group`, the `payload` that would be sent, the actual
  target `endpoint`, and a short-lived, single-use `confirmation_token`.
- `dry_run=false`: returns the fields above plus the send response `send_response` and the ingestion-check row `row`.
- `row=null` means ingestion could not be confirmed within the retry window; it does not confirm that the send failed.

## Decision Rules

1. Call with `dry_run=true`, using an `org_idx` that can access the project confirmed through PROJECT_ID_GATE and the real `app_id`.
   The server looks up `company_cd`/`appid_group` from `app_id` and verifies that organization's access to the project.
2. If you generate several samples, pass the first payload's `userId` and `deviceId` into the later dry-runs as well so the
   test identifiers stay unified.
3. Show the user the returned `payload` and the risk of contaminating real metrics, and have them choose one of the following.
   - Released and live: register one test `userId` or `deviceId` as a user excluded from metrics
   - Pre-launch: register the actual metric start date confirmed with the user
   - Proceed without a configuration change
4. Any user with access can query the current configuration. An administrator registers and re-queries after obtaining a separate
   WRITE_APPROVAL; a non-administrator prepares the metric-exclusion CSV (only after the user agrees to its content and path) or the start-date
   request information to pass to an Analytics administrator.
5. Show the user the final payload, the configuration result, and any remaining contamination risk, and obtain separate approval for the sample send.
6. Once the user approves, pass the payload's `userId`, `deviceId`, and `eventTime` through as `user_id`, `device_id`, and
   `event_time` respectively. Keep `event_attribute` identical to the dry-run input, including the diagnostic `guid`, and
   pass the dry-run's `confirmation_token` along with the call at `dry_run=false`.
7. Report `send_response` and `row` separately. `row=null` means ingestion could not be confirmed within the retry window;
   do not immediately conclude that the send failed.

The configuration change procedure follows `list_except_users`,
`regist_except_users`, `list_start_dates`, and
`regist_start_dates`.

A metric exclusion applies retroactively to past data as well, and registering either `userId` or `deviceId` excludes the user
from every metric. By default, register just the `userId`. The start date is the actual launch or aggregation start time, not the
sample's timestamp, and because it affects the project's entire metric scope, propose it only for a pre-launch project.

A non-administrator can list users excluded from metrics and metric start dates but cannot register or change them. If a metric
exclusion is needed, build the file for the administrator to upload using the
[CSV template](../../axyl-integrate-analytics-log/assets/exclude_user_template.csv) and
[`create_exclude_user_csv.py`](../../axyl-integrate-analytics-log/scripts/create_exclude_user_csv.py). Create the file only after the user
agrees to its content and path; the file format, the consent step, and the generation command follow that skill's
documentation (sample_validation.md).

By default, hold off on the actual sample send until the administrator's change is confirmed; proceed only when the user has
acknowledged the remaining contamination risk and explicitly approved.

`dry_run` builds a flat payload containing the following required properties.

| Property | Generation Rule |
|------|-----------|
| `userId` | A test value built from the `user_` prefix and a unique UUID |
| `deviceId` | A test value built from the `device_` prefix and the same UUID as userId |
| `identifierProvider` | Fixed to `hive` |
| `appId` | The real AppID used in the call |
| `eventTime` | The current RFC 3339 time, including the time zone |
| `eventName` | The real event name used in the call |

### Scope of Verification

Because this tool uses the HTTP receiving path rather than going through the SDK, it verifies only the parsing and ingestion
contract of the flat payload. It does not verify the game code's compilation, call sites, or runtime behavior, nor the SDK's
automatically collected properties. The ingested data's `dataSource` is also the HTTP path value, so do not use it to verify
`custom_sdk` or `axyl_custom_sdk`.

## On Failure

- Payload validation error: fix the event name, the property names and value types, and the property count and size, then start again from the dry-run.
- Invalid AppID: reconfirm the real AppID from PROJECT_ID_GATE and the game repository configuration.
- Organization or project authorization error: reconfirm an `org_idx` that can access the target project. Do not arbitrarily
  use another organization's value or work around it with company permissions alone.
- Test identifier or time error: use the `userId`, `deviceId`, and `eventTime` returned by that same dry-run, exactly as given.
- Send error: report the server response and do not retry automatically.
- `row=null`: do not conclude that the send failed — recheck shortly afterwards with `query_adhoc` within the scope whose permissions are confirmed.

## Recommended Chain

```text
PROJECT_ID_GATE → confirm an org_idx that can access the project → finalize the event specification
→ run_etl_simulation(org_idx, dry_run=true)
→ choose and apply the metric-contamination prevention approach → present the payload and disclose the risk → WRITE_APPROVAL
→ run_etl_simulation(org_idx, dry_run=false, confirmation_token=<value returned by the dry-run>) → query_adhoc if needed
```
