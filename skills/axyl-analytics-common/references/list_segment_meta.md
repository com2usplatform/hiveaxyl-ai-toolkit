# list_segment_meta (List Segment Properties)

> **Prerequisite:** Follow the common rules in [`../SKILL.md`](../SKILL.md). PROJECT_ID_GATE is required. This is the SCHEMA_FIRST step for segments.

## When to Use

- Always, **before** building conditions with `simulate_segment`/`create_segment`. Property names and values that do not appear here cannot be used.
- When interpreting the conditions returned by `list_segment_snapshots`. (With `with_labels=True`, however, that tool already fills in the labels.)

## Parameters

| Parameter | Required | Description |
|---------|------|------|
| `company_cd` | Y | Company code (the `company_cd` from `list_projects`) |
| `org_idx` | Y | Organization idx. Used to verify access to the target project |
| `appid_group` | Y | Project ID (the `appid_group` from `list_projects`) |
| `lang` | N | Label language: `"ko"`\|`"en"`\|`"ja"`\|`"zh_hant"`\|`"th"` (default `"ko"`) |
| `property_category` | N | Query only a specific category (for example, `"userInfo"`). Omit for everything |
| `max_values_per_property` | N | Maximum number of selectable values per property (default `50`) |

## Return Value

Returns the property list by category. Each property includes the name used in calls, the label shown to the user,
the data type, whether period conditions are supported, the value type, the selectable values, and whether the
value list was truncated.

## Decision Rules

- **`value_type` determines how the condition is written.**
  - `"enum"` → choose from the `property_value` entries in `values`. Values not in the list must not be used.
  - `"range"` → a numeric or time type with no selectable values. Specify a range with `start_value` (+ `end_value`).
- **Only properties with `period_yn="Y"` can carry a period condition (`date_type`).** Attaching one to an `"N"` property is an error.
- You do not need to include `property_data_type` in the condition — `create_segment` fills it in automatically from this metadata.
- `values_truncated=true` means the list was cut off at `max_values_per_property`. The full count is in `value_count`.
  Do not treat a truncated list as complete.
- Explain properties to the user with `label` (for example, "Language"), and use `property_name` (for example, `language`) in tool calls.

## On Failure

- Empty result or `ValidationError`: `appid_group` is most likely wrong. Reconfirm it with `list_projects`.

## Recommended Chain

```
(PROJECT_ID_GATE) → list_segment_meta → simulate_segment → [WRITE_APPROVAL] → create_segment
```
