# <Game Name> Analytics Event Usage Guide

## Document Information

| Item | Content |
|------|------|
| Intended readers | Business, operations, and marketing staff |
| Game | <game name> |
| Target AppIDs | <AppID list> |
| As-of date | <YYYY-MM-DD> |
| Document scope | <recommendation / implementation complete / in operation> |

## At a Glance

| Events in this document | Usable | In preparation | Excluded | Needs confirmation |
|------------------|-----------|---------|------|-----------|
| <count> | <count> | <count> | <count> | <count> |

- Core collection purpose: <the user behavior or operational goal the event design makes visible>
- Currently usable scope: <the scope actually collected and verified>
- Check first: <items to confirm before making decisions or operating on this>

### Base design review

Aggregate every event template, and separate AUTO as `SDK automatic collection`.

| Total event template candidates | SDK automatic collection | Total GAME | Implementable | Existing send confirmed | Not currently implementable | Needs further review |
|----------------|----------------|-----------|-----------|----------------|------------------|----------------|
| <count> | <count> | <count> | <count> | <count> | <count> | <count> |

Total event template candidates = `SDK automatic collection + total GAME`, and total GAME must equal the sum of the four statuses that follow.

## Event Status

Record AUTO events in their dedicated list with only the event name, description, and collection ownership. Show the GAME and custom
events that are implementable or already being collected in a separate table, and group the events not implemented by reason in the
next section.

### SDK auto-collected events

| Event | Description | Collection ownership |
|--------|------|-----------|
| `<event_name>` | <event description> | SDK automatic collection |

### GAME and custom events

| Event | User behavior or situation | Purpose | Related metrics and analyses | Collection status |
|--------|------------------|-----------|----------------|-----------|
| `<event_name>` | <when the event occurs> | <why it is needed> | <the metrics, segments, and funnels it makes visible> | <usable / in preparation / excluded / needs confirmation> |

## Events Not Implemented and Why

Do not drop AUTO events from the overall list — show them in the dedicated list in the previous section. Do not duplicate them among
the GAME non-implementation reasons here. Group the GAME events not implemented by reasons a reader can follow, rather than technical
code details, but record every eventName.

The reason categories to use are: `existing send confirmed`, `the game has no such system`, `there is no process that produces the
event`, `the send timing cannot be determined`, `the required information cannot be provided`, `SDK constraint`, `a scope decision is
needed`, `duplication risk on some AppIDs`, `additional information needs confirming`, and `deferred out of this scope at the user's request`.

### <reason category> — <count>

| Event | Status | Reason |
|--------|------|------|
| `<event_name>` | <existing send confirmed / not currently implementable / needs further review> | <why it is not implemented> |

## Per-Event Usage Guide

Write these only for GAME and custom events. For an ordinary AUTO event, record only the event name, description, and
`SDK automatic collection` ownership in the dedicated list above — do not write individual details or an information table.

### <display name> (`<event_name>`)

| Item | Content |
|------|------|
| Event description | <the user behavior and when it occurs, in non-technical terms> |
| Collection purpose | <the question this event is meant to answer> |
| Occurrence condition | <the exact occurrence condition> |
| Usage examples | <metrics, funnels, segments, campaigns, or operational analyses> |
| Collection status | <usable / in preparation / excluded / needs confirmation> |
| Target AppIDs | <break it out if the status differs by AppID> |

#### Information provided

| Information | Meaning | Data type | Example value | Analytical use | Availability |
|------|------|--------|---------|-----------|-----------|
| `<attribute>` | <the property's business meaning> | <number / string / date-time> | `<example>` | <how to classify, filter, or aggregate by it> | <provided / in preparation / not provided / needs confirmation> |

#### Cautions when interpreting

- <the possibility of duplicate occurrences, the aggregation unit, conditions under which a value is not provided, or data lag>

## Usage Scenarios

| Purpose | Events and information to use | How to check it | Assumptions and cautions |
|------|--------------------|-----------|----------------|
| <for example: find where users drop out of the tutorial> | <the eventName and its properties> | <how to build the metric, funnel, or segment> | <the collection status and interpretation conditions> |

## Items for the Owner to Confirm

- <items to decide on metric definitions, operational policy, campaign conditions, or data verification>
