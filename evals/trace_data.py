"""Read recorded outputs, including provider-returned failed generations."""

import hashlib
import json


def provider_error(record):
    try:
        value = json.loads(record.get("response_body", "{}")).get("error", {})
        return value if isinstance(value, dict) else {}
    except (ValueError, TypeError, AttributeError):
        return {}


def output_text(record):
    if isinstance(record.get("raw_output"), str):
        return record["raw_output"]
    failed = provider_error(record).get("failed_generation")
    return failed if isinstance(failed, str) else None


def output_fingerprint(record):
    text = output_text(record)
    if text is None:
        # Older label-only fixtures can identify an already-fingerprinted output.
        if "response_body" not in record and record.get("output_sha256"):
            return record["output_sha256"]
        text = {"http_status": record.get("http_status"), "response_body": record.get("response_body")}
    return hashlib.sha256(json.dumps(text, sort_keys=True, ensure_ascii=False).encode()).hexdigest()


def structural_outcome(record):
    if provider_error(record).get("code") == "json_validate_failed":
        return "provider_schema_rejection"
    return record["structural_status"]
