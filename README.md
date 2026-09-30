# Hive Axyl AI Toolkit

The Hive Axyl plugin for ChatGPT and Codex, provided by Com2uS Platform.

Hive Axyl helps game teams develop and operate games through SDK integration guidance, service configuration workflows, live operations support, and analytics workflows.

| | |
| --- | --- |
| Canonical URL | <https://github.com/com2usplatform/hiveaxyl-ai-toolkit> |
| Product | `hiveaxyl` |
| Domain | `ai` |
| Artifact | `plugin` |
| Version | `1.0.0` |
| Lifecycle | `active` |
| Official status | Official |
| License | Apache-2.0, except the logo images (see [NOTICE](NOTICE)) |
| Product languages | English (default), Korean |

## Related repositories

The official entry points are the Com2uS Platform organization profile and this repository's README. This repository is the single public distribution point for the toolkit; there is no separate companion repository at this time.

## Getting started

In a terminal, use the Codex CLI to add the marketplace source:

```bash
codex plugin marketplace add com2usplatform/hiveaxyl-ai-toolkit
```

Install the Hive Axyl plugin:

```bash
codex plugin add hive-axyl@hiveaxyl-ai-toolkit
```

After installation, ask Codex to help with an Axyl development or operations workflow:

```text
Add sign-in and logout to my game using Hive Axyl.
```

```text
Retrieve store products and implement in-app purchases using Hive Axyl.
```

```text
Analyze my game data using Hive Axyl to understand player behavior.
```

## What this plugin does

Hive Axyl packages Skills and MCP server connections so developers can use natural-language requests for app feature implementation, console configuration, analytics, and live operations workflows.

Common workflows include:

- SDK setup, initialization, and environment checks.
- Login, account, authentication, payment, push notification, mailbox, TCB Connector, and service access control guidance.
- Axyl console authentication, project checks, permission checks, prerequisite validation, and result verification.
- Analytics data querying, interpretation, and summary support.
- Routing to official Axyl developer guides when a requested capability is not covered by a dedicated Skill.

MCP is used when a request requires access to external Axyl systems, including console settings, server-side functions, documentation lookup, or analytics data. Read-only operations can proceed after authentication and permission checks. Change operations require user confirmation before execution.

## Support

GitHub Issues are disabled for this repository. Please use the channels below for questions, bug reports, feature requests, and customer inquiries.

| Purpose | Channel |
| --- | --- |
| Product information | <https://hiveplatform.ai/hiveaxyl> |
| Developer documentation | <https://developers.hiveplatform.ai/axyl/> |
| Questions, bug reports, feature requests | <cs-platform@com2us.com> |
| Enterprise customer inquiries | <cs-platform@com2us.com> |

GitHub is not an official customer support channel, and we do not commit to response or resolution timelines here.

## Contributing

We do not accept external pull requests as a contribution path at this time.

## Versioning

Public releases follow [Semantic Versioning](https://semver.org/) and are tagged `vMAJOR.MINOR.PATCH`. Only the currently approved stable version is kept on `main`.

## License

Licensed under the [Apache License 2.0](LICENSE). See [NOTICE](NOTICE).

The logo images in `assets/` are not licensed under the Apache License 2.0; they may be redistributed only as part of an unmodified copy of this repository or plugin. The license does not grant permission to use the Hive Axyl or Com2uS Platform names, logos, or trademarks except as described in its Section 6, and it grants no right to represent a derivative work as official. See [NOTICE](NOTICE) for details.

