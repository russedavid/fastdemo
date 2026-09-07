# Evidence-backed maintenance reports

The existing generator asks for recommendations and suggested parts in fields that can be read as a record of completed work. The new component separates those meanings and gives missing or disputed facts an explicit representation.

`reporting.py` defines the schema, builds a structured-output request, and validates a returned report. `report-instructions.txt` supplies the source-fidelity instructions. This component is callable through the evaluation runner; integrating the new shape into the app's database and UI is a separate step.

## Source packet

Each text item contains a JSON metadata header followed by the original source text. Source IDs must be unique. Source type, observation time, equipment revision, and document upload time are retained when supplied. The evaluation adapter in `evals/run_reports.py` constructs this packet without including reference answers.

Source text is evidence to interpret, not instructions that override the reporting task. The report records what the packet establishes; it does not independently verify physical events or diagnose equipment.

## Output contract

| Field | Meaning |
|---|---|
| `equipment_id` | The exact source identifier, with a known, unknown, or conflicting state. Descriptive details belong in observations. |
| `observations` | Source-supported findings with identifiers, quantities, units, timing, attribution, and negation preserved. |
| `completed_work` | Work recorded as performed. Disputed or proposed work does not belong here as an established event. |
| `parts_used` | Known installed/consumed parts, explicitly none, unknown, or conflicting. Quantities remain unknown when not supplied. |
| `proposed_actions` | An attributed source recommendation or a labeled request to clarify missing/conflicting information. |
| `uncertainties` | Missing information or competing accounts, with their source references. |
| `priority`, `next_service_date` | Source-supported values or explicit unknown/conflicting states. No default priority or invented appointment. |

Every claim cites its source IDs. A later-written account does not automatically resolve a disagreement; a manual must apply to the relevant equipment revision. Preserve the scope of negative findings: no visible leak at one joint does not establish that the entire unit has no leaks.

## Validation boundary

Pydantic checks field types and disallows extra properties. Additional checks enforce state/value consistency, keep disputed parts out of installed-part lists, require visible explanations for conflicting states, and reject citation IDs outside the packet. Equipment and part identifiers must occur verbatim in their cited source text.

These checks do not prove semantic entailment or entity disambiguation. A wrong claim may cite a real source, and a source may contain several valid identifiers. Review source support separately from structural acceptance. The five included cases are assistant-authored synthetic development fixtures; their labels have not received independent human review.

See [evaluation instructions](../evals/README.md) for offline tests, local execution, retained artifacts, and review guidance.
