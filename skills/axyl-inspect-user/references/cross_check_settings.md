# Cross-Checking Metric Settings (Correcting Conclusions)

The procedure to run when the activity history and a metric disagree, **before concluding data loss
or a bug**.

> **Prerequisite:** Follow the rules in [`../SKILL.md`](../SKILL.md) and [`../../axyl-analytics-common/SKILL.md`](../../axyl-analytics-common/SKILL.md). This is the step before reaching a conclusion.

## Why They Disagree

The two paths query data on different bases.

| | What is applied |
|---|---|
| Metric queries (`preview_chart`, `preview_chart_rank`, and so on) | Users excluded from metrics · metric filters · metric start dates |
| User activity tracking | **None — the raw event log** |

## When It Is in the Activity but Not in the Metric

This is the most common direction. Check the following three.

| Check | Tool | If it applies |
|---|---|---|
| Is this user registered as excluded from metrics | `list_except_users` | An intended exclusion (QA, internal testers) |
| Is the server or app this user used caught by a filter | `list_metric_filters` | An intended exclusion (QA servers, test apps) |
| Is that activity earlier than the metric start date | `list_start_dates` | Data from before aggregation began |

If any of the three applies, **it worked as configured**. Answer like this.

```text
The activity history has a purchase on 9/11, but it does not appear in the revenue metric.
This user is registered as excluded from metrics, so it was left out of aggregation.
```

If none of the three applies, **do not conclude** — report what was checked along with the finding.

## When It Is in the Metric but Not in the Activity

This is rare. Suspect the following first.

- **Period boundary** — the activity time has the user's timezone applied while the time inside the
  event properties is UTC, a 9-hour difference. Around a date boundary, widen the query period by a
  day and look again.
- **User ID** — recheck with `check_user_exists`. It may be an ID from another project.

## When Answering with Figures

Do not state counts from activity tracking **as metric figures**.

```text
X  This user has 3 purchases
O  3 by activity history (this can differ from the revenue metric, which applies the aggregation basis)
```

Apply the same basis when speaking about the cumulative values from `get_user_recent_info`
(`accKrw`, `accPurchaseCnt`).
