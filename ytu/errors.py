from __future__ import annotations

from rich.console import Console
from rich.panel import Panel


def explain_exception(exc: BaseException) -> str:
    text = str(exc)
    lowered = text.lower()
    tips: list[str] = []

    if "requested format is not available" in lowered or "format is not available" in lowered:
        tips.extend(
            [
                "Run: ytdown formats URL",
                "Try --fallback nearest, remove --exact-quality, or choose a lower --quality such as 720p.",
            ]
        )
    if "ffmpeg" in lowered:
        tips.append("Install ffmpeg: sudo apt install ffmpeg")
    if "sign in" in lowered or "login" in lowered or "cookies" in lowered:
        tips.append(
            "For content you are allowed to access, try --cookies-from-browser chrome or --cookies-from-browser firefox."
        )
    if "private" in lowered:
        tips.append("Private videos require access from the account that is allowed to view them.")
    if "copyright" in lowered or "unavailable" in lowered:
        tips.append("The video may be unavailable, removed, region-limited, or blocked by the platform.")
    if "http error 403" in lowered or "forbidden" in lowered:
        tips.append("Try updating yt-dlp: ytdown update-engine. 403 errors are often fixed by extractor updates.")
    if "no url" in lowered:
        tips.append("Pass a URL or use --file urls.txt with one URL per line.")

    if not tips:
        tips.extend(
            [
                "Run ytdown doctor to check dependencies.",
                "Run ytdown formats URL to inspect available qualities.",
                "Run ytdown update-engine if extraction suddenly stopped working.",
            ]
        )

    tip_text = "\n".join(f"• {tip}" for tip in dict.fromkeys(tips))
    return f"{text}\n\nLikely fixes:\n{tip_text}"


def render_error(console: Console, exc: BaseException) -> None:
    console.print(Panel(explain_exception(exc), title="Download error", border_style="red"))
