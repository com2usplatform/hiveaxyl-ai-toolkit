# get_event_spec (Get Standard Event Details)

> **Prerequisite:** Follow the common rules in [`../SKILL.md`](../SKILL.md).

## When to Use

- To finalize the properties to send after mapping `list_recommended_events` candidates to the repository's actual logic.
- To check whether an event or property is collected by the game or automatically by the SDK for the target SDK.
- To check a property's value convention in `attributes[].desc_ko`.

## Parameters

| Parameter | Required | Description |
|---------|------|------|
| `event_name` | Y | Name of the standard event to look up |
| `sdk_type` | Y | `sdk_v4` or `axyl` |

## Return Value

| Field | Meaning |
|------|------|
| `target_collect` | Collection ownership for the event as a whole. `GAME` means the game sends it directly; `AUTO` means the SDK collects it automatically |
| `attributes[].name` | Name of the property to send |
| `attributes[].data_type` | Property data type |
| `attributes[].desc_ko` | Meaning of the property value and its format convention |
| `attributes[].target_collect` | Collection ownership for that property, per SDK |
| `attributes[].field` | Post-ingestion location classification for the property |

`attributes[].field` is not the location you send the value in. The payload you send is flat JSON that keeps required
properties and event properties at the same level. Do not build `attributes`, `eventAttributes`, or `hiveAttributes` nesting.
Do not create a property name starting with `_` either. It is the reserved namespace for pipeline-processed metadata stored in
`hiveAttributes`. SDK auto-collected and header values do not receive an `_` prefix merely
because they are stored in `hiveAttributes`.

## Decision Rules

- Use `event_name` and `sdk_type` exactly as produced by `list_recommended_events` and the SDK determination result.
- If the event's `target_collect=AUTO`, do not generate ordinary send code for it.
- For a property with `attributes[].target_collect=GAME`, confirm the actual value source and type in the repository before sending it.
- Do not arbitrarily change property names, types, or value conventions, and do not guess at missing definitions.
- Do not substitute another SDK's definition for an event that has no mapping for the target SDK.

## On Failure

- `INVALID_ARGUMENT`: fix the missing `event_name` or the invalid `sdk_type`.
- `EVENT_NOT_FOUND`: the event does not exist or is not mapped to that SDK. Do not substitute another SDK's definition.
- `AMBIGUOUS_SPEC` or `SCHEMA_MISMATCH`: report it as a metadata definition error and stop generating code for that event.
- `DB_UNAVAILABLE`: report it as a query failure. Do not guess events or properties.

## Recommended Chain

```text
Phase 3 company_cd confirmed → list_recommended_events → identify repository insertion points
→ get_event_spec → generate send code
```
