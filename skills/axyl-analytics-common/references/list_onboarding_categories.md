# list_onboarding_categories (List Dashboard Recommendation Categories)

> **Prerequisite:** Follow [`../SKILL.md`](../SKILL.md). This is a read tool.

Returns the allowed genre/BM category IDs used by `list_recommended_dashboards`, plus variables that can appear
in recommended names.

## When to Use

- To validate user-provided genre/BM values before personalized dashboard recommendation.
- To present allowed choices when the user wants personalization but the category is uncertain.
- It is not required for platform-only recommendations from `list_dashboard_templates`.

## Parameters

There are no user parameters. Authentication is taken from the MCP context.

## Return Value

Returns `genres`, `bms`, and `variables`. Category rows contain `category_id`, `display_name`, and `description`;
variable rows use `variable_id` with the same display fields.

## Decision Rules

- Use `genres[].category_id` and `bms[].category_id` as tool inputs, not display names.
- `variables[]` explains placeholders such as `{pvp_name}`. Do not invent a project-specific replacement.
- The result is a recommendation taxonomy, not a project classification. Confirm uncertain genre/BM choices with
  the user.

## On Failure

- Empty taxonomy: do not invent category IDs; continue with platform templates when applicable.
- Authentication or query error: report the error and do not call `list_recommended_dashboards` with guessed values.

## Recommended Chain

```text
personalization requested → list_onboarding_categories → confirm genre
→ list_recommended_dashboards
```
