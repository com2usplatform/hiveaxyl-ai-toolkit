# create_segment (Save a Segment)

> **Prerequisite:** Follow the common rules in [`../SKILL.md`](../SKILL.md). PROJECT_ID_GATE + SCHEMA_FIRST (`list_segment_meta`) + **WRITE_APPROVAL** are required.

## When to Use

- After the user has asked to **save** a segment, and you have shown the `simulate_segment` result and obtained approval.
- The saved `segment_idx` is used when adding a snapshot with `create_segment_snapshot`.
- The condition format is identical to `simulate_segment`. Check the estimated user count first with the same conditions,
  obtain approval on the basis of that result, and only then save.

## Parameters

| Parameter | Required | Description |
|---------|------|------|
| `company_cd` | Y | Company code |
| `org_idx` | Y | Organization idx. Used to verify access to the target project |
| `appid_group` | Y | Project ID (the `appid_group` from `list_projects`) |
| `game_name` | Y | Game name (the `game_name` from `list_projects`) |
| `title` | Y | Segment name. Make it **specific enough to convey the conditions** |
| `property_groups` | Y | Extraction conditions (structure below) |
| `description` | N | Segment description (default `''`) |
| `group_connection_type` | N | How condition groups combine: `"AND"`\|`"OR"` (default `"AND"`) |
| `lang` | N | Condition label language (default `"ko"`) |
| `set_base_snapshot` | N | The default `""` **saves only the definition** (recommended). `"set"` also creates one base snapshot right after saving |
| `snapshot_schedules` | N | Scheduled snapshot extraction settings (none by default) |

### property_groups structure

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
      },
      {
        "property_category": "userInfo",
        "property_name": "os",
        "start_value": "I"
      }
    ]
  }
]
```

| Field | Description |
|------|------|
| `property_select_type` | `"LASTEST"` (based on the most recent value) \| `"ALL"` (matched at least once over the whole period). **Use the `LASTEST` spelling exactly as written** |
| `property_connection_type` | How conditions combine within a group / between conditions: `"AND"`\|`"OR"` (default `"AND"`) |
| `property_category` / `property_name` | **Required.** Use only values from the `list_segment_meta` result |
| `start_value` / `end_value` | For a selectable type (`value_type="enum"`), a value from the metadata; for a numeric type, the threshold. `include`/`notinclude` take several comma-separated values |
| `value_range_type` | `""` (value match) \| `"more"` (at least) \| `"less"` (at most) \| `"between"` (between; `end_value` required) \| `"include"` (contains) \| `"notinclude"` (does not contain) |
| `date_type` | `""` (no period condition) \| `"recent"` (a number of days in `start_date`, for example `"0"`, `"7"`) \| `"date"` (`start_date` to `end_date`, YYYY-MM-DD). **Only available for properties with `period_yn="Y"`** |

**Do not pass** `property_category_name`/`property_name_translation`/`property_data_type` —
the server fills them in automatically from `list_segment_meta`.

## Return Value

Returns the saved `segment_idx`, the title, the project, a condition summary, the console URL, and the save result.

- `segment_idx`: pass it straight to `create_segment_snapshot`.
- `conditions`: a summary of the conditions actually saved. Show it to the user as is so they can confirm it matches their intent.
- `url`: the segment detail console link (POST_WRITE_LINK). Return it to the user. Do not assemble it yourself.

## Decision Rules

- **Create only condition-based (`standard`) segments.** CSV upload and direct query methods cannot be created with this tool.
- A careless `title` (for example, "Segment 1") makes the target impossible to judge later. Use a name that reveals the conditions.
- **This tool saves only the condition definition.** With the default (`set_base_snapshot=""`) no snapshot is created, so there is
  not yet a target user set. Create the snapshot with `create_segment_snapshot`, **approved separately** —
  it is a distinct operation whose point in time carries meaning.
- Passing `set_base_snapshot="set"` also starts extracting one base snapshot right after saving. In that case,
  calling `create_segment_snapshot` afterwards would extract a duplicate.

## On Failure

- `ValidationError` (property name): a `property_category.property_name` that is not in the metadata. The message includes the list of available properties.
- `ValidationError` (value): a value not available for a selectable property. The message includes the list of available values.
- `ValidationError` (period): a `date_type` was attached to a property with `period_yn="N"`. Remove the period condition.
- API error: check the server response and fix the parameters. The segment was not created.

## Recommended Chain

```
(PROJECT_ID_GATE) → list_segment_meta → simulate_segment (check the user count)
→ [WRITE_APPROVAL] → create_segment
→ (only if a snapshot is wanted) [separate WRITE_APPROVAL] → create_segment_snapshot → list_segment_snapshots (confirm it completed)
```
