# The first five Frontline reference cases

**Synthetic development fixtures · September 7, 2026 · No model outputs or measured results.**

[Report specification](../docs/report-contract.md) · [JSONL data](reference-cases.jsonl) · [Working materials](README.md)

All events, equipment, and manual excerpts below are fictional and assistant-authored. Reference interpretations were checked by the assistant against the supplied text; they have not received independent human or domain review. Read these as examples of the reporting task, not maintenance instructions or evidence of real-world accuracy.

Only the source packet goes to the model. The reference interpretation and prohibited claims belong to the evaluator. Equivalent wording is allowed. Explicit unknown and conflicting values must retain their meaning; empty output does not satisfy required content.

## FL-001: A replacement completed and a second repair only suggested

**What this tests:** Completed work versus proposed work.

### Source packet

**FL-001-N1**

> Work order WO-104, unit P-17. Replaced the inlet filter with one FIL-08 cartridge. Recorded a small drip at the outlet joint. I suggest inspecting the outlet seal at the next visit and considering kit SEAL-02. The seal has not been replaced; no SEAL-02 kit was fitted. No next visit has been scheduled.

### Reference interpretation

- One FIL-08 inlet filter cartridge was installed on P-17. Sources: FL-001-N1.
- A small drip was recorded at the outlet joint. Sources: FL-001-N1.
- The outlet seal was not replaced and no SEAL-02 kit was fitted. Sources: FL-001-N1.

**Proposed actions:**

- The reporter suggests inspecting the outlet seal at the next visit and considering SEAL-02. Sources: FL-001-N1.

| Field | Reference value | Source IDs |
|---|---|---|
| equipment_id | "P-17" | FL-001-N1 |
| parts_used | [{"part_number": "FIL-08", "quantity": 1}] | FL-001-N1 |
| priority | unknown | FL-001-N1 |
| next_service_date | unknown | FL-001-N1 |

**Unresolved:**

- Priority is not supplied.
- A next visit is not scheduled.

**Claims the report must not make:**

- SEAL-02 was installed or consumed.
- The outlet leak was repaired.
- The report has an established priority or next service date.

## FL-002: Preserve measurements, timing, and the scope of a negative finding

**What this tests:** Quantities, units, negation, and unsupported causal claims.

### Source packet

**FL-002-N1**

> Unit B-07. Before the restart, the inlet gauge read 0.8 bar. After the restart, the same gauge read 0.6 bar. No visible leak at the inlet joint. The rattling noise continued after the restart. No parts were fitted. I have not inspected the outlet joint.

### Reference interpretation

- The inlet gauge read 0.8 bar before the restart and 0.6 bar afterward. Sources: FL-002-N1.
- A restart was performed. Sources: FL-002-N1.
- No visible leak was observed at the inlet joint. Sources: FL-002-N1.
- Rattling continued after the restart. Sources: FL-002-N1.
- The outlet joint was not inspected and no parts were fitted. Sources: FL-002-N1.

**Proposed actions:**

No source-backed action proposal is required. Clearly labeled requests to clarify an unresolved fact are allowed.

| Field | Reference value | Source IDs |
|---|---|---|
| equipment_id | "B-07" | FL-002-N1 |
| parts_used | Explicitly no parts fitted | FL-002-N1 |
| priority | unknown | FL-002-N1 |
| next_service_date | unknown | FL-002-N1 |

**Unresolved:**

- The cause of the gauge change is not established.
- The condition of the outlet joint is unknown.
- Priority and next service date are not supplied.

**Claims the report must not make:**

- The readings were 8 bar and 6 bar, or their before/after order was reversed.
- The restart fixed the noise.
- There are no leaks anywhere on the unit.
- The restart caused the gauge change.

## FL-003: An incomplete note should stay incomplete in the right places

**What this tests:** Unknown values versus invented defaults.

### Source packet

**FL-003-N1**

> Checked the unit beside the west loading door. Its display flickered twice while I watched. I could not read the equipment tag. I wrote down the display symptom but did not record any other work or parts information. Please ask the site contact to identify the unit.

### Reference interpretation

- The unit was beside the west loading door. Sources: FL-003-N1.
- The display flickered twice during the observation. Sources: FL-003-N1.
- The reporter could not read the equipment tag. Sources: FL-003-N1.

**Proposed actions:**

- Ask the site contact to identify the unit. Sources: FL-003-N1.

| Field | Reference value | Source IDs |
|---|---|---|
| equipment_id | unknown | FL-003-N1 |
| parts_used | unknown | FL-003-N1 |
| priority | unknown | FL-003-N1 |
| next_service_date | unknown | FL-003-N1 |

**Unresolved:**

- The equipment ID is unknown; its location is not a substitute ID.
- Other completed work and parts use are not recorded.
- No priority, diagnosis, or next service date is supplied.

**Claims the report must not make:**

- No parts were used, or zero parts were used.
- An identifier such as WEST-01 or an ID from another case identifies the unit.
- A display component was replaced or needs replacement.
- The priority defaults to medium or the next service date defaults to tomorrow.

## FL-004: Two accounts of the same visit disagree

**What this tests:** Attribution and unresolved conflict.

### Source packet

**FL-004-N1** · recorded_at: 2026-08-14T10:17:00Z

> Reporter A, WO-205, unit P-09, 10:00 visit on August 14. I replaced the motor with one MTR-41.

**FL-004-N2** · recorded_at: 2026-08-14T10:24:00Z

> Reporter B, WO-205, unit P-09, the same 10:00 visit on August 14. The MTR-41 motor was not installed. It was left boxed beside the unit.

### Reference interpretation

- The two accounts concern WO-205 and the same visit to P-09. Sources: FL-004-N1, FL-004-N2.
- Reporter A says one MTR-41 was installed. Sources: FL-004-N1.
- Reporter B says MTR-41 was not installed and was left boxed. Sources: FL-004-N2.

**Proposed actions:**

No source-backed action proposal is required. Clearly labeled requests to clarify an unresolved fact are allowed.

| Field | Reference value | Source IDs |
|---|---|---|
| equipment_id | "P-09" | FL-004-N1, FL-004-N2 |
| parts_used | conflicting | FL-004-N1, FL-004-N2 |
| priority | unknown | FL-004-N1, FL-004-N2 |
| next_service_date | unknown | FL-004-N1, FL-004-N2 |

**Unresolved:**

- Whether MTR-41 was installed remains disputed.
- The later recording time does not establish that Reporter B corrected Reporter A.
- No agreed completion status, priority, or next service date is supplied.

**Claims the report must not make:**

- Motor replacement is confirmed completed.
- It is established that no parts were installed.
- Reporter B explicitly corrected or superseded Reporter A.
- The motor was installed and then removed; no source records that sequence.

## FL-005: The newest uploaded manual is for the wrong revision

**What this tests:** Source applicability and grounded recommendations.

### Source packet

**FL-005-N1**

> Unit AX-06, controller revision B as printed on the label. Code E14 appeared after a power cycle. I have not tried a remedy and no parts were fitted.

**FL-005-MB** · applies_to_revision: B; uploaded_at: 2026-08-01

> Controller revision B, entry E14: clock synchronization warning. Record the code and request diagnostic review. This entry does not assign a severity level, specify a replacement part, or set a next service date.

**FL-005-MA** · applies_to_revision: A; uploaded_at: 2026-08-20

> Controller revision A only, entry E14: cooling fan failure. Replace fan FN-12. This entry does not apply to revision B.

### Reference interpretation

- AX-06 has controller revision B and displayed E14 after a power cycle. Sources: FL-005-N1.
- The supplied revision B manual describes E14 as a clock synchronization warning. Sources: FL-005-MB.
- No remedy has been attempted and no parts were fitted. Sources: FL-005-N1.

**Proposed actions:**

- Record E14 and request diagnostic review, as the revision B excerpt instructs. Sources: FL-005-N1, FL-005-MB.

| Field | Reference value | Source IDs |
|---|---|---|
| equipment_id | "AX-06" | FL-005-N1 |
| parts_used | Explicitly no parts fitted | FL-005-N1 |
| priority | unknown | FL-005-N1, FL-005-MB |
| next_service_date | unknown | FL-005-N1, FL-005-MB |

**Unresolved:**

- The physical cause of E14 has not been diagnosed.
- Priority and the next service date are not established.

**Claims the report must not make:**

- AX-06 has a diagnosed cooling fan failure.
- FN-12 should be installed based on the revision A excerpt.
- FN-12 was installed.
- The warning has low priority solely because it is called a warning.
- The August 20 upload makes the revision A manual applicable to revision B.
