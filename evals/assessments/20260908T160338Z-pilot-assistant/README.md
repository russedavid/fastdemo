# Pilot assistant assessment

The owner delegated all 40 reviews to the assistant. [Read the findings and every judgment](report.md), or open [the searchable HTML view](report.html).

- `reviews.jsonl`: 40 final assistant review events with source evidence, provenance, Pass/Fail, critiques, qualitative confidence, and failure categories.
- `open-notes.jsonl`: original notes before category assignment and the consistency pass.
- `revisions.jsonl`: three critique corrections; no verdicts changed.
- `rubric.md`: criteria, boundary decisions, scope, and disclosed adaptation of Husain/Shankar's approach.
- `taxonomy.json`: categories derived from the notes, including one first failure per failed output.
- `manifest.json`: reviewer attribution and artifact fingerprints.
- `report_views.py.snapshot`: application rendering behavior used to assess empty completed-work sections.
- `summary.json`, `report.md`, `report.html`: generated summaries; no model calls are used to regenerate them.

The 21 Pass / 19 Fail judgments are provisional assistant evidence. There are zero human judgments. Four failures are limited to the completed-work section; the report shows the effect of treating that issue as non-blocking. These development examples are not held-out data, production observations, or a calibrated judge dataset.

From the repository root:

```sh
python -m evals.render_assessment --run evals/published/20260908T160338Z-pilot \
  --assessment evals/assessments/20260908T160338Z-pilot-assistant
python -m evals.review_app --run evals/published/20260908T160338Z-pilot \
  --assessment evals/assessments/20260908T160338Z-pilot-assistant
```

Visit `http://127.0.0.1:5003/assessment`. The optional human review interface remains at `/`; it does not import assistant judgments into its journal.

All observations are synthetic. Public-reference attribution and scoped data licensing remain documented in [the corpus card](../../corpus/README.md). The unchanged generation traces and original run metadata are in [the recorded pilot](../../published/20260908T160338Z-pilot/README.md).
