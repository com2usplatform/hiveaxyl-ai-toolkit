# Condition Design Patterns (natural-language request → property_groups)

> **Prerequisite:** Follow the rules in [`../SKILL.md`](../SKILL.md) and [`../../axyl-analytics-common/SKILL.md`](../../axyl-analytics-common/SKILL.md).

## When to Use

- To translate the user's natural-language request ("paying iOS users", "dormant whale users") into the `property_groups` structure.
- A request decomposes the same way regardless of the metric — three steps: **choose the property → choose the operator → decide on a period**.

> Every `property_name` and value below is an **example**. Before an actual call, verify with
> `list_segment_meta(company_cd, org_idx, appid_group)` that the property and value exist for that project, and substitute the returned values (NO_GUESSING).

---

## The Three Decomposition Steps

```
1. Choose the property   → property_category + property_name from list_segment_meta
2. Choose the operator   → determined by value_type
                           enum  → value_range_type="" (value match) / include / notinclude
                           range → more (at least) / less (at most) / between
3. Decide on a period    → only a property with period_yn="Y" can specify date_type
                           "recent" + start_date="7"   → the last 7 days
                           "date" + start_date~end_date → a specific range
```

## Operator Selection Rules

| Phrasing in the request | `value_range_type` | Value |
|---|---|---|
| "users who are X" (one selectable value) | `""` | One value in `start_value` |
| "users who are X or Y" | `"include"` | Several comma-separated values in `start_value` (`"ko,en"`) |
| "users who are not X" | `"notinclude"` | The value to exclude |
| "at least N" | `"more"` | `start_value=N` |
| "more than N", "over N won" (excludes N) | `"more"` | Whole-number values (counts, levels, KRW amounts): `start_value=N+1`. Decimal values: N plus the property's smallest step (`0.01` for USD) |
| "at most N" | `"less"` | `start_value=N` |
| "under N", "less than N" (excludes N) | `"less"` | Whole-number values: `start_value=N-1`. Decimal values: N minus the property's smallest step |
| "between N and M" | `"between"` | `start_value=N`, `end_value=M` |

`"more"` and `"less"` include N itself (at least / at most), so an exclusive phrase needs the adjusted value. Tell the
user which boundary you used; when the property's smallest step is unknown, confirm the boundary with the user.

## Group Combination Rules

```
Conditions within the same group  → property_connection_type (AND/OR)
Between groups                    → group_connection_type   (AND/OR)

If every condition must be satisfied, put them in one group with AND.
For differently shaped buckets such as "users matching A or users matching B", split them into groups with group_connection_type="OR".
```

`property_select_type` decides which point in time the value is taken from.

- `"LASTEST"` — based on the most recent value (for example, users whose language is **currently** Chinese). This is the usual choice.
- `"ALL"` — matched at least once over the whole period (for example, users who ever used Chinese)
- The spelling is `LASTEST`. Writing `LATEST` causes an error.

---

## Pattern 1 — A single selectable value (the simplest)

Request: "users who use Chinese"

```json
[
  {
    "property_select_type": "LASTEST",
    "property_connection_type": "AND",
    "property_group_name": "Property Group 1",
    "property_fields": [
      {
        "property_category": "userInfo",
        "property_name": "language",
        "value_range_type": "",
        "start_value": "zh-hans",
        "property_connection_type": "AND"
      }
    ]
  }
]
```

Take `start_value` from `values[].property_value` in `list_segment_meta`. Even if the user said "Chinese," the actual value
may split into `zh-hans`/`zh-hant`, so confirm which one they mean.

## Pattern 2 — A numeric condition plus a period (period_yn="Y")

Request: "users who paid recently"

```json
[
  {
    "property_select_type": "LASTEST",
    "property_connection_type": "AND",
    "property_group_name": "Property Group 1",
    "property_fields": [
      {
        "property_category": "purchaseInfo",
        "property_name": "usd",
        "value_range_type": "more",
        "start_value": "0.01",
        "date_type": "recent",
        "start_date": "0",
        "property_connection_type": "AND"
      }
    ]
  }
]
```

- "Who paid" means at least one purchase, not at least 1 USD — `usd >= 1` drops payers under a dollar. Prefer a purchase-count
  property from `list_segment_meta` with `more` `1`. If only the amount exists, use `more` with the smallest positive amount
  (`"0.01"`, as in the example): `more` means "at least", so `"0"` would also include non-paying users. Tell the user which basis you used.
- `date_type="recent"` + `start_date="0"` means as of today. For "the last 7 days", use `"7"`.
- A period condition attaches only to a property with `period_yn="Y"`. A cumulative property such as `accUsd` (total payment amount) is usually `"N"`.

## Pattern 3 — Several conditions with AND (intersection)

Request: "paying iOS users"

```json
[
  {
    "property_select_type": "LASTEST",
    "property_connection_type": "AND",
    "property_group_name": "Property Group 1",
    "property_fields": [
      {
        "property_category": "purchaseInfo", "property_name": "usd",
        "value_range_type": "more", "start_value": "0.01",
        "date_type": "recent", "start_date": "0",
        "property_connection_type": "AND"
      },
      {
        "property_category": "userInfo", "property_name": "os",
        "value_range_type": "", "start_value": "I",
        "property_connection_type": "AND"
      }
    ]
  }
]
```

The more conditions you stack with AND, the more sharply the count drops. Use `condition_details` from `simulate_segment` to
identify the bottleneck and explain it to the user (for example, `os=I` 15% → 150,000 users, `usd>=0.01` 0.01% → 100 users).

## Pattern 4 — Including / excluding several values

Request: "Korean and English users, excluding users in China"

```json
[
  {
    "property_select_type": "LASTEST",
    "property_connection_type": "AND",
    "property_group_name": "Property Group 1",
    "property_fields": [
      {
        "property_category": "userInfo", "property_name": "language",
        "value_range_type": "include", "start_value": "ko,en",
        "property_connection_type": "AND"
      },
      {
        "property_category": "userInfo", "property_name": "hiveCountry",
        "value_range_type": "notinclude", "start_value": "CN",
        "property_connection_type": "AND"
      }
    ]
  }
]
```

## Pattern 5 — A range condition

Request: "users in the 1,000–5,000 won payment band"

```json
[
  {
    "property_select_type": "LASTEST",
    "property_connection_type": "AND",
    "property_group_name": "Property Group 1",
    "property_fields": [
      {
        "property_category": "purchaseInfo", "property_name": "accKrw",
        "value_range_type": "between", "start_value": "1000", "end_value": "5000",
        "property_connection_type": "AND"
      }
    ]
  }
]
```

`between` without `end_value` is an error.

---

## Common Requests → Property Mapping

Confirm they exist in the metadata before use. The available properties differ by project.

| Request | Candidate properties | Notes |
|---|---|---|
| Paying users / whales | `purchaseInfo.usd`, `accUsd`, `accKrw`, `userType` | If `userType` has classification values such as `whale`/`dolphin`, using it is more accurate |
| Non-paying users | `userInfo.userType` = `nonPu` | Clearer than an amount condition |
| New users | `loginInfo.newUser` = `Y`, `firstLoginDateTime` | `newUser` is `period_yn="Y"` (new within the period) |
| Dormant users | `loginInfo.lastLoginDateTime` | The label is "days dormant". Use `more` on the day count |
| OS / market / country / language | `userInfo.os`/`market`/`hiveCountry`/`language` | All selectable (enum) |
| Guest users | `userInfo.guestUser` = `Y`\|`N` | |
| Suspended users | `userInfo.hiveUserBlock` = `block`\|`unblock`\|`normal` | Use `notinclude` to exclude them from a send |
| Excluding internal accounts | `userInfo.intraUser` = `exclude` | When internal users must be kept out of metrics or sends |
| Account level | `playInfo.userAccountLevel` | There can be 100+ values, so a range (`more`/`between`) is recommended |

---

## On Failure

| Situation | Response |
|------|------|
| No candidate property in the metadata | Propose an alternative property. If there is none, explain that it cannot be built and stop |
| The value is ambiguous (for example, "Chinese") | Present the metadata's `values[].label` and ask the user to choose |
| The count is zero | **Propose** relaxing conditions (lowering the threshold, widening the period, AND → OR) and get a choice. Do not change them arbitrarily and re-simulate |
| The count is excessive | **Propose** adding conditions or shortening the period. For a send, state the size and reconfirm approval |
