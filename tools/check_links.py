"""Verifies that internal links resolve, in two independent passes.

check_sources() scans every .qmd file for root-relative links and image
references (the '/images/...', '/files/...', and '/section/page.qmd'
paths produced by transform.py) and verifies each resolves to a real
file in the repo.

check_rendered_html() scans the rendered site under _site/ and verifies
that every same-origin href in the emitted HTML resolves to a real file
under _site/. The source check alone cannot catch a link that is
syntactically fine in the .qmd but has no rendered target -- e.g. an
extensionless href="/membership/index", which the source check happily
resolves to membership/index.qmd while the rendered page 404s.

External (http/https/mailto) links are not checked -- they're outside
this migration's control.
"""

import html as html_lib
import re
import sys
from pathlib import Path
from urllib.parse import unquote, urlparse

REPO_ROOT = Path(__file__).parent.parent
SITE_ROOT = REPO_ROOT / "_site"
REF_RE = re.compile(r'(?:href|src)="(/[^"]+)"')
HTML_REF_RE = re.compile(r'(?:href|src)="([^"]*)"')
_EXTERNAL_SCHEME_RE = re.compile(r"^[a-zA-Z][a-zA-Z0-9+.-]*:")
# 'www.python.org', 'apple.com' -- schemeless external links inherited from
# the WordPress content. A browser resolves these relative to the current
# page, but they were plainly meant as external and are not this
# migration's to fix, so they're classed external rather than broken.
_HOSTNAME_LIKE_RE = re.compile(r"^[A-Za-z0-9-]+(?:\.[A-Za-z0-9-]+)+$")
# Final components that mark a hostname-looking first segment as really
# being a file ('contact.html', 'report.pdf') rather than a domain.
_WEB_FILE_EXTENSIONS = {
    "html", "htm", "qmd", "md", "pdf", "txt", "csv", "json", "xml",
    "png", "jpg", "jpeg", "gif", "svg", "webp", "ico",
    "css", "js", "zip", "doc", "docx", "ppt", "pptx", "xls", "xlsx",
    "mp3", "mp4",
}


def resolve(ref: str) -> Path:
    path = ref.lstrip("/")
    candidate = REPO_ROOT / path
    if candidate.suffix == "" and (REPO_ROOT / f"{path}.qmd").exists():
        return REPO_ROOT / f"{path}.qmd"
    return candidate


def check_sources():
    """Returns a list of (source_file, ref) for unresolved .qmd references."""
    broken = []
    for qmd in REPO_ROOT.rglob("*.qmd"):
        if "_extracted" in qmd.parts or "_site" in qmd.parts:
            continue
        text = qmd.read_text()
        for match in REF_RE.finditer(text):
            ref = match.group(1)
            target = resolve(ref)
            if not target.exists():
                broken.append((str(qmd.relative_to(REPO_ROOT)), ref))
    return broken


def _is_internal(href: str) -> bool:
    """True for same-origin references worth resolving on disk.

    Excludes absolute URLs (any scheme, including mailto:/data:),
    protocol-relative //host/path, pure in-page fragments, inline data
    URIs (including the 'posts/data:image/...;base64,' form Quarto emits
    when a listing thumbnail comes from an inline base64 image), and
    schemeless external links like 'www.python.org'.
    """
    if not href or href.startswith("#") or href.startswith("//"):
        return False
    if _EXTERNAL_SCHEME_RE.match(href):
        return False
    if "data:" in href or ";base64," in href:
        return False
    first = href.split("/", 1)[0]
    if _HOSTNAME_LIKE_RE.match(first):
        if first.rsplit(".", 1)[-1].lower() not in _WEB_FILE_EXTENSIONS:
            return False
    return True


def check_rendered_html():
    """Returns a list of (html_file, href) for internal hrefs in _site/
    that don't resolve to a real file, plus a count of files scanned.
    """
    broken = []
    html_files = sorted(SITE_ROOT.rglob("*.html"))
    for html in html_files:
        if "site_libs" in html.parts:
            continue
        text = html.read_text(errors="replace")
        for match in HTML_REF_RE.finditer(text):
            raw = html_lib.unescape(match.group(1).strip())
            if not _is_internal(raw):
                continue
            # Strip query/fragment, then percent-decode to a real path.
            path_part = unquote(urlparse(raw).path)
            if not path_part:
                continue
            if path_part.startswith("/"):
                target = SITE_ROOT / path_part.lstrip("/")
            else:
                target = (html.parent / path_part).resolve()
            # A directory reference serves its index.html.
            if target.is_dir():
                target = target / "index.html"
            if not target.exists():
                broken.append((str(html.relative_to(SITE_ROOT)), raw))
    return broken, len(html_files)


def _report(label, broken):
    if broken:
        print(f"{label}: {len(broken)} broken reference(s):")
        for source, ref in broken:
            print(f"  {source} -> {ref}")
        return False
    print(f"{label}: no broken internal references found.")
    return True


def main():
    ok = _report("source .qmd files", check_sources())

    if not SITE_ROOT.is_dir():
        print(
            "rendered HTML: _site/ not found -- run `quarto render` first "
            "to enable the rendered-link check."
        )
        sys.exit(0 if ok else 1)

    broken_html, scanned = check_rendered_html()
    ok = _report(f"rendered HTML ({scanned} files in _site/)", broken_html) and ok

    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
