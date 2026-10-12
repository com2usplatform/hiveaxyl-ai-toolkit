# regist_event_dimension (Register or Update Event Attribute)

Adds an attribute (dimension) to an event, or updates one that was added earlier. **This is a write.**

> **Prerequisite:** Follow the common rules in [`../SKILL.md`](../SKILL.md).
> Both WRITE_APPROVAL and POST_WRITE_LINK apply.

## When to Use

- Right after creating an event with `regist_event`, to define the values it carries
- When the event exists but a needed attribute is missing from `list_dimensions`

## Parameters

| Parameter | Required | Description |
|---------|------|------|
| `company_cd` | Y | Company code confirmed from `list_projects` |
| `event_idx` | Y | Event idx (`list_events.event_idx`, or `regist_event.event_idx`) |
| `dimension_name` | Y | Attribute name. Letters, digits, and underscores, 1–128 characters |
| `data_type` | Y | One of `STRING` `INT` `TIMESTAMP`. `INT` is the numeric type (decimals included). **Required even for an existing attribute.** For an existing attribute, pass its current type; a different type is rejected unless `change_data_type=true` |
| `change_data_type` | N | `true` only when the user explicitly asked to change an existing attribute's type. Default `false`: a type different from the stored one is not saved, and the error names the stored type and whether the attribute is hidden |
| `description` | N | What the value holds. **Omit to keep an existing attribute's description (including per-language text)**. An existing attribute's visibility and attribute kind (event or platform attribute, not `data_type`) are always kept (a hidden attribute does not appear in `list_dimensions`, but registering the same name updates it) |

**One attribute per call.** Call repeatedly when several are needed.

## It Sits On Top of a Full-Replace API

The server's attribute update API **overwrites every attribute with the list it receives.** Sending
only the new one would remove built-ins such as `appId` and `userId`.

This tool **reads the current attributes first, merges, and sends the whole list back.** The caller
passes only the one attribute being added, and since there is no way to assemble the list, nothing
can be wiped by omission. If the event cannot be read, the tool errors instead of saving; an event with no attributes
yet is the normal path for the first one.

## Return Value

Returns `{"event_idx", "dimension_name", "action", "dimension_count", "dimension_count_before", "console_url",
"dimension"}`.

- `action`: `"added"` or `"updated"`
- `dimension_count`: total attributes sent this call, including built-ins. `dimension_count_before`: the count
  before the call. **If it dropped compared with before the call, something went wrong — tell the user.** A freshly registered event already
  has the 8 built-in attributes, so `dimension_count_before` starts at 8.
- `console_url`: link to the event detail screen. **Always include it when reporting the result.**
- `data_type_before`: present only when the type was changed; report the change from it to the new type.

## Decision Rules

- **Built-in attributes cannot be modified.** `appId`, `appIdGroup`, `dateTime`, `deviceId`,
  `eventName`, `eventTime`, `identifierProvider`, and `userId` are platform-provided, and passing one
  of those names fails.
- **Never guess `data_type` (NO_GUESSING).** It decides what aggregation is possible later — `STRING`
  allows only `COUNT` and `COUNT_DISTINCT`, while `INT` also allows `SUM`, `AVG`, `MIN`,
  and `MAX`. It also decides which buckets a chart can use on the dimension (buckets themselves are set per chart, not here): numeric range buckets require `INT`, `STRING` supports value groups
  only, and `TIMESTAMP` supports no buckets. Registering a numeric log value as `STRING` makes sums and numeric range
  buckets impossible.
- **The attribute name must match the key the log sends exactly.** Otherwise the attribute stays empty.
- **Get user approval before calling (WRITE_APPROVAL).** Read back the name and data type, and say that if a hidden attribute
  with the same name exists, this call updates that attribute with these values (hidden attributes do not appear in `list_dimensions`).
- An existing name is updated (`action="updated"`): the type changes only with `change_data_type=true`; the description
  changes only when passed. Confirm that the update is intended first, and tell the user when a name you expected to be new comes
  back `"updated"` (it was a hidden attribute). A hidden attribute stays hidden and never appears in `list_dimensions`, so confirm the write from the returned `dimension` instead, and tell the user to make it visible in the console (`console_url`) before it can be used in a chart or filter.
- **This tool does not set amount/currency.** An event has at most one amount/currency pair and one side cannot be set alone.
  After registering an amount attribute, set the pair with `update_event`'s `price_dimension`/`currency_dimension`.
  An existing attribute's amount/currency setting is always kept; a new attribute starts without one.

## On Failure

- Built-in attribute name: use a different name (call again after fresh WRITE_APPROVAL (say what changed)) or handle it in the console.
- Could not read the attributes for `event_idx`: nothing is saved. Recheck `event_idx` — saving with
  a wrong one would erase every existing attribute, so the tool blocks it first.
- `data_type` error: use a value from the allowed list verbatim, and call again after fresh WRITE_APPROVAL (say what changed).
- Type differs from the stored one: nothing is saved. Tell the user the stored type (and that the attribute is hidden, when
  the error says so) and ask whether to change it — a type change alters which aggregations work. Call again with
  `change_data_type=true` only after they confirm, with fresh WRITE_APPROVAL; otherwise keep the stored type or use another name.
- API error or session expiry: do not retry automatically; check with `list_dimensions` whether it took effect. If the name
  is still missing, it may be a hidden attribute that `list_dimensions` cannot show; ask the user to check it in the console
  (`console_url`) before calling again.

## Recommended Chain

```text
regist_event → user approval → regist_event_dimension (repeat per attribute)
→ verify with list_dimensions (a hidden attribute: verify from the returned dimension and ask the user to unhide it)
→ for an amount attribute: user approval → update_event (price_dimension/currency_dimension)
→ report with console_url
```
