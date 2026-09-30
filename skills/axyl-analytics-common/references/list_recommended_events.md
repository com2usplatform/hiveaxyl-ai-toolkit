# list_recommended_events (List Standard and Company Event Candidates by SDK)

> **Prerequisite:** Follow the common rules in [`../SKILL.md`](../SKILL.md).

## When to Use

- After confirming which SDK the game repository uses, to query the standard event candidates the game will send itself.
- To check whether an event is collected automatically by the SDK.
- To review company-specific custom events alongside them. MCP excludes candidates whose names match a standard event.

## Parameters

| Parameter | Required | Description |
|---------|------|------|
| `sdk_type` | Y | `sdk_v4` or `axyl`. `unknown` returns no events |
| `company_cd` | Y | The company code confirmed in Phase 3 |
| `event_category` | N | The category to query, one of `User`, `Gameplay`, `Revenue`, `Campaign`, `Advertisement` |

## Return Value

Returns standard events in `events` and company-specific custom candidates in `company_custom_events`, along with the
count for each list. Standard events include the SDK type, collection ownership, and whether they are baseline events.

- `total_count` is the number of standard GAME and AUTO events mapped to the target SDK, and `events` returns all of them.
- `company_custom_count` is the number of company-specific custom events, and `company_custom_events` returns all of them.
- `company_custom_events` holds the company-specific candidates whose names do not collide with an active standard event.
- A company candidate colliding with a standard name is excluded from that array only. If the target SDK mapping is GAME, the standard
  candidate remains in `events`, and whether it is actually collected is confirmed through per-AppID ingestion queries and the repository's send code.
- This exclusion exists to prevent duplicate classification in the default recommendations; it is not a policy that forbids sending the same eventName again.
  When the user explicitly requests it, query the standard definition and the company dimensions separately and follow the parent skill's duplicate-send procedure.
- Query the properties of company-specific candidates with `list_dimensions(company_cd, event_name)`.
- `event_category` applies only to the standard `events`; company-specific candidates are returned in full.
- `events` carries no property details. Query an implementation candidate's properties with `get_event_spec`.
- Sorting puts `is_baseline=Y` first, then orders by `event_name` within the same priority.
- The standard baseline concept does not apply to company-specific custom events, so `is_baseline` is not returned for them.

## Decision Rules

- Do not guess the SDK type. Confirm `sdk_v4` or `axyl` in the repository before calling.
- Use the `company_cd` confirmed in Phase 3, and do not guess it.
- The tool always returns both the GAME and AUTO standard events for the target SDK.
- Do not filter on `is_baseline`; use it only for sorting and prioritizing the recommendation results.
- Classify `target_collect=AUTO` as `SDK automatic collection` and do not treat it as a target for ordinary code generation.
- Use the returned event names and collection ownership exactly as given; do not supplement them from memory or a separate static list.

## On Failure

- `INVALID_ARGUMENT`: fix `sdk_type` or `company_cd`.
- `DB_UNAVAILABLE`: report it as a query failure. Do not treat it as an empty candidate list.
- `sdk_type=unknown`: read the empty `events` and the guidance message in the response, determine the SDK, and call again.

## Recommended Chain

```text
Determine the SDK type → confirm Phase 3 company_cd → list_recommended_events
→ identify repository insertion points → get_event_spec / list_dimensions
```
