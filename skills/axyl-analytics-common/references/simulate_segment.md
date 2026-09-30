# simulate_segment (Query a Segment's Estimated User Count)

> **Prerequisite:** Follow the common rules in [`../SKILL.md`](../SKILL.md). PROJECT_ID_GATE + SCHEMA_FIRST (`list_segment_meta`) are required. **This is a read tool, so WRITE_APPROVAL is not needed.**

## When to Use

- Always, before calling `create_segment`. It catches conditions that are far too narrow (a handful of users) or too broad (hundreds of thousands) before they are created.
- When the user is tuning the size by varying the conditions. It saves nothing, but call again only with conditions the user chose (see below).
- The condition format is identical to `create_segment`; pass the conditions you verified straight to the save step.
  This result is the basis for WRITE_APPROVAL, so do not ask for save approval before showing the user count.

## Parameters

| Parameter | Required | Description |
|---------|------|------|
| `company_cd` | Y | Company code |
| `org_idx` | Y | Organization idx. Used to verify access to the target project |
| `appid_group` | Y | Project ID (the `appid_group` from `list_projects`) |
| `game_name` | Y | Game name (the `game_name` from `list_projects`) |
| `property_groups` | Y | Extraction conditions. Same format as `create_segment` |
| `group_connection_type` | N | How condition groups combine: `"AND"`\|`"OR"` (default `"AND"`) |
| `lang` | N | Condition label language (default `"ko"`) |

## Return Value

Returns the total user count, the estimated extracted count and its proportion, a human-readable condition summary, and each condition's contribution.

## Decision Rules

- **`user_proportion` is expressed in percent (%).** Do not multiply it by 100 again — display it as `%` as given.
- `condition_details` tells you **how many users each individual condition matches**. If the final count is lower than expected,
  use it to point out which condition narrowed the scope and explain that to the user.
- **Call it once with the conditions the user stated, then stop.** Do not adjust thresholds or periods yourself and call again
  because the count seems low or high — that would create a segment the user never asked for.
  Present the result, ask "Would you like to adjust the conditions?", and call again with those conditions only after they choose.
- **Do not save when the count is zero.** Offer alternatives such as relaxing conditions or widening the period, but act only after approval.
- If the count is excessive (when the purpose is sending), state the size explicitly and suggest adding conditions. A snapshot can run to hundreds of thousands of records.
- Base any adjustment proposal on the conditions that actually narrowed the scope in `condition_details`. Do not set thresholds on your own.
- `conditions` is a human-readable sentence. **Show the user only this sentence** —
  do not expose internal code values such as `value_range_type`, `date_type`, or `start_value`
  (the display rules in axyl-analytics-common).

## On Failure

- `ValidationError`: a property name or value in the condition is not in the metadata. Check with `list_segment_meta` and fix it.
- `condition_details` is an empty list: only the detail query failed. The estimated count (`extract_user_cnt`) is still valid.

## Recommended Chain

```
(PROJECT_ID_GATE) → list_segment_meta → simulate_segment
→ [present the count and proportion to the user] → [WRITE_APPROVAL] → create_segment
```
