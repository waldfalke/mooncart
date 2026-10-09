from copy import deepcopy
import json
from pathlib import Path

from jsonschema import Draft202012Validator


skill_root = Path(__file__).parents[2]
schema = json.loads((skill_root / "schemas/order-draft.schema.json").read_text(encoding="utf-8"))
valid = json.loads((Path(__file__).parent / "valid-order-draft.json").read_text(encoding="utf-8"))
validator = Draft202012Validator(schema)

valid_errors = list(validator.iter_errors(valid))
assert not valid_errors, "valid fixture failed: " + "; ".join(error.message for error in valid_errors)

partial_capture = deepcopy(valid)
partial_capture["status"] = "captured"
partial_capture["validated_at"] = None
partial_capture["items"][0]["product_url"] = None
partial_capture["issues"] = [
    {
        "code": "product_url_unobserved",
        "field": "/items/0/product_url",
        "message": "The cart did not expose an item URL.",
        "severity": "blocker",
    }
]
partial_errors = list(validator.iter_errors(partial_capture))
assert not partial_errors, "partial capture failed: " + "; ".join(error.message for error in partial_errors)

prepared = deepcopy(valid)
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
prepared_errors = list(validator.iter_errors(prepared))
assert not prepared_errors, "prepared fixture failed: " + "; ".join(error.message for error in prepared_errors)

blocked_capture = json.loads((Path(__file__).parent / "blocked-order-draft.json").read_text(encoding="utf-8"))
blocked_errors = list(validator.iter_errors(blocked_capture))
assert not blocked_errors, "blocked capture failed: " + "; ".join(error.message for error in blocked_errors)

untitled_capture = deepcopy(partial_capture)
untitled_capture["items"][0]["title"] = None
untitled_capture["issues"].append({
    "code": "title_unobserved", "field": "/items/0/title",
    "message": "A product row was visible but its title was absent.", "severity": "blocker",
})
untitled_errors = list(validator.iter_errors(untitled_capture))
assert not untitled_errors, "untitled capture failed: " + "; ".join(error.message for error in untitled_errors)

invalid_cases = {}

missing_currency = deepcopy(valid)
del missing_currency["merchant"]["currency"]
invalid_cases["missing currency"] = missing_currency

zero_quantity = deepcopy(valid)
zero_quantity["items"][0]["quantity"] = 0
invalid_cases["zero quantity"] = zero_quantity

unknown_status = deepcopy(valid)
unknown_status["status"] = "submitted"
invalid_cases["unknown status"] = unknown_status

sensitive_extra = deepcopy(valid)
sensitive_extra["customer_email"] = "buyer@example.com"
invalid_cases["sensitive extra field"] = sensitive_extra

validated_without_product_url = deepcopy(valid)
validated_without_product_url["items"][0]["product_url"] = None
invalid_cases["validated item without product URL"] = validated_without_product_url

prepared_without_handoff = deepcopy(valid)
prepared_without_handoff["status"] = "prepared"
prepared_without_handoff["prepared_at"] = "2026-10-09T19:05:00+03:00"
invalid_cases["prepared without route and handoff"] = prepared_without_handoff

money_without_currency = deepcopy(valid)
money_without_currency["status"] = "captured"
money_without_currency["validated_at"] = None
money_without_currency["merchant"]["currency"] = None
invalid_cases["money without currency"] = money_without_currency

validated_with_blocker = deepcopy(valid)
validated_with_blocker["issues"] = [
    {
        "code": "unresolved_price",
        "field": "/items/0/unit_price",
        "message": "Price still requires confirmation.",
        "severity": "blocker",
    }
]
invalid_cases["validated with blocker"] = validated_with_blocker

captured_with_validation_metadata = deepcopy(valid)
captured_with_validation_metadata["status"] = "captured"
invalid_cases["captured with validation metadata"] = captured_with_validation_metadata

for field in ("name", "title", "items"):
    candidate = deepcopy(valid)
    if field == "name":
        candidate["merchant"]["name"] = None
    elif field == "title":
        candidate["items"][0]["title"] = None
    else:
        candidate["items"] = []
    invalid_cases[f"validated without {field}"] = candidate

for field in ("name", "title"):
    candidate = deepcopy(partial_capture)
    if field == "name":
        candidate["merchant"]["name"] = ""
    else:
        candidate["items"][0]["title"] = ""
    invalid_cases[f"captured with empty {field}"] = candidate

for label, candidate in invalid_cases.items():
    assert list(validator.iter_errors(candidate)), f"invalid case passed: {label}"

print(f"schema checks passed: 5 valid, {len(invalid_cases)} invalid")
