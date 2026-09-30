# check_user_exists (Check Whether a User Exists)

Checks whether the project holds data for this user. This is the first step of the user activity
tracking tools.

> **Prerequisite:** Follow the common rules in [`../SKILL.md`](../SKILL.md).

## When to Use

- Before every user activity query, to confirm the user ID is valid
- To check whether a user belongs to a specific user group (with `user_group_id`)

## Parameters

| Parameter | Required | Description |
|---------|------|------|
| `company_cd` | Y | Company code confirmed from `list_projects` |
| `org_idx` | Y | Organization idx confirmed from `list_organizations` |
| `appid_group` | Y | Project ID (`list_projects.appid_group`) |
| `user_id` | Y | The user ID to check. Never guessed — taken from what the user supplied or from another query result |
| `user_group_id` | N | User group idx. When given, membership in that group is checked as well |

The project must be connected to the organization. This applies to Analytics administrators too,
because it is a question of whether the project belongs to that organization, not of user privilege.

## Return Value

Returns `{"user_id", "appid_group", "user_group_id", "exists"}`. `exists` is the boolean the server
returns.

## Decision Rules

- **A nonexistent ID returns `false` rather than an error**, so this is where typos are caught.
- If `exists` is `false`, do not move on to activity queries. Recheck whether the user ID is wrong or
  the wrong project was selected — an empty activity result read as "there is no activity" is the
  most common wrong answer.
- With `user_group_id`, `false` means the user is not in that group; it does not mean the user does
  not exist in the project.

## On Failure

- Organization access error: recheck the accessible organizations with `list_organizations`.
- Project access error: that project is not connected to the organization. Recheck with `list_projects`.

## Recommended Chain

```text
list_projects → list_organizations → check_user_exists → get_user_activity_summary
```
