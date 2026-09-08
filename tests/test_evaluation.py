"""Evaluation integrity tests. Synthetic test labels are not study annotations."""

import copy
import importlib.util
import json
import tempfile
import unittest
from pathlib import Path

from evals.scoring import (
    field_checks,
    judge_alignment,
    latest_human_labels,
    latest_labels,
)

ROOT = Path(__file__).resolve().parents[1]
HAS_APP = all(importlib.util.find_spec(name) for name in ("httpx", "PIL", "starlette", "uvicorn"))


def cases():
    return [json.loads(line) for line in (ROOT / "evals/corpus/pilot-v1.jsonl").read_text().splitlines()]


def reference_output(case):
    result = {key: copy.deepcopy(case["reference"]["fields"][key])
              for key in ("equipment_id", "priority", "next_service_date")}
    part = case["reference"]["fields"]["parts_used"]
    result["parts_used"] = {"state": part["state"], "items": copy.deepcopy(part["value"] or []),
                            "source_ids": part["source_ids"]}
    return result


class EvaluationIntegrityTests(unittest.TestCase):
    def test_failed_generation_remains_visible_and_changes_invalidate_labels(self):
        from evals.trace_data import output_fingerprint, output_text, structural_outcome
        raw = '{"equipment_id":{"state":"known","value":"GW-19","source_ids":["FL-019-N1"]}}'
        record = {"response_body": json.dumps({"error": {"code": "json_validate_failed", "failed_generation": raw}}),
                  "http_status": 400, "structural_status": "provider_error"}
        self.assertEqual(output_text(record), raw)
        self.assertEqual(structural_outcome(record), "provider_schema_rejection")
        original = output_fingerprint(record)
        changed = dict(record, response_body=record["response_body"].replace("GW-19", "GW-99"))
        self.assertNotEqual(original, output_fingerprint(changed))

    def test_explicit_none_normalization_does_not_rewrite_historical_data(self):
        corpus = {c["id"]: c for c in cases()}
        original = {c["id"]: c for c in (json.loads(x) for x in (ROOT / "evals/reference-cases.jsonl").read_text().splitlines())}
        self.assertEqual(len(corpus), 20)
        for name in ("FL-002", "FL-005"):
            self.assertEqual(original[name]["reference"]["fields"]["parts_used"]["state"], "known")
            self.assertEqual(corpus[name]["reference"]["fields"]["parts_used"]["state"], "none")
            self.assertEqual(original[name]["sources"], corpus[name]["sources"])
            self.assertTrue(corpus[name]["reference"]["label_changes"])

    def test_wrong_unit_identity_and_parts_count_are_not_hidden_by_valid_json(self):
        case = cases()[7]
        output = reference_output(case)
        output["equipment_id"]["value"] = "P-19"
        output["parts_used"]["items"][0]["quantity"] = 9
        result = {x["criterion"]: x["status"] for x in field_checks(case, {"raw_output": json.dumps(output)})}
        self.assertEqual(result["equipment_id"], "fail")
        self.assertEqual(result["parts_used"], "fail")

    def test_missing_output_is_unavailable_and_not_a_perfect_empty_report(self):
        self.assertTrue(all(x["status"] == "unavailable" for x in field_checks(cases()[0], {"raw_output": None})))

    def test_boolean_quantity_cannot_equal_integer_one(self):
        case = cases()[0]
        output = reference_output(case)
        output["parts_used"]["items"][0]["quantity"] = True
        result = next(x for x in field_checks(case, {"raw_output": json.dumps(output)}) if x["criterion"] == "parts_used")
        self.assertEqual(result["status"], "fail")

    def test_matching_fields_do_not_create_a_semantic_pass(self):
        case = cases()[1]
        output = reference_output(case)
        output["proposed_actions"] = [{"text": "Replace every component."}]
        checks = field_checks(case, {"raw_output": json.dumps(output)})
        self.assertTrue(all(x["status"] == "pass" for x in checks))
        self.assertNotIn("faithfulness", {x["criterion"] for x in checks})

    def test_reviews_do_not_mix_criteria_versions_or_stale_outputs(self):
        records = {"trace-1": {"output_sha256": "output-a"}}
        base = {"trace_id": "trace-1", "output_sha256": "output-a", "reviewer": "synthetic_human_fixture",
                "reviewer_kind": "human", "criteria_version": "v1", "verdict": "fail", "critique": "Test annotation."}
        newer = dict(base, criteria_version="v2", verdict="pass")
        labels = latest_human_labels([base, newer], records, "v1", "synthetic_human_fixture")
        self.assertEqual(labels["trace-1"]["verdict"], "fail")
        with self.assertRaises(ValueError):
            latest_human_labels([dict(base, output_sha256="changed")], records, "v1", "synthetic_human_fixture")
        self.assertFalse(latest_human_labels([dict(base, reviewer_kind="test")], records, "v1", "synthetic_human_fixture"))

    def test_alignment_reports_both_error_types_and_missing_class(self):
        human = {str(i): {"verdict": label, "output_sha256": str(i), "criteria_version": "v1", "reviewer_kind": "human"}
                 for i, label in enumerate(("fail", "fail", "pass", "pass"))}
        predictions = {key: dict(value, verdict=label) for (key, value), label in
                       zip(human.items(), ("fail", "pass", "fail", "pass"))}
        result = judge_alignment(human, predictions)
        self.assertEqual(result["failure_detection_tpr"], 0.5)
        self.assertEqual(result["pass_acceptance_tnr"], 0.5)
        self.assertEqual(result["false_negative"], 1)
        only_pass = {"2": human["2"]}
        self.assertIsNone(judge_alignment(only_pass, predictions)["failure_detection_tpr"])

    def test_judge_cannot_align_a_different_failure_criterion(self):
        human = {"one": {"verdict": "fail", "output_sha256": "a", "criteria_version": "v1",
                         "criterion": "overall_task_success", "reviewer_kind": "human"}}
        predictions = {"one": dict(human["one"], criterion="incorrect_part")}
        with self.assertRaises(ValueError):
            judge_alignment(human, predictions)

    def test_assistant_judgments_cannot_replace_human_labels(self):
        records = {"trace-1": {"output_sha256": "output-a"}}
        human = {"trace_id": "trace-1", "output_sha256": "output-a", "reviewer": "test-reviewer",
                 "reviewer_kind": "human", "criteria_version": "v1", "verdict": "fail", "critique": "Fixture."}
        assistant = dict(human, reviewer_kind="assistant", verdict="pass")
        labels = latest_human_labels([human, assistant], records, "v1", "test-reviewer")
        self.assertEqual(labels["trace-1"]["verdict"], "fail")
        separate = latest_labels([human, assistant], records, "v1", "test-reviewer", "assistant")
        self.assertEqual(separate["trace-1"]["verdict"], "pass")
        self.assertFalse(latest_human_labels([assistant], records, "v1", "test-reviewer"))
        with self.assertRaises(ValueError):
            latest_labels([dict(assistant, output_sha256="changed")], records, "v1", "test-reviewer", "assistant")

    def test_assistant_and_unattributed_labels_cannot_claim_human_alignment(self):
        label = {"verdict": "pass", "output_sha256": "a", "criteria_version": "v1"}
        for kind in (None, "assistant", "test"):
            with self.subTest(kind=kind), self.assertRaises(ValueError):
                judge_alignment({"one": dict(label, reviewer_kind=kind)}, {"one": label})

    def test_published_assessment_keeps_attribution_and_verifies_source_quotes(self):
        import hashlib
        import shutil

        from evals.render_assessment import load_assessment
        run = ROOT / "evals/published/20260908T160338Z-pilot"
        assessment = ROOT / "evals/assessments/20260908T160338Z-pilot-assistant"
        _, events, _, summary = load_assessment(run, assessment)
        self.assertEqual(summary["human_reviewed_traces"], 0)
        self.assertEqual(summary["assistant_reviewed_traces"], len(events))
        self.assertEqual(summary["semantic_evaluation"], "provisional_assistant_review")
        self.assertTrue(all(e["verdict"] == "fail" for e in events if e["structure"] != "accepted"))
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory)
            manifest = json.loads((assessment / "manifest.json").read_text())
            for name in manifest["artifacts"]:
                shutil.copyfile(assessment / name, target / name)
            changed = copy.deepcopy(events)
            changed[0]["evidence"][0]["quote"] = "THIS QUOTE DOES NOT OCCUR IN THE SOURCE"
            path = target / "reviews.jsonl"
            path.write_text("".join(json.dumps(e) + "\n" for e in changed))
            # Even a newly fingerprinted assessment must prove its source quotes.
            manifest["artifacts"]["reviews.jsonl"] = hashlib.sha256(path.read_bytes()).hexdigest()
            (target / "manifest.json").write_text(json.dumps(manifest))
            with self.assertRaisesRegex(ValueError, "quote does not occur"):
                load_assessment(run, target)

    def test_export_describes_single_variant_and_paired_runs_accurately(self):
        from evals.export_run import export_run
        for variant in ("both", "deployed"):
            with self.subTest(variant=variant), tempfile.TemporaryDirectory() as directory:
                root = Path(directory)
                source, destination = root / "source" / "run", root / "destination" / "run"
                source.mkdir(parents=True)
                manifest = {"status": "finished", "planned_requests": 1, "completed": ["trace-a"], "selected_variant": variant}
                (source / "manifest.json").write_text(json.dumps(manifest))
                (source / "prepared-requests.json").write_text("[]")
                (source / "review-order.json").write_text('["trace-a"]')
                (source / "trace-a.json").write_text('{"structural_status":"rejected"}')
                self.assertEqual(export_run(source, destination), 1)
                description = (destination / "README.md").read_text()
                self.assertEqual("two variants" in description, variant == "both")
                self.assertEqual("one instruction variant" in description, variant != "both")
                self.assertTrue((destination / "trace-a.json").exists())


@unittest.skipUnless(HAS_APP, "Install application dependencies for request/review checks")
class PilotRequestTests(unittest.TestCase):
    def test_reference_answers_and_sampling_metadata_never_enter_requests(self):
        from evals.pilot import prepare_requests
        original = cases()[0]
        changed = copy.deepcopy(original)
        changed["reference"] = {"secret": "HIDDEN_REFERENCE_SENTINEL"}
        changed["title"] = changed["family"] = "HIDDEN_METADATA_SENTINEL"
        first = prepare_requests([original])
        second = prepare_requests([changed])
        self.assertEqual([x["request"] for x in first], [x["request"] for x in second])
        self.assertNotIn("HIDDEN_", json.dumps([x["request"] for x in second]))

    def test_paired_requests_differ_only_in_system_instruction(self):
        from evals.pilot import prepare_requests
        requests = prepare_requests(cases())
        self.assertEqual(len(requests), 40)
        for left, right in zip(requests[::2], requests[1::2]):
            a, b = copy.deepcopy(left["request"]), copy.deepcopy(right["request"])
            self.assertNotEqual(a["messages"][0]["content"], b["messages"][0]["content"])
            a["messages"][0]["content"] = b["messages"][0]["content"]
            self.assertEqual(a, b)


@unittest.skipUnless(HAS_APP, "Install application dependencies for review checks")
class ReviewJournalTests(unittest.TestCase):
    def setUp(self):
        from starlette.testclient import TestClient

        from evals.review_app import make_app
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        (self.root / "manifest.json").write_text(json.dumps({"artifacts": {"evals/corpus/pilot-v1.jsonl": "test-dataset"}}))
        (self.root / "review-order.json").write_text('["trace-a"]')
        from evals.trace_data import output_fingerprint
        record = {"trace_id": "trace-a", "raw_output": "{}", "input_sources": [], "structural_status": "accepted"}
        record["output_sha256"] = output_fingerprint(record)
        (self.root / "trace-a.json").write_text(json.dumps(record))
        self.journal = self.root / "journal.jsonl"
        self.client = TestClient(make_app(self.root, self.journal, test_mode=True))
        self.data = {"trace_id": "trace-a", "output_sha256": record["output_sha256"],
                     "reviewer": "UI test", "criteria_version": "v1", "verdict": "fail", "critique": "Synthetic test."}

    def tearDown(self):
        self.client.close()
        self.temp.cleanup()

    def test_saves_are_append_only_and_test_annotations_never_count_as_human(self):
        self.assertEqual(self.client.post("/label", json=self.data).status_code, 200)
        self.assertEqual(self.client.post("/label", json=dict(self.data, verdict="pass")).status_code, 200)
        self.assertEqual(len(self.journal.read_text().splitlines()), 2)
        info = self.client.get("/items?criteria_version=v1&reviewer=UI%20test").json()
        self.assertEqual(info["human_reviewed"], 0)
        self.assertEqual(info["labels"]["trace-a"]["verdict"], "pass")
        self.assertFalse(self.client.get("/items?criteria_version=v2").json()["labels"])

    def test_one_reviewers_labels_do_not_prefill_another_reviewers_form(self):
        self.client.post("/label", json=self.data)
        self.assertFalse(self.client.get("/items?criteria_version=v1&reviewer=Someone%20else").json()["labels"])
        self.assertFalse(self.client.get("/items?criteria_version=v1").json()["labels"])

    def test_unknown_or_changed_trace_and_cross_origin_writes_are_rejected(self):
        for update in ({"trace_id": "../manifest"}, {"output_sha256": "stale"}, {"critique": ""}):
            self.assertEqual(self.client.post("/label", json=dict(self.data, **update)).status_code, 400)
        self.assertEqual(self.client.post("/label", json=self.data, headers={"Origin": "https://elsewhere.example"}).status_code, 403)
        self.assertFalse(self.journal.exists())

    def test_review_manifest_cannot_select_files_outside_the_run(self):
        from evals.review_app import make_app
        (self.root / "review-order.json").write_text('["../private"]')
        with self.assertRaises(ValueError):
            make_app(self.root, self.journal)

    def test_read_only_assessment_never_creates_human_judgments(self):
        from starlette.testclient import TestClient

        from evals.review_app import make_app
        assessment = self.root / "assessment"
        assessment.mkdir()
        (assessment / "manifest.json").write_text(json.dumps({"run_id": self.root.name}))
        (assessment / "report.html").write_text("<p>Assistant assessment fixture</p>")
        self.assertEqual(self.client.get("/assessment").status_code, 404)
        with TestClient(make_app(self.root, self.journal, assessment=assessment)) as client:
            self.assertIn("Assistant assessment fixture", client.get("/assessment").text)
            self.assertEqual(client.get("/items").json()["assistant_assessment_url"], "/assessment")
            self.assertEqual(client.get("/items").json()["human_reviewed"], 0)
            self.assertFalse(self.journal.exists())
        (assessment / "manifest.json").write_text('{"run_id":"another-run"}')
        with self.assertRaisesRegex(ValueError, "another run"):
            make_app(self.root, self.journal, assessment=assessment)


if __name__ == "__main__":
    unittest.main()
