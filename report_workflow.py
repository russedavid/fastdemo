"""Bounded report jobs with immutable source snapshots and persistent results."""

import asyncio
import json
from datetime import datetime, timezone
from uuid import uuid4

from fasthtml.common import Div, P
from monsterui.all import H2, Button, ButtonT

from groq_service import ProviderUnavailable
from hosting_runtime import LimitReached
from report_views import evidence_report_view


def timestamp():
    return datetime.now(timezone.utc).isoformat()


class ReportWorkflow:
    def __init__(self, settings, budget, provider, workspaces, items, reports, jobs):
        self.settings, self.budget, self.provider = settings, budget, provider
        self.workspaces, self.items, self.reports, self.jobs = workspaces, items, reports, jobs
        self.tasks = {}
        self.lock = asyncio.Lock()
        for job in self.jobs(where="status IN ('queued','running')"):
            self.jobs.update({"status": "failed", "error": "The app restarted during generation. Your inputs are saved; please try again.",
                              "updated_at": timestamp()}, job.id)

    def get_workspace(self, workspace_id, user_id):
        try:
            workspace = self.workspaces[workspace_id]
        except Exception as error:
            raise KeyError("Workspace not found") from error
        if workspace.user_id != user_id:
            raise KeyError("Workspace not found")
        return workspace

    def source_records(self, workspace):
        records = []
        for item_id in json.loads(workspace.input_item_ids or "[]"):
            item = self.items[item_id]
            if item.user_id != workspace.user_id:
                raise KeyError("Input not found")
            records.append({"id": item.id, "type": item.file_type,
                            "filename": item.original_filename, "text": item.transcription,
                            "origin": item.text_origin, "uploaded_at": item.uploaded_at,
                            "path": item.file_path})
        if not records:
            raise ValueError("Add a note, recording, or image first.")
        if len(records) > 8:
            raise ValueError("Use at most eight inputs in a report.")
        if sum(len(s["text"]) for s in records) > self.settings.max_source_chars:
            raise ValueError("These notes are too long for the demo. Use at most 9,000 characters per report.")
        return records

    async def prepare_source(self, record, user_id):
        if not record["text"].strip():
            if record["type"] == "audio":
                record["text"] = await self.provider.transcribe(record["path"], user_id)
                record["origin"] = "groq_audio"
            elif record["type"] == "image":
                record["text"] = await self.provider.describe(record["path"], user_id)
                record["origin"] = "groq_image"
            else:
                raise ValueError("One of the notes is empty. Edit or remove it first.")
            self.items.update({"transcription": record["text"], "text_origin": record["origin"], "processed": True}, record["id"])
        return {k: v for k, v in record.items() if k != "path"}

    def save_report(self, workspace, sources, result, metadata, *, title=None):
        report_id = str(uuid4())
        self.reports.insert({
            "id": report_id, "workspace_id": workspace.id, "user_id": workspace.user_id,
            "title": title or workspace.name[:160],
            "description": " ".join(x["text"] for x in result["observations"]),
            "equipment_id": result["equipment_id"]["value"] or result["equipment_id"]["state"],
            "part_numbers": json.dumps([x["part_number"] for x in result["parts_used"]["items"]]),
            "defect_codes": "[]",
            "corrective_action": " ".join(x["text"] for x in result["proposed_actions"]),
            "parts_used": json.dumps([x["part_number"] for x in result["parts_used"]["items"]]),
            "next_service_date": result["next_service_date"]["value"] or "",
            "priority": result["priority"]["value"] or result["priority"]["state"],
            "status": "open", "created_at": timestamp(), "updated_at": timestamp(), "finalized": False,
            "evidence_json": json.dumps(result), "sources_json": json.dumps(sources),
            "model_id": metadata.get("model", ""), "generation_usage": json.dumps(metadata.get("usage", {})),
            "review_notes": "",
        })
        return report_id

    async def start(self, workspace_id, user_id):
        try:
            workspace = self.get_workspace(workspace_id, user_id)
            existing = self.jobs(where="workspace_id=? AND user_id=? AND status IN ('queued','running')",
                                 where_args=[workspace_id, user_id])
            if existing:
                return self.poll(existing[0].id, user_id)
            if len(self.tasks) >= 3:
                raise LimitReached("The demo is busy with three reports. Please try again shortly.")
            sources = self.source_records(workspace)
            self.budget.reserve(user_id, "report")
            job_id = str(uuid4())
            self.jobs.insert({"id": job_id, "user_id": user_id, "workspace_id": workspace_id,
                              "created_at": timestamp(), "updated_at": timestamp(), "status": "queued",
                              "report_id": "", "error": "", "sources_json": ""})
            task = asyncio.create_task(self.run(job_id, sources))
            self.tasks[job_id] = task
            task.add_done_callback(lambda finished, job_id=job_id: self.tasks.pop(job_id, None))
            return self.poll(job_id, user_id)
        except (KeyError, ValueError, LimitReached) as error:
            return self.error_view(str(error), workspace_id)

    async def run(self, job_id, source_records):
        job = self.jobs[job_id]
        try:
            async with self.lock:
                self.jobs.update({"status": "running", "updated_at": timestamp()}, job_id)
                sources = [await self.prepare_source(dict(record), job.user_id) for record in source_records]
                if sum(len(source["text"]) for source in sources) > self.settings.max_source_chars:
                    raise ValueError("The transcribed inputs exceed the demo's 9,000-character report limit. Shorten the text and try again.")
                self.jobs.update({"sources_json": json.dumps(sources)}, job_id)
                items = [{"transcription": json.dumps({k: v for k, v in source.items() if k != "text"})
                          + "\n" + source["text"]} for source in sources]
                result, metadata = await self.provider.generate(items, job.user_id)
                workspace = self.get_workspace(job.workspace_id, job.user_id)
                report_id = self.save_report(workspace, sources, result, metadata)
                self.jobs.update({"status": "done", "report_id": report_id, "updated_at": timestamp()}, job_id)
        except asyncio.CancelledError:
            self.jobs.update({"status": "failed", "error": "The app restarted during generation. Your inputs are saved; please try again.",
                              "updated_at": timestamp()}, job_id)
            raise
        except (LimitReached, ProviderUnavailable, ValueError) as error:
            self.jobs.update({"status": "failed", "error": str(error), "updated_at": timestamp()}, job_id)
        except Exception:  # noqa: BLE001 - persist a safe terminal state for unexpected job failures
            self.jobs.update({"status": "failed", "error": "The report could not be saved. Your workspace may have changed; please open it and try again.",
                              "updated_at": timestamp()}, job_id)

    def poll(self, job_id, user_id):
        job = self.jobs[job_id]
        if job.user_id != user_id:
            raise KeyError("Generation not found")
        if job.status == "done":
            return evidence_report_view(self.reports[job.report_id])
        if job.status == "failed":
            return self.error_view(job.error, job.workspace_id)
        return Div(
            H2("Preparing your report" if job.status == "running" else "Your report is queued"),
            P("You can leave this view and return to the workspace. Your inputs are saved."),
            P("We are reading the sources and checking the report.", role="status", aria_live="polite"),
            P("AI capacity is shared. A queued report may take about a minute."),
            Button("Back to workspace", hx_get=f"/content/workspace/{job.workspace_id}",
                   hx_target="#main-content", cls=ButtonT.secondary),
            hx_get=f"/generation/{job.id}", hx_trigger="every 2s", hx_target="#main-content",
            hx_swap="innerHTML", id="generation-status", cls="p-8 space-y-4",
        )

    def error_view(self, message, workspace_id):
        return Div(H2("Report not generated"), P(message, role="alert"),
                   Button("Back to workspace", hx_get=f"/content/workspace/{workspace_id}",
                          hx_target="#main-content", cls=ButtonT.primary), cls="p-8 space-y-4")

    async def shutdown(self):
        tasks = list(self.tasks.values())
        for task in tasks:
            task.cancel()
        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)
