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
