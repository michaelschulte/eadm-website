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
