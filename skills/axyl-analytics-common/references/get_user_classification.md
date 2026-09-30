# get_user_classification (Get User Classification Distribution)

Returns how users are distributed across classification types over a period, along with country and
OS composition.

> **Prerequisite:** Follow the common rules in [`../SKILL.md`](../SKILL.md).

## When to Use

- To understand the user mix ("how many whales", "what share is non-paying")
- To see whether countries or operating systems skew by type
- To check which cells hold users before extracting a segment

## Parameters

| Parameter | Required | Description |
|---------|------|------|
| `company_cd` | Y | Company code confirmed from `list_projects` |
| `org_idx` | Y | Organization idx confirmed from `list_organizations` |
| `appid_group` | Y | Project ID (`list_projects.appid_group`) |
| `start_date` | Y | Start date `YYYY-MM-DD` |
| `end_date` | Y | End date `YYYY-MM-DD` |

## How Types Are Determined

A type comes from the **combination of activity and purchasing power**. The **last state** within the
period is used, and users whose activity cannot be predicted are excluded.

| Activity \ Purchasing | high | average | low | noPurchase |
|---|---|---|---|---|
| high | whale | dolphin | dolphin | nonPu |
| average | dolphin | middle | middle | nonPu |
| low | dolphin | middle | light | nonPu |
| new | newUser | newUser | newUser | newUser |

When activity is new, the type is new regardless of purchasing power. One type spans several cells
(dolphin and new 4 cells, middle and nonPu 3, whale and light 1), so never read "one type = one cell".

## Return Value

| Field | Content |
|---|---|
| `user_type` | Users and share per type (`user_cnt_*` / `user_rate_*`) |
| `user_active_type` | Activity × purchasing cross table. **Rows are purchasing, columns are activity** |
| `country_type` | Series per country. Values are the **percentage within that type** |
| `os_type` | Series per OS. Values are the **percentage within that type** |
| `character_type` | Play time on the last active day per type (minutes, average) |

### Read With Care

- **`country_type` and `os_type` are percentages, not user counts.** Summing one type's values gives
  100 (99.9 with rounding). Never report them as counts.
- **A rate of `0.0` does not mean zero users.** It is rounded to one decimal place, so even one user
  reads `0.0`. Always take counts from `user_cnt_*`.
- `user_*_grade` in `user_active_type` is neither a count nor a rate; do not aggregate it.
- Countries appear individually only for the top 10 per type; the rest are grouped as `etc`.

## Decision Rules

- **Cross-check.** The total in `user_type` must equal the total in `user_active_type`. If they
  differ, one of them was misread — recheck before reporting any number.
- Rates are meaningless for types with only 1–4 users. Speak in counts instead.
- Metrics other than play time (login days, cumulative purchases, ARPPU and so on) do not come from
  this tool. Use `get_user_classification_detail`.
- To see how types changed during the period, use `get_user_classification_move`.

## On Failure

- Organization or project access error: recheck the organization and project relationship.
- All types zero: no users were classified in that period. Widen the range and query again.

## Recommended Chain

```text
list_projects → list_organizations → get_user_classification
→ (if more metrics are needed) get_user_classification_detail
→ (to extract a target) create_segment_from_classification
```
