# regist_currency (Register or Change a Currency)

Registers the currency used to convert the company's revenue metrics, or changes the currency code of an existing
registration. The currency configuration decides the basis for converting revenue metrics, so changing it changes later
revenue query results.

> **Prerequisite:** Follow SETTING_ADMIN_GATE and WRITE_APPROVAL in [`../SKILL.md`](../SKILL.md).

## When to Use

- To add a currency when the company has no revenue conversion currency, or not enough of them
- To replace a currency code that was registered incorrectly
- Always check the current list and `idx` values with `list_currencies` before calling

## Parameters

| Parameter | Required | Description |
|---------|------|------|
| `currency_code` | Y | A three-letter ISO 4217 code, for example `KRW`. Lowercase input is normalized to uppercase |
| `company_cd` | Y | Company code confirmed from `list_projects` |
| `idx` | N | The idx of the registration to change (`list_currencies.idx`). Omit to register a new one |

## Return Value

Returns `idx`, `currency_code`, `action`, `before`, `previous_idx`, and the stored result.
`action` is `created` (new registration), `updated` (existing registration changed), or `unchanged` (already that code, so no
call was made).

## Decision Rules

- **A change replaces the `idx`.** The server has no currency update API, so the change is performed as a delete followed by a
  re-registration (the console does the same). In the return value, `previous_idx` is the old value that is gone and `idx` is
  the new one. Do not reuse the previous `idx`.
- If the same code is already registered, the tool blocks the registration. If you meant to change it, call again with that `idx`.
- If the target code already exists as another registration, the call is blocked before the delete, so no duplicate is created.
- Code validation checks only the ISO 4217 format. It does not verify that the code is selectable in the console, so if you are
  unsure, check the currency configuration screen in the console first.
- Present the target company, the current value, and the new value along with the fact that the revenue conversion basis
  changes, and obtain approval first.

## On Failure

- Format error or duplicate: blocked before the call, so nothing changed. Fix the value and call again.
- Re-registration failed during a change: the tool restores the original code. The error message contains the restored result
  and the new `idx`.
- Recovery also failed: that currency is left deleted. Follow the guidance in the error message and register it again in the console.
- Administrator privilege error: do not register. Prepare the request details to send to an Analytics administrator.

## Recommended Chain

```text
SETTING_ACCESS_GATE → list_currencies → confirm the current list and idx
→ SETTING_ADMIN_GATE → WRITE_APPROVAL → regist_currency
→ confirm it took effect with list_currencies
```
