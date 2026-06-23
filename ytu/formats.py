from __future__ import annotations

import re
from typing import Any, Literal

QUALITY_RE = re.compile(r"^(?P<height>\d{3,4})(p)?$", re.IGNORECASE)
FallbackPolicy = Literal["lower", "exact", "higher", "nearest", "any"]


class QualityError(ValueError):
    pass


def parse_quality(quality: str | int | None) -> int | None:
    """Return height in pixels, or None for best/original."""
    if quality is None:
        return None
    if isinstance(quality, int):
        if quality <= 0:
            raise QualityError("Quality height must be positive.")
        return quality

    value = str(quality).strip().lower()
    if value in {"best", "max", "highest", "source", "original", "auto"}:
        return None
    match = QUALITY_RE.match(value)
    if not match:
        raise QualityError("Use quality like best, 720p, 1080p, 1440p, or 2160p.")
    height = int(match.group("height"))
    if height < 144:
        raise QualityError("Video height is too small to be useful. Try 144p or higher.")
    return height


def normalize_fallback(fallback: str | None, *, exact: bool = False) -> FallbackPolicy:
    if exact:
        return "exact"
    if fallback is None:
        return "lower"
    value = fallback.strip().lower()
    aliases = {
        "cap": "lower",
        "capped": "lower",
        "below": "lower",
        "lte": "lower",
        "strict": "exact",
        "none": "exact",
        "above": "higher",
        "gte": "higher",
        "closest": "nearest",
        "best": "any",
    }
    value = aliases.get(value, value)
    if value not in {"lower", "exact", "higher", "nearest", "any"}:
        raise QualityError("Fallback must be one of: lower, exact, higher, nearest, any.")
    return value  # type: ignore[return-value]


def _video_audio_selector(video_filter: str, *, compat: bool) -> str:
    """Build one yt-dlp selector for a given video filter."""
    if compat:
        return (
            f"bv*[{video_filter}][ext=mp4]+ba[ext=m4a]/"
            f"bv*[{video_filter}]+ba/"
            f"b[{video_filter}][ext=mp4]/"
            f"b[{video_filter}]"
        )
    return f"bv*[{video_filter}]+ba/b[{video_filter}]"


def build_video_format(
    quality: str | int | None = "best",
    *,
    exact: bool = False,
    format_id: str | None = None,
    compat: bool = False,
    fallback: str | None = "lower",
) -> str:
    """Build a yt-dlp format selector.

    Behavior:
    - best: best separate video + best audio, with single-file fallback
    - lower: best video at or below requested height
    - exact: only the requested height
    - higher: requested height or higher
    - nearest: exact, then lower, then higher, then any
    - any: requested-or-better preference with broad fallback to best available
    - compat: tries MP4/M4A-friendly selectors first, then broader selectors
    """
    if format_id:
        return format_id

    height = parse_quality(quality)
    if height is None:
        if compat:
            return "(bv*[ext=mp4]+ba[ext=m4a]/bv*+ba/b)"
        return "bv*+ba/b"

    policy = normalize_fallback(fallback, exact=exact)
    selectors: list[str] = []

    if policy == "exact":
        selectors.append(_video_audio_selector(f"height={height}", compat=compat))
    elif policy == "lower":
        selectors.append(_video_audio_selector(f"height<={height}", compat=compat))
    elif policy == "higher":
        selectors.append(_video_audio_selector(f"height>={height}", compat=compat))
    elif policy == "nearest":
        selectors.extend(
            [
                _video_audio_selector(f"height={height}", compat=compat),
                _video_audio_selector(f"height<={height}", compat=compat),
                _video_audio_selector(f"height>={height}", compat=compat),
                "bv*+ba/b",
            ]
        )
    elif policy == "any":
        selectors.extend(
            [
                _video_audio_selector(f"height<={height}", compat=compat),
                _video_audio_selector(f"height>={height}", compat=compat),
                "bv*+ba/b",
            ]
        )

    return f"({'/'.join(selectors)})"


def build_audio_format(format_id: str | None = None) -> str:
    return format_id or "ba/bestaudio/best"


def available_video_heights(info: dict[str, Any]) -> list[int]:
    heights = {
        int(fmt["height"])
        for fmt in info.get("formats", []) or []
        if fmt.get("height") and fmt.get("vcodec") != "none"
    }
    return sorted(heights, reverse=True)


def count_formats_by_height(info: dict[str, Any]) -> dict[int, int]:
    counts: dict[int, int] = {}
    for fmt in info.get("formats", []) or []:
        height = fmt.get("height")
        if height and fmt.get("vcodec") != "none":
            counts[int(height)] = counts.get(int(height), 0) + 1
    return dict(sorted(counts.items(), reverse=True))


def smart_default_quality(heights: list[int]) -> str:
    """Pick a practical default for interactive mode."""
    if not heights:
        return "best"
    for preferred in (1080, 720, 480, 360):
        if preferred in heights:
            return f"{preferred}p"
    return f"{heights[0]}p"
