# validate_event_spec_contract (Diagnose Event Metadata Contract)

> **Prerequisite:** Follow the common rules in [`../SKILL.md`](../SKILL.md).

## When to Use

- To check the consistency of all active definitions after an event metadata release or migration.
- When `AMBIGUOUS_SPEC` or `SCHEMA_MISMATCH` recurs across several events.

This is not a tool to call routinely during event recommendation or code generation. It also does not inspect the
game repository's payload or whether logs are actually ingested.

## Parameters

| Parameter | Required | Description |
|---------|------|------|
| `limit` | N | Maximum number of error samples to return. Default 20 |

`limit` restricts only the number of `errors` returned. Check the total error count with `error_count`.

## Return Value

| Field | Meaning |
|------|------|
| `ok` | Whether the whole check passed |
| `checked_event_count` | Number of events that parsed correctly and were checked |
| `error_count` | Total number of errors found |
| `errors` | Error samples, up to `limit` |

Scope of the check:

- Required event fields: `event_name`, `event_category`, `description_ko`, `attributes`
- Whether an `sdk_v4` or `axyl` SDK mapping exists
- Conflicts or omissions between per-SDK collection ownership and the base event configuration
- Validity of property names and ingestion-location fields

## Decision Rules

- If `ok=false`, do not treat the individual failing events as valid definitions.
- If `error_count` is greater than the length of `errors`, `limit` is showing only some of the errors.
- Do not use this tool's result to modify or fill in event names or property names. Report them as items for the metadata management area to fix.
- Recheck one event's full error set and per-SDK definitions with `get_event_spec`.

## On Failure

- `DB_UNAVAILABLE`: do not finalize the metadata consistency result; report it as a database query failure.
- If there are not enough error samples, raise `limit` within the range you need and call again.

## Recommended Chain

```text
Recurring metadata errors
→ validate_event_spec_contract
→ get_event_spec for each failing event
```
