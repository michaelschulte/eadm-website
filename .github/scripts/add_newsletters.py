"""Turn newly uploaded newsletter PDFs into an archive entry, a cover image
and a News post.

Contributors only upload ``files/YYYY/MM/EADM-Newsletter-YYYY-MM.pdf``
(see CONTRIBUTING.md); a doubled ``.pdf.pdf`` or a different folder is
tolerated (see find_pending). For every issue that ``newsletter/index.qmd``
does not list yet, this script:

1. renders page one as ``images/YYYY/MM/eadm-newsletter-YYYY-MM.png``
   (needs ``pdftoppm`` from poppler-utils);
2. adds a line for the issue at the top of ``newsletter/index.qmd``;
3. writes ``news/posts/eadm-newsletter-YYYY-MM.qmd`` in the format of
   the earlier newsletter posts. The intro sentence and the "In this
   issue" list are written by the OpenAI API from the PDF; without an
   OPENAI_API_KEY, or if the call fails, the post gets a short generic
   text instead, so publishing never blocks on the API.

Detection compares files on disk with the archive page rather than a git
diff, so running it again does nothing, and a missed run catches up.

The publish workflow runs it on every push to main. Locally:

    python3 .github/scripts/add_newsletters.py --list     # what is pending
    python3 .github/scripts/add_newsletters.py            # do it
    python3 .github/scripts/add_newsletters.py --no-ai    # skip the API
"""

from __future__ import annotations

import argparse
import base64
import calendar
import datetime as dt
import os
import re
import subprocess
import sys
import textwrap
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
ARCHIVE = Path("newsletter/index.qmd")
# File name only; folders are checked separately. Accepts ".pdf.pdf" and
# any case of the extension.
NAME_RE = re.compile(r"^EADM-Newsletter-(\d{4})-(\d{2})(?:\.pdf)+$", re.IGNORECASE)
MODEL = "gpt-5.5"  # override with the OPENAI_MODEL environment variable


@dataclass(frozen=True)
class Issue:
    year: int
    month: int
    pdf: str  # repository-relative path, e.g. files/2026/11/EADM-Newsletter-2026-11.pdf

    @property
    def slug(self) -> str:
        return f"eadm-newsletter-{self.year}-{self.month:02d}"

    @property
    def month_year(self) -> str:  # "November 2026"
        return f"{calendar.month_name[self.month]} {self.year}"

    @property
    def archive_label(self) -> str:  # "2026 November", as in the archive list
        return f"{self.year} {calendar.month_name[self.month]}"

    @property
    def cover(self) -> str:
        return f"images/{self.year}/{self.month:02d}/{self.slug}.png"

    @property
    def post(self) -> str:
        return f"news/posts/{self.slug}.qmd"


# --------------------------------------------------------------------------
# Detection


def find_pending(root: Path) -> list[Issue]:
    """PDFs named EADM-Newsletter-YYYY-MM.pdf whose issue is not in the
    archive yet, oldest first.

    Uploads are forgiving where the intent is clear: a doubled extension
    (``.pdf.pdf``, from Windows hiding ".pdf") or a PDF outside
    ``files/YYYY/MM/`` is used where it is, since this repository can't
    rename files in the files/ submodule. The issue's year and month come
    from the file name. If the same issue was uploaded more than once,
    the copy at the expected path wins, else the first in sorted order.
    Other names are reported and skipped."""
    archive = (root / ARCHIVE).read_text(encoding="utf-8")
    found: dict[tuple[int, int], list[str]] = {}
    for path in sorted((root / "files").rglob("*")):
        name = path.name.lower()
        if not (path.is_file() and name.endswith(".pdf") and "newsletter" in name):
            continue
        rel = path.relative_to(root).as_posix()
        if f"/{rel}" in archive:
            continue
        m = NAME_RE.match(path.name)
        if not m:
            # Old PDFs with other names are all linked from the archive
            # already, so anything reaching this point is a new upload.
            print(f"warning: skipping {rel}: name must be "
                  "EADM-Newsletter-YYYY-MM.pdf", file=sys.stderr)
            continue
        year, month = int(m[1]), int(m[2])
        if not 1 <= month <= 12:
            print(f"warning: skipping {rel}: {m[1]}-{m[2]} is not a month",
                  file=sys.stderr)
            continue
        found.setdefault((year, month), []).append(rel)

    pending = []
    for (year, month), paths in sorted(found.items()):
        issue = Issue(year, month, "")
        expected = f"files/{year}/{month:02d}/EADM-Newsletter-{year}-{month:02d}.pdf"
        if f">{issue.archive_label}</a>" in archive or (root / issue.post).exists():
            for rel in paths:
                print(f"warning: skipping {rel}: the {issue.month_year} issue "
                      "is already in the archive", file=sys.stderr)
            continue
        chosen = expected if expected in paths else paths[0]
        if chosen != expected:
            print(f"note: using {chosen} where it is; the expected name "
                  f"is {expected}", file=sys.stderr)
        for rel in paths:
            if rel != chosen:
                print(f"warning: skipping {rel}: another copy of the "
                      f"{issue.month_year} issue, {chosen}, is used",
                      file=sys.stderr)
        pending.append(Issue(year, month, chosen))
    return pending


# --------------------------------------------------------------------------
# Archive page


def add_to_archive(root: Path, issue: Issue) -> None:
    """Insert the issue's link as the first entry after the front matter."""
    path = root / ARCHIVE
    text = path.read_text(encoding="utf-8")
    line = f'<a href="/{issue.pdf}">{issue.archive_label}</a>'
    end = text.index("---", 3) + 3  # end of the YAML front matter
    head, body = text[:end], text[end:].lstrip("\n")
    path.write_text(f"{head}\n\n{line}\n\n{body}", encoding="utf-8")


# --------------------------------------------------------------------------
# Cover image


def render_cover(root: Path, issue: Issue) -> None:
    """Page one as a PNG, 1191 px wide like the existing covers."""
    out = root / issue.cover
    if out.exists():
        return
    out.parent.mkdir(parents=True, exist_ok=True)
    subprocess.run(
        ["pdftoppm", "-png", "-f", "1", "-l", "1", "-singlefile",
         "-scale-to-x", "1191", "-scale-to-y", "-1",
         str(root / issue.pdf), str(out.with_suffix(""))],
        check=True,
    )


# --------------------------------------------------------------------------
# Summary from the OpenAI API

SYSTEM = """\
You write the short News-page announcement for a new issue of the EADM
Newsletter (European Association for Decision Making). You get the
newsletter as a PDF and return:

- intro: one or two sentences in plain English that start with
  "The <Month Year> issue of the EADM Newsletter" and name its one or two
  main topics. Factual, no hype, no exclamation marks, no Markdown.
  Do not end with "In this issue:"; that is added for you.
- contents: the newsletter's sections in the order they appear, using
  the section titles as printed (fix only obvious typos or ALL CAPS).
  Where a section is written by a named person, add " – <Name>" (with an
  en dash). Put sub-articles of a section into its subitems; most
  sections have none. Leave out the cover, the table of contents itself,
  and boilerplate such as contact details.

Two earlier announcements, for style:

The November 2025 issue of the EADM Newsletter looks back at SPUDM 2025
in Lucca and honours Karl Halvor Teigen with the EADM Lifetime
Contribution Award.
1. SPUDM 2025 Summary
    - Reflections from the EADM President – Mandeep K Dhami
    - Students' Perspectives on SPUDM 2025
2. EADM Lifetime Contribution Award – Karl Halvor Teigen
3. The Brunswik Society 31st International Meeting (Virtual)

The November 2024 issue of the EADM Newsletter, with the call for award
nominations and the SPUDM 2025 call for papers.
1. EADM Awards: call for nominations
2. EADM open vacancies
3. SPUDM 2025 Lucca, Italy: call for papers
"""


def summarize(root: Path, issue: Issue):
    """Return (intro, contents) from the OpenAI API, or None to use the
    generic text."""
    if not os.environ.get("OPENAI_API_KEY"):
        print("note: OPENAI_API_KEY not set; using the generic post text",
              file=sys.stderr)
        return None
    try:
        import openai
        from pydantic import BaseModel
    except ImportError:
        print("note: the openai package is not installed; "
              "using the generic post text", file=sys.stderr)
        return None

    class Section(BaseModel):
        title: str
        subitems: list[str]

    class Summary(BaseModel):
        intro: str
        contents: list[Section]

    pdf_b64 = base64.standard_b64encode((root / issue.pdf).read_bytes()).decode()
    model = os.environ.get("OPENAI_MODEL") or MODEL
    client = openai.OpenAI()
    try:
        response = client.responses.parse(
            model=model,
            instructions=SYSTEM,
            input=[{
                "role": "user",
                "content": [
                    {"type": "input_file",
                     "filename": Path(issue.pdf).name,
                     "file_data": f"data:application/pdf;base64,{pdf_b64}"},
                    {"type": "input_text",
                     "text": f"This is the {issue.month_year} issue. "
                             "Write its announcement."},
                ],
            }],
            text_format=Summary,
        )
    except openai.OpenAIError as e:
        print(f"warning: OpenAI API call failed ({e}); "
              "using the generic post text", file=sys.stderr)
        return None
    s = response.output_parsed
    if response.status != "completed" or s is None:
        print(f"warning: OpenAI API returned status {response.status} "
              f"(response {response.id}) without a summary; "
              "using the generic post text", file=sys.stderr)
        return None
    if not s.intro.strip() or not s.contents:
        return None
    return s.intro.strip(), [(c.title.strip(), [x.strip() for x in c.subitems])
                             for c in s.contents]


# --------------------------------------------------------------------------
# News post


def render_post(issue: Issue, date: dt.date, summary) -> str:
    alt = f"Cover page of the EADM Newsletter, {issue.month_year}"
    if summary:
        intro, contents = summary
        intro = intro.rstrip() + " In this issue:"
        lines = []
        for n, (title, subitems) in enumerate(contents, 1):
            lines.append(f"{n}. {title}")
            lines += [f"    - {s}" for s in subitems]
        body = textwrap.fill(intro, 72) + "\n\n" + "\n".join(lines)
    else:
        body = (f"The {issue.month_year} issue of the EADM Newsletter "
                "is out.")
    return f"""---
title: "EADM Newsletter, {issue.month_year}"
date: {date.isoformat()}
categories: ["Newsletter"]
image: /{issue.cover}
image-alt: "{alt}"
---

{body}

[![](/{issue.cover}){{.eadm-newsletter-cover fig-alt="{alt}"}}](/{issue.pdf})

[Read the full newsletter (PDF)](/{issue.pdf}) ·
[Newsletter archive](/newsletter/index.qmd)
"""


def write_post(root: Path, issue: Issue, date: dt.date, use_ai: bool) -> None:
    path = root / issue.post
    if path.exists():  # never overwrite a post someone has edited
        return
    summary = summarize(root, issue) if use_ai else None
    path.write_text(render_post(issue, date, summary), encoding="utf-8")


# --------------------------------------------------------------------------


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--list", action="store_true",
                    help="only print the pending PDFs, change nothing")
    ap.add_argument("--no-ai", action="store_true",
                    help="use the generic post text instead of the OpenAI API")
    ap.add_argument("--date", type=dt.date.fromisoformat,
                    default=dt.date.today(), help="post date (YYYY-MM-DD)")
    ap.add_argument("--root", type=Path, default=ROOT, help=argparse.SUPPRESS)
    args = ap.parse_args(argv)

    pending = find_pending(args.root)
    for issue in pending:
        print(issue.pdf)
    if args.list:
        return 0
    for issue in pending:  # oldest first, so the newest ends up on top
        render_cover(args.root, issue)
        write_post(args.root, issue, args.date, use_ai=not args.no_ai)
        add_to_archive(args.root, issue)
        print(f"added {issue.month_year}: {issue.post}, {issue.cover}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
