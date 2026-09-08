Frontline pilot corpus
=====================

pilot-v1.jsonl contains 20 synthetic reporting cases. pilot-v1.manifest.json records the file hash, source hashes, sampling dimensions, prior exposure, and source provenance.

The first five packets preserve the original observations from ../reference-cases.jsonl. The new label representation normalizes explicit “no parts fitted” in FL-002 and FL-005 from the historical known/empty encoding to the report contract's none state. Historical files and runs are unchanged.

The other 15 packets vary record completeness, explicit priority/date, attribution, unresolved and resolved disagreement, duplicate evidence, historical work, ambiguous identifiers, and source applicability. The sampling dimensions are provisional hypotheses for collecting useful traces; they are not human-derived failure categories.

All initial labels are marked provisional_ai_authored. There are no human annotations or final-test cases in this version. Text labeled as simulated OCR is authored text, not output from a vision benchmark. These data cannot estimate how common failures are in real maintenance work.

FL-018 and FL-019 include short summaries of Raspberry Pi Ltd's frequency-management documentation. They cite source commit 9bb5ef62d9d5e32930d5d79ae2e05cf75f0eea4f and retain attribution and CC-BY-SA-4.0 metadata. The summaries were written by the project assistant; the gateway observations are fictional. Treat these two cases as one source group in any future split. [Original document](https://github.com/raspberrypi/documentation/blob/9bb5ef62d9d5e32930d5d79ae2e05cf75f0eea4f/documentation/asciidoc/computers/raspberry-pi/frequency-management.adoc), [documentation licensing](https://www.raspberrypi.com/licensing/).

The pilot corpus and its assistant-authored summaries are offered under [CC BY-SA 4.0](https://creativecommons.org/licenses/by-sa/4.0/), with the upstream attribution retained. This statement covers these data files, not unrelated files or historical media elsewhere in the repository.

Run with the application dependencies installed:

    python -m evals.pilot --prepare
    python -m evals.pilot --credentials .env.hosting.local
    python -m evals.review_app --run evals/runs/RUN_DIRECTORY
    python -m evals.scoring --run evals/runs/RUN_DIRECTORY

The first command makes no model calls. The real run captures both instruction variants and creates a local trace-review page. Human reviews are saved under ignored evals/reviews/ and can be exported from that page.

Read [the evaluation method](../../docs/evaluation-method.md) before interpreting any score.
