"""Offline checks for input separation, source execution, and response preservation."""

import asyncio
import copy
import json
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from evals import run_reports as baseline


class BaselineTests(unittest.TestCase):
    def setUp(self):
        self.cases = baseline.load_cases(baseline.HERE / "reference-cases.jsonl")

    def test_reference_changes_cannot_change_inputs(self):
        original = self.cases[0]
        changed = copy.deepcopy(original)
        changed["reference"] = {"answer": "SECRET_REFERENCE_SENTINEL"}
        changed["title"] = "SECRET_TITLE_SENTINEL"
        changed["focus"] = "SECRET_FOCUS_SENTINEL"
        self.assertEqual(
            baseline.source_items(original), baseline.source_items(changed)
        )
        self.assertNotIn("SECRET_", json.dumps(baseline.source_items(changed)))

    def test_revision_and_timing_metadata_reach_model(self):
        text = json.dumps(baseline.source_items(self.cases[4]))
        for expected in ("FL-005-MA", "FL-005-MB", "applies_to_revision", "2026-08-20"):
            self.assertIn(expected, text)

    def test_existing_parser_errors_are_preserved(self):
        code, _ = baseline.extract_function(baseline.DEFAULT_SOURCE)
        requests = []

        async def sender(url, headers, payload):
            requests.append(payload)
            return baseline.response_object(
                200,
                json.dumps({"choices": [{"message": {"content": "```json\n{}\n```"}}]}),
            )

        result = asyncio.run(
            baseline.invoke_function(
                code, baseline.source_items(self.cases[0]), "test-key", sender
            )
        )
        self.assertEqual(requests[0]["model"], "gpt-3.5-turbo")
        self.assertEqual(requests[0]["temperature"], 0.3)
        self.assertIn(
            "parts_used: array of parts that should be used",
            requests[0]["messages"][1]["content"],
        )
        self.assertEqual(result["error"], "Invalid JSON response")
        self.assertEqual(result["raw_content"], "```json\n{}\n```")

    def test_recording_captures_provider_override_without_leaking_key(self):
        response_body = json.dumps(
            {
                "model": "test-model",
                "choices": [
                    {
                        "message": {"content": '{"title":"test output"}'},
                        "finish_reason": "stop",
                    }
                ],
                "usage": {"total_tokens": 12},
            }
        )
        with tempfile.TemporaryDirectory() as directory:
            args = SimpleNamespace(
                cases=baseline.HERE / "reference-cases.jsonl",
                case=["FL-001"],
                source=baseline.DEFAULT_SOURCE,
                prepare=False,
                provider="gemini",
                model="test-model",
                max_tokens=512,
                timeout_seconds=60,
                output=Path(directory) / "run",
                billing_context="OFFLINE TEST: mocked HTTP response",
            )
            with (
                patch.dict("os.environ", {"GEMINI_API_KEY": "SECRET_TEST_CREDENTIAL"}),
                patch.object(
                    baseline,
                    "post_json",
                    return_value=(200, response_body, "test-request"),
                ) as request,
            ):
                asyncio.run(baseline.run(args))
            record = json.loads((args.output / "FL-001.json").read_text())
            self.assertEqual(request.call_args.args[0], baseline.ENDPOINTS["gemini"][0])
            self.assertEqual(request.call_args.args[2], "SECRET_TEST_CREDENTIAL")
            self.assertEqual(record["original_request"]["model"], "gpt-3.5-turbo")
            self.assertEqual(record["sent_request"]["model"], "test-model")
            self.assertEqual(record["response_body"], response_body)
            self.assertEqual(record["function_result"], {"title": "test output"})
            self.assertEqual(record["usage"]["total_tokens"], 12)
            for path in args.output.iterdir():
                self.assertNotIn("SECRET_TEST_CREDENTIAL", path.read_text())


if __name__ == "__main__":
    unittest.main()
