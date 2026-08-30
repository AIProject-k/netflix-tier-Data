"""Collapse Netflix rows into a single content identity.

Netflix already splits the franchise root (`show_title`) from the season
(`season_title`), so "Squid Game" S2 and S3 both arrive as show_title="Squid Game".
Grouping by the normalized show_title + media type is enough for v1.
"""

from __future__ import annotations

import re

_WS = re.compile(r"\s+")


def media_type(category: str) -> str:
    """"Films", "Films (English)", "TV (Non-English)" -> "film" / "tv"."""
    return "film" if category.strip().lower().startswith("film") else "tv"


def display_title(show_title: str) -> str:
    return _WS.sub(" ", show_title.strip())


def content_key(show_title: str, category: str) -> tuple[str, str]:
    """Stable grouping key from a raw Netflix row: (folded title, media type)."""
    return key_of(show_title, media_type(category))


def key_of(show_title: str, mtype: str) -> tuple[str, str]:
    """Grouping key when the media type ("film"/"tv") is already known."""
    return _WS.sub(" ", show_title.strip()).casefold(), mtype
