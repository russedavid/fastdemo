"""Offline development comparison of reference rankers and applicability filters."""

import argparse
import hashlib
import json
import platform
import sqlite3
import tempfile
import time
from datetime import datetime, timezone
from pathlib import Path

from retrieval import ReferenceIndex, digest, load_references

ROOT = Path(__file__).resolve().parents[1]


def fixtures():
    base = {"models": ["fixture-controller"], "revision": None, "status": "current", "owner_id": None,
            "version": "fictional-v1", "license": "CC0-1.0", "attribution": "Synthetic evaluation fixture by the project assistant",
            "url": "https://example.invalid/fixture", "section": "Synthetic test only", "sha256": "synthetic", "keywords": ""}
    return [
        dict(base, id="FIXTURE-A", title="E14 diagnostic review", revision="A", text="E14 fan failure: replace the fan.", uploaded_at="2026-09-08"),
        dict(base, id="FIXTURE-B", title="E14 diagnostic review", revision="B", text="E14 clock synchronization warning: request diagnostic review.", uploaded_at="2026-08-01"),
        dict(base, id="FIXTURE-PRIVATE", title="Internal caliper calibration recipe", owner_id="alice", text="Caliper calibration recipe for Alice's test workspace."),
        dict(base, id="FIXTURE-REVOKED", title="Tachometer diagnostic Z73", status="revoked", text="Tachometer diagnostic Z73. This fictional guidance was revoked."),
    ]


def run(output):
    output = Path(output)
    output.mkdir(parents=True, exist_ok=False)
    case_path = ROOT / "evals/retrieval-cases.jsonl"
    cases = [json.loads(line) for line in case_path.read_text().splitlines() if line.strip()]
    documents = load_references() + fixtures()
    originals = {d["id"]: d for d in documents}
    for case in cases:
        if not set(case["expected_ids"]) <= set(originals):
            raise ValueError("Unknown relevance label")
    (output / "cases.jsonl.snapshot").write_bytes(case_path.read_bytes())
    (output / "documents.json").write_text(json.dumps(documents, indent=2) + "\n")
    for name in ("retrieval.py", "evals/check_retrieval.py"):
        (output / (Path(name).name + ".snapshot")).write_bytes((ROOT / name).read_bytes())
    rows = []
    with tempfile.TemporaryDirectory() as directory:
        index = ReferenceIndex(Path(directory) / "normal.sqlite3", documents)
        # Offline ablation only. Access and revocation filtering remain enforced.
        ablated = ReferenceIndex(Path(directory) / "ablated.sqlite3", [dict(d, models=["any"], revision=None) for d in documents])
        for method in ("overlap", "bm25", "bm25_without_applicability"):
            for case in cases:
                started = time.perf_counter()
                result = (ablated if method.endswith("without_applicability") else index).search(
                    case["query"], model="any" if method.endswith("without_applicability") else case["model"],
                    revision=case.get("revision"), actor=case.get("actor"), limit=2,
                    method="overlap" if method == "overlap" else "bm25")
                elapsed = (time.perf_counter() - started) * 1000
                ids = [d["id"] for d in result]
                relevant = set(case["expected_ids"])
                hits = len(set(ids) & relevant)
                rows.append({"case_id": case["id"], "method": method, "returned_ids": ids,
                             "scores": [d["retrieval_score"] for d in result], "expected_ids": sorted(relevant),
                             "recall_at_2": hits / len(relevant) if relevant else None,
                             "precision_at_2": hits / len(ids) if ids else 0 if relevant else None,
                             "top_1_relevant": bool(ids and ids[0] in relevant) if relevant else None,
                             "correct_abstention": not ids if not relevant else None,
                             "wrong_applicability": [id for id in ids if case["model"] not in originals[id]["models"]
                                                       or originals[id].get("revision") not in (None, case.get("revision"))],
                             "access_or_revocation_violation": [id for id in ids if originals[id]["status"] != "current"
                                                                 or originals[id].get("owner_id") not in (None, case.get("actor"))],
                             "elapsed_ms": round(elapsed, 4)})
    metrics = {}
    for method in sorted({r["method"] for r in rows}):
        selected = [r for r in rows if r["method"] == method]
        answerable = [r for r in selected if r["expected_ids"]]
        unavailable = [r for r in selected if not r["expected_ids"]]
        metrics[method] = {
            "answerable_cases": len(answerable), "unavailable_cases": len(unavailable),
            "macro_recall_at_2": sum(r["recall_at_2"] for r in answerable) / len(answerable),
            "macro_precision_at_2_answerable": sum(r["precision_at_2"] for r in answerable) / len(answerable),
            "top_1_relevant_cases": sum(r["top_1_relevant"] for r in answerable),
            "correct_abstentions": sum(r["correct_abstention"] for r in unavailable),
            "wrong_applicability_passages": sum(len(r["wrong_applicability"]) for r in selected),
            "access_or_revocation_violations": sum(len(r["access_or_revocation_violation"]) for r in selected),
            "median_query_ms": sorted(r["elapsed_ms"] for r in selected)[len(selected) // 2],
        }
    manifest = {"started_at": datetime.now(timezone.utc).isoformat(), "cases": len(cases), "methods": len(metrics),
                "corpus_sha256": digest(documents), "case_sha256": hashlib.sha256(case_path.read_bytes()).hexdigest(),
                "python": platform.python_version(), "sqlite": sqlite3.sqlite_version,
                "label_status": "Assistant-authored development relevance labels; no held-out or human-validation claim",
                "scope": "Ranker, model/revision eligibility, and access filtering. Context detection and generation are tested separately.",
                "timing_scope": "One local query per case/method after index construction; not production latency or a load test."}
    (output / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    (output / "results.json").write_text(json.dumps({"metrics": metrics, "cases": rows}, indent=2) + "\n")
    print(json.dumps({"output": str(output), "metrics": metrics}, indent=2))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    run(parser.parse_args().output)
