# update_retention (Update Retention)

Updates a saved retention content (`content_type='retention'`). **This is a write.**

> **Prerequisite:** Follow the common rules in [`../SKILL.md`](../SKILL.md).
> WRITE_APPROVAL applies.

## When to Use

- To change the base event or the retention event
- To change the cohort identifier (for example `userId` → `deviceId`)
- To correct the name, description, period, dimensions, or display format

## Parameters

| Parameter | Required | Description |
|---------|------|------|
| `company_cd` | Y | Company code confirmed from `list_projects` |
| `org_idx` | Y | Organization idx |
| `workspace_idx` | Y | Workspace the content belongs to |
| `content_idx` | Y | Content idx to update |
| `content_name` | N | New name |
| `content_description` | N | New description |
| `project` | N | New target project list |
| `chart_type` | N | New chart type (`table`, `line`) |
| `date_params` | N | New period. Same format as `preview_retention` |
| `base_event` | N | New base event `{"idx", "event_name", "filters"(optional)}` |
| `retention_event` | N | New retention event (same format) |
| `identifier` | N | New identifier. Applied to both sides of the condition |
| `dimensions` | N | New dimension list |
| `adhoc_filters` | N | New filter list |
| `display_format` | N | `"percentage"` \| `"figure"` (not validated on update, so pass only these two) |

**At least one** field to change is required.

## Built on a Full-Replace API

Reads the current content, overwrites only what you pass, then sends the whole thing back.
`dimensions` and `adhoc_filters` replace that list entirely when passed.

In the stored format, `identifier` expands into `conditions[].base_dimension` and
`retention_dimension`. There is no way for a caller to assemble the `conditions` array directly —
**passing a single `identifier` changes both sides.**

## Dimensions Belong to the Base Event

**`dimension_idx` differs per event.** For example, `market` is `<first_launch_market_dimension_idx>` on
`app_first_launch` but `<login_market_dimension_idx>` on `app_login`. Passing an idx looked up from a different
event saves without error, but the grouping never takes effect in the console.

So this tool **checks that dimensions belong to the base event before saving and blocks them if
not.** The error lists every dimension of the base event as `name(idx)`, so pick from it and
call again.

**When you change `base_event`, look up `dimensions` again on the new base event and pass them
together.** Changing only the base event leaves the existing dimensions outside the new event,
which is rejected.

## Return Value

Same shape as `update_chart`, with `content_type` of `"retention"`.
**Include `console_url` when reporting a write (POST_WRITE_LINK)**.

## Decision Rules

- **Get user approval before calling (WRITE_APPROVAL).**
- **When changing settings, verify with `preview_retention` first.** There is no undo tool.
- **Verify with `get_content` after saving.**
- **Look up dimension idx with `list_dimensions(company_cd, base event name)` each time.**
  Do not reuse an idx you looked up earlier against a different event.
- Switching `chart_type` to `table` creates default table settings; switching away removes them.
  Table settings configured in the console are preserved as long as `chart_type` is untouched.

## On Failure

| Symptom | What to do |
|------|------|
| Dimension does not belong to the base event | Pick from the dimension list in the error and call again |
| Changed only `base_event`, leaving dimensions mismatched | Pass `dimensions` looked up on the new base event |
| `base_event` / `retention_event` missing `event_name` | Both `idx` and `event_name` are required |
| Project outside the organization's scope | Check with `list_projects(company_cd, org_idx)` |
| Content created by someone else | A workspace member can only edit **content they created**. If `get_content.permission` is not `EDITOR` the save is rejected — ask the user whether to make a copy or request the change from the author |

## Recommended Chain

```text
get_content (check current configuration) → list_events / list_dimensions (re-query on base event)
→ preview_retention (if settings change) → user approval
→ update_retention → verify with get_content → report with console_url
```
