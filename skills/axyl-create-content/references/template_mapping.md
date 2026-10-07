# Template Conversion (platform template params → `create_*` arguments)

Read this document when moving the `params` returned by `get_content_template` into `preview_*`/`create_*` arguments.

> **Prerequisite:** Follow the flow in [`../SKILL.md`](../SKILL.md). Even after conversion, still perform the
> `preview_<type>` verification and WRITE_APPROVAL before saving.

## When to Read This

- When an `axyl-design-dashboard` handoff carries a `platform template reference`
- When the user asks to build content from a specific template
- When building similar content by referring to existing content (`get_content.params`) — the format is the same

## Two Principles

**1. The tool has already converted the idx values. Do not map them yourself.**
`get_content_template` returns the template with its idx values already converted to the target company's, and the
token's `text`/`name`/`field` changed to the company's names as well. Use those values as given, and **carry every token field the
conversion tables below read** (`type`, `measure_field`, `measure_formular`, `measure_group_field`, `measure_group_format`,
`measure_group_interval`, and so on) — the mapping depends on them. The only limit is display: do not show raw token
fields to the user. **Do not look them up again by name** — that either fails or picks the wrong metric (see "Why you must not search by name" below).

When there is no corresponding company entry, that slot is `idx: null` + `unresolved: true`, and the list is gathered in
`params.unresolved_idx`. **That means this company has no such definition, so that measure cannot be built** —
ask the user whether to leave it out or to prepare the metadata and logs first. Do not substitute some other metric on your own.

**2. `params` is the console's save format (tokens).** Its format differs from the `create_*` arguments. Passing the tokens
through as is means the `metric_idx` key is missing, so it is treated as event mode and fails with a missing-required-key error.
You must **expand** them per the table below. Only the **format** changes — **the idx values are already correct**.

## Mapping

| Template `params` | `create_*` argument | Conversion |
|---|---|---|
| `chart_type` | `chart_type` | As is |
| `measure[]` | `event_measures[]` | See "Converting measure" below |
| `dimensions[]` | `dimensions` | As is (the idx values are already the company's) |
| `date_params` | `date_params` | For a `"V"` type, pass only the relative offsets (see Pitfalls) |
| `adhoc_filters` | `adhoc_filters` | The idx values are already the company's; **check the filter values** before carrying them over (see "Dimension filters" below) |
| `grid_config_summary.pivot_col_ids` | `pivot_col_ids` | As is |
| `grid_config_summary.row_group_col_ids` | `row_group_col_ids` | As is |
| `grid_config_summary.aggregation_model` | `aggregation` | **Convert list → dict** (see Pitfalls) |
| `grid_config_summary.hidden_col_ids` | `hidden_col_ids` | As is |
| `base_event`/`retention_event` | The same-named `create_retention` arguments | As is |
| `conditions[].base_dimension` | `create_retention`'s **`identifier`** | See "Converting funnels and retentions" below |
| `sections[]` | `create_funnel`'s `sections` | **The key names differ.** See "Converting funnels and retentions" below |

## Converting measure

Read `measure[].expressions[].tokens` and build the terms.

| Token composition | Form to build |
|---|---|
| A single `{type:"metric", idx, text, measure_field}` | `{"metric_idx": <the token's idx>, "metric_name": <the token's text>}` — both are already the company's values |
| A `{type:"event"}` + `{type:"event_detail"}` pair | `{"event_idx", "event_name", "dimension_idx", "dimension_name", "formular"}` — `event_detail.measure_field` → `dimension_name`, `measure_formular` → `formular` |
| `event_detail` has `measure_group_field`/`measure_group_format` | It is a two-stage aggregation. See "Converting a two-stage aggregation" below |
| `operator` and `number` tokens are mixed in | A formula → `{"operands": [terms...], "operators": ["/", ...]}` |

### Converting a two-stage aggregation

When an `event_detail` token has `measure_group_field` (always `"dateTime"`) and `measure_group_format`, the measure is defined
as a first aggregation by time unit plus a second aggregation (peak concurrent users, and so on). **Do not put
`measure_formular` straight into `formular`** — it is a comma-joined value (`"COUNT_DISTINCT,MAX"`), and passing it through
either saves the wrong aggregation or raises an error. Split it as below.

| Token field | `create_*` argument | Conversion |
|---|---|---|
| The **first** value of `measure_formular` | `formular` | `"COUNT_DISTINCT,MAX"` → `"COUNT_DISTINCT"` (the first aggregation) |
| The **second** value of `measure_formular` | `group_formular` | → `"MAX"` (the second aggregation. `MAX`\|`AVG`\|`LAST`) |
| `measure_group_format` | `group_format` | As is (`MINUTE`\|`H`\|`D`\|`M`\|`Y`) |
| `measure_group_interval` | `group_interval` | Pass it only when `group_format` is `"MINUTE"` (`1`\|`2`\|`5`\|`10`). Otherwise **do not pass it** — the server's saved copy comes back as `0` when unused, and passing that through raises a `ValidationError` |
| `measure_group_field` | — | Do not pass it. The tool fills it in as `"dateTime"` automatically |

The formats and constraints follow the "Two-stage aggregation" section of `preview_chart`.

> **If you see `expressions[].measure_date`**, that term uses a field that exists **only in a metric definition** (it aggregates
> that period into one value and spreads it as a constant across the chart's dates). It cannot be expressed as a `create_*`
> argument, so do not move it into a chart — reference that metric by `metric_idx`, or register a new one with `create_metric`.

Keep the measure-level fields outside.

- `measure[].name_alias` → `alias`
- `measure[].decimal_point` → `decimal_point`
- `measure[].percent` → `percent`
- If `measure[].currency_options` is present → **`currency` is required.** Confirm it with `list_currencies(company_cd)` and use
  `"USD"` if the result is empty. Leaving it blank raises a `ValidationError`.

### Why You Must Not Search by Name

`measure[].name` is the platform metric name, which can differ from the company metric name. An illustrative example:

| Template `name` | Template `name_alias` | Company metric (illustrative) |
|---|---|---|
| `Sales` | In-App Revenue (KRW) | In-App Revenue |
| `Sales Count` | Purchase Count | **Revenue Count** |
| `PU` | PU | PU |

In the `Sales Count` row, neither the name nor the alias matches the company metric — the alias says **Purchase** Count
while the company calls it **Revenue** Count. If the company also has an unrelated metric such as Purchase Quantity, a
partial-match search **picks the wrong metric**.

That is why the tool does the mapping and the skill uses its result. Do not match by name.

## Converting Funnels and Retentions

### Funnels — the template keys differ from the argument keys

| Template `sections[]` | `create_funnel` argument | Handling |
|---|---|---|
| `table_idx` | **`event_idx`** | The value is already the company's idx. **Change the key name when passing it** |
| `event_name` | `event_name` | As is (the tool fills it in when the template lacks it) |
| `title` | `title` | As is |
| `identifier` (first step), `target_identifier` (later steps) | `identifier` | The template stores the first step's identifier in `identifier` and each later step's in `target_identifier`. Pass each step's value as `identifier` (see below) |
| `filters` | `filters` | Only `filter_type="index"` is converted. Leave snapshot/segment as is; if one is not this company's, **do not drop it silently** (see below) |
| `table_description` | `table_description` | As is. May be omitted |
| `table_type` | `table_type` | **The value systems differ.** The template uses `"table"`, the argument uses `"hive"`\|`"adjust"`\|`"appsflyer"` — use the default `"hive"` |
| `identifier_type`, `target_identifier_type`, `logical_operator`, `table_name`, `segment_idx` | none | **Discard them.** The tool builds them internally |

Passing `table_idx` through as is fails with a missing required `event_idx` key.

### Retentions — `conditions` collapses into the single `identifier` argument

The template's save format is an array of conditions, but the tool's argument is a single dimension name.

```
Template  conditions: [{"operator":"=", "base_dimension":"userId", "retention_dimension":"userId"}]
Argument  identifier: "userId"
```

`create_retention` rebuilds `conditions` from `identifier`. If a template has two different dimensions, that composition cannot
be expressed with the current tool arguments, so tell the user.

### identifier can be any dimension of the event

It is not restricted to `userId`/`deviceId`. Dimension **names** are shared between the platform and the company, so no
substitution is needed — just pass them through (the tool still flags a name missing on the company event).

Even with a matching name, however, **there is no guarantee the dimension exists on the company's event** — some dimensions
exist only on the platform and were never derived for the company (for example, `playerId`). So the tool checks existence for you.

```json
{"identifier": "playerId", "identifier_unresolved": true}
```

A slot carrying `{key}_unresolved` means that dimension is not on the company's event, and it also appears in `unresolved_idx`
with `kind: "dimension_name"`. Do not swap in a different dimension — confirm with the user, because a substitution such as
`playerId` → `userId` is a judgment that changes what is being aggregated.

The one exception is a `dimension_substitutions` entry in the design-dashboard context (such as `os → _os` or
`os → hiveAttributes.os`), which the user already approved. Replace every slot that references `X` — measure, breakdown, and
filter — with the chosen dimension's name and `dimension_idx`. Change both the filter's dimension and its value: for example,
when `eventAttributes.os = "A"` becomes `hiveAttributes.os`, map the filter to `hiveAttributes.os = "android"` if that mapping
was confirmed. Carry the literal over unchanged only when the same value was observed in the destination. Never drop a filter
silently. Apply the approved `filter_value_mappings`, confirm the fully substituted result with the preview, and do not apply a
switch that is not in the list.

## Worked Example — "Revenue - Product Revenue by Country"

Template `params` (excerpt)

```json
{"chart_type": "table",
 "measure": [
   {"name": "Sales", "name_alias": "인앱 매출액(KRW)", "decimal_point": 0,
    "expressions": [{"tokens": [{"idx": "<platform_sales_metric_idx>", "type": "metric", "text": "Sales",
                                 "measure_field": "price"}], "filters": []}],
    "currency_options": [{"event_idx": "<platform_purchase_event_idx>", "price_dimension_name": "totalPrice",
                          "currency_dimension_name": "currency"}]},
   {"name": "Sales Count", "name_alias": "유저당 구매 건 수",
    "expressions": [{"tokens": [{"idx": "<platform_sales_count_metric_idx>", "type": "metric", "text": "Sales Count"},
                                {"idx": "0", "type": "operator", "text": "/"}]},
                    {"tokens": [{"idx": "<platform_pu_metric_idx>", "type": "metric", "text": "PU"}]}]}],
 "dimensions": [{"idx": "<platform_country_dimension_idx>", "name": "country"},
                {"idx": "<platform_product_dimension_idx>", "name": "productName"}],
 "grid_config_summary": {"pivot_col_ids": ["country"],
                         "row_group_col_ids": ["dateTime", "productName"],
                         "aggregation_model": [{"col_id": "인앱 매출액(KRW)", "agg_func": "sum"}],
                         "hidden_col_ids": ["dateTime", "productName"]}}
```

Conversion result

```json
{"chart_type": "table",
 "event_measures": [
   {"metric_idx": "<company_sales_metric_idx>", "metric_name": "인앱 매출액", "alias": "인앱 매출액(KRW)",
    "decimal_point": 0, "currency": "KRW"},
   {"alias": "유저당 구매 건 수",
    "operands": [{"metric_idx": "<company_sales_count_metric_idx>", "metric_name": "매출 건 수"},
                 {"metric_idx": "<company_pu_metric_idx>", "metric_name": "PU"}],
    "operators": ["/"]}],
 "dimensions": [{"idx": "<company_country_dimension_idx>", "name": "country"},
                {"idx": "<company_product_dimension_idx>", "name": "productName"}],
 "pivot_col_ids": ["country"],
 "row_group_col_ids": ["dateTime", "productName"],
 "aggregation": {"인앱 매출액(KRW)": "sum"},
 "hidden_col_ids": ["dateTime", "productName"]}
```

The template `params` above is **the original, shown for explanation**; what `get_content_template` actually returns is already substituted.

```json
{"idx": "<company_sales_metric_idx>", "type": "metric", "text": "인앱 매출액", "measure_field": "price"}
```

So the skill's job is **format conversion only**.

- Replace metric and dimension idx placeholders with the actual company values returned by `get_content_template`, then use them as is
- Because `currency_options` is present, `currency: "KRW"` was added (confirmed with `list_currencies`)
- The formula was expanded into `operands`/`operators`, and `alias` was placed outside the measure
- The `aggregation_model` list became the `aggregation` dict

## Pitfalls

- **`aggregation` is a dict.** The template gives a `[{"col_id":..., "agg_func":...}]` list, but the argument is a
  `{col_id: agg_func}` dict. Passing the list through raises a `ValidationError`.
- **`col_id` rules** — the aggregation's `col_id` is the measure's `name_alias` (not the company metric name), while the pivot
  and row-group `col_id` values are dimension names or `dateTime`. In a ranking table, `순위` (Rank) is also available.
- **When `date_params` is `"V"` (relative), pass only the `start_value`/`end_value` offsets.**
  Do not compute `start_date`/`end_date` or copy the template's values. The absolute dates stored alongside in the template were
  resolved at save time and are past values, not the relative period's configuration. The MCP tool also defends against this by
  stripping absolute dates from a `"V"` range.
- **The template author's company and project are removed from params before you get them.** A saved template carries the
  creator's `company_cd`, `appid_group`, and `game_name` (for example, `company_cd: <template_company_cd>`,
  `appid_group: "<template_appid_group>"`), and using them as is would build content for a different company and project. The tool
  strips them, so do not look for the project in params — use the value confirmed through PROJECT_ID_GATE.
- **A funnel section's event idx lives in `table_idx`.** The value comes substituted, but the `create_funnel` argument is
  `event_idx`, so change the key name when passing it (see "Converting funnels and retentions" above).
- **The `idx` of a filter whose `filter_type` is `snapshot`/`segment` is not a dimension** (it is a snapshot or segment number).
  The tool leaves it unsubstituted. If that value is not this company's snapshot or segment, **do not drop it silently** —
  removing it widens the population. Tell the user the filter cannot be carried over, and let them choose: pick this
  company's snapshot or segment for the same purpose (`list_segment_snapshots`), build without it knowing the scope is
  wider, or skip that content.
- **Do not arbitrarily substitute an `unresolved_idx` entry.** The company has no such definition, so putting a similar metric in
  its place would show the user a different metric. Confirm with the user whether to leave it out.
- **Dimension filters (`filter_type="index"`, in `adhoc_filters` and measure `filters`)** — the tool resolves only the
  dimension's idx; the filter **values stay exactly as the template wrote them**. Never let either case change the result silently:
  - **The dimension is unresolved** (not on the company's event): dropping the filter removes it, so the population gets
    **wider**. Say so, and let the user choose: name the company dimension that means the same thing / build without the
    filter knowing the scope is wider / skip that content.
  - **The dimension resolved but a value may not exist here**: before carrying the filter over, check this company's values with
    `query_adhoc(dimension_names=[<that dimension>])` over a recent period. The distribution returns only the top values (20 by
    default), so absence proves absence **only when `values_truncated=false`**. When it is `true`, retry with a larger
    `value_limit` (up to 100); if it is still truncated, mark the filter value `unverified` and ask the user instead of
    concluding it is missing. A value confirmed absent means the filter would match nothing and the content would come out
    **empty or near zero** without any error. Do not save it as is — tell the user and let them choose: replace it with this company's value / build without the filter / skip that content.
    Platform-wide codes such as `os` or `market` usually match; company-specific values such as server or product IDs almost never do.
- For a metric-based measure, get the ingestion-check event and property from the company metric's `metric_config`
  (`{type:"event"}.text` / `{type:"event_detail"}.measure_field`). For an event-based measure, use the same tokens from the
  template params directly. Do not work backwards from an incoming property to the event.
- **Use the default (False) for `include_grid_config`.** Display state such as column widths and scroll position is not needed,
  and the summary (`grid_config_summary`) maps 1:1 to the arguments in the table above.
- Do not put `metric_config` tokens straight into `event_measures`. Without the `metric_idx` key it is treated as event mode and
  fails with missing required keys such as `event_idx`.
- For ratios already registered as company metrics, such as ARPU, ARPPU, and PU RATE (%), use the metric rather than building a formula.
