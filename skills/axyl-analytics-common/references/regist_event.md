# regist_event (Register Event)

Registers an event for the company and returns its `event_idx`. **This is a write.**

**Registration is optional.** An event registers automatically when its first log arrives, so a new
event name needs no registration before logs are sent. Use this tool only to set a description or
categories ahead of the first log.

> **Prerequisite:** Follow the common rules in [`../SKILL.md`](../SKILL.md).
> WRITE_APPROVAL, POST_WRITE_LINK, and DUPLICATE_GATE all apply.

## When to Use

- When the user explicitly wants an event's description or categories in place before its first log arrives
- Do not use it to resolve `NOT_READY / EVENT_NOT_DEFINED`. That verdict means no log has arrived yet;
  what resolves it is sending the log (`axyl-integrate-analytics-log`), not registering the name.

## Parameters

| Parameter | Required | Description |
|---------|------|------|
| `company_cd` | Y | Company code confirmed from `list_projects` |
| `event_name` | Y | Event name. Letters, digits, and underscores, 1–128 characters |
| `description` | N | What the log records |
| `category_name` | N | List of category names to group the event under |

Events are **company-scoped**, not project-scoped. The tool takes no `org_idx` or `appid_group`, and
one registration applies across every project in that company.

## Return Value

Returns `{"event_idx", "event_name", "console_url", "response"}`.
`event_idx` is what later identifies this event in `regist_event_dimension` and chart settings.

`console_url` is the console link to the registered event. **Always include it when reporting the
result.** Do not assemble it yourself; use the value the tool returned (POST_WRITE_LINK).

## Decision Rules

- **Never invent the event name (NO_GUESSING).** It is a contract with whoever sends the log and
  must match exactly, including case. If the name is not settled, ask rather than register.
- **Check for an existing name with `list_events` first (DUPLICATE_GATE).** The tool does not block
  duplicates.
- **Get user approval before calling (WRITE_APPROVAL).** Read back the name and description.
- **It cannot be undone.** No delete tool is provided, so cleanup has to happen in the console.
- **Registering does not start ingestion.** Data arrives only once the client sends logs under that
  name; until then `last_data_date_kst` in `list_events` stays empty. Do not say the event "is being
  collected" right after registering.
- **Registering also creates the 8 built-in attributes** (`appId`, `userId`, `eventTime` and so
  on). Do not add those yourself. Use `regist_event_dimension` for this event's own attributes.

## On Failure

- `event_name` format error: use only letters, digits, and underscores.
- Access error: check that `company_cd` is correct.

## Recommended Chain

```text
list_events (duplicate check) → user approval → regist_event
→ regist_event_dimension (add attributes) → report with console_url
```
