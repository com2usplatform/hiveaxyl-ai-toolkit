# list_currencies (List Currencies)

> **Prerequisite:** Follow the common rules in [`../SKILL.md`](../SKILL.md).

## When to Use

- To confirm the currency code to use before passing a revenue metric (one whose aggregated dimension has `is_price=1`) to `preview_chart`.
- To check the currency candidates configured for the company when the user has not specified a currency.
- To confirm the current list and the `idx` of the registration to change before registering or changing a currency with `regist_currency`.

## Parameters

| Parameter | Required | Description |
|---------|------|------|
| `company_cd` | Y | Company code (the `company_cd` from `list_projects`) |

## Return Value

Returns the currencies configured for the company as a list of `idx` and `currency_code`.
`idx` identifies a single registration row and is used only to point `regist_currency` at the row to change. Currency
lookup itself needs nothing but `currency_code`.

## Decision Rules

- If the company has exactly one configured currency, use it as is.
- If there are several, ask the user which currency basis to use. Do not arbitrarily pick one (NO_GUESSING).
- If the result is empty, use `"USD"` as the default and tell the user that the default was applied because the company has no currency configuration.
- Querying a revenue metric without specifying a currency is handled as a raw SUM (a mixed-currency total), which can make the value inaccurate.
- `idx` is not a stable identifier. Changing a currency with `regist_currency` assigns that registration a new `idx`, so call
  this tool again right after a change to confirm it.

## On Failure

- Empty result: the company has no currency configuration. Use `"USD"` as the default and disclose that the fallback was applied.

## Recommended Chain

```
list_currencies → list_events + list_dimensions (or list_metrics) → (ORG_WORKSPACE_GATE) → preview_chart (with currency specified)
```

When changing the configuration:

```
SETTING_ACCESS_GATE → list_currencies → SETTING_ADMIN_GATE → WRITE_APPROVAL → regist_currency
→ confirm it took effect with list_currencies
```
