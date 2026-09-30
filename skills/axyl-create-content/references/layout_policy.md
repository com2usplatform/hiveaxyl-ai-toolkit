# Dashboard Layout Policy (24-column grid)

`create_dashboard` **places `contents` automatically, in order**. The skill does not compute placement coordinates — for a new
layout it decides the `contents` order (the tool handles the coordinate arithmetic). To keep an existing layout (a template, a
recreated dashboard, or `update_dashboard`), pass each item's `width`/`height`/`memo` as well; omitted sizes fall back to the
defaults below.

## Placement Rules

- Grid width = **24 columns**. It fills left to right, and drops to the next row when the current row has too little width left.
- The row height (`position_size_y`) is the tallest content height in that row. **Maximum 6.**

## Default Sizes by Type (width × height)

| Content | Width `size_x` | Height `size_y` | Per row |
|--------|:---:|:---:|:---:|
| chart · scorecard | 6 | 2 | 4 |
| chart · line/column/bar/pie | 12 | 4 | 2 |
| chart · table | 24 | 6 | 1 |
| chart_rank · table | 24 | 6 | 1 |
| chart_rank · other charts | 12 | 4 | 2 |
| funnel | 12 | 4 | 2 |
| retention | 24 | 6 | 1 |

## Example

```
contents = [scorecard, scorecard, scorecard, scorecard, line, column, table, retention]
→
row 0 (y=0,  h=2): scorecard(x=0,w=6) scorecard(6,6) scorecard(12,6) scorecard(18,6)
row 1 (y=2,  h=4): line(0,12) column(12,12)
row 2 (y=6,  h=6): table(0,24)
row 3 (y=12, h=6): retention(0,24)
```

## Ordering Tips

- If the user wants a placement such as "KPIs at the top" → put the scorecard content **early** in `contents`.
- Wide content (table/retention) monopolizes a row, so grouping the narrow content (scorecards and charts) together first reduces empty space.
