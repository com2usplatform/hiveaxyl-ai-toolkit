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
| `data_type` | Y | One of `STRING` `INT` `INTEGER` `FLOAT` `BOOLEAN` `TIMESTAMP` |
| `description` | N | What the value holds |
| `price` | N | `true` if the attribute is a purchase amount |
| `currency` | N | `true` if the attribute is a currency code |

**One attribute per call.** Call repeatedly when several are needed.

## It Sits On Top of a Full-Replace API

The server's attribute update API **overwrites every attribute with the list it receives.** Sending
only the new one would remove built-ins such as `appId` and `userId`.

This tool **reads the current attributes first, merges, and sends the whole list back.** The caller
passes only the one attribute being added, and since there is no way to assemble the list, nothing
can be wiped by omission. If the read comes back empty, the tool errors instead of saving.

## Return Value

Returns `{"event_idx", "dimension_name", "action", "dimension_count", "console_url", "dimension"}`.

- `action`: `"added"` or `"updated"`
- `dimension_count`: total attributes sent this call, including built-ins. **If it dropped compared
  with before the call, something went wrong — tell the user.** A freshly registered event already
  has the 8 built-in attributes, so `dimension_count_before` starts at 8.
- `console_url`: link to the event detail screen. **Always include it when reporting the result.**

## Decision Rules

- **Built-in attributes cannot be modified.** `appId`, `appIdGroup`, `dateTime`, `deviceId`,
  `eventName`, `eventTime`, `identifierProvider`, and `userId` are platform-provided, and passing one
  of those names fails.
- **Never guess `data_type` (NO_GUESSING).** It decides what aggregation is possible later — `STRING`
  allows only `COUNT` and `COUNT_DISTINCT`, while `INT` and `FLOAT` also allow `SUM`, `AVG`, `MIN`,
  and `MAX`. Registering a numeric log value as `STRING` makes sums impossible.
- **The attribute name must match the key the log sends exactly.** Otherwise the attribute stays empty.
- **Get user approval before calling (WRITE_APPROVAL).** Read back the name and data type.
- An existing name is overwritten (`action="updated"`). Confirm that the update is intended first.
- Using a `price=true` attribute in aggregation makes `currency` required in `preview_chart`'s
  `event_measures`.

## On Failure

- Built-in attribute name: use a different name or handle it in the console.
- Could not read the attributes for `event_idx`: nothing is saved. Recheck `event_idx` — saving with
  a wrong one would erase every existing attribute, so the tool blocks it first.
- `data_type` error: use a value from the allowed list verbatim.

## Recommended Chain

```text
regist_event → user approval → regist_event_dimension (repeat per attribute)
→ verify with list_dimensions → report with console_url
```
