"""Contain artwork cache paths even if a remote content identifier is hostile."""

from pathlib import Path
import re


def thumbnail_path(directory: str, content_id: str) -> tuple[str, str]:
    """Return a validated JPEG name/path, rejecting separators and symlink escapes."""
    if not isinstance(content_id, str) or not re.fullmatch(
        r"[A-Za-z0-9_-][A-Za-z0-9_.:-]{0,199}", content_id
    ):
        raise ValueError("Invalid artwork content identifier")
    base = Path(directory).resolve()
    name = content_id.replace(":", "_") + ".jpg"
    candidate = (base / name).resolve()
    if candidate.parent != base:
        raise ValueError("Artwork thumbnail escapes its cache directory")
    return name, str(candidate)
