# create_segment_from_classification (Create Segment From Classification)

Creates a segment from user classification labels and returns its `segment_idx`. **This is a write.**

> **Prerequisite:** Follow the common rules in [`../SKILL.md`](../SKILL.md).
> Both WRITE_APPROVAL and POST_WRITE_LINK apply.

## When to Use

- After reviewing the classification distribution, to act on "the users of this type"
- When labels alone are enough, unlike `create_segment` where conditions are assembled by hand

## Parameters

| Parameter | Required | Description |
|---------|------|------|
| `company_cd` | Y | Company code confirmed from `list_projects` |
| `org_idx` | Y | Organization idx confirmed from `list_organizations` |
| `appid_group` | Y | Project ID (`list_projects.appid_group`) |
| `start_date` | Y | Start date for collecting target users `YYYY-MM-DD` |
| `end_date` | Y | End date for collecting target users `YYYY-MM-DD` |
| `user_labels` | Y | List of classification labels. At least one |

## Labels

The format is `"activity_purchasing"`, and the two axes use different vocabularies.

- Activity: `high` `average` `low` `new`
- Purchasing: `high` `average` `low` `noPurchase`

**One type spans several cells.** To extract a whole type, pass every label listed for it.

| Type | Cells | Labels |
|---|---:|---|
| whale | 1 | `high_high` |
| dolphin | 4 | `high_average` `high_low` `average_high` `low_high` |
| middle | 3 | `average_average` `average_low` `low_average` |
| light | 1 | `low_low` |
| nonPu | 3 | `high_noPurchase` `average_noPurchase` `low_noPurchase` |
| newUser | 4 | `new_high` `new_average` `new_low` `new_noPurchase` |

> **`low_low` is light, not middle.** Middle has only 3 cells; when both activity and purchasing are
> low the user falls into light. Miscounting the cells mixes another type into the segment.

## Return Value

Returns `{"segment_idx", "url", "appid_group", "start_date", "end_date", "user_labels"}`.
**`segment_idx` is a segment identifier, not a user count.**

`url` is the console link to the created segment. **Always include it when reporting the result.**
Do not assemble it yourself; use the value the tool returned (POST_WRITE_LINK).

## Decision Rules

- **Get user approval before calling (WRITE_APPROVAL).** Read back the period, the labels, and which
  type those labels correspond to.
- **It cannot be undone.** No delete tool is provided, so cleanup has to happen in the console.
- **The name cannot be set.** The server assigns one, and calling twice with the same conditions
  **creates a second identical segment.** No MCP tool can list these segments, so you cannot verify
  duplicates yourself: check whether this conversation already created one with the same period and labels, and
  when asking for approval, tell the user to check the console segment list if one may have been made before.
- Do not create a segment for investigation alone. `get_user_classification` and
  `get_user_classification_detail` already cover counts and metrics per type.
- This segment is not condition-based, so it does not appear in `list_segment_snapshots`. Continue
  follow-up work with the returned `segment_idx` directly.

## On Failure

- An unknown value in `user_labels` fails with a format hint. Check the `activity_purchasing` order
  and the difference between the axes (`new` is activity only, `noPurchase` is purchasing only).
- Organization or project access error: recheck the organization and project relationship.

## Recommended Chain

```text
get_user_classification (confirm target cells and counts) → user approval
→ create_segment_from_classification → report with url
```
