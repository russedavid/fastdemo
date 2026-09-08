Evaluation method: analyze, measure, improve
==========================================

September 8, 2026. This protocol follows the user's request to base evaluation work on Hamel Husain and Shreya Shankar. Their methods take priority over the earlier proposal to begin with a broad scoring taxonomy.

The current work is an evaluation foundation, not a claim that a semantic judge has been calibrated or that Frontline is portfolio-complete.

Current review decision
-----------------------

The owner subsequently delegated all 40 pilot reviews to the assistant because they did not have time to review them personally. Proceed with provisional assistant judgments for engineering decisions. This supersedes the earlier requirement to wait for owner labels before grouping failures or improving the application. It does not turn assistant judgments into human labels or establish human alignment.

The [completed assistant assessment](../evals/assessments/20260908T160338Z-pilot-assistant/report.md) records every verdict, source evidence, uncertainty about boundary decisions, the original open notes, and a consistency pass. The assistant first read outputs without variant names or provisional reference answers, then grouped failures. Prior development/corpus exposure is disclosed. The resulting 21 Pass / 19 Fail judgments include four section-only failures; that sensitivity is reported separately. No new model calls were required. This adapts the authors' trace-review and error-analysis process while explicitly omitting independent human review for now.

Assistant events use reviewer_kind=assistant in a separate assessment file. The scorer requires an explicit reviewer kind and keeps human counts separate. Its human-alignment function rejects assistant and unattributed references. The local review page can link to a read-only assessment without pre-filling or creating human judgments.

Begin with actual traces and human judgment
------------------------------------------

Husain and Shankar recommend inspecting traces, writing open-ended failure notes, grouping the notes into a taxonomy, and then building evaluations for the failures that matter. They recommend personally annotating the first 30 traces before reviewing agent suggestions. Synthetic inputs can seed this process when production data is unavailable, but synthetic outcomes cannot establish production failure prevalence. [Error analysis](https://hamel.dev/blog/posts/evals-faq/why-is-error-analysis-so-important-in-llm-evals-and-how-is-it-performed.html).

The original plan designated the project owner as principal reviewer. The owner has now delegated the initial review as described above. The human workflow remains available for later assessment. The assistant never labels its own critiques as human judgments.

The first review asks one binary question: did the output produce a faithful maintenance record from the supplied evidence? The reviewer marks Pass or Fail and writes a short critique. Skipping leaves an example unreviewed. The interface keeps sources beside the report and exposes the complete model request and technical result in a collapsed section. Variant names, provisional reference labels, and automatic check results are not displayed in the primary review view. [Custom review interfaces](https://hamel.dev/blog/posts/evals-faq/what-makes-a-good-custom-interface-for-reviewing-llm-outputs.html).

This is not a request to invent a universal definition of quality before seeing data. Existing task requirements remain available, but the failure taxonomy should grow out of what the reviewer observes.

A bounded pilot
---------------

The pilot contains 20 source packets and runs two instruction variants on each, yielding 40 planned report-generation traces. Five cases were used in earlier development; 15 are new before this pilot. The owner has already seen some historical failures in conversation, so this review is not presented as a fully blinded assessment. This is a first review batch, below the roughly 100 diverse traces they recommend for broader discovery. Forty outputs from 20 cases are not 40 independent situations.

The corpus uses explicit variation dimensions: single versus multiple sources, completed/planned/unknown/disputed records, source correction and revision, measurement scope, duplicate evidence, input format, and uncertain extraction. These are sampling hypotheses, not a finalized failure taxonomy. All observations are synthetic and all initial reference labels are AI-authored. Two cases include attributed summaries of pinned public Raspberry Pi documentation. [Synthetic-data method](https://hamel.dev/blog/posts/evals-faq/what-is-the-best-approach-for-generating-synthetic-data.html).

Both variants use the same model, source packet, JSON schema, parser, temperature, reasoning setting, and 768-token output cap. The only planned difference is the system instruction: the deployed report contract versus a minimal faithful-report instruction. Arm order alternates between case blocks. Every request is prepared and saved before the first model call, preventing edits during the run from changing later requests.

The pilot evaluates the report-generation component. It does not claim to evaluate retrieval, live transcription, live vision, or the complete application. Its compact source identifiers differ from the application’s UUID identifiers, so output-token overhead and truncation behavior can differ. The uncertain-OCR case supplies simulated derived text; it is not a vision accuracy test.

The runner spaces Groq requests at least 65 seconds apart and stops on provider/transport errors. Failures remain in the record. No automatic retry or selective replacement of an unfavorable output is performed.

Check labels before using them as references
-------------------------------------------

The owner's first Pass/Fail judgments are provisional. After the initial independent review, the assistant audits passing and failing outputs against the source packets, checking for missed unsupported claims, important omissions, critiques that contradict the verdict, and inconsistent treatment of similar cases. The AI-authored expected fields are also open to correction. This is an assistant audit, not independent human validation or a calibrated automated judge.

For each disputed judgment, retain the original verdict and critique, identify the specific output and source passages, and explain the disagreement. Bring a small group of consequential disagreements back to the owner for discussion. The owner confirms or revises the judgment and records the reason. Assistant suggestions remain separate from human review events. When a discussion changes the standard, update the criteria version and revisit affected examples in both variants. Unresolved judgments remain visible in the review history but are excluded from the reference set used to validate judges. [Annotation disagreements](https://hamel.dev/blog/posts/evals-faq/how-many-people-should-annotate-my-llm-outputs.html).

The owner sets product acceptability; factual disputes are resolved against the evidence. Being the project owner does not establish maintenance expertise. This pilot can assess faithful reporting of supplied observations. Questions about the technical correctness of maintenance decisions need adequate documentation or a qualified domain reviewer; assistant agreement alone does not settle them.

The current interface records annotations and revisions. It does not automatically audit or adjudicate labels. Scoring those annotations produces descriptive counts; selecting resolved labels for judge validation is a subsequent explicit step.

Automate objective rules, align semantic evaluators
-------------------------------------------------

The initial code checks compare four structured fields against the explicit provisional references: equipment identity, priority, next-service date, and installed parts/quantity. Structural acceptance is reported separately. These checks can expose wrong values, but cannot determine whether all prose is supported, whether an important fact was omitted, or whether a proposed action is justified.

There is no ROUGE, embedding-similarity, “helpfulness,” or combined quality score. A missing output is recorded as unavailable for field inspection, not as a faithful empty report. Assistant semantic judgments are provisional; human validation remains unperformed. [Application-specific binary checks](https://hamel.dev/blog/posts/evals-faq/are-similarity-metrics-bertscore-rouge-etc-useful-for-evaluating-llm-outputs.html).

After the initial human review:

1. Audit the initial labels and discuss disagreements using the procedure above.
2. Group the reviewer's critiques into proposed failure categories, retaining the original notes.
3. Have the reviewer resolve ambiguous categories and define explicit Pass/Fail criteria.
4. Implement deterministic checks where the rule is objective; use scoped LLM judges only where interpretation is required.
5. Assemble resolved human-labeled passing and failing examples for each judge, grouped to avoid source/case leakage between development and assessment.
6. Measure failure-detection sensitivity and pass-acceptance specificity against held-out human labels. Report missing classes and sample sizes; agreement is not established by testing only easy passing examples.

Their current guidance distinguishes discovery sample sizes from judge validation: an LLM judge generally needs around 100–200 labeled examples per failure mode, while a code evaluator needs coverage of its branches and important edge cases. The 20-case pilot is not sufficient to claim that such a judge is validated. [Evaluation sample sizes](https://hamel.dev/blog/posts/evals-faq/how-many-examples-do-i-need-for-an-eval.html).

Record criteria drift instead of hiding it
----------------------------------------

Shankar and colleagues' EvalGen research describes criteria drift: examining outputs can change what a person considers a good result. Our review journal therefore records the criteria version, reviewer, output fingerprint, verdict, critique, and time for each event. Revisions append to the journal rather than replacing old judgments. Summaries require a single reviewer and criteria version; stale output fingerprints are rejected. If the standard changes, both variants must be reviewed under the same new standard before comparison. [Who Validates the Validators?](https://arxiv.org/abs/2404.12272).

Keep final assessment separate
-----------------------------

Every pilot case remains development data after review. Do not relabel a case as held out after using its output to change a prompt, rubric, or evaluator. A later assessment set must be reserved by source/case family before optimization. The two Raspberry Pi cases share an upstream document and must stay in the same split group even though they test different behaviors.

The next decision
-----------------

The pilot should identify the first concrete failure worth fixing and a criterion that can detect it. It should not be used to declare the deployed prompt a winner before semantic review. The known FL-002 suggestion is a useful historical lead, but its prior assistant critique is hidden from the owner's initial review to reduce anchoring.

The assistant can proceed with the delegated review, provisional failure categories, targeted fixes, source preparation, and retrieval implementation. Comparisons based on assistant judgments must retain that attribution. Claiming human alignment would require actual human labels.

Pilot execution note
--------------------

The first run stopped on request 37 when Groq returned HTTP 400 with json_validate_failed and an incomplete generated object. That unfavorable output was preserved. An explicit continuation used the already-prepared requests for the final three unattempted traces; no completed trace was regenerated. The initial-segment manifest, continuation reason, runner snapshot, and all 40 outcomes are retained. The review tool displays provider-returned failed generations as well as ordinary responses. Missing token-usage data is reported as missing, not counted as zero consumption.

The [recorded pilot bundle](../evals/published/20260908T160338Z-pilot/README.md) and [objective comparison](../evals/published/20260908T160338Z-pilot/objective-report.md) are prepared in the repository. They do not include human review journals or claim a semantic winner.
