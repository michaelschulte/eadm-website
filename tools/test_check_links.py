# tools/test_check_links.py
import unittest

from check_links import is_mangled_data_uri


class TestMangledDataUri(unittest.TestCase):
    def test_flags_data_uri_with_path_prefix(self):
        # Quarto listings emit this when a post's auto-picked thumbnail is an
        # inline base64 image: the post's folder gets prepended, so the
        # browser requests a nonexistent file and shows a broken image.
        self.assertTrue(
            is_mangled_data_uri("posts/data:image/png;base64,iVBORw0KGgo")
        )

    def test_flags_data_uri_with_parent_dir_prefix(self):
        self.assertTrue(
            is_mangled_data_uri("../news/posts/data:image/jpeg;base64,/9j/4AAQ")
        )

    def test_accepts_genuine_inline_data_uri(self):
        self.assertFalse(is_mangled_data_uri("data:image/png;base64,iVBORw0KGgo"))

    def test_accepts_ordinary_paths(self):
        self.assertFalse(is_mangled_data_uri("../images/2023/08/IMG_3047.jpeg"))
        self.assertFalse(is_mangled_data_uri("posts/metadata-notes.html"))


if __name__ == "__main__":
    unittest.main()
