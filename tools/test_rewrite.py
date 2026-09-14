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
