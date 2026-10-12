# update_event (Update Event)

Updates a registered event's description and categories, or its amount/currency attribute pair. **This is a write.**

> **Prerequisite:** Follow the common rules in [`../SKILL.md`](../SKILL.md).
> WRITE_APPROVAL and POST_WRITE_LINK apply.

## When to Use

- To correct an event description that no longer matches what is actually collected
- To group an event under categories, or change that classification
- To designate which attribute is the payment amount and which is its currency code, or clear that designation

## Parameters

| Parameter | Required | Description |
|---------|------|------|
| `company_cd` | Y | Company code confirmed from `list_projects` |
| `event_idx` | Y | Event idx (`list_events.event_idx`) |
| `description` | N | New description. Overwrites the existing one. Omit to keep it |
| `category_name` | N | List of category names |
| `price_dimension` | N | Name of the payment amount attribute (`list_dimensions.dimension_name`) |
| `currency_dimension` | N | Name of the currency code attribute (`list_dimensions.dimension_name`) |
| `clear_price_currency` | N | `true` clears the amount/currency designation. Cannot be combined with `price_dimension`/`currency_dimension` |

Pass **at least one** field to change (`description`, `category_name`, `price_dimension`, `currency_dimension`,
`clear_price_currency`).

**The event name cannot be changed.** For the event itself the server accepts only the description and categories. The
name is a contract with whoever sends the log, and changing it would break ingestion. If the name is
wrong, register a new event and clean up in the console.

## Three Meanings of `category_name`

The value sent **replaces** the whole list, so omitting it differs from sending an empty list.

| Input | Behavior |
|---|---|
| Omitted | Meant to **keep** the existing categories (the tool reads the current value and sends it back). If that read returns no categories, an empty list is sent and they are removed |
| `[]` | **Removes** all categories |
| `["AI Agent"]` | **Replaces** them with that value |

**Omit it unless removal is the intent.** Passing `[]` while only meaning to change the description
wipes the classification. Either way, check `category_name` in the result after the call.

## Amount and Currency Pair

**An event has at most one amount/currency pair, and one side cannot be set alone.** An amount attribute is converted
using the currency attribute next to it, so the server accepts only the pair.

| Input | Behavior |
|---|---|
| Both `price_dimension` and `currency_dimension` | Sets that pair. The previous pair is released |
| Only one of them | Uses the current pair's other side, which may be a hidden attribute. **Rejected before the call when the event has no pair yet** — pass both |
| `clear_price_currency=true` with no pair set | Nothing is sent (`before` and `after` are both `null`) |
| `clear_price_currency=true` | Clears the designation entirely |
| Same pair as now | Nothing is sent (`before` equals `after`) |

- The two names must differ — one attribute cannot be both amount and currency.
- A wrong designation affects chart queries, so check `dimension_data_type` in `list_dimensions` and the actual values
  before setting it: the amount attribute should be numeric (`INT`) and the currency attribute should hold currency codes.
- **Pass both names by default.** `list_dimensions` does not show hidden attributes, but the tool reads the event's full
  attribute list, so a pair whose side is hidden looks absent in `list_dimensions` while the tool still uses it. Passing
  both makes the result independent of what is hidden.
- Using the amount attribute in an aggregation makes `currency` required in `preview_chart` only when the event also has a
  currency attribute (`is_currency=1`), as `list_dimensions` describes. An event whose amount attribute was marked alone
  before the pair rule has no conversion; say so, and offer to set the pair.
- **The pair is set only with this tool.** `regist_event_dimension` has no amount/currency arguments.

## Return Value

Returns `{"event_idx", "console_url", ...}`. Changing the description or categories adds `description`, `category_name`, and
`response`; changing amount/currency adds `price_currency`.

- `price_currency`: `{"before": {"price", "currency"}, "after": {"price", "currency"}}` with attribute names (`null` when
  unset). `after` is **read back from the event after the request**; if the saved pair differs from the request the tool
  raises an error instead of returning, so a returned `after` is a confirmed save
- `category_name`: the categories after saving. Confirm they are what was intended
- `console_url`: link to the event detail screen. **Always include it when reporting the result**
  (POST_WRITE_LINK)
- `response`: the saved event

## Decision Rules

- **When the description or categories changed, confirm that `idx` and `description` in `response` match what was
  requested before reporting.** Never judge from the success code alone. A pair-only change returns no `response`; confirm
  it from `price_currency.after`.
- `display_yn`, `event_name`, and `table_name` may look empty in `response`, but **the stored values
  were not erased** — the response simply does not populate those fields. Do not judge state from them.
- **Get user approval before calling (WRITE_APPROVAL).** Read back what changes from what. For the pair:
  - Name the current pair as `list_dimensions` shows it (`is_price`/`is_currency`), and say that a hidden attribute can be
    part of it without appearing there; the actual previous pair comes back in `price_currency.before`.
  - Name the new pair.
  - Before setting a first pair, replacing one, or clearing one, find the registered metrics affected: in `list_metrics`,
    those whose `metric_config` aggregates this event's current amount attribute or, when the amount attribute is set or
    changes, the new one. List them in the summary — metrics on the current amount attribute lose currency conversion when it
    is replaced or cleared (they are no longer revenue metrics); metrics on the new one become revenue metrics, so every
    query of them must then specify `currency` (a revenue metric without one is rejected) and their values are converted to
    it; and a change of the currency attribute alone changes the conversion of metrics on the amount attribute. Say that
    saved charts built on these metrics may show different values.
  - When `list_dimensions` shows no current amount attribute, it may be hidden, so the metrics on it cannot be found before
    the call. Say in the summary that this impact was not checked, and offer to check the pair in the console
    (`console_url`) first.
- If `price_currency.before` names an attribute that `list_dimensions` does not show, it is hidden; tell the user and give
  `console_url` to check it.
- The description is stored in all five languages with the same text (matching console behavior; it
  is not translated).
- This tool does not add attributes or change their descriptions; use `regist_event_dimension`. It only changes an existing
  event's amount/currency pair.

## On Failure

- Nothing to change: ask the user what to change.
- Blank `description`: the tool does not overwrite with a blank value. Omit it if it is not changing.
- Only one side passed with no current pair: ask the user which attribute is the other side and call again with both.
- `clear_price_currency` passed together with a pair name: the tool rejects it. Ask whether to clear or to set a pair,
  and call again with one of them.
- Attribute not found: the tool checks the event's full attribute list, hidden ones included, so the name is not on this
  event. Confirm the names with `list_dimensions` (or `console_url` for a hidden one).
- `event_idx` not found: confirm the idx with `list_events`.
- Saved pair differs from the request: report the change as not confirmed and give the user `console_url` to check.
- API error or session expiry: do not retry automatically; check with `list_events` (description, categories) or
  `list_dimensions` (`is_price`/`is_currency`) whether it took effect. When the pair involves a hidden attribute,
  `list_dimensions` cannot show it; give the user `console_url` to check.

## Recommended Chain

```text
list_events (check current description) or list_dimensions (check the current pair: is_price/is_currency)
→ for setting, replacing, or clearing a pair, list_metrics (metrics aggregating the current or new amount attribute)
→ user approval → update_event → confirm response (description) or price_currency.after (pair)
→ report with console_url
```
