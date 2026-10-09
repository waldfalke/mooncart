# Prosumer — design

Date: 2026-10-09
Status: approved by the user and implemented; refined by RED/GREEN evaluation

## Outcome

`prosumer` is a personal Codex skill for moving a shopping intention through a browser workflow.
It captures one selected product or one merchant cart through Playwright, preserves the observed
facts in a local JSON order draft, and later uses Playwright to prepare the corresponding form of
a chosen forwarding or buyout partner.

The first release is successful when a cart can be captured, the browser can change pages or the
work can resume later, and the partner form is filled with the same items without retyping them.

## Boundaries

- A `merchant` is any store selected by the user.
- A `forwarder` is any forwarding or buyout partner selected by the user.
- ASOS and CDEK Forward are examples, not privileged implementations.
- There are no merchant or forwarder adapters in the first release. Playwright inspects the live
  page and works from visible labels, values and controls. Partner profiles may cache observed
  field locators: verify their live meaning first, rediscover on a miss, and retain read-back.
- The skill prepares a partner form and verifies it. It does not submit the form in the first
  release.
- Payment, ordering from the merchant, CAPTCHA solving, anti-bot bypass and return management are
  outside the first release.

## Vocabulary

| Term | Meaning |
|---|---|
| `shopping-session` | One transfer of a product or cart from a merchant towards a forwarder |
| `order-draft` | The unsubmitted shopping facts captured from the merchant |
| `capture` | Read the selected product or cart through Playwright |
| `validate` | Check identity, variants, quantities, money and provenance before handoff |
| `handoff` | Fill the chosen forwarder's form from the order draft |
| `route` | The merchant, forwarder and countries involved in this shopping session |

Lifecycle: `captured -> validated -> prepared`.

## Skill shape

```text
prosumer/
  SKILL.md
  PASSPORT-prosumer.md
  schemas/
    order-draft.schema.json
  scripts/
    validate_order_draft.py
  references/
    order-draft.md
  evals/
    capture-single-item/
    capture-store-cart/
    handoff-to-forwarder/
    incomplete-page/
  stand/                         # ignored by Git and excluded from packages
    <shopping-session-id>/
      order-draft.json
  docs/
    2026-10-09-prosumer-design.md
```

`SKILL.md` is the thin entrance. The passport explains the goal, boundaries, locations, authority,
traps and current state. The schema owns the machine-readable contract. The reference explains
field semantics without restating the schema. `stand/` contains user-specific working state and is
never an example or distributable asset.

## Order-draft contract

One order draft represents one merchant product or cart. Different merchants use separate shopping
sessions. The format is forwarder-independent and contains:

- schema version, session identifier, lifecycle status and timestamps;
- merchant name, page URL and currency;
- one line per selected variant, even when titles match;
- product URL, displayed title, observed SKU when present, selected variant attributes, quantity,
  unit price and observed line total;
- observed cart totals and discounts without redistributing a cart-wide discount across items;
- provenance for values that affect identity or money;
- route and handoff metadata only after a forwarder is chosen;
- missing or ambiguous fields as explicit issues, never model guesses.

A blocked capture may contain no observed product rows (`items: []` with an items blocker), or
an observed row whose title is still unknown. Merchant name and item title may be null only in
`captured`, with issues. `validated` and `prepared` still require merchant identity, at least one
item and every item title. This widens partial capture without weakening the handoff boundary.

It never stores account credentials, cookies, payment data, personal delivery addresses or contact
details. Those remain in the user's browser session and the partner's form.

## Browser flow

### Capture

1. Bind the merchant tab selected or identified by the user.
2. Read the current product or cart and the currently selected variants.
3. Preserve separate cart lines and observed cart-level discounts.
4. Write `stand/<shopping-session-id>/order-draft.json`.
5. Run `scripts/validate_order_draft.py`; it applies the schema and cross-field invariants.
6. Report the session id, item count, total and every unresolved field.

### Resume

1. Use the session id supplied by the user.
2. If none is supplied, use the only incomplete session; if several exist, list them and ask which.
3. Run the validator before opening a partner form.

### Handoff

1. Bind the forwarder page selected or identified by the user.
2. Inspect the actual form and map JSON fields by their visible meaning.
3. Create exactly one form row for every order-draft line.
4. Fill only values present in the JSON or already present in the user's browser profile.
5. Read the completed form back and compare URLs, variants, quantities, currency and money.
6. Mark the draft `prepared` only when the visible form matches.
7. Stop before submission.

If login, CAPTCHA, a missing control or an unresolvable field blocks progress, preserve the draft,
record the issue and stop at the observed boundary. Do not change browser security or invent a value.

## Verification

The skill is developed test-first:

1. Baseline prompts without the skill must expose the expected failures: lost cart state, collapsed
   variants, guessed fields or manual re-entry.
2. The schema must reject a missing session id, invalid status and money without currency. The
   validator must prevent lifecycle promotion with missing identity, quantity, evidence or blockers.
3. Cold runs with the skill must cover a single product, a multi-line cart, a partner handoff and an
   incomplete or blocked page.
4. The handoff test passes only when the visible partner form contains the same number of rows and the
   same identifying and monetary values, while its submission control remains untouched.

## Explicitly deferred

- Site-specific adapters and executable selector libraries; observed field addresses in a partner
  profile are a cache, not an integration runtime.
- Automatic merchant checkout or payment.
- Partner-form submission.
- Cross-merchant consolidation inside one order draft.
- Price history, deal monitoring and return or warranty tracking.
- A standalone application, service or database.

## Decisions

- The skill and product name is `prosumer`.
- JSON is the machine-readable transport; YAML is not used in the first release.
- `order-draft` names an intention that has not yet become an order.
- Merchants and forwarders are open roles, not enumerated integrations.
- All browser interaction uses Playwright against pages the user selected or authorized.
- The first release ends at a verified, prepared form.

## Verified external basis — 2026-10-09

- Official Playwright CLI: <https://github.com/microsoft/playwright-cli>. It exposes snapshots,
  stable element refs, form filling and named browser sessions; the installed local `playwright`
  skill wraps this CLI.
- Official Playwright MCP: <https://github.com/microsoft/playwright-mcp>. It offers the same class
  of accessibility-snapshot browser control through MCP.
- Choice for v0.1: use the already installed CLI skill. It covers the required
  observe/fill/read-back loop without a new long-lived server. MCP remains a compatible transport
  alternative, not an additional architecture layer.

## Shopping-agent references inspected — 2026-10-09

These are code references, not evidence that those agents or our skill work on arbitrary live sites.
Only their relevant ideas were inspected; nothing was installed or copied into the runtime.

- [ValuSee, selected variant and price conditions](https://github.com/biheto/ValuSee/blob/0331f05bfda85b2ada01761f43781ce4dea6e28d/app/schemas/shopping.py): identity and quoted price belong to a particular variant and observed eligibility conditions.
- [Heng, basket audit](https://github.com/emmmdty/heng-agent/blob/db32d3bc8846f7d3c67b574e56d433066606f6a1/scripts/eval/audit_basket_sum.py): per-item landed prices can double-count basket delivery; absence of quoted data must remain visible, not become evidence of passing cases.
- [Shopping Autopilot, product-page flow](https://github.com/AndriiShramko/agentic-shopping-autopilot/blob/3761af7e5d9179aedad56eab2dd3eee75cc2449e/skills/allegro.pl/flows/product-page.md): reconsider stale price and availability. Automatic fallback to another ranked product is not adopted: our user owns the exact variant.
- [AI Shopper, selector](https://github.com/charithmadhuranga/agentic-ai-shopper/blob/main/agent.py): counterexample — restoring the full candidate set when filtering yields nothing can silently drop user constraints. No such fallback is adopted.

Application boundary: model decisions through Playwright; the existing JSON validator checks local
structure/invariants and evidence-path coverage, not page truth or freshness. No new price fields,
adapters, audit service or checkout behavior are justified by this research.

The ideas are exercised in [synthetic variant/resume scenarios](../evals/variant-price-and-resume/scenario.md).
Five no-guidance control samples already made the intended decisions. Additional behavioral rules
were therefore not authored merely to repeat those decisions; guided checks use the existing skill.
