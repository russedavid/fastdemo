"""Five synthetic development cases on the deployed adapter's Groq request format."""

import argparse
import asyncio
import hashlib
import json
import os
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import httpx

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from evals.run_reports import load_cases, source_items
from groq_service import BASE, MODEL, report_request
from reporting import parse_report, source_texts_from_items


async def main(args):
    key = os.getenv("GROQ_API_KEY", "")
    if args.credentials:
        for line in args.credentials.read_text().splitlines():
            if line.startswith("GROQ_API_KEY="):
                key = line.split("=", 1)[1].strip().strip("'\"")
    if not key:
        raise ValueError("GROQ_API_KEY is missing")
    cases = load_cases(ROOT / "evals/reference-cases.jsonl")
    output = args.output or ROOT / "evals/runs" / (datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ") + "-groq")
    output.mkdir(parents=True, exist_ok=False)
    manifest = {
        "scope": "Synthetic development cases, one generation each; not held-out accuracy.",
        "provider": "groq", "model": MODEL, "reasoning_effort": "none",
        "max_completion_tokens": 768, "case_ids": [case["id"] for case in cases],
        "status": "running", "completed": [], "started_at": datetime.now(timezone.utc).isoformat(),
        "artifacts": {},
    }
    for name in ("reporting.py", "report-instructions.txt", "groq_service.py", "evals/reference-cases.jsonl", "evals/check_groq.py"):
        content = (ROOT / name).read_bytes()
        manifest["artifacts"][name] = hashlib.sha256(content).hexdigest()
        (output / (Path(name).name + ".snapshot")).write_bytes(content)
    def save(name, value):
        (output / name).write_text(json.dumps(value, indent=2).replace(key, "[REDACTED]") + "\n")
    save("manifest.json", manifest)
    async with httpx.AsyncClient(timeout=90, headers={"Authorization": "Bearer " + key, "User-Agent": "Frontline/0.1"}) as client:
        for index, case in enumerate(cases):
            if index:
                await asyncio.sleep(65)
            items = source_items(case)
            payload = report_request(items)
            started = time.monotonic()
            response = await client.post(BASE + "/chat/completions", json=payload)
            record = {"case_id": case["id"], "request": payload, "http_status": response.status_code,
                      "elapsed_seconds": round(time.monotonic() - started, 4), "response_body": response.text}
            if response.status_code == 200:
                envelope = response.json()
                record["usage"] = envelope.get("usage")
                try:
                    if envelope["choices"][0]["finish_reason"] != "stop":
                        raise ValueError("Incomplete generation")
                    record["report"] = parse_report(envelope["choices"][0]["message"]["content"], source_texts_from_items(items))
                    record["validation"] = "accepted"
                except (ValueError, KeyError, TypeError, IndexError) as error:
                    record["validation"] = "rejected"
                    record["error"] = str(error)
            else:
                record["validation"] = "provider_error"
            save(case["id"] + ".json", record)
            manifest["completed"].append(case["id"])
            save("manifest.json", manifest)
            print(case["id"] + ": " + record["validation"] + " (" + str(record["elapsed_seconds"]) + "s)", flush=True)
            if response.status_code != 200:
                manifest["status"] = "stopped_after_provider_error"
                break
        else:
            manifest["status"] = "finished"
    manifest["finished_at"] = datetime.now(timezone.utc).isoformat()
    save("manifest.json", manifest)
    print("Artifacts: " + str(output), flush=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--credentials", type=Path)
    parser.add_argument("--output", type=Path)
    asyncio.run(main(parser.parse_args()))
