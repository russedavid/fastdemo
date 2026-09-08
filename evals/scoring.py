"""Objective checks and separately attributed human/assistant review summaries.

No string-similarity score or uncalibrated model judge stands in for source support.
"""

import argparse
import json
from collections import Counter, defaultdict
from pathlib import Path

from evals.trace_data import output_fingerprint, output_text, structural_outcome


def canonical(value):
    return json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(",", ":"))


def output_object(record):
    try:
        value = json.loads(output_text(record) or "")
        return value if isinstance(value, dict) else None
    except (ValueError, TypeError):
        return None


def field_checks(case, record):
    """Compare values to explicit provisional references; do not grade prose."""
    report = output_object(record)
    checks = []
    for name in ("equipment_id", "priority", "next_service_date", "parts_used"):
        expected = case["reference"]["fields"][name]
        actual = report.get(name) if report else None
        if not isinstance(actual, dict):
            checks.append({"criterion": name, "status": "unavailable", "expected": expected, "actual": actual})
            continue
        if name == "parts_used":
            expected_value = {"state": expected["state"], "items": expected["value"] or []}
            actual_value = {"state": actual.get("state"), "items": actual.get("items")}
            if isinstance(actual_value["items"], list):
                actual_value["items"] = sorted(
                    [{k: p.get(k) for k in ("part_number", "quantity")} if isinstance(p, dict) else p
                     for p in actual_value["items"]], key=canonical)
                expected_value["items"] = sorted(expected_value["items"], key=canonical)
        else:
            expected_value = {k: expected[k] for k in ("state", "value")}
            actual_value = {k: actual.get(k) for k in ("state", "value")}
        checks.append({
            "criterion": name,
            "status": "pass" if canonical(expected_value) == canonical(actual_value) else "fail",
            "expected": expected_value, "actual": actual_value,
        })
    return checks


def latest_labels(events, records, criteria_version, reviewer, reviewer_kind="human"):
    """Never combine reviewer kinds, rubric versions, or changed outputs."""
    if reviewer_kind not in ("human", "assistant"):
        raise ValueError("Select human or assistant review explicitly")
    result = {}
    for event in events:
        if (event.get("reviewer_kind") != reviewer_kind or event.get("reviewer") != reviewer
                or event.get("criteria_version") != criteria_version
                or event.get("criterion", "overall_task_success") != "overall_task_success"):
            continue
        trace_id = event["trace_id"]
        record = records.get(trace_id)
        if not record or event.get("output_sha256") != output_fingerprint(record):
            raise ValueError("A review does not match its immutable output: " + trace_id)
        if event.get("source_sha256") and event["source_sha256"] != record.get("source_sha256"):
            raise ValueError("A review does not match its input sources: " + trace_id)
        if event.get("verdict") not in ("pass", "fail") or not event.get("critique", "").strip():
            raise ValueError("Review judgments require Pass/Fail and a critique")
        result[trace_id] = event
    return result


def latest_human_labels(events, records, criteria_version, reviewer):
    return latest_labels(events, records, criteria_version, reviewer, "human")


def judge_alignment(human_labels, predictions):
    """Failure is the positive class. Missing a class makes its rate undefined."""
    confusion = {"true_positive": 0, "true_negative": 0, "false_positive": 0, "false_negative": 0}
    missing = 0
    for trace_id, human in human_labels.items():
        if human.get("reviewer_kind") != "human":
            raise ValueError("Human alignment requires explicitly human reference labels")
        prediction = predictions.get(trace_id)
        if prediction is None:
            missing += 1
            continue
        if prediction.get("output_sha256") != human["output_sha256"] or prediction.get("criteria_version") != human["criteria_version"]:
            raise ValueError("Judge prediction and human label use different outputs or criteria")
        if prediction.get("criterion", "overall_task_success") != human.get("criterion", "overall_task_success"):
            raise ValueError("A failure-specific judge cannot be calibrated against an overall outcome label")
        if prediction.get("verdict") not in ("pass", "fail"):
            raise ValueError("Judge predictions must be binary")
        positive, predicted = human["verdict"] == "fail", prediction["verdict"] == "fail"
        key = ("true_positive" if predicted else "false_negative") if positive else ("false_positive" if predicted else "true_negative")
        confusion[key] += 1
    tp, tn, fp, fn = [confusion[k] for k in ("true_positive", "true_negative", "false_positive", "false_negative")]
    return {
        **confusion, "missing_predictions": missing,
        "failure_detection_tpr": tp / (tp + fn) if tp + fn else None,
        "pass_acceptance_tnr": tn / (tn + fp) if tn + fp else None,
        "interpretation": "Agreement on these labeled examples only; no calibrated judge is implied by the existence of this function.",
    }


def summarize(run_dir, *, events=(), criteria_version=None, reviewer=None, reviewer_kind="human"):
    if reviewer_kind not in ("human", "assistant"):
        raise ValueError("Select human or assistant review explicitly")
    run_dir = Path(run_dir)
    cases = {c["id"]: c for c in
             (json.loads(line) for line in (run_dir / "pilot-v1.jsonl.snapshot").read_text().splitlines() if line.strip())}
    manifest = json.loads((run_dir / "manifest.json").read_text())
    records = {record["trace_id"]: record for record in
               (json.loads((run_dir / (trace_id + ".json")).read_text()) for trace_id in manifest["completed"])}
    if any(event.get("run_id") != run_dir.name or
           event.get("dataset_sha256") != manifest["artifacts"]["evals/corpus/pilot-v1.jsonl"]
           for event in events):
        raise ValueError("Review journal belongs to a different run or dataset")
    labels = latest_labels(events, records, criteria_version, reviewer, reviewer_kind) if criteria_version and reviewer else {}
    variants = defaultdict(lambda: {"traces": 0, "structure": Counter(), "fields": defaultdict(Counter),
                                     "fields_by_expected_state": defaultdict(lambda: defaultdict(Counter)),
                                     "human": Counter(), "assistant": Counter(), "latencies": [], "tokens_reported": 0,
                                     "traces_with_usage": 0, "traces_missing_usage": 0})
    for trace_id, record in records.items():
        variant = variants[record["variant"]]
        variant["traces"] += 1
        variant["structure"][structural_outcome(record)] += 1
        for check in field_checks(cases[record["case_id"]], record):
            variant["fields"][check["criterion"]][check["status"]] += 1
            state = cases[record["case_id"]]["reference"]["fields"][check["criterion"]]["state"]
            variant["fields_by_expected_state"][check["criterion"]][state][check["status"]] += 1
        for kind in ("human", "assistant"):
            verdict = labels[trace_id]["verdict"] if kind == reviewer_kind and trace_id in labels else "unreviewed"
            variant[kind][verdict] += 1
        if "elapsed_seconds" in record:
            variant["latencies"].append(record["elapsed_seconds"])
        if "total_tokens" in record.get("usage", {}):
            variant["tokens_reported"] += record["usage"]["total_tokens"]
            variant["traces_with_usage"] += 1
        else:
            variant["traces_missing_usage"] += 1
    return {
        "run": run_dir.name, "planned_requests": manifest["planned_requests"],
        "completed_requests": len(records), "status": manifest["status"],
        "reference_status": "Provisional AI-authored expectations, not human gold labels",
        "semantic_evaluation": (
            ("provisional_assistant_review" if len(labels) == len(records) else "partial_assistant_review")
            if labels and reviewer_kind == "assistant" else
            "reviewed_recorded_traces" if labels and len(labels) == len(records)
            else "partial_human_review" if labels else "pending_" + reviewer_kind + "_review"),
        "human_reviewed_traces": len(labels) if reviewer_kind == "human" else 0,
        "assistant_reviewed_traces": len(labels) if reviewer_kind == "assistant" else 0,
        "criteria_version": criteria_version, "reviewer": reviewer, "reviewer_kind": reviewer_kind,
        "variants": dict(variants),
        "limitation": "Field checks do not establish prose quality. Assistant judgments are provisional and do not establish human alignment or production accuracy. Reviewer kinds remain separate; no combined quality score is calculated.",
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run", type=Path, required=True)
    parser.add_argument("--reviews", type=Path)
    parser.add_argument("--criteria-version")
    parser.add_argument("--reviewer")
    parser.add_argument("--reviewer-kind", choices=("human", "assistant"), default="human")
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    if args.reviews and not (args.reviewer and args.criteria_version):
        parser.error("--reviews requires --reviewer and --criteria-version")
    events = ([json.loads(x) for x in args.reviews.read_text().splitlines() if x.strip()]
              if args.reviews else [])
    result = summarize(args.run, events=events, criteria_version=args.criteria_version,
                       reviewer=args.reviewer, reviewer_kind=args.reviewer_kind)
    text = json.dumps(result, indent=2) + "\n"
    if args.output:
        args.output.write_text(text)
    else:
        print(text)
