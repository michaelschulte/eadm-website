"""Tests for add_newsletters.py. Run: python3 -m pytest .github/scripts"""

import datetime as dt
import shutil
from pathlib import Path

import pytest

import add_newsletters as an

REPO = Path(__file__).resolve().parents[2]
SAMPLE_PDF = REPO / "files/2026/04/Newsletter-Spring-2026-EADM.pdf"
ARCHIVE_TEXT = """---
title: "Newsletter Archive"
---

<a href="/files/2026/04/Newsletter-Spring-2026-EADM.pdf">Spring 2026</a>

<a href="/files/2025/11/Newsletter-Nov-2025-EADM.pdf">2025 November</a>
"""


@pytest.fixture
def site(tmp_path):
    (tmp_path / "newsletter").mkdir()
    (tmp_path / "newsletter/index.qmd").write_text(ARCHIVE_TEXT)
    (tmp_path / "news/posts").mkdir(parents=True)
    old = tmp_path / "files/2026/04/Newsletter-Spring-2026-EADM.pdf"
    old.parent.mkdir(parents=True)
    shutil.copy(SAMPLE_PDF, old)
    return tmp_path


def upload(site, rel):
    path = site / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy(SAMPLE_PDF, path)


def test_nothing_pending_in_the_real_repository():
    assert an.find_pending(REPO) == []


def test_finds_new_pdf_and_ignores_listed_and_misnamed(site, capsys):
    upload(site, "files/2026/11/EADM-Newsletter-2026-11.pdf")
    upload(site, "files/2026/11/Newsletter Autumn.pdf")
    upload(site, "files/2026/11/conference-flyer.pdf")  # not a newsletter
    assert an.find_pending(site) == [
        an.Issue(2026, 11, "files/2026/11/EADM-Newsletter-2026-11.pdf")]
    err = capsys.readouterr().err
    assert "Newsletter Autumn.pdf" in err
    assert "flyer" not in err


@pytest.mark.parametrize("rel", [
    "files/2026/11/EADM-Newsletter-2026-11.pdf.pdf",  # Windows hid ".pdf"
    "files/2026/11/EADM-Newsletter-2026-11.PDF",
    "files/2026/04/EADM-Newsletter-2026-11.pdf",      # wrong month folder
    "files/2026/EADM-Newsletter-2026-11.pdf.pdf",     # no month folder
    "files/EADM-Newsletter-2026-11.pdf",              # no folders at all
])
def test_accepts_doubled_extension_and_wrong_folder_where_it_is(site, rel):
    upload(site, rel)
    assert an.find_pending(site) == [an.Issue(2026, 11, rel)]


def test_same_issue_uploaded_twice_is_added_once(site, capsys):
    upload(site, "files/2026/04/EADM-Newsletter-2026-11.pdf.pdf")
    upload(site, "files/2026/EADM-Newsletter-2026-11.pdf.pdf")
    upload(site, "files/2026/11/EADM-Newsletter-2026-11.pdf")
    # The copy at the expected path wins over misplaced ones.
    assert an.find_pending(site) == [
        an.Issue(2026, 11, "files/2026/11/EADM-Newsletter-2026-11.pdf")]
    err = capsys.readouterr().err
    assert "2026/04/EADM-Newsletter-2026-11.pdf.pdf" in err
    assert "files/2026/EADM-Newsletter-2026-11.pdf.pdf" in err


def test_issue_already_in_archive_under_another_path_is_skipped(site, capsys):
    archive = site / "newsletter/index.qmd"
    archive.write_text(archive.read_text().replace(
        "---\n\n", '---\n\n<a href="/files/2026/11/EADM-Newsletter-2026-11.pdf">'
        "2026 November</a>\n\n", 1))
    upload(site, "files/2026/04/EADM-Newsletter-2026-11.pdf.pdf")
    assert an.find_pending(site) == []
    assert "already in the archive" in capsys.readouterr().err


def test_impossible_month_is_skipped(site, capsys):
    upload(site, "files/2026/13/EADM-Newsletter-2026-13.pdf")
    assert an.find_pending(site) == []
    assert "2026-13" in capsys.readouterr().err


@pytest.mark.skipif(not shutil.which("pdftoppm"), reason="needs pdftoppm")
def test_full_run_without_ai_is_idempotent(site):
    upload(site, "files/2026/11/EADM-Newsletter-2026-11.pdf")
    upload(site, "files/2027/05/EADM-Newsletter-2027-05.pdf")
    an.main(["--root", str(site), "--no-ai", "--date", "2027-05-20"])

    archive = (site / "newsletter/index.qmd").read_text()
    entries = [l for l in archive.splitlines() if l.startswith("<a ")]
    assert entries[:3] == [
        '<a href="/files/2027/05/EADM-Newsletter-2027-05.pdf">2027 May</a>',
        '<a href="/files/2026/11/EADM-Newsletter-2026-11.pdf">2026 November</a>',
        '<a href="/files/2026/04/Newsletter-Spring-2026-EADM.pdf">Spring 2026</a>',
    ]
    assert "---\n\n<a " in archive and "</a>\n\n<a " in archive

    post = (site / "news/posts/eadm-newsletter-2026-11.qmd").read_text()
    assert 'title: "EADM Newsletter, November 2026"' in post
    assert "date: 2027-05-20" in post
    assert "image: /images/2026/11/eadm-newsletter-2026-11.png" in post
    assert "The November 2026 issue of the EADM Newsletter is out." in post
    assert "(/files/2026/11/EADM-Newsletter-2026-11.pdf)" in post

    cover = site / "images/2026/11/eadm-newsletter-2026-11.png"
    assert cover.read_bytes()[:8] == b"\x89PNG\r\n\x1a\n"

    before = archive
    an.main(["--root", str(site), "--no-ai"])
    assert (site / "newsletter/index.qmd").read_text() == before


def test_post_with_summary_matches_existing_format():
    issue = an.Issue(2026, 11, "files/2026/11/EADM-Newsletter-2026-11.pdf")
    summary = (
        "The November 2026 issue of the EADM Newsletter looks back at the "
        "summer school and announces SPUDM 2027 in Limassol.",
        [("SPUDM 2027 – Call for Submissions", []),
         ("Summer School Report", ["Reflections – A. Author", "Photos"])],
    )
    post = an.render_post(issue, dt.date(2026, 11, 20), summary)
    assert "Limassol. In this issue:\n\n1. SPUDM 2027" in post
    assert "2. Summer School Report\n    - Reflections – A. Author\n    - Photos" in post
    assert all(len(l) <= 72 for l in post.split("In this issue:")[0].splitlines()[7:])


def test_summary_falls_back_without_api_key(site, monkeypatch):
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    issue = an.Issue(2026, 4, "files/2026/04/Newsletter-Spring-2026-EADM.pdf")
    assert an.summarize(site, issue) is None
