"""Copy a complete synthetic run into a reviewable bundle; no network writes."""

import argparse
import json
import re
import shutil
from pathlib import Path


def export_run(source, destination):
    source, destination = Path(source), Path(destination)
    manifest = json.loads((source / "manifest.json").read_text())
    if manifest["status"] != "finished" or len(manifest["completed"]) != manifest["planned_requests"]:
        raise ValueError("Only complete runs can be exported; failed outputs are retained")
    if source.name != destination.name:
        raise ValueError("Keep the original run directory name so review identities remain stable")
    names = ["manifest.json", "prepared-requests.json", "review-order.json"]
    if (source / "manifest.initial-segment.json").exists():
        names.append("manifest.initial-segment.json")
    if (source / "environment.json").exists():
        names.append("environment.json")
    for trace_id in manifest["completed"]:
        if not re.fullmatch(r"[A-Za-z0-9_-]+", trace_id):
            raise ValueError("Unsafe trace ID")
        names.append(trace_id + ".json")
    names.extend(path.name for path in source.glob("*.snapshot"))
    destination.mkdir(parents=True, exist_ok=False)
    for name in names:
        shutil.copyfile(source / name, destination / name)
    (destination / "README.md").write_text(
        "Frontline recorded report evaluation\n"
        "====================================\n\n"
        "This bundle preserves all " + str(manifest["planned_requests"]) +
        " recorded requests, including structural failures. It contains synthetic source observations "
        "and generated outputs, not production user records. Human review journals are not included.\n\n" +
        ("The two variants differ only in the system instruction. " if manifest.get("selected_variant", "both") == "both"
         else "This run captures one instruction variant; any historical comparison is described in the manifest. ") +
        "Model requests, source data, "
        "settings, and code snapshots are retained. The initial reference labels are AI-authored "
        "and provisional. This is development data, not a held-out quality benchmark.\n\n"
        "Use the local review tool and evaluation method in the repository to inspect the traces. "
        "The source-corpus attribution and CC-BY-SA-4.0 terms are recorded in "
        "../../corpus/README.md and the corpus snapshot. No semantic winner is declared by this export.\n"
    )
    return len(manifest["completed"])


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    print("Exported " + str(export_run(args.run, args.output)) + " traces.")
