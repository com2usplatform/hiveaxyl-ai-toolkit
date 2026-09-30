# list_recommended_dashboards (List Genre/BM Dashboard Recommendations)

> **Prerequisite:** Use category IDs returned by `list_onboarding_categories`.

Returns genre/BM-based recommended dashboard compositions. These are design recommendations, not saved assets or
platform templates.

Call this tool only when the genre is confirmed. If the genre is unknown, do not guess it or pass an empty
`genres` value; continue recommendations with `list_dashboard_templates`.

## When to Use

- After the genre has been confirmed from `list_onboarding_categories`.
- To add genre/BM-personalized compositions to the always-available platform-template candidates.
- Not for finding saved dashboards or platform template IDs.

## Parameters

| Parameter | Required | Description |
|---|---|---|
| `genres` | Y | One to 50 confirmed genre category IDs |
| `bm` | N | Up to 50 BM category IDs; omit for BM-independent recommendations |
| `include_contents` | N | Include ordered member content. Default: `true` |

## Return Value

Returns recommendations in platform display order with catalog `dashboard_id`, display name, description,
`use_cases`, `importance`, matching genre/BM tags, and optionally ordered `contents`.

## Decision Rules

Use `use_cases` and `importance` as recommendation evidence. `dashboard_id` and `content_id` are catalog IDs and
must never be passed as `template_idx`, `dashboard_idx`, or `content_idx`.

- When the genre is confirmed but BM is unknown, omit `bm` and label the result as genre-based and BM-independent.
- Use `include_contents=false` to narrow dashboard candidates, then re-query selected candidates with content.
- Recommendation results are design proposals; check template mappings and data readiness separately.

## On Failure

- Empty or invalid `genres`: return to `list_onboarding_categories`; never pass an empty or guessed list.
- Empty recommendation result: continue with `list_dashboard_templates` and disclose that no personalized match was found.
- Authentication or query error: report the error without converting a catalog ID into another asset type.

## Recommended Chain

```text
list_onboarding_categories → confirm genre/BM
→ list_recommended_dashboards(include_contents=false)
→ selected recommendations with include_contents=true
→ template and data-readiness checks
```
