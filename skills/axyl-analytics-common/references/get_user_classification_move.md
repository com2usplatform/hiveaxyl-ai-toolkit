# get_user_classification_move (Get User Classification Movement)

Returns how user classification types changed over a period. Specifying a movement path also
returns the IDs of the users who moved along it.

> **Prerequisite:** Follow the common rules in [`../SKILL.md`](../SKILL.md).

## When to Use

- To see which type new users drifted into over the period
- To see which type the users who went inactive originally belonged to
- **To pick users to investigate** — numeric user IDs are impossible for a person to recall, so use
  this alongside user groups and segments as a starting point for identifying targets

## Parameters

| Parameter | Required | Description |
|---------|------|------|
| `company_cd` | Y | Company code confirmed from `list_projects` |
| `org_idx` | Y | Organization idx confirmed from `list_organizations` |
| `appid_group` | Y | Project ID (`list_projects.appid_group`) |
| `start_date` | Y | Start date `YYYY-MM-DD` |
| `end_date` | Y | End date `YYYY-MM-DD` |
| `move_from` | N | Origin type. Omit for all |
| `move_to` | N | Destination type. Omit for all |
| `limit` | N | How many user IDs to receive. 1–100, default 20 |

Supplying **either** `move_from` or `move_to` adds the user ID list (`movers`). Omitting both
returns aggregates only.

## User Classification Types

Determined by the combination of activity and purchasing power. Either the code value or the Korean
label is accepted.

| Code | Korean | Origin type | Destination type |
|---|---|:---:|:---:|
| `whale` | 고래 | O | O |
| `dolphin` | 돌고래 | O | O |
| `middle` | 미들 | O | O |
| `light` | 라이트 | O | O |
| `nonPu` | 무과금 | O | O |
| `newUser` | 신규 | O | ✕ |
| `churn` | 미접속 | ✕ | O |

New cannot be a destination type and inactive cannot be an origin type. Combinations that cannot
occur are rejected with an error rather than an empty result.

**Inactive (`churn`) means no activity for 3 or more days as of the end date.** A user lands here
when their last activity date is 3 or more days before the end date — that is, no activity during
the last 3 days including the end date. The cutoff moves with the period, so the same user can be
inactive or not depending on the range queried.

## Return Value

Returns `{"appid_group", "start_date", "end_date", "max_move", "move", "moved_user_count"}`, plus
`movers` when a movement path is given.

| Field | Content |
|---|---|
| `max_move` | The single most frequent movement |
| `move` | 6 origin-type rows × `user_cnt_*`/`user_rate_*` per destination type |
| `moved_user_count` | Total users whose type changed (inactive included) |
| `movers` | `{"count", "returned", "users"}` — `users` holds `first_type`, `last_type`, `user_id` |

### Read With Care

- **`-1` is not 0.** It marks a cell where movement cannot occur because origin and destination are
  the same type; the console leaves it hatched. `0` means movement was possible but did not happen.
- `user_rate` is rounded to one decimal place, so **it reads `0.0` even for one user.** Do not
  answer "none" from the rate alone.
- `user_id` is a chart tooltip string carrying a prefix, as in `"유저 Id:<user_id>"`. The value
  after the colon is the actual user ID.
- `count > returned` means the list was truncated by `limit`.

## Decision Rules

- **Do not state inactive (`churn`) as churned.** It only means no activity for 3 or more days; it
  does not rule out a return. Say "no activity for 3 or more days", not "churned".
- **Users whose type stayed the same are not counted anywhere.** Do not read these numbers as the
  total user count.
- Narrow candidates to **5 or fewer** and state which path each user moved along.
- **Do not pick one automatically.** The user selects (NO_GUESSING).
- Do not widen the period beyond what is needed; the server aggregates on every call.

## On Failure

- Passing `churn` to `move_from` or `newUser` to `move_to` fails with the allowed list. The
  combination cannot occur, so call again with a different path.
- `movers.count` of 0 means no user moved along that path. Check the matching `user_cnt_*` cell in
  `move` first to confirm the path itself is right.
- Organization or project access error: recheck the organization and project relationship.

## Recommended Chain

```text
get_user_classification_move (aggregates) → identify the path of interest
→ get_user_classification_move (with move_from / move_to) → present 5 or fewer candidates → user selects
→ check_user_exists → activity investigation
```
