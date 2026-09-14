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
