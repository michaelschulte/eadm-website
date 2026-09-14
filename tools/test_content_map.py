import unittest

from content_map import DROP_IDS, PAGE_OVERRIDES, resolve_target


class TestContentMap(unittest.TestCase):
    def test_all_58_published_pages_are_classified(self):
        self.assertEqual(len(DROP_IDS), 19)
        self.assertEqual(len(PAGE_OVERRIDES), 39)
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
        item = {
            "id": 900,
            "type": "post",
            "slug": "the-eadm-interview-adele-diederich",
            "title": "The EADM Interview: Adele Diedrich, Professor",
        }
        cats = {900: {"EADM Interview", "Uncategorized"}}
        self.assertEqual(
            resolve_target(item, cats),
            ("interviews/posts", "the-eadm-interview-adele-diederich"),
        )

    def test_post_without_known_category_falls_back_to_news(self):
        item = {"id": 1, "type": "post", "slug": "some-old-post"}
        self.assertEqual(resolve_target(item, {}), ("news/posts", "some-old-post"))

    def test_interviewee_bio_pages_without_a_post_resolve_to_interviews(self):
        # These 4 pages were wrongly dropped as "duplicate of EADM Interview
        # post (X)" -- no such post exists for any of them.
        expected = {
            740: "mandeep-k-dhami-phd",
            828: "eyal-peer-phd",
            838: "benjamin-scheibehenne-phd",
            843: "iain-d-gilchrist-professor",
        }
        for page_id, slug in expected.items():
            with self.subTest(page_id=page_id):
                self.assertNotIn(page_id, DROP_IDS)
                item = {"id": page_id, "type": "page", "slug": slug}
                self.assertEqual(resolve_target(item, {}), ("interviews/posts", slug))

    def test_mistagged_interview_post_falls_through_to_news(self):
        # ~10 conference announcements carry the 'EADM Interview' category
        # by mistake; only titles that really are interviews may route there.
        item = {
            "id": 1282,
            "type": "post",
            "slug": "spudm-2021-call-for-papers",
            "title": "SPUDM 2021 Call for Papers",
        }
        cats = {1282: {"EADM Interview"}}
        self.assertEqual(
            resolve_target(item, cats),
            ("news/posts", "spudm-2021-call-for-papers"),
        )

    def test_mistagged_interview_post_still_honours_a_later_category(self):
        item = {
            "id": 1264,
            "type": "post",
            "slug": "eadm-tweets-now",
            "title": "EADM tweets now! @EADM_1993",
        }
        cats = {1264: {"EADM Interview", "President's Column"}}
        self.assertEqual(
            resolve_target(item, cats),
            ("presidents-column/posts", "eadm-tweets-now"),
        )


if __name__ == "__main__":
    unittest.main()
