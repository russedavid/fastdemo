"""Meaningful boundary checks; these are not model-quality measurements."""

import asyncio
import copy
import io
import json
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

import reporting
from evals import run_reports


def sample_report():
    def value(state="unknown", data=None):
        return {"state": state, "value": data, "source_ids": ["SOURCE-A"]}

    return {
        "equipment_id": value("known", "UNIT-TEST"),
        "observations": [
            {"text": "A status light blinked.", "source_ids": ["SOURCE-A"]}
        ],
        "completed_work": [],
        "parts_used": {"state": "unknown", "items": [], "source_ids": ["SOURCE-A"]},
        "proposed_actions": [],
        "uncertainties": [],
        "priority": value(),
        "next_service_date": value(),
    }


class ReportingTests(unittest.TestCase):
    def parse(self, report):
        return reporting.parse_report(
            json.dumps(report),
            {
                "SOURCE-A": "UNIT-TEST. A status light blinked. PART-TEST is mentioned.",
                "SOURCE-B": "A second account concerning UNIT-TEST.",
            },
        )

    def test_none_and_unknown_remain_distinct(self):
        unknown = sample_report()
        none = copy.deepcopy(unknown)
        none["parts_used"]["state"] = "none"
        self.assertEqual(self.parse(unknown)["parts_used"]["state"], "unknown")
        self.assertEqual(self.parse(none)["parts_used"]["state"], "none")

    def test_unknown_scalar_cannot_contain_a_guess(self):
        report = sample_report()
        report["priority"]["value"] = "medium"
        with self.assertRaises(ValueError):
            self.parse(report)

    def test_disputed_parts_cannot_be_reported_as_used(self):
        report = sample_report()
        report["parts_used"]["state"] = "conflicting"
        report["parts_used"]["items"] = [
            {"part_number": "PART-TEST", "quantity": 1, "source_ids": ["SOURCE-A"]}
        ]
        report["uncertainties"] = [
            {
                "field": "parts_used",
                "text": "The accounts disagree.",
                "source_ids": ["SOURCE-A", "SOURCE-B"],
            }
        ]
        with self.assertRaises(ValueError):
            self.parse(report)

    def test_conflicting_state_requires_a_visible_explanation(self):
        report = sample_report()
        report["parts_used"]["state"] = "conflicting"
        with self.assertRaises(ValueError):
            self.parse(report)
        report["uncertainties"] = [
            {
                "field": "parts_used",
                "text": "A reports installation; B reports no installation.",
                "source_ids": ["SOURCE-A", "SOURCE-B"],
            }
        ]
        self.assertEqual(self.parse(report)["parts_used"]["state"], "conflicting")

    def test_nonexistent_citation_is_rejected(self):
        report = sample_report()
        report["observations"][0]["source_ids"] = ["SOURCE-OUTSIDE-PACKET"]
        with self.assertRaises(ValueError):
            self.parse(report)

    def test_quantity_cannot_be_a_boolean_or_invented_zero(self):
        for quantity in (True, 0, "1"):
            report = sample_report()
            report["parts_used"]["state"] = "known"
            report["parts_used"]["items"] = [
                {
                    "part_number": "PART-TEST",
                    "quantity": quantity,
                    "source_ids": ["SOURCE-A"],
                }
            ]
            with self.subTest(quantity=quantity), self.assertRaises(ValueError):
                self.parse(report)

    def test_unknown_quantity_is_not_silently_filled(self):
        report = sample_report()
        report["parts_used"]["state"] = "known"
        report["parts_used"]["items"] = [
            {"part_number": "PART-TEST", "quantity": None, "source_ids": ["SOURCE-A"]}
        ]
        self.assertIsNone(self.parse(report)["parts_used"]["items"][0]["quantity"])

    def test_no_fence_stripping_or_extra_fields(self):
        report = sample_report()
        with self.assertRaises(ValueError):
            reporting.parse_report(
                "```json\n" + json.dumps(report) + "\n```", {"SOURCE-A": "UNIT-TEST"}
            )
        report["unreviewed_override"] = True
        with self.assertRaises(ValueError):
            self.parse(report)

    def test_structure_does_not_establish_entailment(self):
        report = sample_report()
        report["observations"][0]["text"] = (
            "An unsupported claim with a valid citation ID."
        )
        self.assertEqual(
            self.parse(report)["observations"][0]["text"],
            report["observations"][0]["text"],
        )

    def test_references_do_not_change_candidate_requests(self):
        case = run_reports.load_cases(run_reports.HERE / "reference-cases.jsonl")[0]
        changed = copy.deepcopy(case)
        changed["reference"] = {"leak": "HIDDEN_REFERENCE_SENTINEL"}
        changed["title"] = "HIDDEN_TITLE_SENTINEL"
        a = reporting.build_request(run_reports.source_items(case), "test-model")
        b = reporting.build_request(run_reports.source_items(changed), "test-model")
        self.assertEqual(a, b)
        self.assertNotIn("HIDDEN_", json.dumps(b))
        self.assertEqual(a["response_format"]["type"], "json_schema")
        self.assertEqual(a["temperature"], 0.3)

    def run_mock_candidate(self, directory, response=None, error=None):
        def open_metadata(url, **kwargs):
            data = (
                {"models": [{"name": "test-model"}]}
                if url.endswith("/api/tags")
                else {"version": "test-runtime"}
            )
            return io.BytesIO(json.dumps(data).encode())

        args = SimpleNamespace(
            cases=run_reports.HERE / "reference-cases.jsonl",
            case=["FL-001"],
            source=run_reports.DEFAULT_SOURCE,
            prepare=False,
            candidate=True,
            provider="ollama",
            model="test-model",
            max_tokens=4096,
            timeout_seconds=180,
            output=Path(directory) / "run",
            billing_context="Offline unit test with mocked HTTP",
        )
        with (
            patch.object(
                run_reports.urllib.request,
                "build_opener",
                return_value=SimpleNamespace(open=open_metadata),
            ),
            patch.object(
                run_reports, "post_json", return_value=response, side_effect=error
            ),
        ):
            asyncio.run(run_reports.run(args))
        return args.output

    def test_candidate_records_actual_request_and_validated_response(self):
        report = json.loads(
            json.dumps(sample_report()).replace("SOURCE-A", "FL-001-N1")
        )
        report["equipment_id"]["value"] = "P-17"
        body = json.dumps(
            {
                "model": "test-model",
                "choices": [
                    {
                        "message": {"content": json.dumps(report)},
                        "finish_reason": "stop",
                    }
                ],
                "usage": {"total_tokens": 7},
            }
        )
        with tempfile.TemporaryDirectory() as directory:
            output = self.run_mock_candidate(directory, response=(200, body, None))
            record = json.loads((output / "FL-001.json").read_text())
            self.assertEqual(record["status"], "returned")
            self.assertEqual(record["function_result"], report)
            self.assertEqual(record["validation"]["status"], "accepted")
            self.assertEqual(
                record["sent_request"]["response_format"]["type"], "json_schema"
            )
            self.assertEqual(record["response_body"], body)
            self.assertTrue((output / "report-instructions.txt.snapshot").is_file())

    def test_candidate_timeout_is_saved_and_stops_the_batch(self):
        with tempfile.TemporaryDirectory() as directory:
            output = self.run_mock_candidate(
                directory, error=TimeoutError("Simulated timeout")
            )
            record = json.loads((output / "FL-001.json").read_text())
            manifest = json.loads((output / "manifest.json").read_text())
            self.assertEqual(record["transport_error_type"], "TimeoutError")
            self.assertEqual(record["status"], "execution_error")
            self.assertEqual(
                manifest["status"], "stopped_after_provider_or_transport_error"
            )
            self.assertEqual(manifest["model_calls_attempted"], 1)

    def test_identifier_cannot_include_added_description(self):
        report = sample_report()
        report["equipment_id"]["value"] = "UNIT-TEST (controller revision B)"
        with self.assertRaisesRegex(ValueError, "verbatim"):
            self.parse(report)

    def test_prior_run_identifier_regression_is_detected_without_repair(self):
        root = run_reports.HERE
        case = next(
            c
            for c in run_reports.load_cases(root / "reference-cases.jsonl")
            if c["id"] == "FL-005"
        )
        content = (
            Path(__file__).parent / "fixtures/identifier-regression.json"
        ).read_text()
        with self.assertRaisesRegex(ValueError, "verbatim"):
            reporting.parse_report(
                content,
                reporting.source_texts_from_items(run_reports.source_items(case)),
            )


if __name__ == "__main__":
    unittest.main()
