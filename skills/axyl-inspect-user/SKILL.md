---
name: axyl-inspect-user
metadata:
  version: "1.0.0"
description: |
  Investigate one individual user's activity history and latest state. This covers CS inquiry checks,
  report verification, and confirmation of a specific user's purchases or logins. Identifying the user
  to investigate is also part of this skill's job.
  Follow the common rules of axyl-analytics-common as a prerequisite.

  TRIGGER when:
  - The user asks to check a specific user's activity, history, or state
  - Verifying "what this user actually did" based on a CS inquiry or report
  - Selecting and investigating one user matching a condition such as whale, dormant, or new

  DO NOT TRIGGER when:
  - Breaking a metric down by dimension (OS/country/market) → axyl-drill-down-metrics
  - Determining whether a metric is anomalous → axyl-detect-anomaly
  - The goal is to define and save a segment → axyl-create-segment
  - Dozens of users or more must be handled in a batch (this skill investigates one user at a time)
---

# axyl-inspect-user

> **CRITICAL — Read the common rules in [axyl-analytics-common](../axyl-analytics-common/SKILL.md) first.**
> **CRITICAL — Use only company_cd, org_idx, and appid_group values confirmed through PROJECT_ID_GATE and organization access validation.**
> **CRITICAL — Obtain the user ID only from the user or a USER_ID_GATE lookup result. Never guess or invent it (NO_GUESSING).**
> **CRITICAL — Call `check_user_exists` first in every investigation. If `exists=false`, do not interpret that as no activity; recheck the user ID and project.**
> **CRITICAL — User activity tracking is a raw log without metric aggregation rules. Do not present activity-history counts as metric values.**
> **CRITICAL — Creating segments, snapshots, or user groups is a write operation. Check existing assets first and do not create them without WRITE_APPROVAL.**

---

## Tools

- **User validation:** `check_user_exists`
- **Activity investigation:** `get_user_activity_summary` / `list_user_activities` / `get_user_recent_info`
- **Investigation target discovery:** `list_user_groups` / `get_user_group` / `preview_chart_rank`
- **Target group creation when needed:** `regist_user_group` — irreversible write requiring WRITE_APPROVAL
- **Metric-setting cross-check:** `list_except_users` / `list_metric_filters` / `list_start_dates`

For detailed arguments, returns, and permission scopes, follow the
[tool references in axyl-analytics-common](../axyl-analytics-common/SKILL.md).
`axyl-create-segment` handles any segment and snapshot creation required before `regist_user_group`.

## Reference Documents

- [Obtaining a user ID](references/user_id_sources.md) — the four USER_ID_GATE paths, actual calls, and candidate presentation format
- [Investigating activity history](references/activity_investigation.md) — narrowing from summary to detail and handling pagination
- [Cross-checking metric settings](references/cross_check_settings.md) — correcting conclusions when raw activity and aggregated metrics differ

---

## Workflow

### Prerequisite — Common Rules

PROJECT_ID_GATE, WRITE_APPROVAL, and NO_GUESSING from axyl-analytics-common apply. Pass the same confirmed
`company_cd`, `org_idx`, and `appid_group` values to every user-investigation tool. This workflow identifies
one user and verifies facts; distinguish it from chart or segment analysis that finds patterns across users.

### Phase 0 — Classify the Request

```
A. The user ID is known                         → user-supplied ID path in Phase 1
B. One user matching a condition must be found → existing-group or ranking path in Phase 1
C. The goal is a multi-user distribution/pattern → axyl-drill-down-metrics or axyl-detect-anomaly
D. The goal is to define or save a segment      → axyl-create-segment
```

Do not ask again when the investigation purpose and period are already available. If no period was provided,
narrow it using available context such as the inquiry or report time. Ask the user when there is no reasonable
basis for choosing a period.

### Phase 1 — Confirm the Project and Investigation Target

```
Step 1-1. PROJECT_ID_GATE
  → confirm company_cd / org_idx / appid_group in the same project scope

Step 1-2. USER_ID_GATE
  ├─ User supplied an ID        → use that value as given
  ├─ Existing condition group   → list_user_groups → get_user_group
  ├─ Arbitrary metric criterion → ORG_WORKSPACE_GATE (workspace_idx), then query candidates with the
  │                               userId dimension in preview_chart_rank
  └─ Existing paths cannot solve it
                               → propose segment, snapshot, and group creation; wait for approval ⛔

Step 1-3. If several candidates remain, present no more than five with identifying evidence
          and wait for the user's selection ⛔

Step 1-4. check_user_exists
  ├─ exists=true  → Phase 2
  └─ exists=false → do not query activity; recheck the user ID and project
```

Follow [Obtaining a user ID](references/user_id_sources.md) for path priority and calls. Never select a candidate
on the user's behalf. Creating a new segment, snapshot, and group is expensive and leaves persisted assets, so
propose that path only when an existing group or ranking cannot satisfy the request.

### Phase 2 — Narrow the Activity Range

```
Step 2-1. get_user_activity_summary
  → check totals for the entire period and counts by date
  → select dates relevant to the inquiry or with concentrated activity

Step 2-2. list_user_activities
  → query only the selected dates or range
  → inspect only the activities and properties needed for the conclusion instead of expanding the full history

Step 2-3. get_user_recent_info (when needed)
  → check the latest classification, cumulative purchases, server, and country from the per-date snapshot
```

Follow [Investigating activity history](references/activity_investigation.md) for detailed lookup and pagination.
Do not keep paging through the entire history. Narrow the period further from the summary or ask which range the
user wants checked.

### Phase 3 — Cross-check Metric Settings and Conclude

Metric-excluded users, metric filters, and metric start dates do not apply to user activity tracking. When activity
history and a metric differ, follow [Cross-checking metric settings](references/cross_check_settings.md) and verify:

| Check | Tool |
|---|---|
| Is this user registered as excluded from metrics? | `list_except_users` |
| Is the server or app used by this user filtered out? | `list_metric_filters` |
| Did the activity occur before the metric start date? | `list_start_dates` |

If one applies, explain the difference as configured aggregation behavior. If none is confirmed, do not declare
data loss or a bug; report confirmed facts separately from remaining uncertainty.

Include the investigation target and period, confirmed activity and latest state, whether metric settings were
cross-checked, and the basis of the evidence. `activity_date_time` reflects the user's timezone, while
`properties.dateTime` is UTC. Since their dates can differ, use `activity_date_time` when explaining times unless
there is a specific reason not to.

---

## Full Chain

```
[Classify request]
→ PROJECT_ID_GATE → USER_ID_GATE
   ├─ Supplied ID             → check_user_exists
   ├─ Existing user group     → list_user_groups → get_user_group → user selection ⛔
   ├─ Arbitrary metric rank   → preview_chart_rank → user selection ⛔
   └─ Existing paths fail     → propose creation scope → WRITE_APPROVAL before each write ⛔
                               → axyl-create-segment → regist_user_group
→ check_user_exists
   ├─ exists=false → stop and recheck the ID and project
   └─ exists=true  → get_user_activity_summary
                    → narrow the range and call list_user_activities
                    → [when needed] get_user_recent_info
                    → [when metrics differ] cross-check settings
                    → report evidence and uncertainty separately
```

---

## Prohibited Actions ❌

| Situation | Prohibited | Correct action |
|------|----------|-----------|
| No user ID | Invent or guess one | Find candidates through an existing group or ranking in USER_ID_GATE and wait for user selection |
| Several candidates | Pick one automatically or present a long list | Present no more than five candidates with identifying evidence |
| `exists=false` | Conclude that there is no activity | Explain that the ID or project may be wrong and recheck |
| Multiple-user investigation | Query users one by one | Use `preview_chart_rank`, a segment, or an analysis skill |
| Detailed activity lookup | Query the whole period and every page from the start | Use per-date summary counts to narrow the range first |
| Presenting results | Dump raw activity history or nested properties | Summarize only the facts and evidence relevant to the investigation purpose |
| Metric mismatch | Immediately conclude data loss or a bug | Cross-check excluded users, filters, start dates, and time boundaries first |
| Activity counts | Present them as metric values | State that they are based on raw activity history |
| Investigation assets | Create a segment, snapshot, or group without checking existing groups | Prefer existing assets and obtain approval before each write |

---

## Exception Handling

| Situation | Response |
|---|---|
| User does not exist in the confirmed project | Stop activity lookup and ask the user to check for a typo or an ID from another project |
| No existing user group matches the condition | Check whether an arbitrary metric ranking can solve it; only then propose creating a segment, snapshot, and group |
| User-ranking result is too large | Narrow the period and filters. Do not assume `rank_limit` reduces response rows |
| Activity summary is empty | Do not conclude that the user does not exist. Recheck `check_user_exists`, the period, project, and time boundary |
| Detailed activity is too large | Narrow the date and event range from the summary; ask the user to choose a range when the needed scope is unclear |
| Latest property value is `-` | Report it as not collected, not as zero or absent |
| Activity and metric disagree | Cross-check settings and time boundaries; leave the cause unconfirmed when it cannot be established |
| Not connected to the Hive Axyl MCP server (first install, never signed in), or the MCP token or Hive session expired (`__AUTH_EXPIRED__`) | Apply MCP_CONNECTION_GATE in axyl-analytics-common. Cannot retry without user action |
