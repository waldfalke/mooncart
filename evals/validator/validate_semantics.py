from copy import deepcopy
import json
from pathlib import Path
import subprocess
import sys
import tempfile


skill_root = Path(__file__).parents[2]
validator = skill_root / "scripts/validate_order_draft.py"
base = json.loads(
    (skill_root / "evals/schema/valid-order-draft.json").read_text(encoding="utf-8")
)


def run(candidate):
    with tempfile.TemporaryDirectory() as temporary_directory:
        draft_path = Path(temporary_directory) / "order-draft.json"
        payload = candidate if isinstance(candidate, str) else json.dumps(candidate)
        draft_path.write_text(payload, encoding="utf-8")
        return subprocess.run(
            [sys.executable, str(validator), str(draft_path)],
            capture_output=True,
            text=True,
            check=False,
            timeout=10,
        )


partial = deepcopy(base)
partial["status"] = "captured"
partial["validated_at"] = None
partial["items"][0]["product_url"] = None
partial["evidence"][1]["paths"].remove("/items/0/product_url")
partial["issues"] = [
    {
        "code": "product_url_unobserved",
        "field": "/items/0/product_url",
        "message": "The cart did not expose an item URL.",
        "severity": "blocker",
    }
]

prepared = deepcopy(base)
prepared["status"] = "prepared"
prepared["prepared_at"] = "2026-10-09T19:05:00+03:00"
prepared["route"] = {
    "forwarder_name": "Example Forwarder",
    "form_url": "https://forwarder.example/request",
    "selected_at": "2026-10-09T19:03:00+03:00",
}
prepared["handoff"] = {
    "verified_at": "2026-10-09T19:05:00+03:00",
    "verified_fields": [
        "/merchant/name",
        "/merchant/currency",
        "/items/0/product_url",
        "/items/0/title",
        "/items/0/sku",
        "/items/0/variant",
        "/items/0/quantity",
        "/items/0/unit_price",
    ],
    "unfilled_fields": ["recipient_address", "card_number"],
    "submitted": False,
}
prepared["evidence"].append(
    {
        "paths": list(prepared["handoff"]["verified_fields"]),
        "source_url": "https://forwarder.example/request",
        "observed_at": "2026-10-09T19:05:00+03:00",
        "method": "form_readback",
    }
)

extended = deepcopy(prepared)
extended["items"][0].update({"brand": "Example Brand", "item_type": "Basketball shoes"})
extended["route"].update({"merchant_country": "Germany", "warehouse": "Leipzig"})
extra_paths = ["/items/0/brand", "/items/0/item_type", "/route/merchant_country", "/route/warehouse"]
extended["evidence"][0]["paths"].extend(extra_paths)
extended["handoff"]["verified_fields"].extend(extra_paths)
extended["evidence"][-1]["paths"].extend(extra_paths)

blocked_capture = json.loads(
    (skill_root / "evals/schema/blocked-order-draft.json").read_text(encoding="utf-8")
)
untitled_capture = deepcopy(partial)
untitled_capture["items"][0]["title"] = None
untitled_capture["evidence"][0]["paths"].remove("/items/0/title")
untitled_capture["issues"].append({
    "code": "title_unobserved", "field": "/items/0/title",
    "message": "A product row was visible but its title was absent.", "severity": "blocker",
})

grouped_evidence = deepcopy(base)
grouped_evidence["evidence"][0]["paths"] = ["/merchant", "/items/0", "/totals"]

redirected = deepcopy(prepared)
redirected["evidence"][-1]["source_url"] = "https://forwarder.example/request/review"

default_port = deepcopy(prepared)
default_port["route"]["form_url"] = "https://FORWARDER.example:443/request"

ipv6 = deepcopy(base)
ipv6["merchant"]["page_url"] = "https://[2001:db8::1]:443/cart"

http_form = deepcopy(prepared)
http_form["route"]["form_url"] = "http://FORWARDER.example:80/request"
http_form["evidence"][-1]["source_url"] = "http://forwarder.example/review"

valid_cases = {"validated": base, "partial capture": partial, "prepared": prepared,
               "prepared with product and route fields": extended,
               "blocked capture before identity": blocked_capture,
               "capture with unknown title": untitled_capture,
               "grouped evidence": grouped_evidence,
               "same-origin form redirect": redirected,
               "equivalent origin with default port": default_port,
               "normal IPv6 host": ipv6,
               "HTTP form with default port": http_form}
for label, candidate in valid_cases.items():
    result = run(candidate)
    assert result.returncode == 0, f"valid {label} failed: {result.stdout}{result.stderr}"

invalid_cases = {}

missing_evidence = deepcopy(base)
missing_evidence["evidence"][0]["paths"].remove("/items/0/unit_price")
invalid_cases["missing evidence"] = missing_evidence

unsafe_url = deepcopy(base)
unsafe_url["merchant"]["page_url"] = "https://merchant.example/cart?token=secret"
invalid_cases["unsafe URL query"] = unsafe_url

sensitive_key = deepcopy(base)
sensitive_key["items"][0]["variant"]["email"] = "buyer@example.com"
invalid_cases["sensitive field key"] = sensitive_key

prepared_without_verified_quantity = deepcopy(prepared)
prepared_without_verified_quantity["handoff"]["verified_fields"].remove(
    "/items/0/quantity"
)
prepared_without_verified_quantity["evidence"][-1]["paths"].remove(
    "/items/0/quantity"
)
invalid_cases["prepared without verified quantity"] = prepared_without_verified_quantity

for path in extra_paths:
    without_evidence = deepcopy(extended)
    for observation in without_evidence["evidence"]:
        observation["paths"] = [value for value in observation["paths"] if value != path]
    invalid_cases[f"missing evidence for {path}"] = without_evidence

    without_readback = deepcopy(extended)
    without_readback["handoff"]["verified_fields"].remove(path)
    without_readback["evidence"][-1]["paths"].remove(path)
    invalid_cases[f"missing read-back for {path}"] = without_readback

empty_warehouse = deepcopy(extended)
empty_warehouse["route"]["warehouse"] = ""
invalid_cases["empty warehouse"] = empty_warehouse

for severity in (None, "warning"):
    candidate = deepcopy(blocked_capture)
    candidate["issues"] = [issue for issue in candidate["issues"] if issue["field"] != "/items"]
    if severity:
        candidate["issues"].append({
            "code": "items_unobserved", "field": "/items",
            "message": "No product rows were observed.", "severity": severity,
        })
    invalid_cases[f"empty capture without items blocker ({severity})"] = candidate

without_merchant_issue = deepcopy(blocked_capture)
without_merchant_issue["issues"] = [issue for issue in without_merchant_issue["issues"] if issue["field"] != "/merchant/name"]
invalid_cases["unknown merchant without issue"] = without_merchant_issue

without_title_issue = deepcopy(untitled_capture)
without_title_issue["issues"] = [issue for issue in without_title_issue["issues"] if issue["field"] != "/items/0/title"]
invalid_cases["unknown title without issue"] = without_title_issue

for key in ("access_token", "api_key", "client_secret", "authorization"):
    for alias in {key, key.replace("_", "-")}:
        candidate = deepcopy(base)
        candidate["items"][0]["variant"][alias] = "synthetic-secret"
        invalid_cases[f"credential alias {alias}"] = candidate

for token in ("NaN", "Infinity", "-Infinity", "1e9999", "-1e9999"):
    payload = json.dumps(base)
    candidate = payload.replace('"unit_price": 70.0', f'"unit_price": {token}')
    assert candidate != payload, "numeric fault was not injected"
    invalid_cases[f"nonfinite money {token}"] = candidate

for pointer in ("/", "/items/0/missing", "/items/-1/title", "/items/00/title",
                "/items/+0/title", "/items/0/title/0", "/items/0/title~2",
                "//merchant/name"):
    candidate = deepcopy(base)
    candidate["evidence"][0]["paths"].append(pointer)
    invalid_cases[f"invalid evidence pointer {pointer}"] = candidate

root_evidence = deepcopy(base)
root_evidence["evidence"] = [deepcopy(base["evidence"][0])]
root_evidence["evidence"][0]["paths"] = ["/"]
invalid_cases["root pointer cannot cover commercial facts"] = root_evidence

for location in ("merchant", "item", "route", "evidence", "issue"):
    candidate = deepcopy(prepared)
    if location == "merchant":
        candidate["merchant"]["page_url"] = "https:/cart"
    elif location == "item":
        candidate["items"][0]["product_url"] = "https:/cart"
    elif location == "route":
        candidate["route"]["form_url"] = "https:/cart"
    elif location == "evidence":
        candidate["evidence"][0]["source_url"] = "https:/cart"
    else:
        candidate["issues"] = [{
            "code": "test_warning", "field": None, "message": "Synthetic warning.",
            "severity": "warning", "source_url": "https:/cart",
        }]
    invalid_cases[f"hostless URL at {location}"] = candidate

for url in ("https://:443/cart", "https://merchant.example:bad/cart",
            "https://merchant.example:65536/cart", "https://merchant%2fexample/cart",
            "https://merchant%00example/cart", "https://merchant%2eexample/cart",
            "https://@merchant.example/cart", "https://merchant.example\n/cart",
            "https://merchant.example\\@evil.example/cart", "https://merchant<example/cart",
            "https://[::1]suffix/cart", "https://[v1.example]/cart"):
    candidate = deepcopy(base)
    candidate["merchant"]["page_url"] = url
    invalid_cases[f"unsafe or non-normalized web URL {url}"] = candidate

for source in ("https://other.example/request", "http://forwarder.example/request",
               "https://forwarder.example:444/request",
               "https://forwarder.example.other.example/request"):
    candidate = deepcopy(prepared)
    candidate["evidence"][-1]["source_url"] = source
    invalid_cases[f"unrelated form origin {source}"] = candidate

invalid_verified = deepcopy(prepared)
invalid_verified["handoff"]["verified_fields"].append("/items/-1/title")
invalid_verified["evidence"][-1]["paths"].append("/items/-1/title")
invalid_cases["invalid verified array index"] = invalid_verified

foreign_early_readback = deepcopy(prepared)
foreign_early_readback["status"] = "validated"
foreign_early_readback["prepared_at"] = None
del foreign_early_readback["handoff"]
foreign_early_readback["evidence"][-1]["source_url"] = "https://other.example/request"
invalid_cases["foreign readback before prepared"] = foreign_early_readback

payload = json.dumps(base)
duplicate_secret = payload.replace(
    '"variant": {', '"variant": {"access_token": "synthetic-secret"}, "variant": {', 1
)
assert duplicate_secret != payload, "duplicate-key fault was not injected"
invalid_cases["duplicate object hides credential key"] = duplicate_secret
invalid_cases["duplicate quantity is ambiguous"] = payload.replace(
    '"quantity": 1', '"quantity": 2, "quantity": 1', 1
)

failures = []
for label, candidate in invalid_cases.items():
    result = run(candidate)
    if result.returncode != 1 or not result.stderr.startswith("invalid:"):
        failures.append(f"{label}: exit={result.returncode}, {result.stdout}{result.stderr}")

if failures:
    print("\n".join(failures), file=sys.stderr)
    raise SystemExit(1)

print(f"semantic checks passed: {len(valid_cases)} valid, {len(invalid_cases)} invalid")
