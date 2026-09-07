"""Compare legacy or revised report generation on source-only cases.

Uses the Python standard library. --prepare captures requests without model calls.
Legacy runs execute the original function's AST without editing the application.
Candidate runs require the project's Pydantic dependency. Overrides are recorded.
"""

import argparse
import ast
import asyncio
import hashlib
import json
import os
import sys
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from types import SimpleNamespace

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
sys.path.insert(0, str(ROOT))
DEFAULT_SOURCE = ROOT / "ai_services.py"
ENDPOINTS = {
    "openai": ("https://api.openai.com/v1/chat/completions", "OPENAI_API_KEY"),
    "gemini": (
        "https://generativelanguage.googleapis.com/v1beta/openai/chat/completions",
        "GEMINI_API_KEY",
    ),
    "ollama": ("http://127.0.0.1:11434/v1/chat/completions", None),
}


def digest(data):
    return hashlib.sha256(data).hexdigest()


def load_cases(path):
    cases = [json.loads(line) for line in path.read_text().splitlines() if line.strip()]
    ids = [case["id"] for case in cases]
    if len(ids) != len(set(ids)):
        raise ValueError("Duplicate case IDs")
    for case in cases:
        if (
            case.get("split") != "development"
            or case.get("provenance", {}).get("origin") != "synthetic"
        ):
            raise ValueError(
                "This starter runner accepts only labeled synthetic development cases"
            )
    return cases


def source_items(case):
    """Explicit allowlist prevents reference answers and case titles entering prompts."""
    items = []
    for source in case["sources"]:
        header = {
            key: source[key]
            for key in (
                "id",
                "type",
                "recorded_at",
                "applies_to_revision",
                "uploaded_at",
            )
            if key in source
        }
        items.append(
            {
                "transcription": json.dumps(header, ensure_ascii=False)
                + "\n"
                + source["text"]
            }
        )
    return items


def extract_function(path):
    source = path.read_text()
    tree = ast.parse(source, filename=str(path))
    nodes = [
        node
        for node in tree.body
        if isinstance(node, ast.AsyncFunctionDef)
        and node.name == "generate_maintenance_report"
    ]
    if len(nodes) != 1:
        raise ValueError("Expected one generate_maintenance_report function")
    node = nodes[0]
    module = ast.Module(body=[node], type_ignores=[])
    return compile(module, str(path), "exec"), ast.get_source_segment(source, node)


async def invoke_function(code, items, credential, send):
    """Supply the HTTP interface the unchanged function calls, without app startup."""

    class Client:
        async def __aenter__(self):
            return self

        async def __aexit__(self, *_):
            return False

        async def post(self, url, *, headers, json):
            return await send(url, headers, json)

    namespace = {
        "os": SimpleNamespace(
            getenv=lambda name: credential if name == "OPENAI_API_KEY" else None
        ),
        "json": json,
        "httpx": SimpleNamespace(AsyncClient=Client),
    }
    # Execute only the selected repository function, never fixture or model text.
    exec(code, namespace)  # noqa: S102
    return await namespace["generate_maintenance_report"](items)


def response_object(status, body):
    return SimpleNamespace(status_code=status, json=lambda: json.loads(body))


def post_json(endpoint, payload, credential, timeout=60):
    request = urllib.request.Request(
        endpoint,
        data=json.dumps(payload).encode(),
        headers={
            "Content-Type": "application/json",
            "Authorization": "Bearer " + credential,
        },
        method="POST",
    )
    try:
        opener = (
            urllib.request.build_opener(urllib.request.ProxyHandler({}))
            if endpoint == ENDPOINTS["ollama"][0]
            else urllib.request.build_opener()
        )
        with opener.open(request, timeout=timeout) as response:
            return (
                response.status,
                response.read().decode("utf-8"),
                response.headers.get("x-request-id"),
            )
    except urllib.error.HTTPError as error:
        return (
            error.code,
            error.read().decode("utf-8", errors="replace"),
            error.headers.get("x-request-id"),
        )


def save_json(path, value, credential=""):
    text = json.dumps(value, ensure_ascii=False, indent=2) + "\n"
    if credential:
        text = text.replace(credential, "[REDACTED]")
    path.write_text(text)


async def run(args):
    candidate = getattr(args, "candidate", False)
    if candidate:
        import reporting

        if not args.prepare and args.provider != "ollama":
            raise ValueError(
                "The first candidate comparison uses only local Ollama inference"
            )
    cases = load_cases(args.cases)
    if args.case:
        cases = [case for case in cases if case["id"] in args.case]
        if {case["id"] for case in cases} != set(args.case):
            raise ValueError("Unknown requested case ID")
    if not cases:
        raise ValueError("No cases to run")
    code, function_source = extract_function(args.source)
    credential = (
        "offline-placeholder"
        if args.prepare
        else (
            "local-no-key"
            if args.provider == "ollama"
            else os.environ.get(ENDPOINTS[args.provider][1])
        )
    )
    if not credential:
        raise ValueError("Selected provider credential is not configured")
    if not args.prepare and args.provider in ("gemini", "ollama") and not args.model:
        raise ValueError(
            "Specify the provider model; the legacy OpenAI model cannot be used there"
        )
    if args.provider == "ollama" and not args.prepare:
        opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
        with opener.open("http://127.0.0.1:11434/api/tags", timeout=5) as response:
            available = json.load(response).get("models", [])
        matches = [model for model in available if model.get("name") == args.model]
        if (
            not matches
            or any(
                model.get("remote_host") or model.get("remote_model")
                for model in matches
            )
            or args.model.endswith(":cloud")
        ):
            raise ValueError("Ollama runs require an already downloaded local model")

    output = args.output or HERE / "runs" / (
        datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
        + ("-prepared" if args.prepare else "-" + args.provider)
    )
    output.mkdir(parents=True, exist_ok=False)
    manifest = {
        "variant": "evidence_report_v1" if candidate else "legacy_prompt",
        "status": "prepared_no_model_calls" if args.prepare else "running",
        "started_at": datetime.now(timezone.utc).isoformat(),
        "scope": "Report-generation component only; no upstream entity extraction, audio, retrieval, UI, or storage execution.",
        "input_adapter": "One text item per source, with source IDs/type and supplied metadata prepended; no extracted_data.",
        "interpretation": "Synthetic development cases, one sample per case; not held-out evidence or production accuracy. Acceptance checks are structural, not semantic fact checking.",
        "provider": None if args.prepare else args.provider,
        "model_override": args.model,
        "original_model": "gpt-3.5-turbo",
        "output_token_cap": None if args.prepare else args.max_tokens,
        "timeout_seconds": None if args.prepare else args.timeout_seconds,
        "temperature": 0.3,
        "source_path": str(args.source.resolve()),
        "source_sha256": digest(args.source.read_bytes()),
        "function_sha256": digest(function_source.encode()),
        "runner_sha256": digest(Path(__file__).read_bytes()),
        "cases_sha256": digest(args.cases.read_bytes()),
        "python": sys.version,
        "case_ids": [case["id"] for case in cases],
        "model_calls_attempted": 0,
        "completed_case_ids": [],
        "billing_context": args.billing_context,
        "deviations": [
            "HTTP adapter uses urllib with the recorded timeout instead of the application httpx client.",
            "Run mode adds an explicit output-token cap; the original request has no explicit cap.",
        ]
        + (
            [
                "Provider/model override: this is the legacy prompt on the selected provider, not the original OpenAI deployment baseline."
            ]
            if args.provider in ("gemini", "ollama")
            else []
        ),
    }
    if args.provider == "ollama" and not args.prepare:
        manifest["local_model_metadata"] = matches[0]
        with opener.open("http://127.0.0.1:11434/api/version", timeout=5) as response:
            manifest["ollama_version"] = json.load(response)["version"]
    if candidate:
        import importlib.metadata

        manifest["pydantic_version"] = importlib.metadata.version("pydantic")
        manifest["candidate_artifacts"] = {}
        for name in (
            "reporting.py",
            "report-instructions.txt",
            "evals/pyproject.toml",
            "evals/uv.lock",
        ):
            path = ROOT / name
            manifest["candidate_artifacts"][name] = digest(path.read_bytes())
            snapshot = output / (name + ".snapshot")
            snapshot.parent.mkdir(parents=True, exist_ok=True)
            snapshot.write_bytes(path.read_bytes())
        manifest["deviations"] += [
            "Candidate instructions, report schema, constrained generation, and validation replace the legacy report-generation component as one revision."
        ]
    (output / "runner-snapshot.py").write_bytes(Path(__file__).read_bytes())
    (output / "source-function.py.txt").write_text(function_source + "\n")
    save_json(output / "manifest.json", manifest)
    for case in cases:
        record = {
            "case_id": case["id"],
            "status": "prepared" if args.prepare else "running",
        }
        items = source_items(case)
        (output / (case["id"] + ".inputs.json")).write_text(
            json.dumps(items, ensure_ascii=False, indent=2) + "\n"
        )

        async def send(url, headers, payload, *, record=record):
            if url != ENDPOINTS["openai"][0]:
                raise ValueError(
                    "Source function endpoint changed; review before running"
                )
            request_key = "component_request" if candidate else "original_request"
            if request_key in record:
                raise ValueError("Unexpected second request for one case")
            record[request_key] = json.loads(json.dumps(payload))
            if args.prepare:
                # Only enables the existing function to finish capturing its request.
                # This placeholder is never saved as a model response or report.
                return response_object(
                    200, '{"choices":[{"message":{"content":"{}"}}]}'
                )
            sent = json.loads(json.dumps(payload))
            if args.model:
                sent["model"] = args.model
            sent["max_tokens"] = args.max_tokens
            record["sent_request"] = sent
            record["endpoint"] = ENDPOINTS[args.provider][0]
            record["requested_at"] = datetime.now(timezone.utc).isoformat()
            manifest["model_calls_attempted"] += 1
            save_json(output / "manifest.json", manifest)
            started = time.perf_counter()
            try:
                status, body, request_id = await asyncio.to_thread(
                    post_json,
                    record["endpoint"],
                    sent,
                    credential,
                    args.timeout_seconds,
                )
            except Exception as error:
                record["transport_error_type"] = type(error).__name__
                raise
            finally:
                record["elapsed_seconds"] = round(time.perf_counter() - started, 4)
            record.update(
                http_status=status,
                response_body=body.replace(credential, "[REDACTED]"),
                response_redacted=credential in body,
                request_id=request_id,
            )
            try:
                envelope = json.loads(body)
                record["usage"] = envelope.get("usage")
                record["returned_model"] = envelope.get("model")
                record["finish_reasons"] = [
                    choice.get("finish_reason")
                    for choice in envelope.get("choices", [])
                ]
            except (ValueError, AttributeError):
                pass
            return response_object(status, body)

        if candidate:
            payload = reporting.build_request(items, args.model or "not-selected")
            returned = None
            try:
                response = await send(ENDPOINTS["openai"][0], {}, payload)
                if not args.prepare:
                    if response.status_code != 200:
                        returned = {
                            "error": f"API request failed: {response.status_code}"
                        }
                    else:
                        content = response.json()["choices"][0]["message"]["content"]
                        returned = reporting.parse_report(
                            content, reporting.source_texts_from_items(items)
                        )
                        record["validation"] = {
                            "status": "accepted",
                            "scope": "Schema, state invariants, citation IDs, and literal identifier occurrence; content still requires review.",
                        }
            except (ValueError, TypeError, KeyError, IndexError, OSError) as error:
                record["validation"] = {
                    "status": "rejected",
                    "error_type": type(error).__name__,
                    "message": str(error),
                }
                returned = {"error": "Candidate generation or validation failed"}
        else:
            returned = await invoke_function(code, items, credential, send)
        if not args.prepare:
            record["function_result"] = returned
            record["status"] = (
                "execution_error"
                if record.get("http_status") != 200
                else (
                    ("validation_error" if candidate else "parser_error")
                    if isinstance(returned, dict) and "error" in returned
                    else "returned"
                )
            )
        save_json(output / (case["id"] + ".json"), record, credential)
        manifest["completed_case_ids"].append(case["id"])
        save_json(output / "manifest.json", manifest)
        print(case["id"] + ": " + record["status"], flush=True)
        if not args.prepare and (
            record.get("http_status") in (401, 403, 404, 429)
            or record.get("transport_error_type")
            or (record.get("http_status") or 0) >= 500
        ):
            manifest["status"] = "stopped_after_provider_or_transport_error"
            break
    else:
        manifest["status"] = "prepared_no_model_calls" if args.prepare else "finished"
    manifest["finished_at"] = datetime.now(timezone.utc).isoformat()
    save_json(output / "manifest.json", manifest)
    print("Artifacts: " + str(output))
    return output


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, default=DEFAULT_SOURCE)
    parser.add_argument("--cases", type=Path, default=HERE / "reference-cases.jsonl")
    parser.add_argument(
        "--case", action="append", help="Run only this ID; may be repeated"
    )
    parser.add_argument(
        "--output",
        type=Path,
        help="New directory; existing results are never overwritten",
    )
    parser.add_argument(
        "--prepare",
        action="store_true",
        help="Capture original requests without network calls",
    )
    parser.add_argument(
        "--candidate",
        action="store_true",
        help="Run the revised evidence-report component instead of the legacy function",
    )
    parser.add_argument("--provider", choices=ENDPOINTS)
    parser.add_argument(
        "--model", help="Explicit model override, recorded in the manifest"
    )
    parser.add_argument("--max-tokens", type=int, default=4096)
    parser.add_argument("--timeout-seconds", type=int, default=60)
    parser.add_argument(
        "--billing-context", default="Not independently verified by the runner"
    )
    args = parser.parse_args()
    if not args.prepare and not args.provider:
        parser.error("Choose --prepare or an explicit --provider")
    if args.prepare and (args.provider or args.model):
        parser.error(
            "--prepare captures the original request; omit provider/model overrides"
        )
    if not 1 <= args.max_tokens <= 4096:
        parser.error(
            "--max-tokens must be between 1 and 4096 for this bounded baseline"
        )
    if not 1 <= args.timeout_seconds <= 600:
        parser.error("--timeout-seconds must be between 1 and 600")
    try:
        asyncio.run(run(args))
    except (ValueError, FileExistsError, FileNotFoundError) as error:
        parser.exit(1, str(error) + "\n")


if __name__ == "__main__":
    main()
