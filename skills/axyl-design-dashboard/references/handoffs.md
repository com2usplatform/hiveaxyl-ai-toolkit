# Handoffs and Log Integration Requirements

Read this when deciding, after the recommendation and readiness diagnosis, whether to proceed to content saving, writing a document
for developers, or actually implementing the log code. Here, "handoff" does not mean calling an external AI or a separate agent.
It means applying another skill's instructions within the same agent working session, carrying the verified context forward.

## States to Distinguish First

| State | Creating empty content | Log follow-up |
|---|---|---|
| The event and property metadata and idx exist; only recent data is missing | Possible after a warning and explicit approval | Either a requirements document or an actual implementation can be chosen |
| The property metadata exists but every value is null | Possible after warning that the breakdown or filter will look empty | Request that those property values be filled in |
| The event, or a property strictly required to compute, break down, or filter this content, has no metadata definition | Not possible — there is no idx to pass to `create_*` | A definition and collection requirements document, or an actual implementation, is needed |
| The data contract is unsettled | Arbitrary mapping is prohibited | Settle the event and property contract with the user first |

Do not treat "no collected data" and "no metadata definition" as the same state. The former allows building empty content in advance,
while the latter cannot even express the content configuration, so you must return to the creation stage after the definitions are ready.

## Options to Present to the User

When there are items needing log improvements, present the following options as clearly separate. Whether to create empty content and
how to improve the logs are independent decisions, so the user can choose them together or separately.

1. Create the content now for items that have metadata definitions, even if the data is empty.
2. Write a log integration requirements document to hand to developers. No game repository is needed.
3. Implement the actual log design and send code. A game client repository is needed.
4. Defer log improvements and proceed only with the content that can be implemented now.

Do not treat a recommendation choice or approval to write a requirements document as approval to save content, modify code, or send a sample.

## DESIGN_APPROVAL_GATE

Before switching to create-content, design-dashboard shows the final result review and waits for the user's response.
Even if the user initially asked to "make me a dashboard," that is not agreement to a recommended composition that had not yet been
presented, so do not treat it as design approval.

At the moment of approval, the following must be settled.

- The dashboard's name, purpose, and audience, plus the content list and display order
- Which of the READY, PARTIAL_READY, and NOT_READY items will be handed to the actual creation stage
- Whether to include content expected to come back empty
- Whether to reuse, copy, or exclude duplicate assets
- Whether items needing log improvements are excluded, deferred, or followed up on

If the user revises the composition, show the whole changed result again and obtain re-approval. Before explicit approval, do not apply
the axyl-create-content instructions or start a preview. Design approval does not stand in for create-content's WRITE_APPROVAL.

## The axyl-create-content Stage

When the user approves the final composition at DESIGN_APPROVAL_GATE, preserve the following context.

```text
project_context:
  verified company/project/app IDs, org_idx, workspace_idx
design_approval:
  approved: true
  approved scope and inclusion/exclusion decisions
dashboard:
  name, description, purpose, persona
  global date basis and filters
contents[]:
  display order
  content name/type/chart type
  verified metric name and target-company metric_idx, or
  verified event/dimension names and target-company idx values
  dimension_substitutions: user-approved X → <other source> switches (such as os → _os), each with the chosen
    dimension name, attribute_source, dimension_idx, affected slots, and filter_value_mappings
  aggregation, filters, currency
  mapping confidence and readiness evidence
  expected_empty: true|false and reason
  platform template reference, if any
excluded[]:
  metadata missing or unresolved items that cannot yet be configured
```

- create-content previews each content item, shows the final composition and the empty-result warnings, and then obtains WRITE_APPROVAL.
- If the user explicitly approves creating empty content, it can be saved with the verified configuration as is.
- If some items cannot be configured, show the composition with them excluded and confirm whether to proceed with it.
- If an identical existing asset exists, the user chooses to reuse it, create a copy, or skip. Reuse applies only to existing content in
  the target workspace with verified permissions.

## Log Integration Requirements Document for Developers

design-dashboard can write this document without a repository. It is a deliverable the user pastes into an issue, ticket, or chat to
hand to developers; the agent does not send it automatically.

Copy the [developer log integration requirements template](../assets/developer-log-integration-spec.md) and fill it in from the following evidence.

- The questions the target dashboard and content are meant to answer
- The project and AppID confirmed through PROJECT_ID_GATE
- The events and properties confirmed from the company metadata or the official event specification
- The absent / null / partially collected states confirmed in the recent-ingestion queries
- The required aggregations, breakdowns, and filters, and why each property is needed

Writing rules:

- Mark a name that exists in the company metadata or the official specification as `existing definition`, and a new name as `proposed`.
- Do not settle on an event name, property name, type, or trigger point without evidence. Leave undecided values as `to be confirmed` and
  put them in the questions for developers to answer.
- Do not guess the SDK type or the collection ownership if you have not confirmed it.
- Explicitly flag anything that may include personal, payment, or in-game currency information as an item needing review.
- Do not promise that implementation is complete or that collection will succeed. Write only the completion criteria and the verification method.

## The axyl-integrate-analytics-log Stage

When the user chooses the actual log design or send code implementation, obtain the game client repository and then apply that skill.
If a requirements document was written first, pass it along as an implementation input.

```text
target_repository
verified project and AppID context
developer log integration requirements, if created
dashboard/content that needs the log
required or proposed event and attributes
expected trigger and business meaning
known company metadata and recent collection evidence
requested scope: design only | code implementation | end-to-end validation
```

The axyl-integrate-analytics-log stage performs SDK determination, confirmation of code locations and value sources, writing the send
code, and verification. Apply the required approval procedures for code changes and actual sample sends exactly as specified.
