# Obtaining the Investigation Target User ID (USER_ID_GATE)

The procedure for settling on the single user to investigate. **Do not guess or invent a user ID.**

> **Prerequisite:** Follow the rules in [`../SKILL.md`](../SKILL.md) and [`../../axyl-analytics-common/SKILL.md`](../../axyl-analytics-common/SKILL.md). This is the USER_ID_GATE step.

## Common Exit Condition

Whichever path you came from, `check_user_exists` must pass before the investigation starts.

```text
check_user_exists(company_cd, org_idx, appid_group, user_id)
  → exists: false  → do not move on to activity queries. Recheck the user ID
  → exists: true   → start the investigation
```

Even a nonexistent ID returns `false` rather than an error, so typos are filtered out here.
Answering "there is no activity" from an empty activity result is this skill's most common wrong answer.

## A. The User Supplied an ID

Use the value from the CS ticket or report as is. Move straight to `check_user_exists` without
another lookup.

At a company with several projects, **it may be an ID from another project.** If `exists: false`
comes back, ask the user whether the user ID is wrong or the wrong project was chosen.

## B. User Groups — Finding Users Matching a Condition

Try this first. The groups the console has prepared describe their condition in their names.

```text
list_user_groups(company_cd, org_idx, appid_group)
  → [{"idx", "type", "name", "segment_id", "segment_snapshot_id"}]
```

| type | Meaning |
|---|---|
| `builtin` | A default user group provided by the Analytics system. It can be top revenue, whale, new, dormant, and so on. |
| `segment` | A group made from a segment. It can be created from a segment, or from a segment plus a segment snapshot. |

Examples of system-provided user groups. The name is the condition.

```text
Top 100 users by revenue over the last 15 days
Top 100 users by cumulative revenue
Users whose last classification type is whale
Users new within the last 7 days
Users dormant for 3 days or more
```

Once a user group is selected, you can get the game user IDs belonging to it.

```text
get_user_group(company_cd, org_idx, appid_group, group_id,
               limit=20, order_name="accKrw", order_type="desc")
  → {"count": 100, "returned": 20, "members": [...]}
```

`count` is the number of rows the server returned (it stops at 100), not the group's total size — never report it as
"the group has N users". `returned` is how many came back after `limit`.

Members carry properties along with the user ID. **Attach these values as identifying evidence when
presenting candidates.**

| Fields worth using as evidence | Content |
|---|---|
| `userType` | User classification type (whale, middle, non-paying, new) |
| `accKrw` / `accUsd` | Cumulative purchase amount |
| `accPurchaseCnt` | Cumulative purchase count |
| `lastLoginDateTime` | Days dormant |
| `serverId` · `market` · `hiveCountry` | Server, market, country |

The presentation format:

```text
Here are the top 5 whale users. Whose activity should we query?
  <user_id_A> · ₩150,000 total · 12 purchases · <country> · <market>
  <user_id_B> · ₩140,000 total · 10 purchases · <country> · <market>
  <user_id_C> · ₩130,000 total ·  9 purchases · <country> · <market>
```

Listing bare numeric IDs leaves the user unable to choose. **Do not present candidates without evidence.**

## C. Finding by Segment Conditions

1. First check whether `list_user_groups` has a `type: "segment"` group → if it does, **same as B**
2. If not, one has to be created. The flow is heavy, so **propose it to the user and proceed only after approval**

```text
Create a segment with axyl-create-segment (WRITE_APPROVAL)
  → extract a snapshot
  → regist_user_group(company_cd, org_idx, appid_group, game_name, name, segment_id, segment_snapshot_id)
  → get_user_group → present candidates
```

`regist_user_group` **cannot be undone** — no group deletion tool is provided. Before calling it,
check with `list_user_groups` that no group for the same purpose exists, and confirm the name with the user.

Creating a new segment, snapshot, and group for a single investigation is expensive. **First confirm
that an existing group or path B or D cannot solve it.**

## D. Finding by Ranking on an Arbitrary Metric

Use this for criteria the built-in groups do not cover — the user with the most tutorial failures,
the most logins, and so on.

`preview_chart_rank` is a chart tool, so it also needs `workspace_idx`: pass ORG_WORKSPACE_GATE first, and
confirm the event and dimension with `list_events`/`list_dimensions` (SCHEMA_FIRST).

```text
preview_chart_rank(
  project=[appid_group], company_cd, org_idx, workspace_idx,
  dimensions=[{"idx": <userId dimension_idx>, "name": "userId"}],
  event_measures=[the metric],
  date_params=a short period,
  adhoc_filters=[restrict by server, market, and so on where possible],
  rank_limit=5, rank_order="desc")
```

**`rank_limit` is for console display and does not reduce the number of response rows.** Every
matching user in that period is included, so narrow the period first. If you do not know the scale,
query the total without dimensions first to check the number of users.

Even when the response is large, **present 5 or fewer** to the user. Do not summarize the rest.

## Choosing a Path

| Situation | Path |
|---|---|
| The ID is already known | A |
| Whale, new, dormant, top revenue | B (built-in group) |
| Based on a segment created earlier | B (segment-type group) → C if there is none |
| Any other arbitrary metric criterion | D |

* Path priority: A > B > D > C
* When B is possible, use it before D.
