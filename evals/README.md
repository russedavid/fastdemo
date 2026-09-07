# Report evaluation

This directory provides five synthetic development cases and a runner for the legacy report function or the new evidence-backed report component. The cases are diagnostic examples, not a representative field dataset or an independent accuracy benchmark.

Run commands from the repository root. Python 3.11+ and [uv](https://docs.astral.sh/uv/) are required; `uv.lock` pins the evaluation dependencies.

## Offline checks

```sh
uv run --project evals python -m unittest discover -s tests -p 'test_*.py' -v
```

The tests make no model calls. They cover state consistency, unknown versus none, citation membership, identifier preservation, reference-answer isolation, and request/response recording. The saved identifier regression in `tests/fixtures` came from an assistant-authored synthetic case and contains no real field data.

Prepare requests without starting a model:

```sh
uv run --project evals python -m evals.run_reports --prepare
uv run --project evals python -m evals.run_reports --candidate --prepare
```

## Local model runs

Use an Ollama version supporting the chosen model. Download the model once, then start the server with cloud features disabled. Qwen3.8-27B was exercised with Ollama 0.33.3; its Q4_K_M package is approximately 18 GB.

```sh
ollama pull qwen3.8:27b
OLLAMA_NO_CLOUD=1 OLLAMA_HOST=127.0.0.1:11434 OLLAMA_CONTEXT_LENGTH=8192 OLLAMA_NUM_PARALLEL=1 ollama serve
```

In a separate terminal, compare the components:

```sh
uv run --project evals python -m evals.run_reports --provider ollama --model qwen3.8:27b --timeout-seconds 180
uv run --project evals python -m evals.run_reports --candidate --provider ollama --model qwen3.8:27b --timeout-seconds 180
```

If the Ollama desktop app is already serving, use that instance with equivalent settings or stop it before starting another server. Model downloads and local compute are explicit operations; the runner neither installs a model nor starts a server.

Each invocation creates a new directory under `evals/runs/`, which Git ignores. It records source-only inputs, prompts, actual requests, raw responses, parser/validator results, model/runtime details, timings, usage where available, and implementation snapshots. Existing run directories are never overwritten. `--case FL-005` limits a run to one case; `--output PATH` selects a new output directory.

Only source packets enter model requests. Case titles, reference interpretations, and prohibited-claim lists remain outside the prompt. The legacy arm executes the existing `generate_maintenance_report` function through a captured HTTP interface, without starting the app or running upstream entity extraction, audio, retrieval, or database code. The Ollama provider substitutes the model and endpoint; it does not measure the original OpenAI deployment.

## Review

Read [the cases](reference-cases.md) and [the report contract](../docs/report-contract.md). Record JSON/validation failures separately from semantic judgments. Check that sources actually support statements, missing information stays unknown, disagreements remain visible, and proposed work is not presented as completed.

A real source ID or schema-valid response does not prove a claim is true. Keep failures and regressions, disclose model and instruction changes, and use a larger fresh assessment set before making stronger quality claims.
