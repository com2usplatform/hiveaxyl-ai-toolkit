---
name: axyl-detect-anomaly
metadata:
  version: "1.0.0"
description: |
  Detects unusual changes in Hive Analytics metrics with a conservative heuristic over raw values returned by
  preview_chart or preview_retention. It compares a completed target interval with same-position historical points,
  reports the numerical deviation, and suggests causes to verify without claiming causality.

  TRIGGER when:
  - The user asks whether a metric has spiked, dropped, or looks unusual
  - The user asks to scan several metrics for unusual changes
  - The user asks for possible reasons behind a metric change

  DO NOT TRIGGER when:
  - The request is only for a metric value → use preview_chart directly
  - The request is a dimension breakdown → use axyl-drill-down-metrics
  - The user asks to save a chart or dashboard → use axyl-create-content
---

# axyl-detect-anomaly

> **CRITICAL — Read [axyl-analytics-common](../axyl-analytics-common/SKILL.md) first.**
> **CRITICAL — Complete PROJECT_ID_GATE, ORG_WORKSPACE_GATE, SCHEMA_FIRST, and EXISTING_ASSET_FIRST before querying.**
> **CRITICAL — This skill produces a heuristic signal, not a statistical proof or a confirmed cause.**

## Supported Scope

Use only values the Analytics tools can actually return.

| Target | Query | Automatic rule |
|---|---|---|
| Any registered numeric metric | `preview_chart` in metric mode | Historical outlier rule |
| Count of a confirmed event | `preview_chart` in event mode | Historical outlier rule |
| Dn retention | `preview_retention` | Historical outlier rule after cohort maturity and size checks |

Do not automatically judge other unregistered derived metrics. A user-provided business threshold is an optional
minimum-effect guardrail; it does not replace the statistical rule.

Do not issue an automatic verdict when:

- an unregistered metric's event, dimension, or aggregation formula is unconfirmed;
- a metric uses `measure_date` and repeats a fixed-period value across chart dates;
- a registered metric's final value is not numeric or its selected time unit is incompatible with its definition;
- the returned response cannot be mapped unambiguously to the requested interval and metric.

Use a registered metric's final returned series as defined; do not reconstruct its ratio, average, or two-stage formula.
`metric_category` and a metric name are not enough to classify revenue. Follow SCHEMA_FIRST and use `is_price=1` on
the aggregated dimension when applying currency display rules. For an event count, use only an event and a non-null
count field confirmed by `list_events` and `list_dimensions` or an existing content definition; never invent the count
definition. Other event-based calculations are outside automatic detection.

## Workflow

### 1. Confirm scope

1. Confirm the project, organization, and workspace through the common gates.
2. Search existing assets first. A saved asset may confirm the intended definition, but anomaly calculation still uses
   `preview_chart` or `preview_retention` with explicit fixed dates.
3. Confirm the metric and its type with `list_metrics`. If it is unregistered, follow SCHEMA_FIRST.
4. Confirm the target interval and the time unit (`date_params.period`). If the time unit is omitted, use `D`. If the
   target interval is omitted, judge the last completed one in that unit (yesterday for `D`, last week for `W`). For Dn
   retention, the default target is the latest cohort whose day n has fully elapsed (the cohort of n + 1 days ago; two
   days ago for D1). Tell the user what was judged.
5. If the user asks to scan everything, select registered metrics that fit the supported scope. List unsupported or
   ambiguous metrics separately instead of silently forcing them into a default threshold.

### 2. Query target and references

Use KST and fixed date parameters (`start_date_type="F"`, `end_date_type="F"`). Do not rely on the tool's relative-date
default for a reproducible anomaly check.

| `date_params.period` | Target | Reference points |
|---|---|---|
| `MINUTE` | One completed minute interval | Same interval on the same weekday in the previous 8 weeks; query one day at a time |
| `H` | One completed hour | Same hour on the same weekday in the previous 8 weeks |
| `D` | One completed day | Same weekday in the previous 8 weeks |
| `W` | One completed Monday–Sunday week | Previous 12 completed Monday–Sunday weeks |
| `M` | One completed calendar month (e.g. 2026-08) | Previous 12 completed calendar months |

`MINUTE` requires `minute_interval` (1, 2, 5, or 10). When the metric is defined on a minute interval, such as
concurrent users measured as `COUNT_DISTINCT(userId)` of a session heartbeat event every 2 minutes, use that interval.

Judge `MINUTE` only for a named interval or the latest intervals within at most one hour (30 intervals at a 2-minute
interval); when the user gives no range, judge only the latest completed interval. When the user asks to find unusual
intervals over a day or several hours without naming a time, judge `H` first and go down to `MINUTE` only inside the
hours that are `watch` or above, and tell the user that a dip shorter than an hour may not show at `H`, so they can name
a time window to check by the minute. When the user names a time window, judge `MINUTE` directly inside it, at most
one hour at a time: a short dip in a distinct-user count can disappear at `H` because most users of the dip are also
counted in the rest of the hour. Minute intervals inside an hour, whether reached by drilling down or by a named window,
are judged under the scan rule in step 5.

For retention, query the target cohort and the previous 8 matured cohorts for the same weekday. A Dn value is usable
only after day n has fully elapsed in KST.

Request enough older history to replace a missing reference. Preserve the same metric definition, filters, project,
time unit, and currency across target and references. The Analytics API response is not a normalized schema; inspect the
returned columns and labels rather than assuming a fixed JSON path.

### 3. Check data reliability

Judge only completed intervals; a completed interval is treated as fully loaded. `list_events.last_data_date_kst` is the
latest company-level activity timestamp for that event. It is useful activity metadata only and must never be used to
claim that a target interval is fully loaded.

- An empty or null value, or a zero that would itself be an outlier (`outlier_score <= -3.5` under step 4, or any zero
  when the baseline is above 0 and the step-4 scale is 0), is
  `not judged — collection check needed` until the project, date range, metric definition, and related event activity
  have been checked. A zero that is not an outlier, common for a small count, is judged normally, but when the
  baseline is above 0, always show a collection note in the user-facing output, whatever the status:
  `no events recorded — check collection` for a count, `value is 0 — check collection` for any other metric. Do not
  silently convert null to zero.
- Replace missing reference points with older same-position points. Require at least 8 valid references; otherwise return
  `not judged — insufficient reference points`.

Known holidays, maintenance, outages, and major game events may be excluded only when supplied by the user or verified
under EXTERNAL_SEARCH_GATE. State each exclusion and replace it with the next older same-position point. Unknown schedules
are not guessed. If the target interval itself falls on such a known day, still judge it and list that day as the first
check.

### 4. Calculate the signal

Variation that common causes alone produce comes from two sources: day-to-day movement and the chance movement of a small
volume. A signal means the change is hard to explain by common causes alone; it does not identify a special cause.

```text
baseline        = median(valid reference values)
usual_variation = median(abs(reference value - baseline))   # day-to-day common-cause variation (technical name: MAD)
size_variation  = chance variation from volume, by metric kind (table below)
scale           = max(usual_variation / 0.6745, size_variation)
outlier_score   = (target - baseline) / scale
```

Classify the metric kind by its aggregation, not by its revenue flag. Read a registered metric's `metric_config` only
to classify it; never pass its tokens to a tool or rebuild the value from them. When unsure, use `other`.

| Metric kind | How to classify | `size_variation` |
|---|---|---|
| Count | An event-mode count, or a registered metric whose `metric_config` has a single expression with `COUNT` or `COUNT_DISTINCT` and no `measure_date` or two-stage aggregation. A `COUNT` over a price field is a count; still pass `currency` as the server requires | `sqrt(max(baseline, 1))` |
| Revenue | A `SUM` over an `is_price=1` field | `baseline / sqrt(max(baseline PU, 1))`, when a comparable registered PU metric is queried for the same references; otherwise 0 |
| Other | Averages, ratios of several expressions, two-stage aggregation, and anything unclassified | 0 |

- `abs(outlier_score) >= 3.5` is the automatic statistical outlier rule for a single check (step 5 raises it for scans).
  This is a heuristic, not a probability or proof.
- If the user supplies a minimum business effect (absolute, relative, or percentage-point), require both the outlier rule
  and that effect before reporting a statistical outlier. If only the outlier rule passes, report `watch`.
- If `usual_variation = 0` and `size_variation = 0`, the statistical threshold is undefined. An unchanged target is
  `normal`; a changed target is `watch — zero historical variability`, unless the user asks for a separate business-rule
  judgment.
- Show the raw difference and relative deviation when `baseline != 0`; these explain magnitude but do not set the default
  threshold.
- For revenue, show the confirmed currency. A comparable registered PU metric may be queried for explanation and for
  `size_variation`, but do not synthesize PU with an unconfirmed fallback definition. If the baseline PU is below 30, PU
  itself is within the usual range, and revenue is `watch` or above, report `watch` and list a few large payers as the
  first check.
- For a count or revenue metric at `D` or `H`, when the target falls on day 1–3 of a month, compare it with the
  recurring month-start pattern, whatever its first status. Skip the comparison for other metrics and when the target's
  own baseline is 0 or below. The same day of the month falls on different weekdays, so compare lifts, not raw values:

  ```text
  lift(day) = value(day) / median(same weekday, and same hour for H, in the 8 weeks before that day)
  ```

  1. Take the same day of the month (and hour) in each of the previous 8 months. Replace a month with an older one
     when the reference day, the day a week before, or the day a week after is a known exclusion (step 3), or when the
     reference day's weekday median is 0 or below; with fewer than 8, keep the status.
  2. Count the pattern months. Measure each reference day's deviation from its own weekday median in units of its own
     step-4 scale (for revenue, with the target's baseline PU). Measure the same weekday one week before and one week
     after it the same way, and take the mean of those two as its comparison deviation; a steady growth or decline moves
     the reference day and its comparison alike and cancels out, and a month-start event that runs longer than a week
     still differs from the week before. When a day's scale is 0, its deviation is a large value in the sign of its
     difference (0 when there is no difference); this applies wherever a day's deviation is used below. The pattern direction is above the
     weekday median when the median of the reference deviations is positive and below it when negative; a median of
     exactly 0 means no pattern. A reference month is a pattern month when, in the pattern direction, its deviation is
     at least 1 and its deviation minus its comparison deviation is also at least 1; a reference day whose own scale is
     0 and that differs in the pattern direction passes both tests. With fewer than 6 pattern months the pattern is not
     established: keep the status. A pattern that began 4 months ago is rarely established; one that began 5 months ago
     is established about a third of the time.
     Compute this with code when available. Otherwise lay out one row per reference month (day value, weekday median,
     scale, deviation, comparison deviation, difference, pattern month yes/no) before deciding.
  3. Judge the target lift (`target / baseline`) against the 8 reference lifts with the step-4 rule and the single-check
     threshold 3.5, even inside a scan. Their `size_variation` is `sqrt(max(baseline × median lift, 1)) / baseline` for a
     count and `median lift / sqrt(max(baseline PU, 1))` for revenue, otherwise 0. When their scale is 0, an identical
     target lift is within the usual range and any other lift is not.
  4. If the first status is `watch` or above and the target lift is within the usual range, report `normal` with the
     note `recurring month-start pattern`. If the first status is `normal` but the pattern is established and the target
     lift is outside the usual range, report `watch` with the note `usual month-start pattern missing`: the value looks
     ordinary only because the month-start rise did not happen. Otherwise keep the status and say whether the
     month-start pattern could be checked.

  One query covering about 12 months at the target's time unit supplies every value (query further back when months
  are replaced, and split it if the range is rejected); for `H`, keep only the target hour. Such a pattern can come
  from monthly pass renewals, paydays, or monthly spending-limit resets; do not assume which. This comparison moves a
  status only as item 4 above says: down to `normal`, or up to `watch` at most.
- For additive monthly metrics such as revenue or event count, compare monthly totals divided by calendar days when month
  lengths differ, and display both the normalized value and the raw total. For a normalized count, take `size_variation`
  from the raw total, not from the per-day value: `sqrt(max(baseline × days, 1)) / days`, where `days` is the target
  month's calendar days. Do not divide monthly unique users; query MAU with `period="M"`. When the target month differs
  from the median reference month by 2 or more calendar days (February), month length alone can move the value
  between the baseline and the prorated baseline (`baseline × target days / median reference days`). If a monthly
  unique-user count that is `watch` or above lies in that range, widened by `3.5 × scale` on each side, report at most
  `watch` with a month-length note that a drop of up to that size can be hidden by the shorter month; a change beyond
  it keeps its status.

Assign one status from the score, then apply the adjustments above in this order: the `watch` caps (minimum business
effect, small PU revenue, February monthly unique users), then the month-start comparison. Each result has exactly one
status:

| Signal status | Rule |
|---|---|
| `statistical outlier` | At least 8 valid references and `abs(outlier_score) >= 3.5` (7 in a scan), with no `watch` cap and no month-start lowering |
| `watch` | A `watch` cap applies; both variations are 0 with a changed target; a scan check has `3.5 <= abs(outlier_score) < 7`; or the usual month-start pattern is missing — in each case with no month-start lowering |
| `normal` | At least 8 valid references and `abs(outlier_score) < 3.5` with no month-start raising, or a recurring month-start pattern |
| `not judged` | Unsupported definition, missing data, immature retention, or fewer than 8 references |

A statistical outlier does not become a confirmed business incident.

### 5. Scan several checks

The more checks in one request, the more flags appear from common causes alone. When one request judges 3 or more
metric-interval checks:

- require `abs(outlier_score) >= 7` for `statistical outlier`; `3.5 <= abs(outlier_score) < 7` is `watch`;
- sort by status, then by `abs(outlier_score)`, and describe only the top 5 in detail;
- if more than 4 metrics of the same project are `watch` or above in the same target interval, list a data-collection
  check first.

Do not state probabilities or false-alarm rates to the user; the status labels carry the result.

### 6. Retention rule

Use the target Dn percentage and the previous 8 matured same-weekday cohort percentages. The target cohort can be much
smaller than the references, so add only the chance variation that its smaller size brings.

```text
baseline        = median(reference_retention_percent)
usual_variation = median(abs(reference_retention_percent - baseline))
p               = baseline / 100
v_ref           = 10000 × p(1 - p) / median(reference cohort size)
v_target        = 10000 × p(1 - p) / target cohort size
scale           = sqrt(max((usual_variation / 0.6745)², v_ref, (resolution / sqrt(6))²) + max(0, v_target - v_ref))
outlier_score   = (target_retention_percent - baseline) / scale
```

`resolution` is the rounding step of the returned percentages: 1 for whole percents (about 0.41 after `/ sqrt(6)`),
0.1 for one decimal place, 0.01 for two, 0 when they are not rounded; use the coarser step when the target and the references
differ. Rounded reference percentages can show no variation even when the true rate moves; this floor keeps a
difference smaller than the rounding error from becoming a signal. When a retention result is `normal` but the relative
change is 20% or more, apply the output rule below with `3.5 × sqrt(v_target)` in place of `3.5 × size_variation`.

Require the target and each included reference cohort to contain at least 100 users, replacing smaller references with
older same-weekday cohorts. Require 8 valid references. If cohort size is absent from the response, return `not judged`.
Apply the status table and scan rule above.

### 7. Explain and optionally investigate

Report the numerical evidence first. Then provide one to three hypotheses phrased as checks, not conclusions. Choose
related metrics based on the observed metric definition; do not use equations such as `AU ≈ NU + retention`, because a
rate is not an additive user count.

For a revenue signal, an optional aggregate explanation is:

```text
ARPPU = revenue / PU
revenue ratio = (target PU / baseline PU) × (target ARPPU / baseline ARPPU)
```

Use the same reference revenue baseline and reference PU baseline, and label this as aggregate decomposition. Skip it if
comparable PU is unavailable or the baseline or target PU is 0. Do not run `preview_chart_rank` by default: `rank_limit`
controls console display but does not limit returned rows, so a userId ranking can be very large. If the user explicitly
requests concentration analysis, use a narrow target interval and present it as descriptive concentration, not causal
contribution.

After a signal is found, external context is optional and must pass EXTERNAL_SEARCH_GATE. If verified context disqualifies
a reference date, replace that point and calculate once more. Otherwise state that internal schedules were not verified.

## User-Facing Output

Lead with the decision and the next action. Keep statistical terminology in the final evidence line.

| Internal status | User-facing label |
|---|---|
| `statistical outlier` | `Needs attention` |
| `watch` | `Monitor` |
| `normal` | `Within usual range` |
| `not judged` | `Pending data` |

For one metric, use this order:

```text
[Needs attention] Daily revenue — 2026-09-28

What changed: 13,420 USD, 36.9% above the recent same-weekday baseline of 9,800 USD.
What it means: This change is hard to explain as normal day-to-day fluctuation; this does not identify the cause.
Check first:
1. Campaign, promotion, or product changes on the date
2. Payment or service incidents
3. Related traffic or payer metrics

Analysis basis (reference): 8 comparable Mondays · typical level 9,800 USD · no internal schedule provided · automatic outlier rule passed
```

Adapt `What it means` and `Check first` to the confirmed metric definition. Do not invent business impact or a cause.
If the status is normal, omit the cause checklist unless the user asks. If it is pending data, lead with what is missing
and what would make the check possible. For a recurring month-start pattern, say that the change from the usual weekday
level matches the same day of recent months; that note replaces the explanation below. For `usual month-start pattern
missing`, state in `What changed` the expected month-start level (`baseline × median reference lift`) and the change
against it, use that change in the `Change vs usual` column, and list the monthly renewal, payment, or reset schedule as
the first check. For a recurring month-start row, measure the change against the expected month-start level
(`baseline × median reference lift`), not against the usual weekday level, when deciding whether it changed 20% or
more, and give `recurring month-start pattern` as its reason. When a result is `normal` but
the change is 20% or more, say why in `What it means`: a small volume when the change is smaller than
`3.5 × size_variation`, otherwise the metric's usual swing. For example: `The change is large, but at this small volume
changes this size happen without a specific cause.`

For several metrics, start with one line of counts and a compact action table sorted as in step 5, then explain only
`Needs attention` and `Monitor` rows:

```text
Checked 12 metrics for 2026-09-28: 1 needs attention, 1 to monitor, 10 within usual range.
Within usual range but changed 20% or more: Tutorial completions (-24%, small volume).
```

List the `Within usual range` rows that changed 20% or more on that second line with their reasons, up to 5 by size of
change, and summarize the rest as `N more metrics moved 20% or more within their usual range`, so a large normal change
is never silent. For retention, show both forms, for example `-8.0%p (-20% relative)`.

| Status | Metric | Target interval | Change vs usual | Check first | Basis |
|---|---|---|---|---|---|
| Needs attention | Daily revenue | 2026-09-28 | +36.9% | Promotion/payment schedule | 8 Mondays |
| Monitor | D1 retention | 2026-09-27 cohort | -6.2%p (-15.5% relative) | Cohort mix/acquisition source | 8 Sundays · cohort 1,240 users |

Put reference dates, typical level, exclusions, cohort sizes, and optional business thresholds under
`Analysis basis (reference)` after the action-oriented summary. Show the technical MAD and outlier score only when the
user asks for statistical details. Never expose internal identifiers.

## Never Do This

- Do not claim `last_data_date_kst` proves interval completeness.
- Do not judge the current minute interval, hour, week, or month as if it were complete.
- Do not use only the previous point when same-position references are available.
- Do not treat an empty response as a normal value, or report a zero against a baseline above 0 without a collection note.
- Do not call the outlier score a probability, confidence level, or proof of an incident.
- Do not infer an anomaly's cause from timing alone.
- Do not save or modify Analytics assets while running this read-only skill.
