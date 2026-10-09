# Variant price and resume — 2026-10-09

## Scope and decision

Input: [scenario.md](scenario.md), a synthetic observation replay. It does not model a particular
store's DOM, transport or rendering implementation. The oracle is the selected variant, raw price
region state and cart rows supplied in that file, together with the user's exact choice and authority.

Five fresh no-guidance samples were run before considering instruction edits. They exposed no failure
in these cases. Following `writing-skills`, no additional behavioral guidance was authored.
Five fresh samples then exercised the unchanged public `SKILL.md` with its passport/data reference.
This is a baseline and regression check, not evidence of a RED -> GREEN improvement.

No-guidance agents could read only the scenario from the skill. Guided agents received the same
scenario and the skill entrypoint, not the oracle, expected answers or earlier results. Every response
was read manually for the retained values, next action and user message. No scoring by keyword count.

## Decisions observed

| Case and falsifier | No guidance | Existing skill |
|---|---|---|
| A: Black/EU 42.5 must use the settled 49 EUR quote, not transitional/from 39 or unverified club 44; no invented line total | 5/5 passed | 5/5 passed |
| B: current 55 differs from stored 49; report change, retain history and pause preparation for a user decision | 5/5 passed | 5/5 passed |
| C: exact variant unavailable; no automatic size/color substitute and no current prepared-form claim | 5/5 passed | 5/5 passed |
| D: quantities 2/1, unit prices 20/30, line totals 40/30; one order discount 5 and shipping 6, total 71 | 5/5 passed | 5/5 passed |
| E: schema exit 0 passes that check; zero executed live cases are not a passing live run | 5/5 passed | 5/5 passed |

Samples: `variant_control_1` through `variant_control_5`, followed by `variant_guided_1` through
`variant_guided_5`. No production instructions were changed between the arms. All samples converged
on the decisions above; this small synthetic sample does not establish reliability on arbitrary sites.

Representative verbatim control-1 outcomes:

> В 19:00:01 захват не завершаю: цена ещё обновляется.

> Цена выросла с 49 до 55 EUR. Подготовить форму по текущей цене 55 EUR?

> Сейчас подготовленной формы нет: прежняя вкладка закрыта, новая пуста.

> Подытог 70 EUR; скидка заказа 5 EUR; доставка 6 EUR; итог заказа 71 EUR.

> «Обнаружено 0 ошибок» не подтверждает работоспособность.

## Persisted artifact check

Guided-4 also wrote independent A/D captures with the existing schema and validator, using
`apply_patch`. The artifacts are isolated replay files, not private shopping-session updates:

- отдельный временный `A/order-draft.json`
- отдельный временный `D/order-draft.json`

Машинные пути и временные артефакты не распространяются. Для повторения поведенческой проверки
нужен свежий агент с входом из `scenario.md`, создающий новые изолированные A/D captures.

The author read both files, independently asserted variant/SKU/currency/quantity/price, unknown
money in A, both line amounts and order totals in D, and absence of invented route/handoff.
Native PowerShell assertions exited 0:

```text
replay artifact assertions passed: A selected variant 49 EUR; D order total 71 EUR
```

The author also reran `python scripts/validate_order_draft.py <artifact>` for each: both exit 0,
status `captured`. Synthetic provenance is explicit in their issues; timestamps are replay processing
times, not a claim of live observation. Temporary artifacts may be removed by ordinary temp cleanup.

## Contract checks and boundaries

- `python evals/schema/validate.py`: exit 0, 5 valid / 14 invalid.
- `python evals/validator/validate_semantics.py`: exit 0, 6 valid / 17 invalid.
- Maintainer-only Codex `skill-creator/quick_validate.py`: exit 0; this external tool is not bundled.
- Private shopping state was not changed or included in this distribution.
- Schema, validator, partner profiles, `SKILL.md` and data reference: unchanged.

Passed: decisions under supplied observations and the local persisted-JSON checks above.
Failed: no failure observed in these cases; no claim of a newly fixed defect.
Not checked: real asynchronous rendering, live variant-specific prices, actual merchant refresh on
resume, multi-item live form transfer, server currency acceptance, checkout or purchase.

The model owns source interpretation and current-value comparison through Playwright in a real run.
The validator owns local structure/invariants and evidence-path coverage; it does not fetch pages or
prove that a claimed value matches a current merchant observation.
