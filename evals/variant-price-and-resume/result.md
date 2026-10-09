# Variant price and resume — 2026-10-09

## Method

Input: [scenario.md](scenario.md), a synthetic observation replay. It does not model a particular
store's DOM, transport or rendering implementation. The oracle is the selected variant, raw price
region state and cart rows supplied in that file, together with the user's exact choice and authority.

Five fresh agents received only the scenario; five more received the same scenario and `SKILL.md`
with its passport/data reference. The skill was unchanged between the groups.

Neither group received expected answers or earlier results. Responses were reviewed for retained
values, next action and user message, not scored by keyword count.

## Decisions observed

| Case and falsifier | No guidance | Existing skill |
|---|---|---|
| A: Black/EU 42.5 must use the settled 49 EUR quote, not transitional/from 39 or unverified club 44; no invented line total | 5/5 passed | 5/5 passed |
| B: current 55 differs from stored 49; report change, retain history and pause preparation for a user decision | 5/5 passed | 5/5 passed |
| C: exact variant unavailable; no automatic size/color substitute and no current prepared-form claim | 5/5 passed | 5/5 passed |
| D: quantities 2/1, unit prices 20/30, line totals 40/30; one order discount 5 and shipping 6, total 71 | 5/5 passed | 5/5 passed |
| E: schema exit 0 passes that check; zero executed live cases are not a passing live run | 5/5 passed | 5/5 passed |

Both groups passed these cases. This small sample does not establish reliability on arbitrary sites
or demonstrate an improvement caused by the skill.

## Persisted artifact check

One agent using the skill also saved separate A/D drafts. Independent assertions checked the
variant, SKU, currency, quantity and price; unknown money in A; both line amounts and order totals
in D; and absence of invented route/handoff. Assertions passed: A selected variant 49 EUR,
D order total 71 EUR.

`python scripts/validate_order_draft.py <draft>` exited 0 for both, with status `captured`.
Synthetic provenance was recorded in issues; timestamps described replay processing, not live
observation. To repeat this check, give a fresh agent [scenario.md](scenario.md) and have it save
new isolated A/D drafts.

## Contract checks and boundaries

- `python evals/schema/validate.py`: exit 0, 5 valid / 14 invalid.
- `python evals/validator/validate_semantics.py`: exit 0, 6 valid / 17 invalid.

Passed: decisions under supplied observations and the local persisted-JSON checks above.
Failed: no failure observed in these cases.
Not checked: real asynchronous rendering, live variant-specific prices, actual merchant refresh on
resume, multi-item live form transfer, server currency acceptance, checkout or purchase.

The model owns source interpretation and current-value comparison through Playwright in a real run.
The validator owns local structure/invariants and evidence-path coverage; it does not fetch pages or
prove that a claimed value matches a current merchant observation.
