"""Validate and render a recorded assistant assessment without model calls."""

import argparse
import hashlib
import html
import json
import re
from collections import Counter, defaultdict
from pathlib import Path

from evals.scoring import summarize
from evals.trace_data import output_text, structural_outcome


def read_json(path):
    return json.loads(path.read_text())


def load_assessment(run, assessment):
    run, assessment = Path(run), Path(assessment)
    manifest = read_json(assessment / "manifest.json")
    if manifest["run_id"] != run.name or manifest["reviewer_kind"] != "assistant":
        raise ValueError("Select the matching, explicitly assistant-authored assessment")
    for name, expected in manifest["artifacts"].items():
        if Path(name).name != name or hashlib.sha256((assessment / name).read_bytes()).hexdigest() != expected:
            raise ValueError("Assessment artifact changed: " + name)
    events = [json.loads(line) for line in (assessment / "reviews.jsonl").read_text().splitlines() if line.strip()]
    run_manifest = read_json(run / "manifest.json")
    completed = run_manifest["completed"]
    if len(completed) != run_manifest["planned_requests"]:
        raise ValueError("Complete the planned run before rendering its assessment")
    if len(events) != len(completed) or {e["trace_id"] for e in events} != set(completed):
        raise ValueError("Assessment must cover every completed trace exactly once")
    if {e["review_number"] for e in events} != set(range(1, len(events) + 1)):
        raise ValueError("Review numbers must be unique and complete")
    records = {}
    for event in events:
        tid = event["trace_id"]
        if not re.fullmatch(r"[A-Za-z0-9_-]+", tid):
            raise ValueError("Unsafe trace ID")
        path = run / (tid + ".json")
        if hashlib.sha256(path.read_bytes()).hexdigest() != event["trace_file_sha256"]:
            raise ValueError("Recorded trace changed: " + tid)
        if (event["reviewer_kind"] != "assistant" or event.get("human_calibration_eligible") is not False
                or event["reviewer"] != manifest["reviewer"]
                or event["criteria_version"] != manifest["criteria_version"]):
            raise ValueError("Assessment attribution is inconsistent")
        record = records[tid] = read_json(path)
        if event["case_id"] != record["case_id"] or event["variant"] != record["variant"]:
            raise ValueError("Assessment case/variant changed")
        sources = {s["id"]: s for s in record["input_sources"]}
        for evidence in event["evidence"]:
            if evidence["source_id"] not in sources or evidence["quote"] not in sources[evidence["source_id"]]["text"]:
                raise ValueError("Review quote does not occur in its source: " + tid)
        if structural_outcome(record) != "accepted" and event["verdict"] != "fail":
            raise ValueError("A rejected generation cannot count as a usable report")
    summary = summarize(run, events=events, criteria_version=manifest["criteria_version"],
                        reviewer=manifest["reviewer"], reviewer_kind="assistant")
    taxonomy = read_json(assessment / "taxonomy.json")
    for event in events:
        tags = [c["id"] for c in taxonomy["categories"] if event["review_number"] in c["review_numbers"]]
        if event["failure_categories"] != tags or (event["verdict"] == "fail") != bool(tags):
            raise ValueError("Failure coding and verdict disagree")
        if event["first_failure"] != taxonomy["first_failure"].get(str(event["review_number"])):
            raise ValueError("First failure differs from the coding record")
        if (tags and event["first_failure"] not in tags) or (not tags and event["first_failure"] is not None):
            raise ValueError("Each failed trace needs one first failure from its own categories")
    summary["overall_assistant_judgments"] = dict(Counter(e["verdict"] for e in events))
    summary["failure_categories"] = [{
        "id": c["id"], "title": c["title"],
        "traces": sum(c["id"] in e["failure_categories"] for e in events),
        "cases": len({e["case_id"] for e in events if c["id"] in e["failure_categories"]}),
        "first_failure_traces": sum(e["first_failure"] == c["id"] for e in events),
    } for c in taxonomy["categories"]]
    section_only = [e for e in events if e["failure_categories"] == ["omitted_completed_check"]]
    summary["section_rule_sensitivity"] = {
        "section_only_failures": [e["trace_id"] for e in section_only],
        "passes_if_section_only_failures_are_nonblocking": sum(e["verdict"] == "pass" for e in events) + len(section_only),
        "interpretation": "Alternative interpretation of the completed-work section only; the recorded verdicts are unchanged.",
    }
    paired = defaultdict(dict)
    for e in events:
        paired[e["case_id"]][e["variant"]] = e["verdict"]
    if any(set(p) != {"deployed", "minimal"} for p in paired.values()):
        raise ValueError("Each situation needs both prompt variants")
    summary["paired_outcomes"] = dict(Counter(
        "both_pass" if all(v == "pass" for v in p.values()) else
        "both_fail" if all(v == "fail" for v in p.values()) else
        "deployed_only_pass" if p.get("deployed") == "pass" else "minimal_only_pass"
        for p in paired.values()))
    return manifest, events, records, summary


def escaped(value):
    # Expose control-character damage instead of silently repairing model output.
    value = "".join(f"[U+{ord(c):04X}]" if ord(c) < 32 and c not in "\n\t" else c for c in str(value))
    return html.escape(value)


def render(assessment, manifest, events, records, summary):
    assessment = Path(assessment)
    titles = {c["id"]: c["title"] for c in summary["failure_categories"]}
    counts = summary["overall_assistant_judgments"]
    num_cases = len({e["case_id"] for e in events})
    deployed_passes = summary["variants"]["deployed"]["assistant"].get("pass", 0)
    minimal_passes = summary["variants"]["minimal"]["assistant"].get("pass", 0)
    pairs = summary["paired_outcomes"]
    categories = {c["id"]: c["traces"] for c in summary["failure_categories"]}
    sensitivity = summary["section_rule_sensitivity"]
    section_only_count = len(sensitivity["section_only_failures"])
    alternate_passes = sensitivity["passes_if_section_only_failures_are_nonblocking"]
    intro = (f"Reviewed all {len(events)} outputs from {num_cases} synthetic situations. "
             f"{counts.get('pass', 0)} Pass; {counts.get('fail', 0)} Fail. "
             "These are provisional assistant judgments, with zero human reviews.")
    findings = [
        f"Fix the missing-versus-none parts distinction first. {categories['missing_as_none']} outputs incorrectly assert that no parts were used.",
        f"Separate clarification from new maintenance advice. {categories['unsupported_action']} outputs add unsupported actions or falsely attribute them to the source.",
        f"Clarify the completed-work contract and empty-state wording. {categories['omitted_completed_check']} outputs omit a performed check; {section_only_count} fail solely for this section inconsistency.",
        "Investigate both invalid generations and reject unexpected control characters in report prose. Preserve failures when comparing subsequent changes.",
        "Use these development findings for targeted fixes, then evaluate reference retrieval separately. Reserve new source families before optimization; RAG is not part of this pilot.",
    ]
    comparison = (f"The current prompt passes {deployed_passes}/{num_cases} and the minimal prompt {minimal_passes}/{num_cases} in this batch. "
                  f"{pairs.get('both_pass', 0)} cases pass under both prompts, {pairs.get('both_fail', 0)} fail under both, "
                  f"{pairs.get('deployed_only_pass', 0)} pass only under the current prompt, and {pairs.get('minimal_only_pass', 0)} pass only under the minimal prompt. ")
    md = [f"# Frontline: assistant review of all {len(events)} outputs", "", intro, "", comparison +
          "This small, synthetic, assistant-reviewed development batch does not establish a general winner or production accuracy.", "",
          "## Findings", "", "| Finding | Outputs | Distinct cases | First failure |", "|---|---:|---:|---:|"]
    for c in summary["failure_categories"]:
        md.append(f"| {c['title']} | {c['traces']} | {c['cases']} | {c['first_failure_traces']} |")
    md += ["", ("Categories overlap; first-failure counts sum to the failed-output count. "
           f"{section_only_count} failures depend solely on requiring performed checks in completed_work because the application otherwise says no completed work is established. "
           f"Treating that issue as non-blocking would change the result to {alternate_passes} Pass / {len(events) - alternate_passes} Fail; it does not alter the recorded judgments."), "",
           "## What to fix next", ""] + [f"{i}. {text}" for i, text in enumerate(findings, 1)]
    md += ["", "## Review method", "",
           ("Read [the criteria and boundary decisions](rubric.md). Original open notes, three subsequent critique corrections, "
           "source/output fingerprints, and every final verdict are retained. Variant names and expected labels were omitted "
           "from the initial reading, but the assistant had prior authoring/development exposure. "
           "The paired consistency pass is not independent validation. Confidence is qualitative, not a probability."), "",
           "[Interactive reading view](report.html) · [Review events](reviews.jsonl) · [Computed summary](summary.json)", "",
           "## Every judgment", ""]
    cards = []
    for e in sorted(events, key=lambda x: (x["case_id"], x["variant"])):
        tid, record = e["trace_id"], records[e["trace_id"]]
        md += [f"### {tid}: {e['verdict'].upper()}", "", e["critique"], "",
               f"Confidence: {e['confidence']}. Structure: {e['structure']}.", ""]
        for proof in e["evidence"]:
            md.append(f"- {proof['source_id']}: “{proof['quote']}”")
        if e.get("boundary_note"):
            md += ["", "Boundary decision: " + e["boundary_note"]]
        if e["minor_notes"]:
            md += ["", "Minor improvements: " + " ".join(e["minor_notes"])]
        md += [""]
        sources = "".join(f"<article><h4>{escaped(s['id'])}</h4><p>{escaped(s['text'])}</p></article>" for s in record["input_sources"])
        raw = output_text(record)
        try:
            rendered_output = json.dumps(json.loads(raw), ensure_ascii=False, indent=2)
        except (TypeError, ValueError):
            rendered_output = raw or "No model output returned."
        # JSON serialization escapes C0 controls, making their exact code points visible.
        proofs = "".join(f"<li><strong>{escaped(p['source_id'])}:</strong> {escaped(p['quote'])}</li>" for p in e["evidence"])
        tags = "; ".join(titles[t] for t in e["failure_categories"]) or "No blocking failure identified"
        boundary = f"<p><strong>Boundary decision:</strong> {escaped(e['boundary_note'])}</p>" if e.get("boundary_note") else ""
        minor = f"<p><strong>Minor improvements:</strong> {escaped(' '.join(e['minor_notes']))}</p>" if e["minor_notes"] else ""
        cards.append(f"""<details class="case" id="{escaped(tid)}" data-verdict="{e['verdict']}" data-variant="{e['variant']}">
<summary><span class="badge {e['verdict']}">{e['verdict'].upper()}</span> {escaped(tid)} <span class="muted">{escaped(tags)}</span></summary>
<div class="case-body"><p>{escaped(e['critique'])}</p><p class="muted">Confidence: {e['confidence']} · Structure: {escaped(e['structure'])} · Assistant review</p>
<ul>{proofs}</ul>{boundary}{minor}<div class="columns"><section><h3>Original sources</h3>{sources}</section>
<section><h3>Recorded model output</h3><p class="muted">Original values, before validation. JSON escapes expose damaged control characters.</p><pre>{escaped(rendered_output)}</pre></section></div></div></details>""")
    table = "".join(f"<tr><td>{escaped(c['title'])}</td><td>{c['traces']}</td><td>{c['cases']}</td><td>{c['first_failure_traces']}</td></tr>" for c in summary["failure_categories"])
    page = """<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Frontline — assistant assessment</title><style>
:root{font:16px/1.55 system-ui,sans-serif;color:#392f27;background:#f6f1e9}*{box-sizing:border-box}body{margin:0}main{max-width:1250px;margin:auto;padding:2rem}h1{font-size:2rem}h2{margin-top:2rem}a{color:#75512f}p,li{max-width:85ch}.muted{color:#685c51;font-size:.88rem}table{border-collapse:collapse;width:100%}td,th{padding:.6rem;text-align:left;border-bottom:1px solid #d4c4b2}th{background:#e9ddcc}.table-wrap{overflow:auto}.filters{display:flex;gap:1rem;flex-wrap:wrap;align-items:end;margin:1rem 0}label{display:grid;gap:.3rem}input,select{font:inherit;color:inherit;background:#fffdf9;border:1px solid #bea88d;border-radius:5px;padding:.5rem}.case{background:#fffdf9;border:1px solid #d4c4b2;border-radius:7px;margin:.7rem 0}summary{cursor:pointer;padding:1rem}.case-body{padding:0 1rem 1rem}.badge{display:inline-block;padding:.1rem .5rem;border-radius:4px;font-size:.8rem;font-weight:700;margin-right:.5rem}.pass{background:#e2eadc;color:#29452c}.fail{background:#f0dcd6;color:#782e24}.columns{display:grid;grid-template-columns:1fr 1fr;gap:1rem}.columns section{min-width:0}pre{font:13px/1.5 ui-monospace,monospace;white-space:pre-wrap;overflow-wrap:anywhere;background:#f5eee4;padding:1rem;max-height:65vh;overflow:auto}article{border-bottom:1px solid #e3d6c6}article p{white-space:pre-wrap;overflow-wrap:anywhere}[hidden]{display:none!important}@media(max-width:760px){main{padding:1rem}.columns{grid-template-columns:1fr}h1{font-size:1.6rem}}@media print{.filters{display:none}pre{max-height:none}}
</style><main>"""
    page += f"<p class='muted'>Frontline · {escaped(manifest['recorded_at'][:10])} · {escaped(manifest['criteria_version'])}</p><h1>What the {len(events)} reports actually got right and wrong</h1>"
    page += f"<p>{escaped(intro)}</p><p>The current prompt passes <strong>{deployed_passes}/{num_cases}</strong>; the minimal prompt passes <strong>{minimal_passes}/{num_cases}</strong>. These are development observations, not production accuracy or an independently validated model ranking.</p>"
    page += f"<h2>Recurring failures</h2><div class='table-wrap'><table><thead><tr><th>Finding</th><th>Outputs</th><th>Cases</th><th>First failure</th></tr></thead><tbody>{table}</tbody></table></div>"
    page += f"<p class='muted'>Categories overlap. {section_only_count} outputs fail only because completed checks are missing from the work section and the app displays an incorrect no-work message. Treating that section issue as non-blocking gives {alternate_passes} Pass / {len(events) - alternate_passes} Fail.</p>"
    page += "<h2>What to fix next</h2><ol>" + "".join(f"<li>{escaped(x)}</li>" for x in findings) + "</ol>"
    page += "<details><summary>Method and limits</summary><p>The assistant read every source packet and output, wrote open notes, checked paired cases consistently, and then grouped failures. The assistant also helped develop the app and corpus. Its review is provisional; no independent human validation, live media evaluation, retrieval test, or production study is implied. Three critique corrections are preserved. Pass allows minor presentation improvements. Full criteria and provenance are stored beside this report in the repository.</p></details>"
    page += """<h2>Inspect any judgment</h2><div class="filters"><label>Verdict<select id="verdict"><option value="">All</option><option>fail</option><option>pass</option></select></label><label>Prompt<select id="variant"><option value="">Both</option><option>deployed</option><option>minimal</option></select></label><label>Find text<input id="query" type="search" placeholder="Case, part, source, or critique"></label><span id="count" role="status"></span></div>"""
    page += "".join(cards)
    page += """</main><script>
const cases=[...document.querySelectorAll('.case')],v=document.getElementById('verdict'),p=document.getElementById('variant'),q=document.getElementById('query');
function filter(){let n=0;for(const c of cases){c.hidden=Boolean((v.value&&c.dataset.verdict!==v.value)||(p.value&&c.dataset.variant!==p.value)||(q.value&&!c.textContent.toLowerCase().includes(q.value.toLowerCase())));if(!c.hidden)n++;}document.getElementById('count').textContent=n+' of '+cases.length+' outputs';}
for(const x of [v,p,q])x.addEventListener('input',filter);filter();if(location.hash){const c=document.getElementById(decodeURIComponent(location.hash.slice(1)));if(c?.classList.contains('case'))c.open=true;}
</script></html>"""
    (assessment / "report.md").write_text("\n".join(md))
    (assessment / "report.html").write_text(page)
    (assessment / "summary.json").write_text(json.dumps(summary, indent=2) + "\n")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run", type=Path, required=True)
    parser.add_argument("--assessment", type=Path, required=True)
    args = parser.parse_args()
    data = load_assessment(args.run, args.assessment)
    render(args.assessment, *data)
    print(json.dumps({"reviewed": len(data[1]), "human_reviews": 0, "verdicts": data[3]["overall_assistant_judgments"]}))
