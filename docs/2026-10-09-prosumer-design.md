# Prosumer — design

## Architecture

`prosumer` is a Codex skill for transferring selected shopping data between sites.
It captures one selected product or one merchant cart through Playwright, preserves the observed
facts in a local JSON order draft, and later uses Playwright to prepare the corresponding form of
a chosen forwarding or buyout partner.

The JSON draft preserves state across browser sessions. The model interprets the current page;
the validator checks local data, not page truth or freshness.

## Boundaries

- A `merchant` is any store selected by the user.
- A `forwarder` is any forwarding or buyout partner selected by the user.
- ASOS and CDEK Forward are examples, not privileged implementations.
- There are no merchant or forwarder adapters. Playwright inspects the live
  page and works from visible labels, values and controls. Partner profiles may cache observed
  field locators: verify their live meaning first, rediscover on a miss, and retain read-back.
- The skill prepares a partner form and verifies it. It does not submit the form.
- Payment, ordering from the merchant, CAPTCHA solving, anti-bot bypass and return management are
  outside the skill's scope.

## Data and lifecycle

`captured -> validated -> prepared`

One draft represents one merchant product or cart; different merchants use separate sessions.
Selected variants remain separate lines, and order-level discounts are not redistributed across them.
Missing data stays explicit rather than being guessed. A partial `captured` draft can preserve a
blocked page, but it cannot advance until the required data is observed and validated.

`prepared` means the filled form was read back and matched the draft, not that an order was placed
or that the browser form is permanently saved. Credentials and personal data stay out of the draft.

Field definitions, browser procedures and cache validation are maintained in
[the data reference](../references/order-draft.md); the executable checks are in
[the validator](../scripts/validate_order_draft.py). Test scenarios and results are in [evals](../evals/).

## Browser-control references

- Official Playwright CLI: <https://github.com/microsoft/playwright-cli>. It exposes snapshots,
  stable element refs, form filling and named browser sessions.
- Official Playwright MCP: <https://github.com/microsoft/playwright-mcp>. It offers the same class
  of accessibility-snapshot browser control through MCP.

The skill uses the `playwright` browser-control skill. It needs observation, form filling and
read-back; it does not add its own browser server or integration runtime.

## Shopping-agent references inspected — 2026-10-09

These code references illustrate useful patterns and counterexamples, not verified compatibility
with live stores.

- [ValuSee, selected variant and price conditions](https://github.com/biheto/ValuSee/blob/0331f05bfda85b2ada01761f43781ce4dea6e28d/app/schemas/shopping.py): identity and quoted price belong to a particular variant and observed eligibility conditions.
- [Heng, basket audit](https://github.com/emmmdty/heng-agent/blob/db32d3bc8846f7d3c67b574e56d433066606f6a1/scripts/eval/audit_basket_sum.py): per-item landed prices can double-count basket delivery; absence of quoted data must remain visible, not become evidence of passing cases.
- [Shopping Autopilot, product-page flow](https://github.com/AndriiShramko/agentic-shopping-autopilot/blob/3761af7e5d9179aedad56eab2dd3eee75cc2449e/skills/allegro.pl/flows/product-page.md): reconsider stale price and availability. Automatic fallback to another product would violate the user's exact selection.
- [AI Shopper, selector](https://github.com/charithmadhuranga/agentic-ai-shopper/blob/main/agent.py): counterexample — restoring the full candidate set when filtering yields nothing can silently drop user constraints.

The ideas are exercised in [synthetic variant/resume scenarios](../evals/variant-price-and-resume/scenario.md).
