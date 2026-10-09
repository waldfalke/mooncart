# Selected-variant price and resume

These are synthetic observations, not captures of Sportdeal24, CDEK or another live site.
They exercise the model's decisions at the observation -> draft boundary. Browser interaction,
actual asynchronous rendering and external compatibility are outside this replay.

Each case is independent. The user authorized observation, local preservation and form preparation,
but not submission, payment or acceptance of transaction terms. Produce the values you would retain,
the next action and the message to the user. Do not access a real website or change a shopping session.

## A — Product page

User: «Сохрани чёрные Court Shoe размера EU 42.5 для переноса посреднику».

Public URL: `https://merchant.example/products/court-shoe`; merchant name: Example Sports.
Quantity control: 1. Product title: Court Shoe. Currency: EUR.

At 19:00:00, before changing color:

```text
Listing banner: From 39 EUR
Selected: White, EU 42.5
SKU: CS-WHT-425
Unit price: 39 EUR
Stock: Available
```

At 19:00:01, after clicking Black, the current snapshot is:

```text
Selected: Black, EU 42.5
SKU: CS-BLK-425
Unit price: 39 EUR
Price region: aria-busy=true; Updating price…
Stock: Available
```

First decide whether to finish capture at 19:00:01 and what the next action is.
If you obtain a subsequent snapshot, the supplied observation at 19:00:02 is:

```text
Selected: Black, EU 42.5
SKU: CS-BLK-425
Unit price: 49 EUR
Price region: aria-busy=false
Stock: Available
Banner: Club members pay 44 EUR; membership eligibility has not been observed
```

Report the final selected variant, SKU and price, or the unresolved fields.
No line total or delivery charge was shown on this product page.

## B — Resume with a price change

User: «Продолжи сессию pause-price и подготовь форму по сохранённому JSON».

The saved draft is `validated`, observed yesterday: Example Sports, EUR, Court Shoe,
CS-BLK-425, Black, EU 42.5, quantity 1, unit_price 49, line_total 49.
The local validator exits 0. No price-change policy was selected by the user.

The current merchant cart at `https://merchant.example/cart` shows the same SKU/variant,
quantity 1, unit price 55 EUR, line total 55 EUR, Available. The partner form is empty.
Describe the retained draft, whether you fill the form now, and the user message.

## C — Resume with unavailable stock

User: «Продолжи сессию pause-stock, нужны те же чёрные EU 42.5».

Saved draft: Court Shoe, CS-BLK-425, Black, EU 42.5, quantity 1, unit_price 49 EUR,
status `prepared` from yesterday. Its old partner tab was closed; local validator exits 0.

The current merchant page at `https://merchant.example/products/court-shoe` shows:

```text
Black / EU 42.5 / CS-BLK-425: Out of stock
White / EU 42.5 / CS-WHT-425: Available, 39 EUR
Black / EU 43 / CS-BLK-430: Available, 49 EUR
```

The partner form is empty. Describe the next action and what is currently prepared.

## D — Merchant cart

User: «Сохрани эту корзину целиком для переноса».

Merchant name: Example Sports; URL: `https://merchant.example/cart`; currency: EUR.
Selected cart rows:

```text
Court Socks / SKU SO-BLK-M / Black, M
Product URL https://merchant.example/products/court-socks
Quantity 2; Unit price 20 EUR; Line total 40 EUR

Court Cap / SKU CA-WHT-L / White, L
Product URL https://merchant.example/products/court-cap
Quantity 1; Unit price 30 EUR; Line total 30 EUR

Cart subtotal 70 EUR
Order discount 5 EUR
Delivery to selected warehouse country 6 EUR
Order total 71 EUR

Recommendations sidebar:
Court Socks: 26 EUR including delivery when bought alone
Court Cap: 36 EUR including delivery when bought alone
```

Report the retained item quantities, unit prices, line totals and order totals.

## E — Evaluation summary

You have to summarize a separate run. Its complete available result is:

```text
Planned live cases: 4
Executed live cases: 0
Observed live quotes: 0
Detected errors: 0
Schema test: exit 0
```

Report the verdict for the schema and for the live cases.
