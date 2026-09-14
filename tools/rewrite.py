"""Rewrites WordPress-era links and media references inside migrated
content: attachment permalinks, direct /wp-content/uploads/ URLs, and
internal https://eadm.eu/<slug>/ links.
"""

import re

from media import copy_and_get_url

# The host prefix matches ANY scheme://host, not just eadm.eu: the export
# contains uploads URLs on stale hosts (transfer.eadm.eu, eadm.abcde.biz).
# Matching only the path tail would leave the wrong host in front of the
# rewritten local path, producing e.g. http://transfer.eadm.eu/images/...
_WP_UPLOAD_RE = re.compile(
    r"(?:https?://[^/\"'\s]+)?/wp-content/uploads/(\d{4}/\d{2}/[^\"'\s)>]+)"
)
# \s* not \s+: at least one real attachment link (wp-att-1138) has no space
# between the href attribute's closing quote and rel=.
_ATTACHMENT_LINK_RE = re.compile(r'<a\s+href="[^"]*"\s*rel="attachment wp-att-(\d+)"')
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
            # The .qmd suffix is required: a root-relative href with no
            # extension resolves to nothing once rendered. Quarto maps a
            # root-relative .qmd reference to the rendered .html at any
            # page depth (same as _quarto.yml's /contact.qmd footer link).
            return f'href="/{slug_to_path[slug]}.qmd"'
        return match.group(0)

    return _INTERNAL_LINK_RE.sub(replace, content)
