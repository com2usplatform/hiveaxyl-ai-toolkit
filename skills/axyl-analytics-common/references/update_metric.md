# update_metric (Update Metric)

Updates a registered metric's name, description, display format, or aggregation definition.
**This is a write.**

> **Prerequisite:** Follow the common rules in [`../SKILL.md`](../SKILL.md).
> WRITE_APPROVAL applies.

## When to Use

- To correct a metric name or description that no longer matches the actual formula
- To tidy up the classification (`metric_category`)
- To fix an aggregation definition that was registered incorrectly

## Parameters

| Parameter | Required | Description |
|---------|------|------|
| `company_cd` | Y | Company code confirmed from `list_projects` |
| `metric_idx` | Y | Metric idx (`list_metrics.idx`) |
| `metric_name` | N | New name |
| `metric_description` | N | New description |
| `metric_category` | N | New classification. Follow the values used in `list_metrics` |
| `decimal_point` | N | Number of decimal places |
| `percent` | N | Show as percentage, `"Y"` or `"N"` |
| `change_rate` | N | Show change rate, `"Y"` or `"N"` |
| `measures` | N | Aggregation definition, same structure as `create_metric.measures` |

**At least one** field to change is required. Anything not passed is preserved.

## It Sits On Top of a Full-Replace API

The server's update API takes the **whole** metric. This tool **reads the current metric first,
overwrites only the given fields, and sends everything back**, so changing just the name does not
require reassembling the aggregation definition.

## Return Value

Returns `{"metric_idx", "metric_name", "changed", "console_url", "response"}`.

- `changed`: list of the fields changed in this call
- `console_url`: detail screen for the updated metric. **Include it when reporting a write
  (POST_WRITE_LINK)**
- `response`: what the server returned after saving. **The `metric_name`, `metric_description`, and
  `metric_category` in here are what was actually stored**

## Decision Rules

- **Check the response before reporting.** If a value in `response` differs from what was requested,
  it was not saved — do not report success. Never judge from the success code alone.
- **Get user approval before calling (WRITE_APPROVAL).** Read back what changes from what.
- **Changing the name also changes the display name in existing charts** that use this metric. State
  the blast radius first.
- **Changing `measures` recalculates past periods under the new definition.** Numbers reported
  earlier may change, so disclose this and get approval before doing it.
- **`measures` cannot be partially edited.** Passing it replaces the whole definition, so even adding
  one filter means rebuilding all of it. Check the current definition in `list_metrics.metric_config`.
- The only way to revert is to call this tool again with the previous values. Record them beforehand.

## On Failure

- No field to change was passed: ask the user which field to change.
- `metric_idx` not found: nothing is saved. Confirm the idx with `list_metrics` — saving with a wrong
  one would erase the existing definition, so the tool blocks it first.
- `percent` or `change_rate` value error: use only `"Y"` or `"N"`.

## Recommended Chain

```text
list_metrics (check current definition and metric_config) → state blast radius → user approval
→ update_metric → confirm stored values in response, then report
```
