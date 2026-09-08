"""Public-demo isolation, persistence, quota, and provider failure boundaries."""

import asyncio
import importlib.util
import json
import os
import sys
import tempfile
import threading
import time
import unittest
import uuid
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
HAS_APP = all(importlib.util.find_spec(x) for x in ("fasthtml", "monsterui", "fastlite", "aiofiles", "httpx", "PIL"))


@unittest.skipUnless(HAS_APP, "Install the app dependencies")
class HostingTests(unittest.TestCase):
    def setUp(self):
        from starlette.testclient import TestClient
        self.runtime = tempfile.TemporaryDirectory(prefix="frontline-hosting-test-")
        self.env = patch.dict(os.environ, {"FRONTLINE_DEMO": "1", "FRONTLINE_DATA_DIR": self.runtime.name, "GROQ_API_KEY": ""})
        self.env.start()
        self.name = "frontline_hosting_test_" + uuid.uuid4().hex
        spec = importlib.util.spec_from_file_location(self.name, ROOT / "main.py")
        self.app = importlib.util.module_from_spec(spec)
        sys.modules[self.name] = self.app
        spec.loader.exec_module(self.app)
        self.client = TestClient(self.app.app, base_url="https://testserver")
        self.client.__enter__()
        self.client.post("/demo/start")
        self.user = self.app.users()[0]
        self.workspace = self.app.workspaces()[0]
        self.item = self.app.input_items()[0]
        self.report = self.app.maintenance_reports()[0]

    def tearDown(self):
        self.client.__exit__(None, None, None)
        self.app.db.conn.close()
        self.env.stop()
        self.runtime.cleanup()
        sys.modules.pop(self.name, None)

    def test_visitors_cannot_read_or_modify_each_others_data(self):
        from starlette.testclient import TestClient
        with TestClient(self.app.app, base_url="https://testserver") as other:
            other.post("/demo/start")
            for path in (f"/content/view-report/{self.report.id}", f"/content/view-input/{self.item.id}",
                         f"/uploads/text/{self.item.filename}", f"/content/workspace/{self.workspace.id}"):
                self.assertEqual(other.get(path).status_code, 404, path)
            self.assertEqual(other.put("/update-workspace/" + self.workspace.id, data={"name": "stolen"}).status_code, 404)
            self.assertEqual(other.post("/upload", data={"workspace_id": self.workspace.id},
                                        files={"files": ("x.txt", b"wrong owner", "text/plain")}).status_code, 404)
        self.assertEqual(self.app.workspaces[self.workspace.id].name, self.workspace.name)

    def test_workspace_updates_cannot_change_ownership_or_input_ids(self):
        self.client.put("/update-workspace/" + self.workspace.id,
                        data={"name": "Renamed", "user_id": 999, "input_item_ids": '["forged"]'})
        result = self.app.workspaces[self.workspace.id]
        self.assertEqual(result.user_id, self.user.id)
        self.assertEqual(result.input_item_ids, self.workspace.input_item_ids)
        self.assertEqual(result.name, "Renamed")

    def test_upload_limit_preserves_existing_inputs_without_model_calls(self):
        with patch.object(self.app.groq, "_request", side_effect=AssertionError("Upload called AI")):
            response = self.client.post("/upload", data={"workspace_id": self.workspace.id},
                                        files={"files": ("large.txt", b"a" * (4 * 1024 * 1024 + 1), "text/plain")})
        self.assertIn("4 MB", response.text)
        self.assertEqual(len(self.app.input_items()), 1)
        self.assertTrue(Path(self.item.file_path).is_file())
        response = self.client.post("/upload", content=b"x" * (10 * 1024 * 1024))
        self.assertEqual(response.status_code, 413)

    def test_cross_origin_mutation_is_rejected(self):
        response = self.client.delete("/delete-input/" + self.item.id, headers={"Origin": "https://unrelated.example"})
        self.assertEqual(response.status_code, 403)
        self.assertEqual(len(self.app.input_items()), 1)

    def test_expired_cookie_cannot_authenticate_a_reused_user_id(self):
        self.app.users.update({"username": "different-visitor"}, self.user.id)
        response = self.client.get("/content/view-report/" + self.report.id, follow_redirects=False)
        self.assertEqual(response.status_code, 303)
        self.assertIn("Explore the demo", self.client.get("/").text)

    def test_upload_does_not_trust_a_browser_supplied_html_content_type(self):
        self.client.post("/upload", data={"workspace_id": self.workspace.id},
                         files={"files": ("note.txt", b"<script>alert(1)</script>", "text/html")})
        item = next(item for item in self.app.input_items() if item.original_filename == "note.txt")
        response = self.client.get("/uploads/text/" + item.filename)
        self.assertTrue(response.headers["content-type"].startswith("text/plain"))
        self.assertEqual(response.headers["x-content-type-options"], "nosniff")

    def test_generation_preserves_original_sources_after_input_edit(self):
        original = self.item.transcription
        entered, release = threading.Event(), threading.Event()
        result = json.loads(self.report.evidence_json)

        async def generate(items, actor):
            entered.set()
            await asyncio.to_thread(release.wait, 3)
            source_id = json.loads(items[0]["transcription"].split("\n", 1)[0])["id"]
            def replace_ids(value):
                if isinstance(value, dict):
                    if "source_ids" in value:
                        value["source_ids"] = [source_id]
                    for x in value.values():
                        replace_ids(x)
                elif isinstance(value, list):
                    for x in value:
                        replace_ids(x)
            replace_ids(result)
            return result, {"model": "test-model", "usage": {"total_tokens": 100}}

        with patch.object(self.app.groq, "generate", side_effect=generate):
            response = self.client.post("/content/generate-report", data={"workspace_id": self.workspace.id})
            self.assertIn("generation-status", response.text)
            self.assertTrue(entered.wait(2))
            self.client.put("/update-transcription/" + self.item.id, data={"transcription": "Edited after generation began."})
            release.set()
            job = self.app.generations()[0]
            deadline = time.monotonic() + 3
            while self.app.generations[job.id].status in ("queued", "running") and time.monotonic() < deadline:
                time.sleep(0.01)
        job = self.app.generations[job.id]
        self.assertEqual(job.status, "done", job.error)
        report = self.app.maintenance_reports[job.report_id]
        self.assertEqual(json.loads(report.sources_json)[0]["text"], original)
        self.assertEqual(self.app.input_items[self.item.id].transcription, "Edited after generation began.")
        self.assertIn("Sources used for this report", self.client.get("/generation/" + job.id).text)
        self.assertEqual(report.priority, "unknown")

    def test_quota_failure_never_saves_an_error_as_a_report(self):
        from hosting_runtime import LimitReached
        with patch.object(self.app.groq, "generate", side_effect=LimitReached("Demo quota reached")):
            self.client.post("/content/generate-report", data={"workspace_id": self.workspace.id})
            deadline = time.monotonic() + 2
            while self.app.generations()[0].status in ("queued", "running") and time.monotonic() < deadline:
                time.sleep(0.01)
        job = self.app.generations()[0]
        self.assertEqual(job.status, "failed")
        self.assertIn("Demo quota reached", self.client.get("/generation/" + job.id).text)
        self.assertEqual(len(self.app.maintenance_reports()), 1)

    def test_reference_example_retrieves_and_snapshots_guidance_before_generation(self):
        self.client.post("/demo/reference-example")
        workspace = next(w for w in self.app.workspaces() if w.id != self.workspace.id)
        captured = []
        async def generate(items, actor):
            sources = [json.loads(item["transcription"].partition("\n")[0]) for item in items]
            captured.extend(sources)
            note_id = sources[0]["id"]
            reference_id = next(s["id"] for s in sources if s.get("reference_id") == "RP-PI5-FAN")
            unknown = {"state": "unknown", "value": None, "source_ids": [note_id]}
            result = {"equipment_id": {"state": "known", "value": "GW-19", "source_ids": [note_id]},
                      "observations": [{"text": "The fan stayed off during warm-up.", "source_ids": [note_id]},
                                       {"text": "The reference describes the default fan threshold.", "source_ids": [reference_id]}],
                      "completed_work": [], "parts_used": {"state": "unknown", "items": [], "source_ids": [note_id]},
                      "proposed_actions": [], "uncertainties": [], "priority": unknown, "next_service_date": unknown}
            return result, {"model": "offline-fixture", "usage": {}}
        with patch.object(self.app.groq, "generate", side_effect=generate):
            self.client.post("/content/generate-report", data={"workspace_id": workspace.id})
            deadline = time.monotonic() + 2
            while self.app.generations()[0].status in ("queued", "running") and time.monotonic() < deadline:
                time.sleep(.01)
        job = self.app.generations()[0]
        self.assertEqual(job.status, "done", job.error)
        report = self.app.maintenance_reports[job.report_id]
        trace = json.loads(report.retrieval_json)
        self.assertIn("RP-PI5-FAN", trace["selected_ids"])
        self.assertTrue(any(s.get("evidence_role") == "reference" for s in captured))
        page = self.client.get("/content/view-report/" + report.id).text
        self.assertIn("Reference guidance", page)
        self.assertIn("Read the original documentation", page)
        self.assertNotIn("No completed work is established", page)
        self.assertEqual(json.loads(job.retrieval_json)["corpus_sha256"], trace["corpus_sha256"])
        # A model can omit reference-only claims. Preserve its output while exposing the actual retrieved passages.
        report_data = json.loads(report.evidence_json)
        report_data["observations"] = [report_data["observations"][0]]
        self.app.maintenance_reports.update({"evidence_json": json.dumps(report_data)}, report.id)
        page = self.client.get("/content/view-report/" + report.id).text
        self.assertIn("Reference guidance", page)
        self.assertIn("Retrieved passages, shown directly from the saved sources.", page)
        self.assertIn("50 degrees Celsius", page)
        self.assertEqual(json.loads(self.app.maintenance_reports[report.id].evidence_json), report_data)

    def test_expired_demo_removes_only_that_visitors_data(self):
        from starlette.testclient import TestClient
        self.app.users.update({"demo_expires_at": "2000-01-01T00:00:00+00:00"}, self.user.id)
        self.app._last_cleanup = 0
        with TestClient(self.app.app, base_url="https://testserver") as other:
            other.post("/demo/start")
            self.assertEqual(len(self.app.users()), 1)
            self.assertNotEqual(self.app.users()[0].id, self.user.id)
            self.assertEqual(len(self.app.input_items()), 1)
        self.assertFalse(Path(self.item.file_path).exists())

    def test_restart_keeps_secret_and_marks_interrupted_job(self):
        from hosting_runtime import DemoSettings
        from report_workflow import ReportWorkflow
        self.assertEqual(DemoSettings().session_key, self.app.settings.session_key)
        job_id = str(uuid.uuid4())
        self.app.generations.insert({"id": job_id, "user_id": self.user.id, "workspace_id": self.workspace.id,
                                     "created_at": "now", "updated_at": "now", "status": "running",
                                     "report_id": "", "error": "", "sources_json": ""})
        ReportWorkflow(self.app.settings, self.app.budget, self.app.groq, self.app.workspaces,
                       self.app.input_items, self.app.maintenance_reports, self.app.generations)
        self.assertEqual(self.app.generations[job_id].status, "failed")
        self.assertIn("restarted", self.app.generations[job_id].error)


@unittest.skipUnless(HAS_APP, "Install the app dependencies")
class ProviderBoundaryTests(unittest.IsolatedAsyncioTestCase):
    async def test_429_is_persistent_and_does_not_trigger_an_automatic_retry(self):
        import httpx

        from groq_service import GroqService
        from hosting_runtime import Budget, LimitReached
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "usage.sqlite3"
            calls = []
            def handler(request):
                calls.append(request)
                return httpx.Response(429, headers={"retry-after": "30"}, json={"error": {"message": "Quota exhausted"}})
            service = GroqService(Budget(path), "synthetic-test-key", httpx.MockTransport(handler))
            payload = {"messages": [{"role": "user", "content": "test"}], "max_completion_tokens": 10}
            with self.assertRaises(LimitReached):
                await service._request("/chat/completions", 1, payload=payload)
            service.budget = Budget(path)
            with patch("groq_service.asyncio.sleep"), self.assertRaises(LimitReached):
                await service._request("/chat/completions", 1, payload=payload)
            self.assertEqual(len(calls), 1)

    async def test_daily_limit_survives_reopening_database_and_then_expires(self):
        from hosting_runtime import Budget, LimitReached
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "usage.sqlite3"
            for _ in range(3):
                Budget(path).reserve("visitor", "report", now=100000)
            with self.assertRaises(LimitReached):
                Budget(path).reserve("visitor", "report", now=100001)
            Budget(path).reserve("visitor", "report", now=186401)


if __name__ == "__main__":
    unittest.main()
