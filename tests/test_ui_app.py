"""App-stack regressions, using a temporary database and no model calls."""

import importlib.util
import os
import sys
import tempfile
import unittest
import uuid
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
APP_DEPS = ("fasthtml", "monsterui", "fastlite", "aiofiles", "httpx", "PIL")


@unittest.skipUnless(
    all(importlib.util.find_spec(name) for name in APP_DEPS),
    "Install the app dependencies to run UI/backend smoke checks",
)
class AppSmokeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.runtime = tempfile.TemporaryDirectory(prefix="frontline-ui-test-")
        previous = Path.cwd()
        try:
            os.chdir(cls.runtime.name)
            spec = importlib.util.spec_from_file_location(
                "frontline_test_app", ROOT / "main.py"
            )
            cls.module = importlib.util.module_from_spec(spec)
            sys.modules[spec.name] = cls.module
            spec.loader.exec_module(cls.module)
        finally:
            os.chdir(previous)

    @classmethod
    def tearDownClass(cls):
        cls.module.db.conn.close()
        cls.runtime.cleanup()
        sys.modules.pop("frontline_test_app", None)

    def setUp(self):
        from starlette.testclient import TestClient

        self.previous = Path.cwd()
        os.chdir(self.runtime.name)
        self.client = TestClient(self.module.app)
        self.client.__enter__()
        self.username = "test-" + uuid.uuid4().hex[:10]

    def tearDown(self):
        self.client.__exit__(None, None, None)
        os.chdir(self.previous)

    def register(self):
        response = self.client.post(
            "/register-user",
            data={
                "username": self.username,
                "email": self.username + "@example.invalid",
                "password": "test-password",
            },
            headers={"HX-Request": "true"},
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn("Registration successful", response.text)
        return self.module.users(where=f"username = '{self.username}'")[0]

    def test_registration_and_login_store_a_serializable_user_id(self):
        user = self.register()
        self.assertIsInstance(user.id, int)
        self.assertIn(self.username, self.client.get("/").text)
        self.client.get("/logout")
        response = self.client.post(
            "/send_login", data={"username": self.username, "password": "test-password"}
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn(self.username, response.text)

    def test_workspace_upload_edit_and_removal_roundtrip(self):
        user = self.register()
        headers = {"HX-Request": "true"}
        self.client.get("/content/workspace", headers=headers)
        workspace = self.module.workspaces(where=f"user_id = {user.id}")[0]
        self.client.put(
            "/update-workspace/" + workspace.id,
            data={"name": "Inspection workspace"},
            headers=headers,
        )
        self.assertEqual(
            self.module.workspaces[workspace.id].name, "Inspection workspace"
        )
        response = self.client.post(
            "/upload",
            data={"workspace_id": workspace.id},
            files={
                "files": ("note.txt", b"Filter replaced; seal unchanged.", "text/plain")
            },
            headers=headers,
        )
        self.assertEqual(response.status_code, 200)
        item = self.module.input_items(where=f"user_id = {user.id}")[0]
        response = self.client.put(
            "/update-transcription/" + item.id,
            data={"transcription": "Updated inspection note."},
            headers=headers,
        )
        self.assertEqual(
            self.module.input_items[item.id].transcription, "Updated inspection note."
        )
        self.assertIn("input-item-article", response.text)
        self.assertIn('hx-swap-oob="true"', response.text)
        response = self.client.delete(
            f"/remove-from-workspace/{workspace.id}/{item.id}",
            headers=headers,
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(self.module.workspaces[workspace.id].input_item_ids, "[]")

    def test_page_loads_one_htmx4_runtime_and_local_ui_script(self):
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.text.count('src="https://cdn.jsdelivr.net/npm/htmx.org@4.0.0/'), 1
        )
        self.assertNotIn("htmx.org@2.", response.text)
        self.assertIn('data-theme="light"', response.text)
        self.assertIn('src="/static/app.js"', response.text)
        self.assertEqual(self.client.get("/static/app.js").status_code, 200)


if __name__ == "__main__":
    unittest.main()
