# Event Design and Code Generation

This document decides **which events to recommend or exclude, and where to insert them**. Payload and value rules follow the SDK log send rules, and per-SDK differences follow the selected SDK flow.

## 1. Determine the request type

Determine the request type before querying events.

### Broad recommendation

With no specific target metric, query every GAME event and map it to the systems present in the repository.
SDK v4 collects the core events automatically, so having few or none can be normal — check the game logic events as well.
`is_baseline=Y` means review and display it first; it is not a condition that narrows the query scope.

```
Example questions: "Send logs to Analytics", "Write the code to send event logs to Analytics"
```

### Goal based

Break the goal down into metrics and dimensions, then find the supporting events in the description_ko of the event query results.
- AU by server: the AU supporting event + the serverId dimension
- Revenue by country: the revenue supporting event + the country dimension
- Concurrent users: the session-maintenance supporting event and its send interval
```
Example questions: "Write the event send code so we can see revenue by country", "Write the event send code so we can see the concurrent users metric"
```

If there are several candidates, explain the differences in trigger and metric meaning. If the goal event is AUTO, do not convert
it into an ordinary creation candidate — move to the AUTO event enrichment exception in section 3.

## 2. Query the event definitions

Determine event templates only from the MCP definition query results.
Do not supplement event names, property names, or collection ownership from memory or a static list.

| Tool | Purpose |
|------|------|
| list_recommended_events | Query the SDK event template candidates and the company-specific custom candidates whose names do not collide with an event template |
| get_event_spec | Query a send candidate event's property names, types, automatic collection status, and value descriptions |
| list_dimensions | Query a company-specific custom event, or a property registered for the company under the same name as a standard one |

Call rules:

- Use the sdk_type confirmed in Phase 1.
- Always pass the company_cd confirmed in Phase 3.
- list_recommended_events always returns the target SDK's GAME and AUTO event templates together.
- Do not use is_baseline for filtering; use it only for sorting and prioritizing the recommendation results.
- Query detailed properties with get_event_spec only for events whose insertion point you found.
- If the tool is unavailable, do not guess the event templates. Confirm whether to proceed with unique custom events only.

MCP excludes from `company_custom_events` any company-specific row whose name collides with an active event template. Such a row
does not settle whether it was auto-copied or pre-registered by the customer, and if the target SDK mapping is GAME, the event
template candidate under that name stays in `events`. The skill does not reclassify it as company-unique custom or AUTO — it checks
the actual ingestion per AppID and the repository's send code.

Review candidates in this order: `events the user explicitly requested → SDK event template baseline → SDK event template
non-baseline → company-specific custom → repository-unique custom`. Within each event template group, record AUTO's status only and
review GAME as implementation candidates.

A company-specific custom candidate is also not implemented automatically if you cannot confirm the system, trigger, and property
value sources in the repository — leave it in the excluded or needs-further-review reasons.

For an additional send under the same eventName, distinguish ruling out duplicates among the default recommendation candidates from
a user-specified implementation. The model does not propose a duplicate send on its own, but it is not prohibited when the user
explicitly requests one. Check that event template's definition with `get_event_spec`, and the company's registered properties with
`list_dimensions(company_cd, event_name)`.

Check the following right after the query.

1. Separate out the total event template candidate count and the GAME/AUTO and `is_baseline=Y`/`N` counts.
2. Classify AUTO as `SDK automatic collection` and map the GAME candidates to the repository.
3. Do not settle the recommendation or implementation scope before classifying every candidate.

Key response fields:

| Field | Where it is used |
|------|--------|
| event_name | Used as is in code and queries |
| target_collect | Whether ordinary creation is possible |
| is_baseline | Recommendation priority |
| event_category | Grouping the results |
| description_ko | Judging the trigger, target metric, and insertion location |
| attributes[].name | The property name to send |
| attributes[].data_type | The type to send |
| attributes[].target_collect | Judging which properties the game fills in |
| attributes[].desc_ko | Judging the value convention and the value source in code |
| attributes[].field | Reference for the ingestion location. Not to be used as the send structure |
| company_custom_count | The total number of company-specific custom candidates |
| company_custom_events[] | Company-specific candidates whose names do not collide with an event template |

## 3. Judge the creation candidates

| target_collect | Ordinary behavior |
|----------------|-----------|
| GAME | A creation candidate |
| AUTO | Marked `SDK automatic collection` in the recommendation results and excluded from ordinary code generation |

Include AUTO in the overall recommendation results too, but classify it as `SDK automatic collection`. The same event can have a
different target_collect per SDK, so do not judge creatability from the event name alone. Do not add event templates from a separate
list when they were not returned for the target SDK.

### AUTO event enrichment exception

Only when the user wants to add property values to an auto-collected event (target_collect=AUTO), present the following options and
let the user decide.

#### A. Separate event name

- Advantage: no impact on the existing metrics or the auto-collected event.
- Caution: it adds one more metric definition and eventName.
- Propose a name that describes the actual trigger and settle it with the user.

#### B. Same eventName + dataSource distinction

- Advantage: keeps the eventName.
- Caution: the ingested value is found in hiveAttributes' `_dataSource`.
- Caution: the SDK auto-collected portion and the directly sent portion coexist, so every query, dashboard, and verification needs a
  dataSource filter. Without the filter, the two paths are summed together.

If option B is chosen, state that SDK's direct-send dataSource in the recommendation, the code review, the duplicate check, the
sample verification, and the query examples. Do not describe it as turning off or overwriting the SDK's automatic collection path.

### Unique custom event candidates

Add these as creation candidates only for game-unique systems that the event templates do not cover.

- eventName: lowercase letters, digits, and underscores, in noun_verb form
- Properties: use only variables and parameters actually confirmed in the repository
- Values: use only numeric or string scalars
- Evidence: record the file, line, function, and type together

Do not propose a duplicate of an event template's behavior under a new name. A new eventName is automatically synchronized, so it
does not require pre-registration in the console.

## 4. Map to the repository

Use description_ko's trigger as the primary evidence and find the insertion point in the repository's actual control flow.
Record the file, line, function, and value source for each event.

Search hints:

| Code signal | Event family to check |
|-------------|---------------------|
| Level, Exp, LevelUp | account/character/guild/skill level change |
| Currency, Gold, Gem + Add/Gain | asset_get |
| Currency, Gold, Gem + Spend/Consume | asset_use |
| Quest, Stage, Dungeon + Accept/Enter | contents_accept |
| Quest, Stage, Dungeon + Clear/Success | contents_success |
| Quest, Stage, Dungeon + Fail/Lose | contents_fail |
| A shop/store product click | store_product_click |
| Confirming an in-game currency purchase | store_product_purchase |
| Mail/Claim/Receive | the mailbox family |
| Friend/Guild/Party invitations | the society invite family |
| SDK initialization and app lifecycle | entry events such as app_start |
| The login screen and auth callbacks | the login family |
| Download start and completion | the download family |
| heartbeat/keep-alive | app_session_maintain |

This table is only a search hint, not the official event list. The actual eventName and target_collect follow the query results.

Cautions:

- Distinguish product_purchase (IAP) from store_product_purchase (an in-game currency purchase).
- Find serverId in the server selection result, the login response, or the session object.
- For a periodically sent event, you must also find the login start, the logout or expiry, and any existing heartbeat/keep-alive logic.
- If is_baseline=Y but you cannot find an insertion point, do not hide it — mark it `needs further review: insertion point to be confirmed`.
- If is_baseline=N and there is no system evidence, exclude it from the specific recommendations.

## 5. Rule out duplicates

Registration in list_events is not evidence that collection is happening. After settling the creation candidates and eventNames
through repository mapping, judge in this order.

1. Confirm actual ingestion over the last 7–14 days with query_adhoc. Always include the `org_idx`, `appid_groups`, and AppID
   confirmed in Phase 3 in the query conditions.
2. Search the repository for Analytics.sendAnalyticsLog, sendEvent, existing wrappers, and the eventName.

Run query_adhoc in the confirmed company_cd, org_idx, and appid_groups context. For a single AppID use a `filters.appId` equality
condition; for several, use the `app_ids` array and query once per event. An `app_ids` result is one latest row per AppID, so compare
the requested list against the returned appIds to judge each AppID's collection status. Do not invent an IN operator or a filters
array structure.

Query basis per candidate:

- Ordinary GAME event: by appId + eventName
- AUTO enrichment option A: by appId + the newly settled eventName
- AUTO enrichment option B: by appId + the existing eventName + that SDK's direct-send dataSource. `filters` accepts
  only top-level columns, so `_dataSource` cannot go there, and the latest-row mode of `app_ids` may return an SDK
  auto-collected row. Query the value distribution instead: `event_name=<existing eventName>`, `filters.appId` (one
  AppID) or `app_ids` (several — combined with `dimension_names` it only filters), and
  `dimension_names=["_dataSource"]`. The direct send exists only if the SDK's exact direct-send value
  (`custom_sdk` / `axyl_custom_sdk`) appears in the distribution; its absence counts only when `values_truncated=false`
  (otherwise raise `value_limit`, up to 100, and query again). Judge per AppID by querying one AppID at a time
  when the distribution must be split by AppID.
- Unique custom event: by appId + the proposed new eventName

The unit of judgment is appId × eventName, and option B additionally includes dataSource.

| Result per AppID | Judgment | Handling |
|--------------|------|------|
| Collection confirmed on every appId | Being collected | Do not implement it again by default |
| Collection unconfirmed on every appId | Recent collection unconfirmed | Keep it as an implementation candidate |
| Collection confirmed on only some appIds | Partially collected | Check the game engine's shared code, the per-OS and per-market build settings, and deployed version differences |

Adding shared send code straight away in a partially collected state can cause duplicate sends on the appIds already collecting it.
By default, do not proceed with code generation before identifying the cause and securing an insertion point or condition that
applies only to the appIds where recent collection was not confirmed. When the user explicitly chooses an additional send under the
same eventName, follow the exception procedure below.

### User-specified duplicate sending

When the user explicitly asks to additionally send the same eventName as an existing collection, check the following.

1. Confirm the existing collection counts per AppID and the existing send points in the repository.
2. Explain that an additional send under the same eventName will be summed and double-counted in eventName-based metrics.
3. If the purpose is property enrichment, first propose merging the company-defined properties into the single existing send.
4. If the purpose is analyzing a distinct behavior, first propose a different eventName.
5. If the user understands the impact and chooses the additional send under the same eventName, implement it within that scope.

This exception is not a rule for putting the same name back into `company_custom_events`. Record it as a user-specified additional
send while keeping the event template definition, and state the target AppIDs, the existing and additional triggers, and the
double-counting possibility in the report.

If actual data or active send code is confirmed, mark that appId as collecting. If there is no row, report "recent collection over
the last 7–14 days not confirmed on that appId". Report a query error as "ingestion unconfirmed" and do not treat it as uncollected.

| SDK | Direct-send dataSource |
|-----|-----------------------|
| Hive SDK v4 | custom_sdk |
| Hive Axyl | axyl_custom_sdk |

The pipeline generates dataSource. Do not create a substitute field such as log_source in the game properties.

## 6. Recommendation output

Among all event templates, classify AUTO as `SDK automatic collection`. Classify GAME events into one of the four statuses below,
and do not conclude `not currently implementable` merely because you failed to find something in a search.

| Status | Judgment criterion |
|------|-----------|
| Implementable | The game system, execution flow, insertion point, and the value sources of the required GAME properties are all confirmed, and it passed the duplicate check |
| Existing send confirmed | Existing send code or actual ingestion is confirmed, so no additional implementation |
| Not currently implementable | It is confirmed that the system, flow, send point, required value, or SDK contract needed for implementation does not exist |
| Needs further review | There is not enough information to judge implementability, or a scope, duplication, or policy decision is deferred |

Break each status into these reason categories.

| Status | Reason categories |
|------|---------------|
| Existing send confirmed | Existing send code confirmed, recent actual ingestion confirmed |
| Not currently implementable | No target system, no event occurrence flow, no available send point, no way to obtain a required value, SDK constraint |
| Needs further review | A policy or scope decision is needed, duplication risk on some AppIDs, system existence to be confirmed, event occurrence flow to be confirmed, insertion point to be confirmed, required value source to be confirmed, SDK API to be confirmed, deferred out of this scope at the user's request |

Present `existing send confirmed`, `not currently implementable`, and `needs further review` **grouped by reason**, as follows.

```text
[No target system — 3]
- guild_create, guild_join: no guild system
- pvp_match_start: no PvP system

[No execution flow — 2]
- contents_fail: no flow that finalizes a failure result

[Cannot obtain a required property value — 1]
- asset_use: cannot obtain the before and after currency values together

[Already being collected — 2]
- account_level_change: existing send code and recent ingestion confirmed

[Needs further review: duplication risk on some AppIDs — 2]
- asset_get, asset_use: existing send confirmed on only some AppIDs
```

- Record both the count and every eventName in a reason group. Even with many events, do not omit the eventNames and show only the count.
- Events sharing a reason can be grouped on one line, but split the sentence for different specific reasons.
- Classify what you could not confirm in the code as `needs further review`, not as `no system` or `no flow`.
- Record separately in the evidence whether you confirmed existing send code or actual ingestion.
- Include AUTO events in the total event template candidate count and in the `SDK automatic collection` count and list. When AUTO
  enrichment was reviewed separately, show the original automatic collection status together with the `AUTO enrichment exception`.
- For an ordinary AUTO event, record only the eventName, the description, and the AUTO collection ownership. Do not write the
  `get_event_spec` detailed properties, the repository value sources, or a payload example.

Present implementable events in this format.

    [Event template / GAME] asset_get
    - Trigger: completion of acquiring in-game currency
    - Insertion evidence: Assets/Scripts/Inventory.cs:212 - AddGold(int amount)
    - Value sources confirmed: assetName, amountPrev, amountCurr, actionName, isPaid
    - Duplicate check per AppID: com.example.android recent collection unconfirmed / com.example.ios recent collection unconfirmed
    - Judgment: implementable

Keep AUTO enrichment separate from the ordinary recommendations and mark it as needing an A/B decision. Mark unique custom events as
"unique custom". If there are many candidates, present the core events and the events with repository evidence first, and you may
summarize the rest as counts per category.
However, show every eventName for `SDK automatic collection` and for the base-design GAME events' `existing send confirmed`,
`not currently implementable`, and `needs further review` lists, per the rules above.

If the user asks to implement "everything" or "all of them" from a broad recommendation result, the targets are all GAME candidates
in the full query results that have repository evidence and passed the duplicate check. Do not implement only the baseline candidates
and describe that as a full implementation.
Summarize in the results the total event template candidate count, the GAME/AUTO counts, the baseline/non-baseline counts, and the
counts for implementable, existing send confirmed, not currently implementable, and needs further review. The sum of `SDK automatic
collection` and the four GAME statuses must equal the total event template candidate count. Do not assign `is_baseline` arbitrarily
to company-specific custom events — show them as a separate count.
