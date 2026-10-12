# list_dimensions (List Event Dimensions)

> **Prerequisite:** Follow the common rules in [`../SKILL.md`](../SKILL.md).

## When to Use

- After confirming an event name with `list_events`, when you need that event's dimension (measure_field) list.
- Before confirming the `dimension_name` and `adhoc_filters.field` values for `preview_chart`.
- In log integration, when checking a company-specific custom event or a property registered for the company under the same name as a standard one.
- If a dimension list has already been confirmed in the same conversation, do not call this again.

## Parameters

| Parameter | Required | Description |
|---------|------|------|
| `company_cd` | Y | Company code. The `company_cd` value from `list_projects` |
| `event_name` | Y | Name of the event to query. The `event_name` value from `list_events` |

## Return Value

For each dimension, returns `dimension_idx`, the name and description, the data type, `attribute_source`,
whether it is an amount (`is_price`), and whether it is a currency (`is_currency`).

- `is_price` and `is_currency` are returned as `1` or `0`.
- `attribute_source=null` means a top-level common property; `hiveAttributes` and `eventAttributes` are values
  ingested into the corresponding property group. This is a post-ingestion location classification and does not
  describe the structure of the payload you send.
- Only `identifierProvider`, `userId`, `deviceId`, `appId`, and `appIdGroup` can be used directly in `query_adhoc.filters`. For the rest, read the value from the
  corresponding property group in the raw query result.
- `dimension_description` is `null` when absent.
- `get_content_template` handles mapping a template's common dimensions, so do not remap them separately.

## Decision Rules

- Use `dimension_name` as is for `preview_chart`'s `event_measures[].dimension_name` and `adhoc_filters[].field`.
- `dimension_data_type` is one of `STRING`, `INT`, and `TIMESTAMP`. `INT` means a numeric type, not integers only (decimals included). If it is `STRING`, use
  `COUNT` / `COUNT_DISTINCT`. If it is `INT`, `SUM` / `AVG` / `MIN` / `MAX` are also available. This value
  also decides which bucket kinds a dimension allows (the "Dimension buckets" section of `preview_chart`).
- A dimension with `is_price=1` is a revenue metric when the event also has an `is_currency=1` dimension. Then specify
  `currency` as well when calling `preview_chart`; otherwise pass none and state that the amounts are not converted.
- A dimension with `is_currency=1` is the currency filter dimension. `preview_chart` uses it automatically for `currency_options` internally.
- Use `dimension_idx` for `adhoc_filters[].idx`.

## On Failure

- Unknown `event_name`: the call fails. Check it against the `list_events` result.

## Recommended Chain

```
list_events → list_dimensions → (ORG_WORKSPACE_GATE) → preview_chart
```
