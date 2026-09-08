# Assistant review criteria: assistant-v1

The owner delegated review of all 40 recorded outputs to the interactive assistant on September 8, 2026. These are provisional assistant judgments, with no human labels or independent domain validation. They can guide engineering work; they do not establish a human-calibrated judge or production accuracy.

The question is whether the attempt produced a usable, faithful maintenance record from the supplied packet under the current report contract and application presentation. Every output was read, including both rejected generations. A Pass allows concise paraphrase and minor presentation improvements. A Fail requires a material unsupported claim, consequential omission or contradiction, incorrect evidence state, or failure to deliver a valid report.

The initial reading omitted variant names and reference answers. The reviewer already had development and corpus-authoring context; this is not a blinded or independent study. Open notes preceded the failure categories. After the first pass, paired cases and boundary decisions were checked for consistency. Original notes and subsequent corrections are retained.

## Decisions applied consistently across both variants

- **Unknown is different from none.** “No parts use was recorded” does not establish that no parts were used. Known installation with an unknown quantity uses a known parts state and a null quantity.
- **Statements need support, including recommendations.** A technician's suggestion or applicable manual instruction can be retained as a proposal. A negative statement that a test was not performed does not authorize that test. A clarification can ask for an unknown cause, confirmed identity, or reconciliation of conflicting accounts; it must not attribute a new directive to the source, prescribe an unsupported repair/test, or supply the missing answer.
- **Performed checks count as completed work.** The existing app renders an empty completed_work array as “No completed work is established by these sources.” Explicit technician checks or inspections must therefore appear in this section. Facts retained only in observations still cause a section-consistency failure. This is a product-contract decision, and the report separately shows how results change if these section-only failures are treated as non-blocking.
- **An event is not automatically technician work.** A power cycle with no recorded actor and an explicit statement that no remedy was tried can remain an observation. Do not invent ownership. On rereading the restart case, the omission from completed_work was removed as a definite failure; the unsupported inspection remains sufficient to fail it.
- **Read the whole report.** A plainly negated motor non-replacement beside a real filter replacement is a presentation issue, not a claim of motor installation. A suggested visit remains tentative when the report explicitly preserves its unapproved status and leaves the service date unknown. Keep these qualifications in the action sentence as an improvement.
- **Preserve scope and uncertainty.** Check-specific negative findings do not establish global health; current work must remain separate from historical work; unresolved conflicts remain attributed; explicit corrections can resolve earlier errors. Uncertain OCR does not establish equipment identity.
- **Rejected generations are failures.** Source-faithful fragments do not compensate for an absent usable report. Do not infer the root cause of a provider failure merely from a partial object.

Confidence labels are qualitative judgments about the critique, not estimated probabilities. Pass is not a claim of ideal writing. Minor notes are retained without inflating the failure count.

## Scope and limitations

There are 20 synthetic situations and two outputs per situation. All cases are development data; related source families must be kept together in any later reserved assessment set. The report-generation component and its current display semantics were reviewed. Retrieval, live audio/image processing, physical maintenance correctness, and production failure prevalence were not evaluated. Applicable public references were supplied inside the packets, not retrieved.

The same assistant participated in corpus design, implementation, and review. A second consistency pass is not an independent review. Human review can later revise these judgments, but it is not a prerequisite for the engineering work the owner has now authorized.

Method basis: [Husain and Shankar on error analysis](https://hamel.dev/blog/posts/evals-faq/why-is-error-analysis-so-important-in-llm-evals-and-how-is-it-performed.html), [annotation disagreements](https://hamel.dev/blog/posts/evals-faq/how-many-people-should-annotate-my-llm-outputs.html), and [Shankar et al. on criteria drift](https://arxiv.org/abs/2404.12272). Substituting assistant review for their recommended initial human review is a disclosed project choice, not a claim that the authors recommend this substitution.
