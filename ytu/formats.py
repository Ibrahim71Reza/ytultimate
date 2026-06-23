from __future__ import annotations

import re

QUALITY_RE = re.compile(r"^(?P<height>\d{3,4})(p)?$", re.IGNORECASE)


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
    if value in {"best", "max", "highest", "source", "original"}:
        return None
    match = QUALITY_RE.match(value)
    if not match:
        raise QualityError("Use quality like best, 720p, 1080p, 1440p, or 2160p.")
    height = int(match.group("height"))
    if height < 144:
        raise QualityError("Video height is too small to be useful. Try 144p or higher.")
    return height


def build_video_format(
    quality: str | int | None = "best",
    *,
    exact: bool = False,
    format_id: str | None = None,
    compat: bool = False,
) -> str:
    """Build a yt-dlp format selector.

    Default behavior:
    - best: best separate video + best audio, with single-file fallback
    - 720p: best video at or below 720p + best audio, with single-file fallback
    - exact=True: require exact height, e.g. exactly 720p
    - compat=True: first tries MP4/M4A/H.264-friendly choices, then falls back
    """
    if format_id:
        return format_id

    height = parse_quality(quality)
    if height is None:
        if compat:
            return "(bv*[ext=mp4]+ba[ext=m4a]/bv*+ba/b)"
        return "bv*+ba/b"

    op = "=" if exact else "<="
    limit = f"height{op}{height}"

    if compat:
        return (
            f"(bv*[{limit}][ext=mp4]+ba[ext=m4a]/"
            f"bv*[{limit}]+ba/"
            f"b[{limit}][ext=mp4]/"
            f"b[{limit}]/"
            f"best[{limit}])"
        )

    return f"(bv*[{limit}]+ba/b[{limit}]/best[{limit}])"


def build_audio_format(format_id: str | None = None) -> str:
    return format_id or "ba/bestaudio/best"
