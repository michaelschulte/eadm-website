"""Scans every .qmd file for root-relative links and image references
(the '/images/...', '/files/...', and '/section/page' paths produced by
transform.py) and verifies each resolves to a real file in the repo.
External (http/https) links are not checked -- they're outside this
migration's control.
"""

import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).parent.parent
REF_RE = re.compile(r'(?:href|src)="(/[^"]+)"')


def resolve(ref: str) -> Path:
    path = ref.lstrip("/")
    candidate = REPO_ROOT / path
    if candidate.suffix == "" and (REPO_ROOT / f"{path}.qmd").exists():
        return REPO_ROOT / f"{path}.qmd"
    return candidate


def main():
    broken = []
    for qmd in REPO_ROOT.rglob("*.qmd"):
        if "_extracted" in qmd.parts:
            continue
        text = qmd.read_text()
        for match in REF_RE.finditer(text):
            ref = match.group(1)
            target = resolve(ref)
            if not target.exists():
                broken.append((str(qmd.relative_to(REPO_ROOT)), ref))

    if broken:
        print(f"{len(broken)} broken reference(s):")
        for source, ref in broken:
            print(f"  {source} -> {ref}")
        sys.exit(1)
    print("No broken internal references found.")


if __name__ == "__main__":
    main()
