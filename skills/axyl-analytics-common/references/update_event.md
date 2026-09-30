# update_event (Update Event)

Updates a registered event's description and categories. **This is a write.**

> **Prerequisite:** Follow the common rules in [`../SKILL.md`](../SKILL.md).
> WRITE_APPROVAL and POST_WRITE_LINK apply.

## When to Use

- To correct an event description that no longer matches what is actually collected
- To group an event under categories, or change that classification

## Parameters

| Parameter | Required | Description |
|---------|------|------|
| `company_cd` | Y | Company code confirmed from `list_projects` |
| `event_idx` | Y | Event idx (`list_events.event_idx`) |
| `description` | Y | New description. Overwrites the existing one |
| `category_name` | N | List of category names |

**The event name cannot be changed.** The server accepts only the description and categories. The
name is a contract with whoever sends the log, and changing it would break ingestion. If the name is
wrong, register a new event and clean up in the console.

## Three Meanings of `category_name`

The value sent **replaces** the whole list, so omitting it differs from sending an empty list.

| Input | Behavior |
|---|---|
| Omitted | **Keeps** the existing categories (the tool reads the current value and sends it back) |
| `[]` | **Removes** all categories |
| `["AI Agent"]` | **Replaces** them with that value |

**Omit it unless removal is the intent.** Passing `[]` while only meaning to change the description
wipes the classification.

## Return Value

Returns `{"event_idx", "description", "console_url", "category_name", "response"}`.

- `category_name`: the categories after saving. Confirm they are what was intended
- `console_url`: link to the event detail screen. **Always include it when reporting the result**
  (POST_WRITE_LINK)
- `response`: the saved event

## Decision Rules

- **Confirm that `idx` and `description` in `response` match what was requested before reporting.**
  Never judge from the success code alone.
- `display_yn`, `event_name`, and `table_name` may look empty in `response`, but **the stored values
  were not erased** — the response simply does not populate those fields. Do not judge state from them.
- **Get user approval before calling (WRITE_APPROVAL).** Read back what changes from what.
- The description is stored in all five languages with the same text (matching console behavior; it
  is not translated).
- Attributes (dimensions) are untouched by this tool. Use `regist_event_dimension` for those.

## On Failure

- Empty `description`: it is required. The tool does not overwrite with a blank value.
- `event_idx` not found: confirm the idx with `list_events`.

## Recommended Chain

```text
list_events (check current description) → user approval → update_event
→ confirm stored values in response → report with console_url
```
