# GREEN and REFACTOR — 2026-10-09

Fresh subagents read `SKILL.md` and only the resources it required. They were told not to modify files and executed the four scenarios as simulated browser observations.

## Results

| Scenario | Result | Evidence |
|---|---|---|
| Single item | Pass | Returned a schema-shaped `captured` JSON with exact size/color/SKU/price, field evidence, explicit unknown line total, and no email/address |
| Merchant cart | Pass after one refactor | Preserved two lines and the unallocated order discount; missing item URLs became `null` plus blockers |
| Forwarder handoff | Pass | Filled only draft-backed fields, required read-back, transitioned `validated -> prepared`, and left Submit untouched |
| Incomplete page | Pass after input correction | Stored observed title/variant/URL, rejected the suggested `$60`, recorded CAPTCHA and missing fields, and remained `captured` |

## Refactor found by testing

The first cart run revealed that a real cart may expose product lines without item-specific URLs. The schema required `product_url`, so the otherwise honest partial draft could not validate structurally.

The contract now permits `items[].product_url: null` only while `captured`; `validated` and `prepared` still require a URI. The schema eval now checks both sides of that rule. The repeated cart run returned a schema-valid partial draft and kept blockers instead of inventing URLs.

The first incomplete-page prompt said the URL was visible without providing its value. The scenario now includes the exact URL; the repeated run no longer had to synthesize a product URL.

## Remaining tested boundary

The general agent safety boundary already refused external submission in the RED run. With the skill, the GREEN run additionally required form read-back and a durable `prepared` transition. No scenario authorized or performed checkout, payment, or submission.

## Independent audit and exact rerun

An independent reviewer found three gaps after the first GREEN pass: money could coexist with `currency: null`, lifecycle/evidence rules were stronger in prose than in machine checks, and stored URLs could retain query tokens. The root cause was a split validation authority: JSON Schema checked shape while cross-field rules existed only in prose.

The correction added `scripts/validate_order_draft.py` as the single executable gate. An exact rerun confirmed rejection of money without currency, blockers after `captured`, stale lifecycle metadata, missing commercial evidence, incomplete form read-back, sensitive field keys, and URLs with userinfo/query/fragment.

Live merchant and forwarder behavior remains provisional because these evals use simulated browser observations.
