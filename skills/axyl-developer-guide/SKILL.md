---
name: axyl-developer-guide
description: Use when implementing an Axyl feature that is not covered by a more specific skill; verify the official Axyl developer guide before coding uncovered login, payment, push, mailbox, TCB Connector, account/auth, or service access control behavior.
metadata:
  short-description: Implement Axyl features from official Axyl guides
---

# Axyl Developer Guide

Use this skill when the user asks to develop or modify an Axyl feature and no more specific skill covers the requested feature or business flow.

## Scope

- Prefer a feature-specific skill when one exists. For mixed requests, use that skill for the covered portion and this skill only for the uncovered Axyl behavior.
- Supported Axyl product areas are login, payment, push notification, mailbox, TCB Connector, account and authentication, and service access control.
- Do not treat the absence of a feature-specific skill as evidence that Axyl does not support the requested feature.
- Do not implement Axyl SDK, API, console, permission, or callback behavior from memory. Verify the current official guide first.

## Official Documentation

The Axyl guide root is:

https://developers.hiveplatform.ai/axyl/

When implementation details are needed, read the relevant page under that Axyl documentation site. If a product-specific route is available, use [references/product-guides.md](references/product-guides.md) as the routing index. Treat that reference only as an index; never implement from the index text alone.

## Workflow

1. Identify the requested Axyl product, feature, SDK or API surface, target platform, and existing project conventions.
2. Read [references/product-guides.md](references/product-guides.md) and select only the relevant product row.
3. Open the product-specific guide URL when it is filled in. If the product URL is blank or stale, start from the Axyl guide root and navigate or search within the official Axyl developer site for the requested product and feature.
4. Follow the documentation to the exact function, setup, configuration, callback, result-code, or platform-specific page required for the task. Do not rely on landing-page summaries.
5. If the official Axyl page cannot be accessed or does not document the requested behavior, tell the user what could not be verified instead of guessing.
6. Implement using the verified names, types, call order, result handling, and prerequisites from the official guide while preserving the project's existing architecture and style.

## Implementation Rules

- Match the SDK version, platform, engine, language, async model, and error-handling style already used by the project whenever possible.
- Include required initialization, console setup, permissions, platform configuration, and dependency changes when the guide requires them.
- Never invent an Axyl class, method, enum, parameter, callback, result code, endpoint, permission, or console setting.
- If two official pages conflict and the conflict affects correctness, report the conflict and avoid implementing the affected portion until it is resolved.
- If documentation requires user-side console configuration or credentials, make the code changes that are safe locally and clearly report what the user must configure outside the repository.

## Completion Notes

When finished, report:

- what was changed;
- which Axyl guide page or pages governed the implementation;
- any console, credential, platform, permission, or deployment setup the user still needs to complete;
- what was verified locally and what remains unverified.
