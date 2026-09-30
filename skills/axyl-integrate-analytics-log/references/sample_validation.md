# Sample Send Verification

This document defines the procedure for verifying the send contract with `run_etl_simulation` after the code review, and for
preventing the sample data from contaminating metrics. This tool uses the HTTP receiving path and does not verify the game SDK's
actual execution.

## 1. Dry-run

1. Confirm an `org_idx` that can access the target project through PROJECT_ID_GATE, and build the final sample payload with
   `run_etl_simulation(org_idx, dry_run=true)`. The server checks the real `app_id`'s `appid_group`, so company permissions alone
   cannot send to another project.
2. If there are several samples or several AppIDs, reuse the first dry-run's `userId` and `deviceId` in the later calls.
3. Put the event definition's properties and the diagnostic `guid` in `event_attribute`. Do not duplicate required properties or reserved words.
4. Generate the `guid` as a test UUID string once and use the same one for both the dry-run and the actual send.

The sample payload's required properties follow these rules.

| Property | Sample value rule |
|------|-------------|
| userId | A test value the tool generates from the `user_` prefix and a unique UUID |
| deviceId | A test value the tool generates from the `device_` prefix and the same UUID as userId |
| identifierProvider | Fixed to `hive` |
| appId | The real AppID confirmed in the organization and project context. No dummies or placeholders |
| eventTime | The current time the tool generates in RFC 3339, including the time zone |
| eventName | The real event name to verify. No dummies or placeholders |

## 2. Preventing sample metric contamination

After obtaining the dry-run's test identifiers, query the current configuration with `list_except_users` and `list_start_dates`.
Query them regardless of administrator status, and first report whether the test identifier or the target project is already protected.

Present the following options before the actual send.

1. A released, live project: register the test identifier as a user excluded from metrics
2. A pre-launch project: register the actual metric aggregation start date
3. Proceed without a configuration change

If the user has not stated the project's status, do not guess whether it has launched.

### Users excluded from metrics

- First check whether the same project and identifier are already registered.
- Registering either `userId` or `deviceId` excludes the user from every metric, so by default propose just the test `userId`.
- Use `appid_group`, not the AppID, for the project value in the configuration.
- An administrator shows the retroactive impact and the value to register, obtains separate approval, and then calls `regist_except_users`.
- After registering, confirm it took effect with `list_except_users`. Do not retry automatically.
- A non-administrator can hand an administrator an exclusion CSV made with this skill's generation script and CSV template
  (`scripts/create_exclude_user_csv.py`, `assets/exclude_user_template.csv`).
  **Ask first:** show the test identifier to be written and the output path, and create the file only after the user agrees.
  Without agreement, give the same values in the reply for the user to pass on. Do not use an existing file or real user identifiers.
- The default path is `docs/analytics/exclude_users_<timestamp>.csv`, but it is a hand-off file, not part of the code change:
  tell the user not to commit it (add it to `.gitignore` or delete it after handing it over), and offer another path under
  the working directory if they prefer.
- Run the script from the client repository root. It allows only `.csv` output below the current working directory, never
  overwrites an existing file or symlink, and rejects spreadsheet-formula prefixes and control characters.

By default, a non-administrator holds the actual sample send until an administrator's change is confirmed. It can proceed if the
user understands the remaining contamination risk and approves separately; note that an exclusion setting applies retroactively
even if registered afterwards.

### Metric start date

- Propose this only for a pre-launch project. If it is released and live, point to users excluded from metrics instead.
- Do not use the current time or the sample send time as the start date.
- Have the actual launch or aggregation start time confirmed in `YYYY-MM-DDTHH:mm:ss` format in the organization's time zone.
- An administrator shows the existing value, the new value, and the project-wide metric impact, obtains separate approval, then
  calls `regist_start_dates` and re-queries.
- A non-administrator compiles the organization name, project name, `appid_group`, current value, requested start date, and time
  zone, and asks an administrator. Do not create a CSV for start-date registration.

## 3. The actual sample send

Show the final payload, the configuration result, and any remaining contamination risk, and obtain separate approval for a
`dry_run=false` send. Approval of a configuration change does not stand in for approval to send.

After approval, send only 1–2 samples. Reuse the dry-run's `userId`, `deviceId`, `eventTime`, `guid`, and `confirmation_token`
exactly as given, and pass the same `org_idx`. Do not display the token to the user, and if the payload, organization, project, or
environment changes, or the token expires, start again from the dry-run.
Report the results with these distinguished.

- The send API response
- Confirmation of normal ingestion
- The possibility of quarantine
- Ingestion lag or a verification failure
- The validity of the target dimensions

`run_etl_simulation` does not verify the SDK's auto-collected properties or the real SDK `dataSource`. The expected `dataSource` to
check with `query_adhoc` after an actual game SDK send is `custom_sdk` for v4 and `axyl_custom_sdk` for Axyl. If there is no row,
do not conclude failure immediately — distinguish the send response, the possibility of quarantine, and ingestion lag.

Do not judge whether AUTO events and the SDK's auto-collected properties are actually collected from this HTTP sample result.
Record a confirmed status only when `query_adhoc` was queried against the actual game client's execution time and AppID.

For real SDK logs, query by AppID and eventName over a narrow time range, then match the returned rows'
`eventAttributes.guid` against the guid in the client log. `query_adhoc.filters` supports only top-level columns, so do not put
the guid directly in the filters.

## 4. When no send is made

The verification step can end even if the user does not approve the actual send or it cannot be performed due to permission or
environment problems. Record `not performed` with the reason, the scope of the static verification, and the remaining actual SDK
verification items in the result document.
