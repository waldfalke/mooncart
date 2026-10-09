# Eval: capture a merchant cart

## Prompt

You are controlling a merchant cart in a real browser. The user has spent an hour selecting variants and says: “Save the whole cart quickly. We will enter it into an unknown forwarding service later.”

The cart visibly contains:

1. `Running Top`, SKU `RT-BLK-M`, color `Black`, size `M`, quantity `2`, unit price `$40.00`, line total `$80.00`.
2. `Court Shoe`, SKU `CS-WHT-425`, color `White`, size `EU 42.5`, quantity `1`, unit price `$70.00`, line total `$70.00`.

Cart summary: subtotal `$150.00`, order-level discount `$15.00`, total `$135.00`. The page does not allocate the discount to individual lines. Merchant name is `Example Sports`; currency is USD; cart URL is `https://merchant.example/cart`.

Create the smallest reliable artifact another browser session can use. Do not ask follow-up questions.

## Passing observations

- Keeps two distinct item lines and exact selected variants/quantities.
- Stores subtotal, order-level discount, and total separately.
- Does not invent per-line discounted prices or a forwarder.
- Makes the draft resumable without relying on chat history.
