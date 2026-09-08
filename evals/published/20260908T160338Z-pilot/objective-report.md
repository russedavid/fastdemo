Frontline paired pilot — objective results
=========================================

September 8, 2026. Twenty synthetic input cases, two instruction variants, 40 recorded requests. All observations and initial reference labels are AI-authored. **Human semantic review is pending.**

The report preserves every attempted outcome. Both variants use the same model, source packet, schema, validator, temperature, reasoning setting, and output cap. Only the system instruction differs. See [the protocol](../../../docs/evaluation-method.md).

| Recorded outcome | Deployed instructions | Minimal instructions |
|---|---|---|
| Requests attempted | 20 | 20 |
| Structurally accepted | 19 | 19 |
| Application-validator rejection | 0 | 1 |
| Provider schema rejection | 1 | 0 |
| Reported tokens | 39552 | 31859 |
| Requests missing usage data | 1 | 0 |
| Median HTTP round trip (seconds) | 1.074 | 1.076 |

The provider rejected FL-019-deployed with HTTP 400 and included its incomplete generated JSON. The initial runner stopped on that error. A documented continuation executed only the three unattempted requests; FL-019-deployed was not regenerated. The original failure and initial-segment manifest remain in the bundle.

Field agreement with provisional references
------------------------------------------

These checks examine available fields even in a rejected or partial generation. A matching field does not turn a failed report into a successful one. This table is not report accuracy, citation entailment, or a semantic Pass/Fail verdict.

| Field | Deployed: match / disagree / unavailable | Minimal: match / disagree / unavailable |
|---|---|---|
| equipment_id | 20 / 0 / 0 | 20 / 0 / 0 |
| priority | 19 / 0 / 1 | 20 / 0 / 0 |
| next_service_date | 20 / 0 / 0 | 20 / 0 / 0 |
| parts_used | 16 / 3 / 1 | 13 / 7 / 0 |

Only one case establishes priority and one establishes a service date. The [machine-readable summary](objective-summary.json) therefore also separates checks by expected known/unknown/conflicting state. All 20 equipment-ID values matched the provisional references in both variants, but two overall outputs were still structurally rejected.

Inspect the disagreements
-------------------------

Reference expectations below have not been adjudicated by the owner. Each link opens the complete recorded trace, including source text and the original provider response.

| Trace | Check | Expected | Recorded |
|---|---|---|---|
| [FL-003-minimal](FL-003-minimal.json) | parts_used: fail | {"state":"unknown","items":[]} | {"state":"none","items":[]} |
| [FL-009-minimal](FL-009-minimal.json) | parts_used: fail | {"state":"known","items":[{"part_number":"CLP-7","quantity":null}]} | {"state":"unknown","items":[{"part_number":"CLP-7","quantity":null}]} |
| [FL-012-minimal](FL-012-minimal.json) | parts_used: fail | {"state":"unknown","items":[]} | {"state":"none","items":[]} |
| [FL-012-deployed](FL-012-deployed.json) | parts_used: fail | {"state":"unknown","items":[]} | {"state":"none","items":[]} |
| [FL-014-minimal](FL-014-minimal.json) | parts_used: fail | {"state":"unknown","items":[]} | {"state":"none","items":[]} |
| [FL-014-deployed](FL-014-deployed.json) | parts_used: fail | {"state":"unknown","items":[]} | {"state":"none","items":[]} |
| [FL-018-minimal](FL-018-minimal.json) | parts_used: fail | {"state":"unknown","items":[]} | {"state":"none","items":[]} |
| [FL-018-deployed](FL-018-deployed.json) | parts_used: fail | {"state":"unknown","items":[]} | {"state":"none","items":[]} |
| [FL-019-deployed](FL-019-deployed.json) | priority: unavailable | {"source_ids":["FL-019-N1"],"state":"unknown","value":null} | null |
| [FL-019-deployed](FL-019-deployed.json) | parts_used: unavailable | {"source_ids":["FL-019-N1"],"state":"unknown","value":null} | null |
| [FL-019-minimal](FL-019-minimal.json) | parts_used: fail | {"state":"unknown","items":[]} | {"state":"none","items":[]} |
| [FL-020-minimal](FL-020-minimal.json) | parts_used: fail | {"state":"unknown","items":[]} | {"state":"none","items":[]} |

Decision boundary
-----------------

No semantic winner is declared. The deployed instructions agree with more of the provisional parts labels, but prose omissions, unsupported statements, and citation support still need human review. The comparison is a purposive development pilot with one output per case and variant, not a held-out or production-prevalence study.

Next: complete the initial human open-coding round, derive failure categories from the critiques, resolve the reference/criteria disagreements, and then select the first failure-specific evaluator or improvement.
