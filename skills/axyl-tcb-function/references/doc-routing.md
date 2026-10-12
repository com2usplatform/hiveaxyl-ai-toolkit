# TCB Document Routing

> **Prerequisite:** Follow the rules in [`../SKILL.md`](../SKILL.md). This file is an index only. Open the document itself before acting; never implement from the summaries below.

Every document here is served by the `hive-axyl` MCP server under product `tcb`. Ids are globally unique and already carry the `tcb-` prefix.

## Lookup rules

- Each `get_*` tool returns documents of its own category only. An id passed to the wrong tool returns `not found` with `candidates`. Switch to the tool that matches the category instead of retrying.
- If an id is missing or renamed, rediscover it with `list_docs(product='tcb', category=...)` or `get_doc_tree`. Never guess an id.
- Categories: `setup-guide`, `feature`, `samples`, `errors`, `version-requirements` (service documents) and `resource` (Console document).
- Responses include `lastUpdated`. When two documents disagree, report it to the user. For the Console TCB settings, prefer `tcb-resource-tcb-settings` and the tool descriptions.
- "Console" in TCB service documents means the Tencent CloudBase console, except the "TCB settings" credential in `tcb-setup-scf-execution-api`: that is the Hive Axyl Console (`tcb-resource-tcb-settings`).

| Category | Read with |
|---|---|
| `setup-guide` | `get_setup_guide(topicId)` |
| `feature` | `get_feature_spec(featureId)` |
| `samples` | `get_sample_code(sampleId)` |
| `errors` | `get_error_guide(query)` takes an error code, a keyword, or the exact id. It has no `product` argument. Several matches return `message` and `matches` (not an error); retry with the exact id. |
| `version-requirements` | `get_version_requirements(product='tcb')` returns the TCB documents and any product-agnostic ones, all in full. |
| `resource` (Console) | `get_console_doc(docId)` |

## Stage map — `start_tcb_workflow`

Without `stage`, the tool returns `tcb-setup-workflow`, which is the overview, the stage gates, and the common-failure table. With `stage`, it returns one document. Read the "also" column yourself.

| `stage` | Returned document | Also read when relevant |
|---|---|---|
| `bootstrap` | `tcb-setup-bootstrap` | `tcb-setup-mysql` (MySQL chosen), `tcb-version-requirements`, `tcb-version-dependency-audit` (npm audit warnings) |
| `develop` | `tcb-feature-development-guide` | `tcb-feature-getting-started`, the stack guide (`tcb-feature-mysql`, `tcb-feature-docdb`, `tcb-feature-storage`), `tcb-sample-example-functions`; for real-time requirements only: `tcb-feature-websocket`, `tcb-feature-realtime-patterns` |
| `deploy` | `tcb-setup-deploy-invoke` | `tcb-setup-websocket-deploy` (WebSocket functions are deployed separately) |
| `test` | `tcb-setup-test-checklist` | `tcb-setup-deploy-invoke` (setup functions, per-function invoke commands, SDK invoke fallback), `tcb-errors-handling` |
| `wrap-up` | `tcb-setup-workflow` (its wrap-up section) | `tcb-setup-test-checklist` (result record format; the overview's stage table names it for wrap-up), `tcb-setup-websocket-deploy` checklist if a WebSocket demo was deployed |

`wrap-up` is accepted even though the parameter description lists only the four main stages. An unknown `stage` returns `error` with `validStages`.

## Document catalog

| Document id | Category | Covers |
|---|---|---|
| `tcb-setup-workflow` | setup-guide | Five-stage playbook, completion gates per stage, common failures and workarounds |
| `tcb-setup-bootstrap` | setup-guide | Environment check, the pinned template version (the only place it is kept), database choice, `.env` keys, smoke check |
| `tcb-setup-mysql` | setup-guide | First-time MySQL setup in the CloudBase console |
| `tcb-setup-deploy-invoke` | setup-guide | Build and deploy commands, invoke commands per example function, SDK invoke fallback, setup and seed functions |
| `tcb-setup-test-checklist` | setup-guide | Standard invoke test checklist: normal flow, idempotent retry, errors, data isolation, transient failures, result format |
| `tcb-setup-websocket-deploy` | setup-guide | WebSocket build, deploy, Function URL, connection tests, pre-deploy checklist |
| `tcb-setup-scf-execution-api` | setup-guide | How a game server runs a deployed function in production through the Hive Axyl HTTP API. Requires a registered Console TCB credential. |
| `tcb-feature-development-guide` | feature | Invariant rules: entry point, data isolation, PlayerId format, error classes, idempotency, query design, the pre-deploy check (MUST) |
| `tcb-feature-getting-started` | feature | Project structure, local test, deploy, adding a new function |
| `tcb-feature-mysql` | feature | MySQL usage, transactions, idempotency patterns, multi-line SQL and cold-connection pitfalls, timer triggers |
| `tcb-feature-docdb` | feature | Document DB usage, queries, transactions, watch trust boundary, idempotency patterns |
| `tcb-feature-storage` | feature | Cloud Storage, path ownership scope, direct upload flow, temporary URL handling |
| `tcb-feature-websocket` | feature | WebSocket execution model, limits, one-time ticket auth, shared state, heartbeat (normative) |
| `tcb-feature-realtime-patterns` | feature | General real-time sync patterns with TCB notes (non-normative) |
| `tcb-sample-example-functions` | samples | Catalog of the template's example functions and their handlers |
| `tcb-errors-handling` | errors | Error classes, standard validation errors, MySQL and Document DB errors, transient failures, CLI errors |
| `tcb-version-requirements` | version-requirements | Runtime, bundling target, environment variables per middleware module |
| `tcb-version-dependency-audit` | version-requirements | Known npm audit findings that come from the CloudBase SDK |
| `tcb-resource-tcb-settings` | resource (Console) | Console TCB settings: fields, what the tools can and cannot do, failure resolution |

For a game-server production call, also read `auth-feature-auth-model` (`get_feature_spec`). It is the auth document that the execution API guide points to for access tokens and domains.

## Scaffolded project files

A project created from the template may register this same MCP server under a different name in its own files, for example `axyl-docs` in its `AGENTS.md`. The tools are the same, so the `hive-axyl` tools satisfy those instructions. Where the project's local notes and the served documents differ, follow the served documents for content: versions, commands, and API contracts. Neither the notes nor the documents weaken the approval, secret, or Console gate rules in [`../SKILL.md`](../SKILL.md); for example, DEPLOY_CONFIRM still comes before a deploy that a document runs right after the pre-check report.
