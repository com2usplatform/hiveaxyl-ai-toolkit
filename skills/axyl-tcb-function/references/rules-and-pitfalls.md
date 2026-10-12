# TCB Rules and Pitfalls by Document

> **Prerequisite:** Follow the rules in [`../SKILL.md`](../SKILL.md). Each table row only says which document holds a rule or a fix; a line marked **Skill note** is this skill's own guidance, not a document rule. Open the document (see [doc-routing.md](doc-routing.md) for the tool) and follow its current text; values, versions, and commands come from the document, not from this file.

## Invariant development rules

| Rule | Document |
|---|---|
| Entry point is the middleware handler wrapper; the base handler returns business data only. | `tcb-feature-development-guide` |
| Data isolation: scope every query by the project index from the request context and the player ID. Never use request-body values as the isolation key. | `tcb-feature-development-guide` |
| Player IDs are digit strings of 1 to 19 characters, in tests too. Do not parse them into JS numbers. | `tcb-feature-development-guide` |
| Three error classes: business validation, domain error, and middleware-handled request errors. Do not throw the middleware's request error yourself. | `tcb-feature-development-guide`, `tcb-errors-handling` |
| State changes such as currency or payment are idempotent, scoped by project index, player, and idempotency key. | `tcb-feature-development-guide`, `tcb-feature-mysql`, `tcb-feature-docdb` |
| Query design: separate queries with batched lookups by default. JOIN only in the two documented cases. | `tcb-feature-development-guide`, `tcb-feature-mysql` |
| Function file names are unique project-wide. Register every new function, with its environment-variable keys, in `cloudbaserc.json`. | `tcb-feature-development-guide`, `tcb-feature-getting-started` |
| If a requirement mentions file URLs, ask the user whether to store external URLs or upload to Cloud Storage before implementing. | `tcb-feature-development-guide`, `tcb-feature-storage` |
| Storage paths and file IDs are owner-scoped. Persist file IDs, not temporary URLs. | `tcb-feature-storage` |
| Timer triggers use a plain handler and the documented cron format. They are active resources: never deploy one as a demo. | `tcb-feature-mysql` |
| WebSocket only when real-time is required. Follow the normative guide; the patterns guide is non-normative. | `tcb-feature-websocket`, `tcb-feature-realtime-patterns`, `tcb-setup-websocket-deploy` |
| When a type is unclear, check the middleware's type declarations in the project; do not guess. | `tcb-feature-development-guide` |

## Environment and bootstrap

| Rule | Document |
|---|---|
| Scaffold only with the pinned template command from the bootstrap document. Never switch to `@latest`. | `tcb-setup-bootstrap` |
| Local Node and the function runtime differ. Check both requirements. | `tcb-setup-bootstrap`, `tcb-version-requirements` |
| The CLI login is interactive and only the user can run it. `tcb env list` confirms authentication. | `tcb-setup-bootstrap` |
| `.env`: required keys, region never guessed, UTF-8 without BOM, no inline comments, never committed or dumped whole. Report values only as its output rule allows (final `TCB_REGION`; other keys set or unset). An env-ID/region preset at scaffolding also writes them into `cloudbaserc.json`. | `tcb-setup-bootstrap` |
| Region source order: the `.env` value, then a read-only `tcb env list` only if no value is set, then ask the user. | `tcb-feature-development-guide` |
| MySQL needs first-time setup in the CloudBase console. | `tcb-setup-mysql` |
| Do not run a forced npm audit fix. Some audit findings are known and come from the CloudBase SDK. | `tcb-setup-bootstrap`, `tcb-version-dependency-audit` |

## Deploy, test, wrap-up

| Rule | Document |
|---|---|
| Pre-deploy check (MUST) before any deploy or live invoke, reported in the documented format. Stop if any item is unclear. The format shows the final `TCB_REGION` and the test PlayerId, never passwords or credentials; it matches the `.env` output rule in `tcb-setup-bootstrap`. | `tcb-feature-development-guide`, `tcb-setup-workflow`, `tcb-setup-bootstrap` |
| Invoke runs the deployed code. Rebuild and redeploy after every source change. | `tcb-setup-deploy-invoke`, `tcb-errors-handling` |
| WebSocket functions are excluded from the normal deploy and deployed separately. | `tcb-setup-workflow`, `tcb-setup-websocket-deploy` |
| Verify with scenario scripts that cover normal flow, idempotent retry, data isolation, domain errors, and validation errors. | `tcb-setup-workflow`, `tcb-setup-test-checklist` |
| Setup and seed functions only run where the documented setup flag was deployed. They are for development only. | `tcb-setup-deploy-invoke` |
| Wrap-up: tell the user which setup and seed functions and which setup flag to remove before production, delete any WebSocket demo, and report results in the recommended record format. | `tcb-setup-workflow`, `tcb-setup-deploy-invoke` (setup flag), `tcb-setup-websocket-deploy` (demo), `tcb-setup-test-checklist` (record format) |

**Skill note — DEPLOY_CONFIRM (approval before any deploy or live invoke):** the pre-check report in the table above is not approval. A live invoke is anything that runs a deployed function: `tcb fn invoke`, `node scripts/invoke.js`, the `test` stage's scenario scripts (`scripts/test-<feature>.js`) with their setup steps, and WebSocket connection tests, read-only functions included. After the report, show the user:

- the environment as the pre-check reports it: the `.env` in use, the final `TCB_REGION`, and `TCB_ENV_ID` as set or unset (the `.env` output rule; never its value or any credential). These do not tell a development environment from a production one, so ask the user to confirm which environment that `.env` targets (for example, development, not production); they can check `TCB_ENV_ID` there themselves. If they cannot confirm it, do not deploy or invoke;
- what will run: the functions to deploy (named, or a full deploy; WebSocket functions separately), or the invoke scenarios (function, test PlayerId, purpose);
- the impact: a deploy replaces the deployed code of those functions; setup, seed, and state-changing invokes write real data in that environment; a timer trigger keeps running once deployed.

Then wait for the user's explicit approval, and deploy or invoke only what was approved. Ask again when the scope changes: another function, environment, or scenario, or code changed since the approval. For the fix-and-redeploy loop, you may ask once whether redeploying the same functions to the same environment after fixes is approved; without that, ask before each redeploy. Approval comes first even where `tcb-setup-workflow` deploys right after the report or `tcb-setup-deploy-invoke` has the agent deploy named functions: documents govern versions, commands, and API contracts, not approval. Without a local shell the user runs each command, and running it is the approval. Work that neither deploys nor runs a deployed function needs no approval: `npm run build`, `npm test` (mocked, no TCB connection), and read-only checks such as `tcb env list`.

**Skill note:** if a documented bash block also contains prose, run only its command lines, one at a time.

## Production calls

| Rule | Document |
|---|---|
| Game servers run deployed functions through the Hive Axyl execution API with an access token. | `tcb-setup-scf-execution-api`, `auth-feature-auth-model` |
| The execution API needs a credential registered in the Console TCB settings. Without one, the call is rejected. | `tcb-setup-scf-execution-api`, `tcb-resource-tcb-settings` |
| Distinguish the two kinds of invocation failure: an infrastructure failure, versus a runtime error in the function code that needs a code fix. | `tcb-setup-scf-execution-api` |

## Common pitfalls

| Symptom | Where the fix is |
|---|---|
| CLI invoke fails with `ClientContext parameter error` | Not a function bug. Switch to the SDK invoke script: `tcb-setup-deploy-invoke`, `tcb-errors-handling` |
| SDK invoke authenticates silently wrong, or reports a region mismatch | SDK credential field and region: `tcb-setup-deploy-invoke`, `tcb-errors-handling` |
| Authentication expired during CLI or SDK work | `tcb-setup-bootstrap` (section 1): run `tcb env list` once, outside a project whose `cloudbaserc.json` has an empty env ID; if it still fails, ask the user to run `tcb login`. |
| A setup function answers `SETUP_DISABLED` | Setup flag not deployed: `tcb-setup-deploy-invoke` |
| `.env` keys not found | Encoding, path, and inline comments: `tcb-setup-bootstrap`, `tcb-setup-workflow` |
| MySQL `Malformed communication packet` | Multi-line SQL: `tcb-feature-mysql`, `tcb-errors-handling` |
| First database call fails, then succeeds | Cold connection and idempotent retry: `tcb-feature-mysql`, `tcb-errors-handling` |
| Document DB `RESOURCE_NOT_FOUND` or an `_id` update error | Collections, instance settings, and document body: `tcb-errors-handling`, `tcb-feature-docdb` |
| Requests rejected with `BAD_REQUEST` | Header or player ID format: `tcb-feature-development-guide` |
| Unexpected error right after a code change | Stale deployment: `tcb-errors-handling` |
| WebSocket handshake or URL errors | `tcb-setup-websocket-deploy` |
| Agent shell cannot run Windows executables, or the CLI deploy fails in a sandbox | `tcb-feature-development-guide`, `tcb-errors-handling` |
