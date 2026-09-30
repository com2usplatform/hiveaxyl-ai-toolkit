# list_dimensions (List Event Dimensions)

> **Prerequisite:** Follow the global rules in [`../SKILL.md`](../SKILL.md).

## When to Use

- After confirming an event name with `list_events`, when you need that event's dimension (measure_field) list.
- Before confirming the `dimension_name` and `adhoc_filters.field` values for `preview_chart`.
- In log integration, when checking a company-specific custom event or a property registered for the company under the same name as a standard one.
- If a dimension list has already been confirmed in the same conversation, do not call this again.

## Parameters

| Parameter | Description |
|---------|------|
| `company_cd` | Company code. The `company_cd` value from `list_projects` |
| `event_name` | Name of the event to query. The `event_name` value from `list_events` |

## Return Value

For each dimension, returns `dimension_idx`, the name and description, the data type, `attribute_source`,
whether it is an amount (`is_price`), and whether it is a currency (`is_currency`).

- `is_price` and `is_currency` are returned as `1` or `0`.
- `attribute_source=null` means a top-level common property; `hiveAttributes` and `eventAttributes` are values
  ingested into the corresponding property group. This is a post-ingestion location classification and does not
  describe the structure of the payload you send.
- Top-level common properties can be used directly in `query_adhoc.filters`. For the rest, read the value from the
  corresponding property group in the raw query result.
- `dimension_description` is `null` when absent.
- `get_content_template` handles mapping a template's common dimensions, so do not remap them separately.

## Decision Rules

- Use `dimension_name` as is for `preview_chart`'s `event_measures[].dimension_name` and `adhoc_filters[].field`.
- If `dimension_data_type` is `STRING`, use `COUNT` / `COUNT_DISTINCT`. If it is `INT`, `SUM` / `AVG` are also available. `TIMESTAMP` also exists.
- A dimension with `is_price=1` is a revenue metric. Specify `currency` as well when calling `preview_chart`.
- A dimension with `is_currency=1` is the currency filter dimension. `preview_chart` uses it automatically for `currency_options` internally.
- Use `dimension_idx` for `adhoc_filters[].idx`.

## On Failure

- Empty result: check `event_name` against the `list_events` result.

## Recommended Chain

```
list_events → list_dimensions → (ORG_WORKSPACE_GATE) → preview_chart
```
