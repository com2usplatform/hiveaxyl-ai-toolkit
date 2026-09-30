# get_user_group (Get User Group Members)

Returns the members of one user group. Use it to identify the user to investigate after choosing a
group with `list_user_groups`.

> **Prerequisite:** Follow the common rules in [`../SKILL.md`](../SKILL.md).

## When to Use

- To pick an investigation target from a group such as whale, new, or dormant users
- To check who belongs to a group created from a segment

## Parameters

| Parameter | Required | Description |
|---------|------|------|
| `company_cd` | Y | Company code confirmed from `list_projects` |
| `org_idx` | Y | Organization idx confirmed from `list_organizations` |
| `appid_group` | Y | Project ID (`list_projects.appid_group`) |
| `group_id` | Y | User group idx (`list_user_groups.idx`) |
| `limit` | N | Number of users to return. Default 20; the server returns up to 100 |
| `lang` | N | Label language. Default `ko` |
| `order_name` | N | Sort field (for example `userId`, `accKrw`) |
| `order_type` | N | Sort direction (`desc` or `asc`) |

## Return Value

Returns `{"appid_group", "group_id", "count", "returned", "members"}`.
`count` is the number of rows the server returned — **not the group's total size**; the server stops at 100, so
`count=100` means "100 or more". `returned` is how many of those came back after `limit`. For an exact size, use the
segment snapshot's `snapshot_user_cnt` (`list_segment_snapshots`).

Members carry `userId` together with user properties, with labels applied.

| Field worth using as evidence | Content |
|---|---|
| `userType` | User classification type (whale, middle, non-paying, new) |
| `accKrw` / `accUsd` | Cumulative purchase amount |
| `accPurchaseCnt` | Cumulative purchase count |
| `lastLoginDateTime` | Days dormant |
| `serverId` · `market` · `hiveCountry` | Server, market, country |

## Decision Rules

- **Present candidates with identifying evidence.** Bare numeric IDs leave the user unable to choose.
- Narrow what you present to **5 or fewer**, even when more were returned.
- **Do not pick one automatically.** The user selects (NO_GUESSING).
- To see a different part of the group, raise `limit` or bring the wanted side forward with
  `order_name` and `order_type` rather than paging blindly.
- The values are raw; metric settings are not applied.

## On Failure

- Organization or project access error: recheck the organization and project relationship.
- Empty result: the group has no members. For a segment-type group, check the source segment.

## Recommended Chain

```text
list_user_groups → get_user_group → present 5 or fewer candidates → user selects
→ check_user_exists → activity investigation
```
