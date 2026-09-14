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
