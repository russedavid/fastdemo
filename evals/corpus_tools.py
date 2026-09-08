"""Deterministic corpus validation and coverage reporting; no model calls."""

import argparse
import hashlib
import json
from collections import Counter, defaultdict
from pathlib import Path

HERE = Path(__file__).resolve().parent


def quality_report(path):
    path = Path(path)
    cases = [json.loads(x) for x in path.read_text().splitlines() if x.strip()]
    by_id = {c["id"]: c for c in cases}
    if len(by_id) != len(cases):
        raise ValueError("Duplicate case IDs")
    fields = ("equipment_id", "parts_used", "priority", "next_service_date")
    exact_sources = defaultdict(list)
    reference_cases = defaultdict(set)
    families = defaultdict(list)
    source_count = 0
    for case in cases:
        source_ids = {s["id"] for s in case["sources"]}
        if len(source_ids) != len(case["sources"]):
            raise ValueError("Duplicate source IDs in " + case["id"])
        families[case["family"]].append(case["id"])
        for source in case["sources"]:
            if not source["text"].strip():
                raise ValueError("Empty source")
            source_count += 1
            exact_sources[hashlib.sha256(source["text"].encode()).hexdigest()].append(
                {"case_id": case["id"], "source_id": source["id"]})
            if source.get("reference_uri"):
                reference_cases[source["reference_uri"]].add(case["id"])
                if not source.get("license") or not source.get("attribution"):
                    raise ValueError("Public reference is missing licensing/provenance")
        for item in list(case["reference"]["fields"].values()) + case["reference"]["statements"] + case["reference"]["proposals"]:
            if not item["source_ids"] or not set(item["source_ids"]) <= source_ids:
                raise ValueError("Invalid reference source IDs")
        expected = case["reference"]["fields"]
        for name in fields:
            value = expected[name]
            if value["state"] == "known" and value["value"] is None:
                raise ValueError("Known reference has no value")
            if value["state"] in ("unknown", "conflicting") and value["value"] is not None:
                raise ValueError("Unknown/conflicting reference contains an answer")
        if expected["equipment_id"]["state"] == "known" and not any(
            expected["equipment_id"]["value"] in s["text"] for s in case["sources"]
            if s["id"] in expected["equipment_id"]["source_ids"]
        ):
            raise ValueError("Reference equipment ID is not in its cited source")
        parts = expected["parts_used"]
        if parts["state"] == "known" and not parts["value"]:
            raise ValueError("Empty known parts reference; use none if explicitly supported")
        if parts["state"] == "none" and parts["value"] != []:
            raise ValueError("Explicit none must have an empty parts list")
        for part in parts["value"] or []:
            quantity = part["quantity"]
            if quantity is not None and (type(quantity) is not int or quantity < 1):
                raise ValueError("Invalid reference quantity")
            if not any(part["part_number"] in source["text"] for source in case["sources"]
                       if source["id"] in parts["source_ids"]):
                raise ValueError("Reference part number is not in its cited source")
    states = {name: dict(Counter(c["reference"]["fields"][name]["state"] for c in cases)) for name in fields}
    return {
        "dataset_sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
        "cases": len(cases), "sources": source_count,
        "splits": dict(Counter(c["split"] for c in cases)),
        "exposure": dict(Counter(c["exposure"] for c in cases)),
        "reference_review": dict(Counter(c["reference"]["status"] for c in cases)),
        "expected_field_states": states, "sampling_families": dict(families),
        "shared_reference_groups": [sorted(ids) for ids in reference_cases.values() if len(ids) > 1],
        "exact_duplicate_source_groups": [group for group in exact_sources.values() if len(group) > 1],
        "coverage_warnings": [
            "Only one case establishes a known priority and one establishes a next-service date; do not infer broad performance from mostly unknown-value cases.",
            "Conflicting equipment IDs and conflicting service dates are not covered in this pilot.",
            "Simulated OCR text is not a live vision evaluation; all field observations are synthetic.",
            "No human-reviewed labels or final holdout are present.",
        ],
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--corpus", type=Path, default=HERE / "corpus/pilot-v1.jsonl")
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    report = quality_report(args.corpus)
    text = json.dumps(report, ensure_ascii=False, indent=2) + "\n"
    if args.output:
        args.output.write_text(text)
    else:
        print(text)
