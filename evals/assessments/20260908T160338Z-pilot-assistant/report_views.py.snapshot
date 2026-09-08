"""Evidence report presentation; model output and reviewer notes stay separate."""

import json

from fasthtml.common import (
    A,
    Details,
    Div,
    Form,
    Input,
    Li,
    Option,
    P,
    Pre,
    Select,
    Small,
    Strong,
    Summary,
    Textarea,
    Ul,
)
from monsterui.all import (
    H1,
    H2,
    H3,
    Button,
    ButtonT,
    Card,
    CardBody,
    CardHeader,
    Container,
    ContainerT,
    TextPresets,
)


def evidence_report_view(record):
    report = json.loads(record.evidence_json)
    sources = json.loads(record.sources_json)
    source_numbers = {source["id"]: i + 1 for i, source in enumerate(sources)}

    def citations(ids):
        return [A(f"[{source_numbers[source_id]}]", href=f"#source-{source_numbers[source_id]}",
                  cls="source-citation", title="Read supporting source") for source_id in ids]

    def claims(title, items, empty):
        return Card(
            CardHeader(H3(title)),
            CardBody(Ul(*(Li("Clarification: " if item.get("basis") == "clarification" else "",
                            item["text"], " ", *citations(item["source_ids"]), cls="mb-3") for item in items))
                     if items else P(empty, cls=TextPresets.muted_sm)),
            body_cls="p-0", cls="mb-4",
        )

    def value(label, item):
        text = item["value"] if item["state"] == "known" else {"unknown": "Not recorded", "conflicting": "Conflicting sources"}[item["state"]]
        return P(Strong(label + ": "), text, " ", *citations(item["source_ids"]))

    parts = report["parts_used"]
    parts_description = {
        "unknown": "The sources do not establish whether parts were used.",
        "none": "The sources explicitly record that no parts were fitted.",
        "conflicting": "The sources disagree about parts use. No installation is asserted.",
    }
    parts_body = (Ul(*(Li(Strong(p["part_number"]),
                          f" — quantity {p['quantity']}" if p["quantity"] is not None else " — quantity not recorded",
                          " ", *citations(p["source_ids"])) for p in parts["items"]))
                  if parts["state"] == "known"
                  else P(parts_description[parts["state"]], " ", *citations(parts["source_ids"])))
    source_cards = []
    for i, source in enumerate(sources, 1):
        origin = source.get("origin", "user")
        origin_label = {"user": "Written note", "groq_audio": "AI transcript — review against the recording",
                        "groq_image": "AI image description — review against the image",
                        "user_edited": "User-edited source text", "synthetic": "Synthetic example note"}.get(origin, origin)
        source_cards.append(
            Details(Summary(f"[{i}] {source.get('filename', 'Source')}"),
                    P(origin_label, cls=TextPresets.muted_sm),
                    Pre(source["text"], cls="source-text"),
                    id=f"source-{i}", open=True, cls="source-panel")
        )
    return Container(
        H1(record.title),
        P("Draft for review. Check the cited evidence before using this report.", cls=TextPresets.muted_sm),
        Card(CardBody(value("Equipment", report["equipment_id"]),
                      value("Priority", report["priority"]),
                      value("Next service date", report["next_service_date"])),
             body_cls="p-0", cls="my-4"),
        claims("Observations", report["observations"], "No observations recorded."),
        claims("Completed work", report["completed_work"], "No completed work is established by these sources."),
        Card(CardHeader(H3("Parts used")), CardBody(parts_body), body_cls="p-0", cls="mb-4"),
        claims("Proposed actions", report["proposed_actions"], "No proposed actions recorded."),
        claims("Uncertainties and disagreements", report["uncertainties"], "No additional disagreements were identified; fields marked “Not recorded” remain unknown."),
        Card(CardHeader(H3("Reviewer notes")),
             CardBody(P(record.review_notes or "No reviewer notes yet.", cls="source-text"),
                      Button("Edit title and reviewer notes", hx_get=f"/content/edit-report/{record.id}",
                             hx_target="#main-content", cls=ButtonT.secondary)),
             body_cls="p-0", cls="mb-4"),
        H2("Sources used for this report"),
        P("This snapshot preserves the text used at generation time. Later edits to workspace inputs do not change it.", cls=TextPresets.muted_sm),
        *source_cards,
        Small(f"Generated with {record.model_id or 'an earlier model'} · {record.created_at[:10]}",
              cls=TextPresets.muted_sm),
        Div(Button("Open workspace", hx_get=f"/content/workspace/{record.workspace_id}",
                   hx_target="#main-content", cls=ButtonT.primary), cls="mt-4"),
        cls=ContainerT.lg,
    )


def evidence_report_editor(record):
    return Container(
        H1("Review report"),
        P("The generated findings and source snapshot are preserved. Add your corrections or interpretation in reviewer notes."),
        Form(
            P(Strong("Title")),
            Input(name="title", value=record.title, maxlength=160, required=True),
            P(Strong("Reviewer notes")),
            Textarea(record.review_notes, name="review_notes", rows=8, maxlength=6000, cls="w-full"),
            P(Strong("Status")),
            Select(*(Option(label, value=value, selected=record.status == value) for value, label in
                     (("open", "Open"), ("in_progress", "In progress"), ("completed", "Completed"), ("closed", "Closed"))),
                   name="status"),
            Button("Save review", type="submit", cls=ButtonT.primary),
            Button("Cancel", type="button", hx_get=f"/content/view-report/{record.id}",
                   hx_target="#main-content", cls=ButtonT.secondary),
            hx_post=f"/update-report-content/{record.id}", hx_target="#main-content", cls="space-y-4 mt-6",
        ),
        cls=ContainerT.lg,
    )
