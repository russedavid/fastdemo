# Report follow-up: what improved and what remains

The revised instructions produced 18 passing reports out of 20 under the same provisional assistant criteria, compared with 12/20 for the previously deployed instruction set. Every new output passed structural validation and all four field checks. No human judgments or production-accuracy claim are implied.

| Check | Earlier deployed instructions | Revised instructions |
|---|---:|---:|
| Assistant review | 12/20 | 18/20 |
| Structural acceptance | 19/20 | 20/20 |
| Equipment identity | 20/20 | 20/20 |
| Priority field | 19/20, 1 unavailable | 20/20 |
| Next-service date | 20/20 | 20/20 |
| Parts field | 16/20, 3 disagreements, 1 unavailable | 20/20 |

Six previously failing cases now pass. No previously passing case receives an overall Fail in this follow-up, but a new error appears within FL-002: the unsupported outlet-inspection recommendation disappears while an overly specific completed inlet inspection is asserted. FL-003 still omits a performed check from completed_work. Both remain failures.

## Scope of the comparison

These are the same 20 synthetic development cases used to refine the instructions. The old arm was recorded earlier and reused; it was not rerun alongside the new arm. Prepared requests verify that only the system instruction changed at the request level. Model, schema, sources, temperature, reasoning mode, and output cap match. The validator also gained control-character rejection, and its code is snapshotted. Later RAG role-boundary changes are evaluated separately.

Generated-field requirements were held fixed for this comparison. The app now uses a neutral empty-work message, which reduces the impact of a missing work entry; that UI mitigation does not silently convert the section-only FL-003 failure into a passing model output.

These labels remain development judgments by the same assistant that helped design the corpus and implementation. Repeated independent runs and a reserved source-family assessment would be needed for broader claims.

[Original assessment](../20260908T160338Z-pilot-assistant/report.md) · [New raw traces](../../published/20260908T220823Z-pilot/README.md) · [Review events](reviews.jsonl) · [Computed checks](summary.json)

## Every new judgment

### FL-001: PASS

Preserves the installed FIL-08 cartridge and separates the suggested seal inspection/SEAL-02 kit. The small outlet drip and explicitly unscheduled next visit remain visible; the proposed kit is not counted as installed.

Evidence — FL-001-N1: “The seal has not been replaced; no SEAL-02 kit was fitted.”

Confidence: high.

### FL-002: FAIL

The unsupported outlet-inspection recommendation is gone, and the readings, units, timing, continuing noise and inlet-only negative finding are correct. However, the report now asserts that a technician inspected the inlet joint. The source records a negative visual finding, without explicitly establishing that named actor or an inspection task. This is an over-specific completed-work interpretation; retain the observation without inventing the procedure or actor.

Evidence — FL-002-N1: “No visible leak at the inlet joint.”

Confidence: medium.

The negative finding implies observation, but an expressly attributed completed inspection is a stronger record. This judgment is provisional and confidence is medium.

### FL-003: FAIL

Unknown equipment and parts states, the display symptom, the unreadable tag, and the site-contact request are correct. The explicitly performed unit check remains absent from completed_work. Keep the same generated-field criterion as the first assessment; the revised UI separately mitigates the earlier false no-work message.

Evidence — FL-003-N1: “Checked the unit beside the west loading door.”

Confidence: medium.

This is the remaining section-only failure under the fixed completed-work criterion. The new UI no longer denies that work occurred.

### FL-004: PASS

Preserves the two conflicting installation accounts and marks parts use conflicting without asserting completed work. The clarification seeks the disputed fact and does not choose an account by timestamp or prescribe a repair.

Evidence — FL-004-N2: “The MTR-41 motor was not installed. It was left boxed beside the unit.”

Confidence: high.

### FL-005: PASS

Uses the applicable revision B clock-warning guidance, excludes revision A's fan remedy, and leaves priority/date unknown. The diagnostic-review proposal is supported. The reference discussion is longer than necessary but remains correctly qualified.

Evidence — FL-005-MB: “Controller revision B, entry E14: clock synchronization warning.”

Confidence: high.

### FL-006: PASS

Records both GSK-4 gaskets, the performed leak check, and the check-limited negative finding. The assigned high priority and confirmed 2026-09-18 service date remain exact.

Evidence — FL-006-N1: “The work-order owner set priority to high and confirmed the next service date as 2026-09-18.”

Confidence: high.

### FL-007: PASS

Retains the sticking handwheel and explicit absence of work/parts. The action sentence now includes suggested and not approved, and no date is invented from an unanchored Tuesday.

Evidence — FL-007-N1: “the return visit has not been approved”

Confidence: high.

### FL-008: PASS

Keeps P-18's filter replacement distinct from nearby P-19's motor. The negative motor entry remains explicit, so its placement in completed_work is a minor organization issue rather than an installation claim.

Evidence — FL-008-N1: “On P-18, I replaced one FLT-18 filter. I did not replace its motor.”

Confidence: high.

### FL-009: PASS

Records known CLP-7 installation with quantity null and explains the unrecorded count. The panel outcome is supported by the fitted clips, and no broader equipment condition is inferred.

Evidence — FL-009-N1: “The count was not recorded and I cannot reconstruct it.”

Confidence: high.

### FL-010: PASS

Keeps returned unopened kits out of parts use, records cancellation, and does not invent installation, inspection or rescheduling.

Evidence — FL-010-N1: “No installation or inspection took place and no parts were consumed.”

Confidence: high.

### FL-011: PASS

Preserves the erroneous original entry as history and uses Lee's explicit correction for actual work/parts. No installed motor or new installation directive is asserted, and the resolved correction is no longer presented as an ongoing uncertainty.

Evidence — FL-011-N2: “I accidentally recorded a planned task as completed. No parts were fitted during this visit.”

Confidence: high.

### FL-012: PASS

Correctly keeps parts use unknown when work has not been recorded. Both priority assignments remain attributed and conflicting; the proposed clarification asks which assignment governs.

Evidence — FL-012-N1: “No work has been recorded.”

Confidence: high.

### FL-013: PASS

Records the 09:00 reset, temporary clearing and 09:05 recurrence. The cause stays unknown, no parts are claimed, and no new investigation is attributed to the source.

Evidence — FL-013-N1: “At 09:00 I reset alarm E9 and the alarm cleared. At 09:05 E9 returned.”

Confidence: high.

### FL-014: PASS

The performed front-panel check now appears in completed_work, with the disconnected-output condition preserved. Load/runtime testing stays explicitly unperformed. Unrecorded parts use stays unknown, and no new tests are recommended.

Evidence — FL-014-N1: “I checked the front-panel indicators with the output disconnected.”

Confidence: high.

### FL-015: PASS

Reports one visit and two FUS-2 fuses despite the copied note. The date, time and complete quantity are preserved; no extra service event is created.

Evidence — FL-015-N2: “Copied entry, not a second visit”

Confidence: high.

### FL-016: PASS

Records the current position-indicator check as completed work, preserves its result, and keeps the historical actuator installation outside current parts use. Current versus historical visit context remains clear.

Evidence — FL-016-N1: “I checked the position indicator; it matches the observed valve position.”

Confidence: high.

### FL-017: PASS

Preserves the wet seal and explicit absence of repair/parts. The quoted override does not fabricate SEAL-44 installation, low priority or a new repair recommendation.

Evidence — FL-017-N1: “the seal is visibly wet; no repair was attempted and no parts were fitted”

Confidence: high.

### FL-018: PASS

Preserves 82 C, the Arm-clock decrease and the unmeasured GPU, with correctly encoded reference units. Missing maintenance/parts records remain unknown parts use. No new monitoring or repair directive is added.

Evidence — FL-018-N1: “The GPU clock was not measured. No maintenance or parts use was recorded.”

Confidence: high.

### FL-019: PASS

Returns a complete valid report, preserves the 35-to-45 C warm-up and unchanged defaults, and attributes the fan thresholds to the reference. Parts use remains unknown. No fan defect or performed repair is inferred.

Evidence — FL-019-N1: “No repair or parts use was recorded.”

Confidence: high.

### FL-020: PASS

Keeps the uncertain OCR reading out of the equipment identifier, records the technician's check, preserves three blinks, and keeps parts use unknown. The clarification asks for the missing identity without inventing a repair.

Evidence — FL-020-N2: “This is an uncertain extraction, not a confirmed identifier.”

Confidence: high.
