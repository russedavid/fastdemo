Frontline: portfolio completion criteria
=======================================

Assessment: September 8, 2026. Application revision: acb32e4.

Evaluation-method update: the user subsequently selected Hamel Husain and Shreya Shankar's frameworks. Follow [the evaluation method](evaluation-method.md): human open coding precedes the failure taxonomy and semantic judges. The 20-case pilot is a review starting point, not a validated evaluator.

Progress update: the 20-case corpus and 40-output paired pilot are complete. The owner delegated the initial review to the assistant; [all 40 judgments and findings](../evals/assessments/20260908T160338Z-pilot-assistant/report.md) are recorded as provisional assistant evidence. The next engineering work can proceed from those findings without waiting for owner labels. README cleanup, offline CI preparation, and preserving the local database while removing it from source tracking have also been completed locally. The original deployment-time inventory below is retained as an assessment snapshot.

Further progress: revised report instructions received a complete 20-case follow-up review (18 provisional passes, two retained failures). Reference retrieval is implemented with pinned manufacturer sources, model/revision/access filtering, a lexical comparison and applicability ablation, and four reviewed retrieval-plus-generation traces. [Report follow-up](../evals/assessments/20260908T220823Z-pilot-assistant/report.md) · [Retrieval implementation and evidence](reference-retrieval.md). Broader source families, reserved assessment, and operational quality monitoring remain open.

Frontline now demonstrates delivery of a working AI application. To complete the role evidence planned for this project, the next work must establish measured retrieval and report quality, observable operation, and a concise technical explanation that another engineer can verify.

This assessment follows The Generative AI Career Masterplan (Arsanjani et al., 2026), especially printed pp. 46–47, 59–60, 81–85, 192–206, 248–259, and 269–270. It maps to our original six-project plan, whose Frontline deliverables are APP-01 through APP-04. The old plan's implementation-status fields predate the public deployment.

The book's central portfolio advice on pp. 253–254 is to show complete, coherent systems, evaluation, operational awareness, and accessible proof. The work packages and acceptance criteria below are our application of that advice, not verbatim requirements from the book.

What already exists
-------------------

- A public HTTPS demo with separate visitor workspaces, editable inputs, live Qwen reports, audio transcription, and image descriptions.
- A report contract that separates observations, completed work, proposals, unknown values, and disagreement.
- Immutable source snapshots and validation of schema, evidence states, source IDs, and literal equipment/part identifiers.
- Persistent quotas, bounded uploads, queued generation, ownership checks, and tested restart/sleep recovery.
- 33 local tests; 12 hosting-specific tests also run on alwaysdata.
- Five assistant-authored synthetic development cases, retained local comparisons, and a five-case hosted run.
- A deployment and operating guide, with real constraints and failures documented.

These establish a substantial engineering foundation. Five development cases do not establish general report accuracy, and the validators do not check full semantic support. The current application receives supplied evidence packets; it does not retrieve references from an indexed corpus.

The GitHub repository is public, but the application revision was still local at assessment time. The README also retains stale deferred-work items and an inherited “under 20 hours” statement that should be removed or substantiated before portfolio promotion. No CI workflow or license file was found among tracked files. A runtime database remains tracked and should be excluded from the source release while preserving the local copy.

Finish the planned Frontline evidence
------------------------------------

| Original artifact | Current state | What closes it |
|---|---|---|
| APP-01: task specification and decisions | Report contract and deployment decisions exist, spread across documents | One concise problem/task specification and decision log connecting requirements, alternatives, observed failures, and choices |
| APP-02: runnable product and architecture case study | Product is deployed; source snapshots and review work | Add the planned reference retrieval and a readable architecture case study |
| APP-03: retrieval and product evaluation | Small generation-component pilot only | A versioned dataset, controlled comparison, separate retrieval/report metrics, failure analysis, and reserved assessment cases |
| APP-04: reproducible demo and operating guide | Hosted demo and hosting guide exist | Current public source release, clean-setup reproduction, automated checks, and a short recorded walkthrough |

1. Build the shared corpus and evaluation protocol first
-------------------------------------------------------

Complete the originally proposed 20-case pilot, then broaden toward roughly 100 diverse cases as an initial study scale. The book discusses this approximate learning scale; it is not a statistical guarantee. Choose the final sample size from the claims we want to support.

Use publicly usable technical references and clearly labeled self-authored or synthetic observations. Real manuals paired with synthetic notes are still a synthetic reporting benchmark; do not describe them as real field records. Record source versions, permissions, transformations, expected facts, and label rationale. Keep related document/case families together when splitting development and reserved assessment data.

Score separate dimensions: correct fields, required facts retained, unsupported assertions, handling of unknown/conflicting facts, and citation support. Include end-to-end audio/image cases so upstream interpretation errors are visible. Have the project owner review a small source-backed reference subset; if labels are only AI-authored, say so. A model judge is optional and needs calibration against documented reference judgments.

Freeze the assessment set before further tuning. Compare the current system with a useful simple baseline under the same provider/model/settings, repeat selected stochastic cases, and report denominators and uncertainty. Retain losses and regressions.

The first concrete case to address is FL-002: its hosted output passed structural validation but proposed an outlet inspection as a clarification, beyond strictly extracting recorded actions. The evaluator must be able to identify this distinction. This is an actual reason to build semantic evaluation.

Completion evidence: a dataset card, source/split manifest, labeling guide, reproducible scoring command, and a comparison report explaining which decision the results changed. Book basis: pp. 84–85, 107–115, 196–199, 254.

2. Add a useful reference-retrieval workflow
------------------------------------------

Given a field note identifying equipment and a revision, retrieve the applicable manual or procedure, cite the relevant passage, and keep that guidance separate from recorded work. If the equipment cannot be identified or no applicable document exists, preserve the gap. A later upload of an obsolete manual must not outrank the applicable revision simply because it is newer.

Begin with a lexical retrieval baseline suitable for identifiers and error codes. Compare it with a justified dense or hybrid alternative. Add reranking only if it earns its cost on the task. Precompute indexes where appropriate to respect the small host; do not select a larger infrastructure stack solely for its resume keywords.

Evaluate retrieval separately from generation: relevant-source recall, ranking, wrong-revision selection, and access filtering. Then measure how those retrieval changes affect the finished report. Permission checks belong before unauthorized content reaches the model.

Completion evidence: a reviewer can run normal, ambiguous, absent-reference, obsolete-reference, and denied-access examples; reproduce the baseline comparison; and understand the chosen architecture. Book basis: pp. 60, 81–85, 253.

3. Demonstrate operation beyond successful startup
------------------------------------------------

Persist useful generation traces: compatible code/prompt/model/data versions, retrieved sources, validation outcome, tokens, queue wait, model time, and end-to-end time. Protect visitor content in logs. Build a small view or report that diagnoses slow and incorrect responses.

Use a disclosed owner-run observation window and a controlled traffic/failure exercise. Distinguish real-provider measurements from simulated load. Include quotas, timeouts, restarts, and a semantic regression where the API remains healthy but begins returning unsupported facts. Detect it and demonstrate a recovery procedure that accounts for prompt, schema, and data compatibility.

Report latency distributions with sample sizes, accepted-task rate, token/cost accounting, and recovery observations. A zero-dollar free-tier bill does not establish the economics of unrestricted usage.

Completion evidence: an operating report, a replayable failure exercise, and a demonstrated quality-regression release gate. Book basis: pp. 59, 199–206, 253.

4. Extend web isolation into AI-specific security evidence
-------------------------------------------------------

The current ownership, cookie, MIME, and request-origin tests are useful web security evidence. Add a focused threat model and owned-environment tests for instructions embedded in notes/manuals/images, attempts to fabricate work history, retrieval across access boundaries, and stale or revoked context.

Document which controls are enforced outside the model, what failed before a mitigation, and what remains unresolved. Passing a finite attack set is evidence about those tests, not a guarantee of immunity.

Completion evidence: a bounded attack corpus, mitigation results, and an explanation of the data and authority boundaries. Book basis: pp. 60, 145–150, 156–158, 203–204.

5. Package the proof for a hiring reviewer
----------------------------------------

The first screen should offer the problem, demo, source, a small results table, and a two-minute walkthrough. The next layer should explain the architecture and a few consequential decisions. The final layer should expose reproduction commands, dataset/rubric versions, representative failures, and sanitized run artifacts.

Rewrite the README around the current contribution. Remove stale claims, publish the reviewed source revision, add CI for deterministic checks, and make a clean setup reproducible. Give datasets and code clear reuse terms. Keep runtime data and credentials out of the release.

Prepare one focused case study about preserving operational evidence. The distinction between valid JSON and a faithful report is a useful narrative already supported by the development work. Add the final benchmark results when available; do not invent adoption, time savings, or customer ROI.

Prepare a consistent project entry for the relevant resume profiles, a portfolio page, and LinkedIn Featured. A useful technical article can direct readers to those artifacts. Publishing or outreach remains a separate action; this assessment does not publish them.

The project owner should be able to reproduce a run, explain the important alternatives, diagnose a failure, and defend the limits of each claim. This is part of demonstrating capability with AI-assisted development.

Completion evidence: a reviewer can understand the contribution quickly, run the demo, inspect a difficult case, and reproduce the key result without a private conversation. Book basis: pp. 248–259, 269–270.

Role coverage and stopping point
--------------------------------

| Career path | Frontline's intended contribution |
|---|---|
| GenAI / AI Engineer | Primary evidence once the complete workflow, retrieval, evaluation, and operating decisions are demonstrated |
| RAG / Retrieval Engineer | Primary evidence after corpus/retrieval comparison and authorization behavior are measured |
| AI Evaluation / LLM Quality Engineer | Supporting application evidence; the reusable harness, calibration, and failure study belong to the Evaluation Lab |
| LLMOps / GenAIOps Engineer | Supporting deployed-system evidence; the full operating/serving comparison belongs to the Operations Kit |
| AI Security Engineer | Supporting evidence from tested AI-specific controls, developed further in the agent and operations projects |
| Applied Scientist / Data Scientist | Supporting experimental/data material; rigorous analytical depth belongs to the shared evaluation and model studies |
| Agentic AI Engineer | A future consumer and integration target; the current background job queue is not an autonomous agent |
| AI / ML Researcher | No original research contribution established by this application |

Keep the original six-project structure. This work completes Frontline while building useful portions of the Corpus, Evaluation Lab, and Operations Kit. It does not finish those projects automatically or require adding agents and fine-tuning to the application.

The next work package is to address the reviewed report failures and build the reference-retrieval comparison. Frontline is ready for deliberate portfolio promotion when APP-01 through APP-04 can be inspected and reproduced, known failures are disclosed, and its role-specific claims are supported. Outside customers or a stakeholder pilot are not prerequisites in the agreed plan.
