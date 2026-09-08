# Reference retrieval in Frontline

Frontline adds applicable manufacturer passages to the source packet before generating a report. A Raspberry Pi 5 fan remaining off during a 35–45 degree warm-up can be interpreted alongside the documented default fan thresholds. The field observation, reference guidance, and any recorded maintenance work retain distinct meanings.

The first library is deliberately narrow: nine summaries from two pinned manufacturer documentation files, covering Raspberry Pi 3 Model B+, 4, and 5. See [provenance and reuse terms](../reference-data/README.md).

## How a report gets its references

1. Capture the workspace inputs and prepare any audio/image text.
2. Look for a supported model in written or user-edited notes. Competing model/revision mentions, obvious uncertainty, and unreviewed media interpretations do not establish retrieval context. This is a conservative text heuristic, not a general entity resolver or physical verification.
3. Search an indexed corpus using SQLite FTS5 and BM25. Require current documents, matching model/revision, and public or matching-owner access before selecting the top passages. Queries mentioning recognized components must match at least one of them, preventing a fan question from returning a generic temperature passage solely because of a shared word.
4. Add at most two whole passages within the existing source-character budget. Record source versions, scores, selected IDs, context exclusions, and retrieval time. Keep the complete augmented source snapshot with the report.
5. Generate and validate the report. Reference-only citations cannot establish completed work, installed part identifiers, or an assigned priority/service date. Claims based solely on references appear in a separate guidance section. These code checks do not prove every sentence is semantically supported.

The curated library is public. Owner and revocation filters are exercised with fictional private evaluation fixtures; the app does not yet provide a private-manual upload workflow. Content selected for a report remains under the report's existing ownership checks. A frozen historical report retains its source snapshot when the current index changes; revocation prevents future retrieval, not retroactive erasure of earlier reports.

## Why this implementation

| Option | Benefit | Cost or limitation | Decision |
|---|---|---|---|
| Keyword overlap over eligible passages | Simple baseline with inspectable matches | No stemming or established relevance scoring | Retain for comparison |
| SQLite FTS5 / BM25 | Built-in indexing, stemming, ranked matches; no extra hosted service | Lexical matching needs care with wording and relevance | Use for the initial narrow library |
| Dense embeddings or a hybrid ranker | Can connect paraphrases with few shared words | Adds a model/API or offline index pipeline; query inference must fit the small host | Defer until a broader failure set justifies it |

The actual alwaysdata Python environment supports FTS5 and JSON functions on SQLite 3.40.1. The reference index is a small derived file in the private runtime directory; deployment does not require an embedding service, an additional API key, or a new cloud account. SQLite's [FTS5 documentation](https://www.sqlite.org/fts5.html) describes the tokenizer and BM25 ordering used here.

## What the development comparison showed

Twenty assistant-authored retrieval cases compare keyword overlap, BM25, and an offline BM25 ablation that removes model/revision applicability. Access and revocation checks remain enabled in every method. There are 12 answerable cases and eight cases where the corpus cannot supply applicable, authorized guidance. These are development relevance labels, not human-adjudicated or held-out measurements.

The initial run returned generic temperature passages for a Pi 4 fan-threshold question. A component-match requirement corrected that error. Both runs are retained; the second uses the same cases after that development fix.

| Revised comparison | Relevant top result, answerable cases | Macro recall at 2 | Macro precision at 2, answerable cases | Correct abstentions | Wrong-applicability passages |
|---|---:|---:|---:|---:|---:|
| Keyword overlap | 11/12 | 1.00 | 0.708 | 8/8 | 0 |
| BM25 | 12/12 | 1.00 | 0.708 | 8/8 | 0 |
| BM25 without applicability | 12/12 | 1.00 | 0.667 | 3/8 | 12 |

All three methods returned zero inaccessible or revoked passages in these fixtures. The ablation demonstrates why a plausible top result is insufficient: extra results can still belong to the wrong hardware/revision. Precision below 1.0 also exposes unnecessary second passages. Future work should test adaptive passage selection and broader paraphrase coverage before adding more retrieval machinery.

Recorded local query timings are single measurements after index construction. They are not production latency or load-test results. Model-context extraction is covered by separate boundary tests; report quality is assessed separately from retrieval relevance.

Reproduce from the repository root, using a fresh output directory:

```sh
python -m evals.check_retrieval --output /tmp/frontline-retrieval-check
```

The command makes no model calls. It saves the cases, corpus, code snapshots, per-query rankings, scores, and metric definitions. Preserve the first and revised runs when publishing the evidence.
