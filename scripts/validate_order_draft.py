#!/usr/bin/env python3
import argparse
import json
import math
from pathlib import Path
import re
import sys
from urllib.parse import urlsplit

from jsonschema import Draft202012Validator, FormatChecker


SENSITIVE_KEYS = {
    "access_token",
    "account",
    "account_id",
    "address",
    "api_key",
    "authorization",
    "card",
    "card_number",
    "client_secret",
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
        path == required_path or required_path.startswith(path + "/")
        for path in paths
    )


def resolve_pointer(document, pointer):
    if not pointer.startswith("/") or re.search(r"~(?![01])", pointer):
        raise ValueError("invalid JSON Pointer")
    value = document
    for raw_part in pointer[1:].split("/"):
        part = raw_part.replace("~1", "/").replace("~0", "~")
        if isinstance(value, list):
            if not re.fullmatch(r"0|[1-9][0-9]*", part):
                raise ValueError("invalid array index")
            value = value[int(part)]
        elif isinstance(value, dict):
            value = value[part]
        else:
            raise TypeError("pointer traverses a scalar")
    return value


def finite_number(value):
    number = float(value)
    if not math.isfinite(number):
        raise ValueError("non-finite JSON number")
    return number


def unique_object(pairs):
    value = {}
    for key, child in pairs:
        if key in value:
            raise ValueError("duplicate JSON object field")
        value[key] = child
    return value


def web_origin(url):
    if "\\" in url or any(ord(char) <= 32 or ord(char) == 127 for char in url):
        raise ValueError("URL contains whitespace, controls or backslashes")
    parsed = urlsplit(url)
    host = parsed.hostname
    if parsed.scheme not in {"http", "https"} or not host:
        raise ValueError("URL must have an HTTP(S) scheme and host")
    if not host.isascii() or any(char in "%/#?@[]<>^|" for char in host):
        raise ValueError("URL must use the browser-normalized ASCII host")
    if parsed.netloc.startswith("[") and not re.fullmatch(
        r"\[[0-9a-fA-F:.]+\](?::[0-9]+)?", parsed.netloc
    ):
        raise ValueError("invalid bracketed web host")
    if parsed.username is not None or parsed.password is not None or parsed.query or parsed.fragment:
        raise ValueError("URL must contain only scheme, host and path")
    port = parsed.port
    return parsed.scheme, host, port if port is not None else (
        443 if parsed.scheme == "https" else 80
    )


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
    evidence_paths = set()
    for evidence in draft["evidence"]:
        for path in evidence["paths"]:
            try:
                resolve_pointer(draft, path)
            except (KeyError, IndexError, TypeError, ValueError):
                errors.append(f"evidence field is not a draft pointer: {path}")
            else:
                evidence_paths.add(path)
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

    origins = {}
    for path, url in iter_urls(draft):
        try:
            origins[path] = web_origin(url)
        except ValueError:
            errors.append(f"invalid or unsafe web URL at {path}")

    readback_paths = set()
    form_origin = origins.get("/route/form_url")
    for index, evidence in enumerate(draft["evidence"]):
        if evidence["method"] != "form_readback":
            continue
        if form_origin is None or origins.get(f"/evidence/{index}/source_url") != form_origin:
            errors.append(f"form_readback source differs from selected form origin: /evidence/{index}")
            continue
        readback_paths.update(evidence["paths"])

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
        for path in verified:
            try:
                resolve_pointer(draft, path)
            except (KeyError, IndexError, TypeError, ValueError):
                errors.append(f"verified field is not a draft pointer: {path}")
            if not covers(readback_paths, path):
                errors.append(f"verified field lacks form_readback evidence: {path}")
    return errors


def main():
    parser = argparse.ArgumentParser(description="Validate a Mooncart order draft")
    parser.add_argument("draft", type=Path)
    args = parser.parse_args()
    skill_root = Path(__file__).parents[1]
    try:
        schema = json.loads(
            (skill_root / "schemas/order-draft.schema.json").read_text(encoding="utf-8")
        )
        draft = json.loads(
            args.draft.read_text(encoding="utf-8"),
            parse_float=finite_number,
            parse_constant=finite_number,
            object_pairs_hook=unique_object,
        )
    except (OSError, ValueError) as error:
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
