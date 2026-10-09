---
name: prosumer
description: Use when a user wants to preserve a product or online-store cart across browser sessions, resume a shopping transfer, or prepare item data in a parcel-forwarder or buyout form, especially when exact variants, prices, and provenance must survive between sites.
---

# Prosumer

**REQUIRED SUB-SKILL:** Use `playwright` for browser actions.

## Core contract

Move only browser-observed commerce data through one local `order-draft.json`:

`merchant page -> order draft -> forwarder form`

The draft is the boundary between browser sessions. A browser action is not complete until its result is observed; an unobserved value is an issue, never a guess.

Before the first action in a run, read [PASSPORT-prosumer.md](PASSPORT-prosumer.md). Before creating or changing a draft, read [references/order-draft.md](references/order-draft.md). After every write, run `python <skill-root>/scripts/validate_order_draft.py <draft>`; the script owns both schema and semantic validation.

## Actions

| Action | Use it for | Finished when |
|---|---|---|
| `capture` | One merchant product or cart | `stand/<session-id>/order-draft.json` has observed fields, evidence, and issues; status is `captured` |
| `validate` | Structural and semantic checks | The validator exits 0 with status `validated` |
| `handoff` | One user-selected forwarder form | Stored fields are filled and read back; status is `prepared`; submit remains untouched |

Use one `shopping-session` per merchant. Different merchants require different sessions.

## Browser loop

Use Playwright browser control. Snapshot before reading or using element references; snapshot again after navigation or significant UI change.

1. Observe the active page and selected controls.
2. Write only values supported by the page and add evidence paths.
3. Record absent, ambiguous, login-gated, region-gated, or CAPTCHA-gated data in `issues`.
4. Save and run the validator. Never rely on chat history as storage.

For `handoff`, read the chosen partner's profile in `references/partners/` when present. Try its observed locator cache first, checking the target's live meaning and row; on a miss or mismatch, discover that field from the live form and refresh the cache. See [partner locator cache](references/order-draft.md#кэш-локаторов-партнёра). This is a navigation hint, not an adapter or a source of purchase values. Fill only draft-backed values, read the populated form back, compare it with the draft, then record `prepared`. Never click a control that submits, pays, places an order, or creates an external request.

## Authority and privacy

The user chooses the merchant, forwarder, product, and external submission. This skill may observe, persist product facts, and prepare a form. It may not submit.

Do not store credentials, cookies, payment data, recipient addresses, phone numbers, or account identifiers. Persist URLs without userinfo, query, or fragment; if the path itself is personalized, keep only a safe public URL and record a blocker. If a required form field needs personal data, leave it untouched and report the blocker.

## Resume

Use the requested session ID. If none is given, inspect `stand/*/order-draft.json`; resume automatically only when exactly one unfinished session exists. If several exist, ask the user which one.

A requested `prepared` session records a past read-back, not a permanently saved partner form. If its tab is gone or inaccessible, validate the draft again, restore the fields in the authorized form and save a fresh read-back; never claim the old form is still populated.

## Common failures

- Chat-only or Markdown handoff: create the JSON draft.
- Claimed click, cart state, or validation without observed evidence: keep `captured` and add an issue.
- Cart discount spread across lines without page evidence: keep it only in `totals.discount`.
- `prepared` before read-back: compare the form first.
- Login or CAPTCHA barrier: save a partial `captured` JSON even before item identification, as described in the data reference; do not invent a line or title, and stop for the user.
