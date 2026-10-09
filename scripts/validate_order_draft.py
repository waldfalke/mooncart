#!/usr/bin/env python3
import argparse
import json
from pathlib import Path
import sys
from urllib.parse import urlsplit

from jsonschema import Draft202012Validator, FormatChecker


SENSITIVE_KEYS = {
    "account",
    "account_id",
    "address",
    "card",
    "card_number",
    "cookie",
    "cookies",
    "cvc",
    "cvv",
    "delivery_address",
    "email",
    "iban",
    "password",
    "phone",
    "phone_number",
    "recipient_address",
    "refresh_token",
    "token",
    "user_id",
    "username",
}


def pointer_escape(value):
    return str(value).replace("~", "~0").replace("/", "~1")


def commercial_paths(draft):
    for key in ("name", "page_url", "currency"):
        if draft["merchant"].get(key) is not None:
            yield f"/merchant/{key}"
    for index, item in enumerate(draft["items"]):
        prefix = f"/items/{index}"
        for key in ("product_url", "title", "brand", "item_type", "sku", "quantity", "unit_price", "line_total"):
            if item.get(key) is not None:
                yield f"{prefix}/{key}"
        for key, value in item.get("variant", {}).items():
            if value is not None:
                yield f"{prefix}/variant/{pointer_escape(key)}"
    for key, value in draft.get("totals", {}).items():
        if value is not None:
            yield f"/totals/{key}"
    for key in ("merchant_country", "warehouse"):
        if draft.get("route", {}).get(key) is not None:
            yield f"/route/{key}"


def covers(paths, required_path):
    return any(
        path == required_path or required_path.startswith(path.rstrip("/") + "/")
        for path in paths
    )


def resolve_pointer(document, pointer):
    value = document
    for raw_part in pointer.lstrip("/").split("/"):
        part = raw_part.replace("~1", "/").replace("~0", "~")
        value = value[int(part)] if isinstance(value, list) else value[part]
    return value


def iter_keys(value, path=""):
    if isinstance(value, dict):
        for key, child in value.items():
            child_path = f"{path}/{pointer_escape(key)}"
            yield child_path, key
            yield from iter_keys(child, child_path)
    elif isinstance(value, list):
        for index, child in enumerate(value):
            yield from iter_keys(child, f"{path}/{index}")


def iter_urls(draft):
    yield "/merchant/page_url", draft["merchant"]["page_url"]
    for index, item in enumerate(draft["items"]):
        if item.get("product_url"):
            yield f"/items/{index}/product_url", item["product_url"]
    if draft.get("route"):
        yield "/route/form_url", draft["route"]["form_url"]
    for collection in ("evidence", "issues"):
        for index, entry in enumerate(draft.get(collection, [])):
            if entry.get("source_url"):
                yield f"/{collection}/{index}/source_url", entry["source_url"]


def semantic_errors(draft):
    errors = []
    evidence_paths = {
        path for evidence in draft["evidence"] for path in evidence["paths"]
    }
    for required_path in commercial_paths(draft):
        if not covers(evidence_paths, required_path):
            errors.append(f"missing evidence for {required_path}")

    issue_fields = {issue.get("field") for issue in draft["issues"]}
    nullable_paths = ["/merchant/name", "/merchant/currency"]
    for index, item in enumerate(draft["items"]):
        nullable_paths.extend(
            f"/items/{index}/{key}"
            for key in ("product_url", "title", "sku", "quantity", "unit_price", "line_total")
        )
    for path in nullable_paths:
        if resolve_pointer(draft, path) is None and path not in issue_fields:
            errors.append(f"null field lacks an issue: {path}")

    if not draft["items"] and not any(
        issue.get("field") == "/items" and issue["severity"] == "blocker"
        for issue in draft["issues"]
    ):
        errors.append("empty capture lacks a blocker for /items")

    line_ids = [item["line_id"] for item in draft["items"]]
    if len(line_ids) != len(set(line_ids)):
        errors.append("duplicate item line_id")
    if draft["status"] != "captured" and any(
        issue["severity"] == "blocker" for issue in draft["issues"]
    ):
        errors.append(f"{draft['status']} draft contains a blocker")

    for path, key in iter_keys(draft):
        if key.lower().replace("-", "_") in SENSITIVE_KEYS:
            errors.append(f"sensitive field key: {path}")

    for path, url in iter_urls(draft):
        parsed = urlsplit(url)
        if parsed.scheme not in {"http", "https"}:
            errors.append(f"non-web URL at {path}")
        if parsed.username or parsed.password or parsed.query or parsed.fragment:
            errors.append(f"URL must contain only scheme, host and path: {path}")

    if draft["status"] == "prepared":
        verified = set(draft["handoff"]["verified_fields"])
        required_verified = {"/merchant/name", "/merchant/currency"}
        for index, item in enumerate(draft["items"]):
            prefix = f"/items/{index}"
            required_verified.update(
                {
                    f"{prefix}/product_url",
                    f"{prefix}/title",
                    f"{prefix}/quantity",
                    f"{prefix}/unit_price",
                }
            )
            for key in ("sku", "brand", "item_type"):
                if item.get(key) is not None:
                    required_verified.add(f"{prefix}/{key}")
            for key in item.get("variant", {}):
                required_verified.add(f"{prefix}/variant/{pointer_escape(key)}")
        for key in ("merchant_country", "warehouse"):
            if draft.get("route", {}).get(key) is not None:
                required_verified.add(f"/route/{key}")
        for path in required_verified:
            if not covers(verified, path):
                errors.append(f"prepared field was not read back: {path}")
        readback_paths = {
            path
            for evidence in draft["evidence"]
            if evidence["method"] == "form_readback"
            for path in evidence["paths"]
        }
        for path in verified:
            try:
                resolve_pointer(draft, path)
            except (KeyError, IndexError, TypeError, ValueError):
                errors.append(f"verified field is not a draft pointer: {path}")
            if not covers(readback_paths, path):
                errors.append(f"verified field lacks form_readback evidence: {path}")
    return errors


def main():
    parser = argparse.ArgumentParser(description="Validate a Prosumer order draft")
    parser.add_argument("draft", type=Path)
    args = parser.parse_args()
    skill_root = Path(__file__).parents[1]
    try:
        schema = json.loads(
            (skill_root / "schemas/order-draft.schema.json").read_text(encoding="utf-8")
        )
        draft = json.loads(args.draft.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        print(f"invalid: {error}", file=sys.stderr)
        return 1

    validator = Draft202012Validator(schema, format_checker=FormatChecker())
    errors = [error.message for error in validator.iter_errors(draft)]
    if not errors:
        errors.extend(semantic_errors(draft))
    if errors:
        for error in errors:
            print(f"invalid: {error}", file=sys.stderr)
        return 1
    print(f"valid: {args.draft} (status={draft['status']})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
