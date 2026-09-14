# EADM Website Migration Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Turn the WordPress export of https://eadm.eu into a working, modern, easily-restyleable Quarto website in a new repo at `/Users/michael/git_stuff/eadm-website/`, committed to git and pushed to a new public GitHub repo.

**Architecture:** A one-time Python ETL (`tools/`) pulls curated content out of a scratch MariaDB import of the WordPress database as JSON, rewrites internal links and media references, and writes `.qmd` files straight into the Quarto project tree. Hand-written files cover the parts that aren't 1:1 WordPress migrations (Home page, the three blog listing indexes, `_quarto.yml`, `_brand.yml`). The site never needs a database at runtime — it's fully static once rendered.

**Tech Stack:** Quarto 1.9 (website project), Python 3 stdlib only (no pip installs required), Docker (scratch MariaDB 10.11 container for querying the dump), `gh` CLI for the GitHub push.

**Spec:** `docs/superpowers/specs/2026-09-14-eadm-website-migration-design.md`

## Global Constraints

- Source WordPress export lives at `/Users/michael/git_stuff/wp_eadm/eadm-eu-20260914-054440-ujh0nuxckrsu/` — **read-only**, never modified, never `git add`ed anywhere.
- The new project's own `git init` happens only in `/Users/michael/git_stuff/eadm-website/` — never in `/Users/michael/git_stuff/wp_eadm/` (that directory holds a 3.2GB `.wpress` backup and a 493MB raw `uploads/` export that must never enter any git history).
- All 73 PDF attachments are vendored into the repo as-is (no Git LFS) — confirmed no single file exceeds 60MB, well under GitHub's 100MB hard limit.
- Images: only the largest on-disk rendition of each WordPress-generated size family is copied; WordPress thumbnail-size duplicates (`-150x150`, `-1024x682`, etc.) are dropped.
- Design must be easy to re-skin: colors/fonts live in `_brand.yml`, the Bootswatch base theme name is a single key in `_quarto.yml`, and custom CSS lives in one `styles.scss` layered on top — never hardcoded into page content.
- WordPress content is stored as blank-line-separated plain text with a few embedded HTML tags (verified: Pandoc's HTML reader collapses these paragraphs, so it is **not** run through Pandoc). It is used near-verbatim as the `.qmd` body — Quarto/Pandoc's Markdown renderer passes the embedded raw HTML straight through (verified).
- `mysql` CLI must be invoked with `-N -B -r` (raw mode) when reading JSON output — verified that plain `-N -B` double-escapes backslashes inside `JSON_OBJECT()` output and corrupts the JSON.
- Quarto silently produces an empty `_site/` with exit code 0 if the project root directory's own name starts with a dot (verified) — never scaffold or test under a dot-prefixed directory.

---

## Task 1: Project scaffold — `_quarto.yml`, `_brand.yml`, theme, navbar

**Files:**
- Create: `/Users/michael/git_stuff/eadm-website/_quarto.yml`
- Create: `/Users/michael/git_stuff/eadm-website/_brand.yml`
- Create: `/Users/michael/git_stuff/eadm-website/styles.scss`
- Create: `/Users/michael/git_stuff/eadm-website/.gitignore`
- Create: `/Users/michael/git_stuff/eadm-website/index.qmd`

**Interfaces:**
- Produces: the navbar hrefs below are a contract — every later task that creates content must land at exactly these paths, or the navbar links break.

- [ ] **Step 1: Write `_quarto.yml`**

```yaml
project:
  type: website
  brand: _brand.yml

website:
  title: "EADM"
  site-url: "https://eadm.eu"
  description: "The European Association for Decision Making"
  navbar:
    left:
      - href: index.qmd
        text: Home
      - text: About EADM
        menu:
          - href: about/index.qmd
            text: About EADM
          - href: about/mission-statement.qmd
            text: Mission Statement
          - href: about/code-of-conduct.qmd
            text: Code of Conduct
          - href: about/executive-board.qmd
            text: Executive Board
          - href: about/past-executive-boards.qmd
            text: Past Executive Boards
          - href: presidents-column/index.qmd
            text: "President's Column"
          - href: contact.qmd
            text: Contact
      - text: Membership
        menu:
          - href: membership/index.qmd
            text: Membership
          - href: membership/mailing-list.qmd
            text: Mailing List
      - text: Funding
        menu:
          - href: funding/index.qmd
            text: EADM Funding
          - href: funding/jane-beattie-travel-scholarship.qmd
            text: Jane Beattie Travel Scholarship
          - href: funding/workshop-grants/index.qmd
            text: Workshop Grants
          - href: funding/summer-school/index.qmd
            text: EADM Summer School
      - text: Prizes
        menu:
          - href: prizes/index.qmd
            text: Prizes
          - href: prizes/de-finetti-prize.qmd
            text: De Finetti Award
          - href: prizes/jane-beattie-award.qmd
            text: Jane Beattie Scientific Recognition Award
          - href: prizes/eadm-lifetime-contribution-award.qmd
            text: Lifetime Contribution Award
      - text: SPUDM
        menu:
          - href: spudm/index.qmd
            text: SPUDM
          - href: spudm/history.qmd
            text: History
          - href: spudm/past-conferences.qmd
            text: Past Conferences
          - href: spudm/spudm-2013.qmd
            text: "SPUDM 2013"
          - href: spudm/images.qmd
            text: "SPUDM Images"
      - href: news/index.qmd
        text: News
      - href: newsletter/index.qmd
        text: Newsletter Archive
      - href: interviews/index.qmd
        text: "EADM Interview"
  page-footer: "[Contact](contact.qmd)"

format:
  html:
    theme:
      light: [zephyr, styles.scss]
      dark: [darkly, styles.scss]
    toc: false
    grid:
      body-width: 850px
```

(This exact `theme:`/`brand:`/navbar-dropdown combination was rendered end-to-end in a throwaway test project during design and confirmed to produce a working light/dark toggle with brand colors compiled into both CSS bundles.)

- [ ] **Step 2: Write `_brand.yml`**

```yaml
meta:
  name: EADM
  link: https://eadm.eu

color:
  palette:
    eadm-blue: "#1f4e79"
    eadm-slate: "#33424f"
    eadm-gray: "#5a6570"
  primary: eadm-blue
  secondary: eadm-slate
  foreground: eadm-gray
  background: "#ffffff"

typography:
  fonts:
    - family: Inter
      source: google
      weight: [400, 500, 600, 700]
    - family: "Source Serif 4"
      source: google
      weight: [400, 600]
  base:
    family: Inter
    size: 1rem
    line-height: 1.6
  headings:
    family: "Source Serif 4"
    weight: 600
    line-height: 1.25
  link:
    color: primary
    weight: 500
```

- [ ] **Step 3: Write `styles.scss`**

```scss
/*-- scss:rules --*/

.navbar {
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.08);
}

main.content {
  padding-top: 1.5rem;
}

.quarto-listing .listing-item {
  border-radius: 0.5rem;
}
```

- [ ] **Step 4: Write `.gitignore`**

```
_site/
.quarto/
/tools/_extracted/
.DS_Store
```

- [ ] **Step 5: Write `index.qmd` (Home page)**

```markdown
---
title: "EADM — European Association for Decision Making"
---

The European Association for Decision Making (EADM) is an interdisciplinary
organisation dedicated to the study of normative, descriptive, and
prescriptive theories of decision making. It has its origins in a Research
Conference on Subjective Probability, organised in 1969 by Wendt, Stael von
Holstein and Vlek in Hamburg, and was formally founded in August 1993.

## Get involved

- [About EADM](about/index.qmd) — history, mission, and the Executive Board
- [Membership](membership/index.qmd) — who can join and how
- [SPUDM](spudm/index.qmd) — the Association's biennial conference
- [News](news/index.qmd) and the [EADM Interview](interviews/index.qmd) series
- [Prizes](prizes/index.qmd) and [Funding](funding/index.qmd) opportunities
```

(`contact.qmd` is **not** hand-written here — it is WordPress page ID 176,
which Task 6's `transform.py` will generate from the real migrated content
at the repo root. Writing a placeholder here would just be clobbered by
Task 6; the navbar above already references `contact.qmd` at the path
Task 6 produces.)

- [ ] **Step 6: Verify the Home page renders**

Run: `cd /Users/michael/git_stuff/eadm-website && quarto render index.qmd`
Expected: `Output created: index.html` with no errors. Then remove the stray
output: `rm -f index.html && rm -rf index_files`.

(Full-project render is deferred to Task 8, once every navbar target file
exists — a project-level `quarto render` does not error on missing files
mid-navbar the same way, but there's no reason to check it before the
target pages exist.)

- [ ] **Step 7: Commit**

```bash
cd /Users/michael/git_stuff/eadm-website
git add _quarto.yml _brand.yml styles.scss .gitignore index.qmd
git commit -m "Scaffold Quarto project: navbar, brand theme, home page"
```

---

## Task 2: Content classification rules — `tools/content_map.py`

**Files:**
- Create: `/Users/michael/git_stuff/eadm-website/tools/content_map.py`
- Create: `/Users/michael/git_stuff/eadm-website/tools/test_content_map.py`

**Interfaces:**
- Produces: `resolve_target(item, categories_by_post_id) -> tuple[str, str] | None`, where `item` is `{"id": int, "type": "page"|"post", "slug": str}`. Returns `None` for dropped items, else `(section, filename)` with no leading/trailing slashes and no `.qmd` extension (`section` may be `""` for repo-root files like `contact`). Later tasks (`transform.py`) rely on exactly this signature.

- [ ] **Step 1: Write the failing test**

```python
# tools/test_content_map.py
import unittest

from content_map import DROP_IDS, PAGE_OVERRIDES, resolve_target


class TestContentMap(unittest.TestCase):
    def test_all_58_published_pages_are_classified(self):
        self.assertEqual(len(DROP_IDS), 23)
        self.assertEqual(len(PAGE_OVERRIDES), 35)
        self.assertEqual(len(DROP_IDS) + len(PAGE_OVERRIDES), 58)

    def test_no_duplicate_page_targets(self):
        targets = list(PAGE_OVERRIDES.values())
        self.assertEqual(len(targets), len(set(targets)))

    def test_dropped_page_returns_none(self):
        item = {"id": 442, "type": "page", "slug": "beispiel-seite"}
        self.assertIsNone(resolve_target(item, {}))

    def test_known_page_resolves_to_override(self):
        item = {"id": 93, "type": "page", "slug": "who-are-we"}
        self.assertEqual(resolve_target(item, {}), ("about", "index"))

    def test_unclassified_page_raises(self):
        item = {"id": 999999, "type": "page", "slug": "mystery"}
        with self.assertRaises(KeyError):
            resolve_target(item, {})

    def test_post_routes_by_category_priority(self):
        item = {"id": 900, "type": "post", "slug": "the-eadm-interview-adele-diederich"}
        cats = {900: {"EADM Interview", "Uncategorized"}}
        self.assertEqual(
            resolve_target(item, cats),
            ("interviews/posts", "the-eadm-interview-adele-diederich"),
        )

    def test_post_without_known_category_falls_back_to_news(self):
        item = {"id": 1, "type": "post", "slug": "some-old-post"}
        self.assertEqual(resolve_target(item, {}), ("news/posts", "some-old-post"))


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run the test to verify it fails**

Run: `cd /Users/michael/git_stuff/eadm-website && python3 tools/test_content_map.py`
Expected: `ModuleNotFoundError: No module named 'content_map'`

- [ ] **Step 3: Write `tools/content_map.py`**

```python
"""Classifies every published WordPress page/post into either a drop
decision or a target (section, filename) in the new Quarto site.

Every one of the 58 published WordPress pages is accounted for below,
either in DROP_IDS (with a reason) or PAGE_OVERRIDES (with its target).
Posts are routed by category instead, since there are 63 of them and
their WordPress slugs already make fine filenames.
"""

# WordPress page IDs to drop entirely, with the reason.
DROP_IDS = {
    442: "Beispiel-Seite -- WordPress-default German placeholder page",
    79: "Jobs -- empty page, zero content",
    650: "thanks -- empty post-payment redirect page",
    86: "News -- empty stub page, superseded by news/index.qmd listing",
    50: "Past Workshops -- empty stub page, not referenced in the live nav menu",
    331: "About EADM (about-eadm-2) -- byte-identical duplicate of page 93",
    404: "EADM (about-eadm) -- near-duplicate draft of page 93",
    1075: "EADM Summer Schools -- stale subset of page 167's fuller list",
    # 15 bio pages under the private 'The EADM Interview' parent (id 800),
    # each word-for-word identical to a published 'EADM Interview' post.
    903: "duplicate of EADM Interview post (Adele Diederich)",
    838: "duplicate of EADM Interview post (Benjamin Scheibehenne)",
    918: "duplicate of EADM Interview post (Bernadette Kamleitner)",
    1079: "duplicate of EADM Interview post (Bettina von Helversen)",
    983: "duplicate of EADM Interview post (Cornelia Betsch)",
    1106: "duplicate of EADM Interview post (Dirk Wulff)",
    828: "duplicate of EADM Interview post (Eyal Peer)",
    843: "duplicate of EADM Interview post (Iain D. Gilchrist)",
    740: "duplicate of EADM Interview post (Mandeep K. Dhami)",
    997: "duplicate of EADM Interview post (Nathaniel Phillips)",
    1108: "duplicate of EADM Interview post (Peter Wakker)",
    913: "duplicate of EADM Interview post (Robin Hogarth)",
    950: "duplicate of EADM Interview post (Rui Mata)",
    993: "duplicate of EADM Interview post (Sabine Scholl)",
    990: "duplicate of EADM Interview post (Tim Rakow)",
}

# WordPress page ID -> (section folder, filename without extension).
# section "" means the file lands at the repo root (e.g. contact.qmd).
PAGE_OVERRIDES = {
    93: ("about", "index"),
    156: ("about", "mission-statement"),
    1397: ("about", "code-of-conduct"),
    206: ("about", "executive-board"),
    203: ("about", "past-executive-boards"),
    142: ("about", "does-anyone-know-whats-going-on-out-there"),
    176: ("", "contact"),
    74: ("membership", "index"),
    183: ("membership", "mailing-list"),
    639: ("membership", "membership-payment"),
    646: ("membership", "membership-payment-instructions"),
    1405: ("newsletter", "index"),
    35: ("funding", "index"),
    41: ("funding", "jane-beattie-travel-scholarship"),
    357: ("funding", "small-group-meeting-efficient-science-2013"),
    47: ("funding/workshop-grants", "index"),
    167: ("funding/summer-school", "index"),
    1224: ("funding/summer-school", "2018-salzburg"),
    58: ("funding/workshop-grants", "decision-making-in-football"),
    55: ("funding/workshop-grants", "environmental-decisions-risks-and-uncertainties"),
    52: ("funding/workshop-grants", "intuition-methods-and-recent-findings"),
    71: ("funding/workshop-grants", "european-group-of-process-tracing-studies"),
    1048: ("funding/workshop-grants", "jdm-workshop-2013"),
    1154: ("funding/workshop-grants", "egproc-bonn-2016"),
    1256: ("funding/workshop-grants", "workshop-grants-2019"),
    1472: ("funding/workshop-grants", "workshop-2025-economic-inequality"),
    1385: ("prizes", "index"),
    37: ("prizes", "de-finetti-prize"),
    44: ("prizes", "jane-beattie-award"),
    1383: ("prizes", "eadm-lifetime-contribution-award"),
    21: ("spudm", "index"),
    586: ("spudm", "history"),
    316: ("spudm", "past-conferences"),
    23: ("spudm", "spudm-2013"),
    25: ("spudm", "images"),
}

# Post category name -> blog section, in priority order (first match wins;
# a post can carry more than one category).
POST_CATEGORY_SECTION = [
    ("News", "news"),
    ("President's Column", "presidents-column"),
    ("EADM Interview", "interviews"),
]
DEFAULT_POST_SECTION = "news"


def resolve_target(item, categories_by_post_id):
    """Return (section, filename) for a kept item, or None to drop it.

    item: {"id": int, "type": "page"|"post", "slug": str}
    categories_by_post_id: dict[int, set[str]] of category names by post id.
    Raises KeyError for a page that is in neither DROP_IDS nor
    PAGE_OVERRIDES -- every published page must be explicitly classified.
    """
    if item["id"] in DROP_IDS:
        return None
    if item["type"] == "page":
        if item["id"] not in PAGE_OVERRIDES:
            raise KeyError(
                f"page {item['id']} ({item['slug']!r}) is not classified in "
                "DROP_IDS or PAGE_OVERRIDES -- classify it explicitly"
            )
        return PAGE_OVERRIDES[item["id"]]
    categories = categories_by_post_id.get(item["id"], set())
    for name, section in POST_CATEGORY_SECTION:
        if name in categories:
            return (f"{section}/posts", item["slug"])
    return (f"{DEFAULT_POST_SECTION}/posts", item["slug"])
```

(The `DROP_IDS` dict above is written as `id: reason` for auditability, and
`PAGE_OVERRIDES` similarly maps directly to targets — both are plain dicts,
so `len()` and membership checks in the tests work as written.)

- [ ] **Step 4: Run the test to verify it passes**

Run: `cd /Users/michael/git_stuff/eadm-website && python3 tools/test_content_map.py -v`
Expected: 7 tests, all `ok`.

- [ ] **Step 5: Commit**

```bash
git add tools/content_map.py tools/test_content_map.py
git commit -m "Add content classification rules for WordPress migration"
```

---

## Task 3: Media resolution — `tools/media.py`

**Files:**
- Create: `/Users/michael/git_stuff/eadm-website/tools/media.py`
- Create: `/Users/michael/git_stuff/eadm-website/tools/test_media.py`

**Interfaces:**
- Produces: `strip_size_suffix(filename: str) -> str`, `find_best_local_file(rel_path: str, uploads_root: Path) -> Path | None`, `copy_and_get_url(rel_path: str, uploads_root: Path, images_out: Path, files_out: Path) -> str | None`. `rewrite.py` (Task 4) calls `copy_and_get_url`.

- [ ] **Step 1: Write the failing test**

```python
# tools/test_media.py
import tempfile
import unittest
from pathlib import Path

from media import copy_and_get_url, find_best_local_file, strip_size_suffix


class TestMedia(unittest.TestCase):
    def test_strip_size_suffix_removes_wp_thumbnail_dimensions(self):
        self.assertEqual(
            strip_size_suffix("AdeleDiederich-1024x682.jpg"), "AdeleDiederich.jpg"
        )

    def test_strip_size_suffix_is_a_noop_without_a_size_suffix(self):
        self.assertEqual(
            strip_size_suffix("Newsletter-Spring-2026-EADM.pdf"),
            "Newsletter-Spring-2026-EADM.pdf",
        )

    def test_find_best_local_file_picks_the_largest_variant(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            d = root / "2014" / "07"
            d.mkdir(parents=True)
            (d / "AdeleDiederich-150x150.jpg").write_bytes(b"x" * 100)
            (d / "AdeleDiederich-1024x682.jpg").write_bytes(b"x" * 5000)
            (d / "AdeleDiederich.jpg").write_bytes(b"x" * 20000)
            result = find_best_local_file("2014/07/AdeleDiederich-1024x682.jpg", root)
            self.assertEqual(result.name, "AdeleDiederich.jpg")

    def test_find_best_local_file_returns_none_when_missing(self):
        with tempfile.TemporaryDirectory() as tmp:
            self.assertIsNone(find_best_local_file("2099/01/missing.jpg", Path(tmp)))

    def test_copy_and_get_url_copies_image_into_images_out(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "uploads"
            d = root / "2014" / "07"
            d.mkdir(parents=True)
            (d / "Photo.jpg").write_bytes(b"x" * 1000)
            images_out = Path(tmp) / "images"
            files_out = Path(tmp) / "files"
            url = copy_and_get_url("2014/07/Photo.jpg", root, images_out, files_out)
            self.assertEqual(url, "/images/2014/07/Photo.jpg")
            self.assertTrue((images_out / "2014" / "07" / "Photo.jpg").exists())

    def test_copy_and_get_url_copies_pdf_into_files_out(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "uploads"
            d = root / "2026" / "04"
            d.mkdir(parents=True)
            (d / "Newsletter.pdf").write_bytes(b"x" * 1000)
            images_out = Path(tmp) / "images"
            files_out = Path(tmp) / "files"
            url = copy_and_get_url("2026/04/Newsletter.pdf", root, images_out, files_out)
            self.assertEqual(url, "/files/2026/04/Newsletter.pdf")
            self.assertTrue((files_out / "2026" / "04" / "Newsletter.pdf").exists())

    def test_copy_and_get_url_returns_none_when_source_missing(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "uploads"
            root.mkdir()
            url = copy_and_get_url(
                "2099/01/missing.jpg", root, Path(tmp) / "images", Path(tmp) / "files"
            )
            self.assertIsNone(url)


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run the test to verify it fails**

Run: `cd /Users/michael/git_stuff/eadm-website && python3 tools/test_media.py`
Expected: `ModuleNotFoundError: No module named 'media'`

- [ ] **Step 3: Write `tools/media.py`**

```python
"""Resolves WordPress /wp-content/uploads/ references to on-disk files,
deduplicates WordPress's auto-generated thumbnail sizes, and copies the
chosen file into the new site's images/ or files/ directory.
"""

import re
import shutil
from pathlib import Path

IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".gif", ".tiff", ".webp"}
_SIZE_SUFFIX_RE = re.compile(r"-\d+x\d+(?=\.\w+$)")


def strip_size_suffix(filename: str) -> str:
    """'AdeleDiederich-1024x682.jpg' -> 'AdeleDiederich.jpg'.

    No-op for filenames without a WordPress '-WIDTHxHEIGHT' size suffix.
    """
    return _SIZE_SUFFIX_RE.sub("", filename)


def find_best_local_file(rel_path: str, uploads_root: Path) -> Path | None:
    """rel_path is like '2014/07/AdeleDiederich-1024x682.jpg'.

    Returns the largest on-disk file sharing the same base name (any
    WordPress-generated size of the same source image), or None if no
    matching file exists under uploads_root.
    """
    rel = Path(rel_path)
    base = strip_size_suffix(rel.name)
    directory = uploads_root / rel.parent
    if not directory.is_dir():
        return None
    candidates = [
        f
        for f in directory.iterdir()
        if f.is_file() and strip_size_suffix(f.name) == base
    ]
    if not candidates:
        exact = directory / rel.name
        return exact if exact.exists() else None
    return max(candidates, key=lambda f: f.stat().st_size)


def copy_and_get_url(
    rel_path: str, uploads_root: Path, images_out: Path, files_out: Path
) -> str | None:
    """Copy the best local file for rel_path into images_out or files_out
    (mirroring its YYYY/MM directory), and return its new root-relative
    site URL ('/images/...' or '/files/...'), or None if unresolved.
    """
    src = find_best_local_file(rel_path, uploads_root)
    if src is None:
        return None
    is_image = src.suffix.lower() in IMAGE_EXTENSIONS
    out_root = images_out if is_image else files_out
    dest_rel = Path(rel_path).parent / src.name
    dest = out_root / dest_rel
    dest.parent.mkdir(parents=True, exist_ok=True)
    if not dest.exists():
        shutil.copyfile(src, dest)
    prefix = "images" if is_image else "files"
    return f"/{prefix}/{dest_rel.as_posix()}"
```

- [ ] **Step 4: Run the test to verify it passes**

Run: `cd /Users/michael/git_stuff/eadm-website && python3 tools/test_media.py -v`
Expected: 7 tests, all `ok`.

- [ ] **Step 5: Commit**

```bash
git add tools/media.py tools/test_media.py
git commit -m "Add media resolution: dedup WordPress thumbnails, copy originals"
```

---

## Task 4: Link/media rewriting — `tools/rewrite.py`

**Files:**
- Create: `/Users/michael/git_stuff/eadm-website/tools/rewrite.py`
- Create: `/Users/michael/git_stuff/eadm-website/tools/test_rewrite.py`

**Interfaces:**
- Consumes: `copy_and_get_url` from `media.py` (Task 3).
- Produces: `rewrite_attachment_links`, `rewrite_wp_uploads_links`, `rewrite_internal_links` — all `(content: str, ...) -> str`. `transform.py` (Task 6) applies them in that exact order (attachment links first, since their href doesn't match the plain uploads pattern; internal-link rewriting last, so it only sees whatever wasn't already resolved to `/images/` or `/files/`).

- [ ] **Step 1: Write the failing test**

```python
# tools/test_rewrite.py
import tempfile
import unittest
from pathlib import Path

from rewrite import (
    rewrite_attachment_links,
    rewrite_internal_links,
    rewrite_wp_uploads_links,
)


class TestRewrite(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.uploads_root = Path(self.tmp.name) / "uploads"
        self.images_out = Path(self.tmp.name) / "images"
        self.files_out = Path(self.tmp.name) / "files"

    def tearDown(self):
        self.tmp.cleanup()

    def _make_upload(self, rel_path, size=1000):
        p = self.uploads_root / rel_path
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_bytes(b"x" * size)

    def test_rewrite_wp_uploads_links_rewrites_image_src(self):
        self._make_upload("2014/07/AdeleDiederich-1024x682.jpg")
        content = (
            '<img src="http://eadm.eu/wp-content/uploads/2014/07/'
            'AdeleDiederich-1024x682.jpg" alt="x">'
        )
        result = rewrite_wp_uploads_links(
            content, self.uploads_root, self.images_out, self.files_out
        )
        self.assertIn('/images/2014/07/AdeleDiederich-1024x682.jpg', result)

    def test_rewrite_wp_uploads_links_leaves_unresolved_refs_untouched(self):
        content = '<img src="http://eadm.eu/wp-content/uploads/2099/01/gone.jpg">'
        result = rewrite_wp_uploads_links(
            content, self.uploads_root, self.images_out, self.files_out
        )
        self.assertEqual(result, content)

    def test_rewrite_attachment_links_resolves_by_attachment_id(self):
        self._make_upload("2013/06/Report2024.pdf")
        content = (
            '<a href="https://eadm.eu/some/pretty/permalink/" '
            'rel="attachment wp-att-1435">2024 Summer School Berlin</a>'
        )
        attachment_files = {1435: "2013/06/Report2024.pdf"}
        result = rewrite_attachment_links(
            content, attachment_files, self.uploads_root, self.images_out, self.files_out
        )
        self.assertIn('<a href="/files/2013/06/Report2024.pdf"', result)

    def test_rewrite_internal_links_rewrites_known_slug(self):
        slug_to_path = {"membership": "membership/index"}
        content = 'See <a href="http://eadm.eu/membership/">Membership</a>.'
        result = rewrite_internal_links(content, slug_to_path)
        self.assertIn('href="/membership/index"', result)

    def test_rewrite_internal_links_leaves_unknown_slug_untouched(self):
        slug_to_path = {"membership": "membership/index"}
        content = 'See <a href="http://eadm.eu/some-other-page/">Other</a>.'
        result = rewrite_internal_links(content, slug_to_path)
        self.assertEqual(result, content)


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run the test to verify it fails**

Run: `cd /Users/michael/git_stuff/eadm-website && python3 tools/test_rewrite.py`
Expected: `ModuleNotFoundError: No module named 'rewrite'`

- [ ] **Step 3: Write `tools/rewrite.py`**

```python
"""Rewrites WordPress-era links and media references inside migrated
content: attachment permalinks, direct /wp-content/uploads/ URLs, and
internal https://eadm.eu/<slug>/ links.
"""

import re

from media import copy_and_get_url

_WP_UPLOAD_RE = re.compile(
    r"(?:https?://eadm\.eu)?/wp-content/uploads/(\d{4}/\d{2}/[^\"'\s)>]+)"
)
_ATTACHMENT_LINK_RE = re.compile(r'<a\s+href="[^"]*"\s+rel="attachment wp-att-(\d+)"')
_INTERNAL_LINK_RE = re.compile(r'href="https?://eadm\.eu/([a-zA-Z0-9\-_/]+)/?"')


def rewrite_wp_uploads_links(content, uploads_root, images_out, files_out):
    """Rewrite every direct /wp-content/uploads/... reference to a copied
    local file under images_out or files_out. References that can't be
    resolved to an on-disk file are left untouched.
    """

    def replace(match):
        rel_path = match.group(1)
        url = copy_and_get_url(rel_path, uploads_root, images_out, files_out)
        return url if url is not None else match.group(0)

    return _WP_UPLOAD_RE.sub(replace, content)


def rewrite_attachment_links(content, attachment_files, uploads_root, images_out, files_out):
    """Rewrite <a href="..." rel="attachment wp-att-NNNN"> links, which use
    WordPress's pretty attachment-page permalink rather than a direct
    /wp-content/uploads/ URL, by resolving the attachment ID instead.
    attachment_files maps attachment post ID -> its uploads-relative path
    (WordPress's '_wp_attached_file' postmeta).
    """

    def replace(match):
        attachment_id = int(match.group(1))
        rel_path = attachment_files.get(attachment_id)
        if rel_path is None:
            return match.group(0)
        url = copy_and_get_url(rel_path, uploads_root, images_out, files_out)
        if url is None:
            return match.group(0)
        return f'<a href="{url}"'

    return _ATTACHMENT_LINK_RE.sub(replace, content)


def rewrite_internal_links(content, slug_to_path):
    """Rewrite href="https://eadm.eu/<slug>/" links to the new site's
    relative path when <slug> is a known migrated page/post. Unmapped
    slugs (dropped pages, or slugs not in this migration) are left as
    absolute external links, so they keep working via the live site.
    """

    def replace(match):
        slug = match.group(1).rstrip("/").split("/")[-1]
        if slug in slug_to_path:
            return f'href="/{slug_to_path[slug]}"'
        return match.group(0)

    return _INTERNAL_LINK_RE.sub(replace, content)
```

- [ ] **Step 4: Run the test to verify it passes**

Run: `cd /Users/michael/git_stuff/eadm-website && python3 tools/test_rewrite.py -v`
Expected: 5 tests, all `ok`.

- [ ] **Step 5: Commit**

```bash
git add tools/rewrite.py tools/test_rewrite.py
git commit -m "Add link and media reference rewriting for migrated content"
```

---

## Task 5: Extract WordPress content from the database — `tools/extract.py`

**Files:**
- Create: `/Users/michael/git_stuff/eadm-website/tools/extract.py`

**Interfaces:**
- Produces: `tools/_extracted/pages.json`, `posts.json`, `categories.json`, `attachments.json` (gitignored — scratch data, regenerable by rerunning this script). `transform.py` (Task 6) reads these four files.

- [ ] **Step 1: Set up the scratch database (idempotent — skip if already running)**

The dump was already imported into a running container named
`eadm_mysql_import` during design exploration. If it is not running (check
with `docker ps --filter name=eadm_mysql_import`), recreate it:

```bash
docker rm -f eadm_mysql_import 2>/dev/null
docker run -d --name eadm_mysql_import \
  -e MYSQL_ROOT_PASSWORD=root -e MYSQL_DATABASE=eadm mariadb:10.11
# wait for it to accept connections
until docker exec eadm_mysql_import mysql -uroot -proot -e "SELECT 1" >/dev/null 2>&1; do sleep 2; done
docker cp /Users/michael/git_stuff/wp_eadm/eadm-eu-20260914-054440-ujh0nuxckrsu/database.sql \
  eadm_mysql_import:/database.sql
docker exec eadm_mysql_import sh -c "mysql -uroot -proot eadm < /database.sql"
```

- [ ] **Step 2: Write `tools/extract.py`**

```python
"""Pulls curated WordPress content out of the scratch MariaDB import as
JSON. Uses JSON_ARRAYAGG(JSON_OBJECT(...)) so MySQL itself handles all
string escaping -- far more robust than parsing the raw SQL dump by hand.

Must invoke the mysql CLI with -r (raw mode): plain -N -B batch output
double-escapes backslashes inside the JSON text and corrupts it (verified
during design).
"""

import json
import subprocess
from pathlib import Path

CONTAINER = "eadm_mysql_import"
OUT_DIR = Path(__file__).parent / "_extracted"

QUERIES = {
    "pages.json": """
        SELECT JSON_ARRAYAGG(JSON_OBJECT(
            'id', ID, 'type', post_type, 'title', post_title,
            'slug', post_name, 'date', post_date, 'content', post_content
        )) FROM SERVMASK_PREFIX_posts
        WHERE post_status = 'publish' AND post_type = 'page';
    """,
    "posts.json": """
        SELECT JSON_ARRAYAGG(JSON_OBJECT(
            'id', ID, 'type', post_type, 'title', post_title,
            'slug', post_name, 'date', post_date, 'content', post_content
        )) FROM SERVMASK_PREFIX_posts
        WHERE post_status = 'publish' AND post_type = 'post';
    """,
    "categories.json": """
        SELECT JSON_ARRAYAGG(JSON_OBJECT('post_id', p.ID, 'category', t.name))
        FROM SERVMASK_PREFIX_posts p
        JOIN SERVMASK_PREFIX_term_relationships tr ON tr.object_id = p.ID
        JOIN SERVMASK_PREFIX_term_taxonomy tt
            ON tt.term_taxonomy_id = tr.term_taxonomy_id AND tt.taxonomy = 'category'
        JOIN SERVMASK_PREFIX_terms t ON t.term_id = tt.term_id
        WHERE p.post_status = 'publish' AND p.post_type = 'post';
    """,
    "attachments.json": """
        SELECT JSON_ARRAYAGG(JSON_OBJECT(
            'id', p.ID,
            'file', (SELECT meta_value FROM SERVMASK_PREFIX_postmeta pm
                     WHERE pm.post_id = p.ID AND pm.meta_key = '_wp_attached_file'
                     LIMIT 1)
        )) FROM SERVMASK_PREFIX_posts p WHERE p.post_type = 'attachment';
    """,
}


def run_query(sql: str) -> list:
    full_sql = "SET SESSION group_concat_max_len = 1000000000;\n" + sql
    result = subprocess.run(
        ["docker", "exec", "-i", CONTAINER, "mysql", "-uroot", "-proot", "-N", "-B", "-r", "eadm"],
        input=full_sql,
        capture_output=True,
        text=True,
        check=True,
    )
    raw = result.stdout.strip()
    return json.loads(raw) if raw else []


def main():
    OUT_DIR.mkdir(exist_ok=True)
    for filename, sql in QUERIES.items():
        data = run_query(sql)
        # Normalize WordPress's Windows-style line endings.
        for row in data:
            if "content" in row and row["content"] is not None:
                row["content"] = row["content"].replace("\r\n", "\n")
        (OUT_DIR / filename).write_text(json.dumps(data, indent=2))
        print(f"{filename}: {len(data)} rows")


if __name__ == "__main__":
    main()
```

- [ ] **Step 3: Run it and verify counts**

Run: `cd /Users/michael/git_stuff/eadm-website && python3 tools/extract.py`
Expected output:
```
pages.json: 58 rows
posts.json: 63 rows
categories.json: <some number >= 63> rows
attachments.json: 133 rows
```
If `pages.json` or `posts.json` counts differ from 58/63, stop and
investigate before continuing — Task 2's `content_map.py` was built against
exactly these counts.

- [ ] **Step 4: Commit**

```bash
git add tools/extract.py
git commit -m "Add WordPress content extraction script"
```

(`tools/_extracted/*.json` is gitignored and not committed — it's
regenerable scratch data.)

---

## Task 6: Generate the site content — `tools/transform.py`

**Files:**
- Create: `/Users/michael/git_stuff/eadm-website/tools/transform.py`

**Interfaces:**
- Consumes: `resolve_target` (Task 2), `copy_and_get_url` (Task 3), `rewrite_attachment_links` / `rewrite_wp_uploads_links` / `rewrite_internal_links` (Task 4), and the four JSON files from Task 5.
- Produces: one `.qmd` file per kept page/post under the paths `resolve_target` returns, plus `CONTENT_AUDIT.md` at the repo root.

- [ ] **Step 1: Write `tools/transform.py`**

```python
"""Generates the Quarto site's migrated content: reads the extracted
WordPress JSON, classifies each item via content_map, rewrites its
internal links and media references, and writes one .qmd file per kept
item. Also writes CONTENT_AUDIT.md listing everything that was dropped.

This is a one-time migration script, run once against the exported
WordPress database -- not part of the served site.
"""

import json
from pathlib import Path

from content_map import resolve_target
from rewrite import (
    rewrite_attachment_links,
    rewrite_internal_links,
    rewrite_wp_uploads_links,
)

REPO_ROOT = Path(__file__).parent.parent
EXTRACTED = Path(__file__).parent / "_extracted"
UPLOADS_ROOT = Path(
    "/Users/michael/git_stuff/wp_eadm/eadm-eu-20260914-054440-ujh0nuxckrsu/uploads"
)
IMAGES_OUT = REPO_ROOT / "images"
FILES_OUT = REPO_ROOT / "files"


def load(name):
    return json.loads((EXTRACTED / name).read_text())


def build_categories_by_post_id(categories):
    result = {}
    for row in categories:
        result.setdefault(row["post_id"], set()).add(row["category"])
    return result


def build_attachment_files(attachments):
    return {a["id"]: a["file"] for a in attachments if a["file"]}


def build_slug_to_path(items, categories_by_post_id):
    slug_to_path = {}
    for item in items:
        target = resolve_target(item, categories_by_post_id)
        if target is None:
            continue
        section, filename = target
        path = f"{section}/{filename}" if section else filename
        slug_to_path[item["slug"]] = path
    return slug_to_path


def yaml_quote(value: str) -> str:
    return value.replace("\\", "\\\\").replace('"', '\\"')


def build_frontmatter(item, categories_by_post_id):
    lines = ["---", f'title: "{yaml_quote(item["title"])}"']
    if item["type"] == "post":
        lines.append(f"date: {item['date'][:10]}")
        cats = sorted(categories_by_post_id.get(item["id"], set()))
        if cats:
            quoted = ", ".join(f'"{yaml_quote(c)}"' for c in cats)
            lines.append(f"categories: [{quoted}]")
    lines.append("---")
    return "\n".join(lines)


def main():
    pages = load("pages.json")
    posts = load("posts.json")
    items = pages + posts
    categories_by_post_id = build_categories_by_post_id(load("categories.json"))
    attachment_files = build_attachment_files(load("attachments.json"))
    slug_to_path = build_slug_to_path(items, categories_by_post_id)

    written, dropped = [], []
    for item in items:
        target = resolve_target(item, categories_by_post_id)
        if target is None:
            dropped.append(item)
            continue
        section, filename = target
        out_dir = REPO_ROOT / section if section else REPO_ROOT
        out_dir.mkdir(parents=True, exist_ok=True)

        content = item["content"]
        content = rewrite_attachment_links(
            content, attachment_files, UPLOADS_ROOT, IMAGES_OUT, FILES_OUT
        )
        content = rewrite_wp_uploads_links(content, UPLOADS_ROOT, IMAGES_OUT, FILES_OUT)
        content = rewrite_internal_links(content, slug_to_path)

        frontmatter = build_frontmatter(item, categories_by_post_id)
        (out_dir / f"{filename}.qmd").write_text(f"{frontmatter}\n\n{content}\n")
        written.append((item, section, filename))

    write_content_audit(dropped, written)
    print(f"Wrote {len(written)} .qmd files, dropped {len(dropped)} items.")


def write_content_audit(dropped, written):
    from content_map import DROP_IDS

    lines = [
        "# Content Audit",
        "",
        "Generated by `tools/transform.py` — do not hand-edit. Lists every",
        "published WordPress page/post that was dropped or merged during",
        "migration, and why.",
        "",
        "## Dropped or merged items",
        "",
    ]
    for item in sorted(dropped, key=lambda i: i["id"]):
        reason = DROP_IDS.get(item["id"], "unspecified")
        lines.append(f"- **{item['title']}** (WP id {item['id']}, slug `{item['slug']}`): {reason}")
    lines += ["", f"## Migrated: {len(written)} items", ""]
    (REPO_ROOT / "CONTENT_AUDIT.md").write_text("\n".join(lines) + "\n")


if __name__ == "__main__":
    main()
```

- [ ] **Step 2: Run it**

Run: `cd /Users/michael/git_stuff/eadm-website && python3 tools/transform.py`
Expected: `Wrote 98 .qmd files, dropped 23 items.` (35 kept pages + 63 posts = 98).
If the numbers differ, stop and check `CONTENT_AUDIT.md` against
`content_map.py`'s `DROP_IDS`/`PAGE_OVERRIDES` before continuing.

- [ ] **Step 3: Spot-check the output**

```bash
cat about/index.qmd          # should start with the EADM description paragraph
cat about/executive-board.qmd  # should contain the <table> markup, unmangled
ls news/posts | wc -l         # should be a small number, roughly matching the News category count
ls interviews/posts | wc -l   # should be roughly 22
```

- [ ] **Step 4: Commit the generated content**

```bash
cd /Users/michael/git_stuff/eadm-website
git add about/ membership/ funding/ prizes/ spudm/ newsletter/ \
        news/ presidents-column/ interviews/ images/ files/ CONTENT_AUDIT.md
git status --short   # sanity check nothing unexpected is staged
git commit -m "Generate migrated site content from WordPress export"
```

---

## Task 7: Broken-link check — `tools/check_links.py`

**Files:**
- Create: `/Users/michael/git_stuff/eadm-website/tools/check_links.py`

**Interfaces:**
- Produces: exits non-zero and prints every broken reference if any root-relative link/image in any `.qmd` file doesn't resolve to a file that exists in the repo.

- [ ] **Step 1: Write `tools/check_links.py`**

```python
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
```

- [ ] **Step 2: Run it**

Run: `cd /Users/michael/git_stuff/eadm-website && python3 tools/check_links.py`
Expected: `No broken internal references found.` If it reports broken
references, fix them in the source content (or, for a page that was
legitimately dropped per `CONTENT_AUDIT.md`, remove the dangling link from
whichever `.qmd` still references it) before moving on.

- [ ] **Step 3: Commit**

```bash
git add tools/check_links.py
git commit -m "Add internal link checker"
```

---

## Task 8: Blog listing pages, full-site render, and fidelity check

**Files:**
- Create: `/Users/michael/git_stuff/eadm-website/news/index.qmd`
- Create: `/Users/michael/git_stuff/eadm-website/presidents-column/index.qmd`
- Create: `/Users/michael/git_stuff/eadm-website/interviews/index.qmd`

**Interfaces:**
- Consumes: the `news/posts/*.qmd`, `presidents-column/posts/*.qmd`, `interviews/posts/*.qmd` files Task 6 generated (each carries `title`, `date`, and `categories` frontmatter).

- [ ] **Step 1: Write `news/index.qmd`**

```markdown
---
title: "News"
listing:
  contents: posts
  type: default
  sort: "date desc"
  categories: false
---

Announcements and updates from EADM.
```

- [ ] **Step 2: Write `presidents-column/index.qmd`**

```markdown
---
title: "President's Column"
listing:
  contents: posts
  type: default
  sort: "date desc"
  categories: false
---

Regular columns from the EADM President.
```

- [ ] **Step 3: Write `interviews/index.qmd`**

```markdown
---
title: "EADM Interview"
listing:
  contents: posts
  type: default
  sort: "date desc"
  categories: false
---

A recurring series of interviews with EADM members.
```

- [ ] **Step 4: Full-project render**

Run: `cd /Users/michael/git_stuff/eadm-website && quarto render`
Expected: exits 0, with a `Rendering: <file>` line for every `.qmd` file
in the project (98 generated + the hand-written scaffold pages) and a
final `Output created: _site/index.html`. If any single page errors, fix
that page's content (most likely cause: a stray unescaped character from
the original WordPress HTML) and re-render just that file first with
`quarto render <path>.qmd` before re-running the full build.

- [ ] **Step 5: Run the link checker again post-render**

Run: `python3 tools/check_links.py`
Expected: `No broken internal references found.`

- [ ] **Step 6: Fidelity spot-check against the live site**

Open `_site/about/index.html`, `_site/about/executive-board.html`,
`_site/news/posts/<any one file>.html`, and `_site/newsletter/index.html`
in a browser (`quarto preview` or `open _site/index.html`), and compare
each against the corresponding live page at https://eadm.eu — confirm
text content matches, the Executive Board table renders correctly, and at
least one Newsletter PDF link opens the vendored file.

- [ ] **Step 7: Commit**

```bash
git add news/index.qmd presidents-column/index.qmd interviews/index.qmd
git commit -m "Add News, President's Column, and Interview blog listings"
```

---

## Task 9: README and final housekeeping

**Files:**
- Create: `/Users/michael/git_stuff/eadm-website/README.md`

- [ ] **Step 1: Write `README.md`**

```markdown
# EADM Website

Quarto rebuild of the [EADM](https://eadm.eu) (European Association for
Decision Making) website, migrated from its WordPress export.

## Rendering locally

```bash
quarto render
quarto preview
```

## Changing the design

The look of the site is deliberately kept swappable:

- **Colors and fonts** — edit `_brand.yml`. Change the hex values in
  `color.palette`, or swap the Google Font names under `typography`.
- **Base theme** — edit the `theme:` key in `_quarto.yml`. It's a
  light/dark pair of built-in Quarto/Bootswatch themes (currently
  `zephyr` / `darkly`); swap either name for any other Bootswatch theme
  Quarto ships (`cosmo`, `flatly`, `litera`, `lux`, ...).
- **Anything else** — small custom CSS rules live in `styles.scss`,
  layered on top of the theme and brand.

## Content provenance

Content was migrated from a WordPress export (All-in-One WP Migration
bundle) using the one-time scripts in `tools/`. See
`docs/superpowers/specs/2026-09-14-eadm-website-migration-design.md` for
the migration design, and `CONTENT_AUDIT.md` for exactly what was dropped
or merged during migration and why. The `tools/` scripts are kept for
provenance but are not part of the served site and won't run again
without the original WordPress export and its scratch database import.
```

- [ ] **Step 2: Review `CONTENT_AUDIT.md`**

Read through it once; confirm every dropped item still makes sense (no
surprises versus the spec's §3 curation list).

- [ ] **Step 3: Commit**

```bash
git add README.md
git commit -m "Add README with design-switching and content-provenance notes"
```

---

## Task 10: Push to GitHub

**Files:** none (repo-level operation)

- [ ] **Step 1: Ensure the GitHub CLI is available**

Run: `which gh || brew install gh`

- [ ] **Step 2: Check authentication**

Run: `gh auth status`
If it reports not logged in, **stop and ask the user** to run
`gh auth login` interactively (this cannot be scripted) before continuing.

- [ ] **Step 3: Create the repo and push**

```bash
cd /Users/michael/git_stuff/eadm-website
gh repo create eadm-website --public --source=. --remote=origin --push
```

- [ ] **Step 4: Verify**

Run: `gh repo view --web=false` and `git log --oneline -1 origin/main`
Expected: the repo exists under the user's account and the local and
remote `main` branches match.

- [ ] **Step 5: Wire up the GitHub link now that the real URL is known**

Task 1 deliberately left the navbar without a GitHub link, since the repo
didn't exist yet and its URL depends on whichever account `gh auth login`
is authenticated as. Get the real URL:

Run: `gh repo view --json url -q .url`

Then add it to `_quarto.yml`'s `website.navbar` (as a `right:` entry) and
footer:

```yaml
    right:
      - icon: github
        href: "<the URL printed above>"
        aria-label: GitHub repository
  page-footer: "[Contact](contact.qmd) · [Source on GitHub](<the URL printed above>)"
```

Re-render (`quarto render`), then commit and push:

```bash
git add _quarto.yml
git commit -m "Link the GitHub repo from the navbar and footer"
git push
```

---

## Task 11: Tear down the scratch database

**Files:** none

- [ ] **Step 1: Remove the scratch MariaDB container**

Run: `docker rm -f eadm_mysql_import`

This container was only ever a query interface onto `database.sql` for
Task 5's extraction step; nothing later in the pipeline depends on it
staying alive.
