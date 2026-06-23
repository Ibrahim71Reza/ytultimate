from __future__ import annotations

import json
import shutil
from pathlib import Path
from typing import Any, Iterable

from rich.console import Console
from rich.table import Table

from .config import expand_path
from .formats import build_audio_format, build_video_format
from .progress import DownloadProgress, RichLogger

SUPPORTED_CONTAINERS = {"mp4", "mkv", "webm", "mov", "flv", "avi"}
SUPPORTED_AUDIO_FORMATS = {"best", "aac", "alac", "flac", "m4a", "mp3", "opus", "vorbis", "wav"}


def ensure_ffmpeg(console: Console) -> None:
    if not shutil.which("ffmpeg"):
        console.print(
            "[yellow]ffmpeg was not found.[/yellow] Install it for reliable video+audio merging: "
            "[bold]sudo apt install ffmpeg[/bold]"
        )


def parse_cookies_from_browser(value: str | None) -> tuple[str, ...] | None:
    if not value:
        return None
    parts = [p.strip() for p in value.split(":") if p.strip()]
    if not parts:
        return None
    return tuple(parts)


def normalize_urls(urls: Iterable[str], url_file: Path | None = None) -> list[str]:
    final = [u.strip() for u in urls if u and u.strip()]
    if url_file:
        with url_file.expanduser().open("r", encoding="utf-8") as f:
            for line in f:
                value = line.strip()
                if value and not value.startswith("#"):
                    final.append(value)
    # Preserve order while removing duplicates.
    return list(dict.fromkeys(final))


def build_ydl_opts(
    *,
    output_dir: Path,
    output_template: str,
    quality: str,
    exact_quality: bool,
    format_id: str | None,
    compat: bool,
    container: str,
    playlist: bool,
    playlist_items: str | None,
    subtitles: bool,
    auto_subtitles: bool,
    embed_subtitles: bool,
    sub_langs: str,
    thumbnail: bool,
    embed_thumbnail: bool,
    metadata: bool,
    safe_names: bool,
    archive: bool,
    archive_path: Path | None,
    rate_limit: str | None,
    retries: int,
    fragment_retries: int,
    concurrent_fragments: int,
    cookies_from_browser: str | None,
    ffmpeg_location: str | None,
    sponsorblock_remove: str | None,
    dry_run: bool,
    audio_only: bool = False,
    audio_format: str = "mp3",
    audio_quality: str = "0",
    console: Console | None = None,
) -> dict[str, Any]:
    output_dir.mkdir(parents=True, exist_ok=True)
    outtmpl = str(output_dir / output_template)

    if container not in SUPPORTED_CONTAINERS:
        raise ValueError(f"Unsupported container '{container}'. Use one of: {', '.join(sorted(SUPPORTED_CONTAINERS))}")
    if audio_format not in SUPPORTED_AUDIO_FORMATS:
        raise ValueError(
            f"Unsupported audio format '{audio_format}'. Use one of: {', '.join(sorted(SUPPORTED_AUDIO_FORMATS))}"
        )

    postprocessors: list[dict[str, Any]] = []
    if audio_only:
        postprocessors.append(
            {
                "key": "FFmpegExtractAudio",
                "preferredcodec": audio_format,
                "preferredquality": audio_quality,
            }
        )
    if metadata:
        postprocessors.append({"key": "FFmpegMetadata", "add_chapters": True, "add_metadata": True})
    if embed_thumbnail:
        postprocessors.append({"key": "EmbedThumbnail"})

    opts: dict[str, Any] = {
        "format": build_audio_format(format_id) if audio_only else build_video_format(quality, exact=exact_quality, format_id=format_id, compat=compat),
        "outtmpl": {"default": outtmpl},
        "paths": {"home": str(output_dir)},
        "merge_output_format": container,
        "noplaylist": not playlist,
        "playlist_items": playlist_items,
        "writesubtitles": subtitles,
        "writeautomaticsub": auto_subtitles,
        "embedsubtitles": embed_subtitles,
        "subtitleslangs": [s.strip() for s in sub_langs.split(",") if s.strip()],
        "writethumbnail": thumbnail or embed_thumbnail,
        "restrictfilenames": safe_names,
        "retries": retries,
        "fragment_retries": fragment_retries,
        "concurrent_fragment_downloads": concurrent_fragments,
        "ratelimit": rate_limit,
        "ignoreerrors": False,
        "continuedl": True,
        "overwrites": False,
        "nopart": False,
        "quiet": False,
        "no_warnings": False,
        "simulate": dry_run,
        "skip_download": dry_run,
        "postprocessors": postprocessors,
        "logger": RichLogger(console or Console()),
    }

    if archive:
        opts["download_archive"] = str(archive_path or (output_dir / ".download-archive.txt"))
    if cookies_from_browser:
        opts["cookiesfrombrowser"] = parse_cookies_from_browser(cookies_from_browser)
    if ffmpeg_location:
        opts["ffmpeg_location"] = ffmpeg_location
    if sponsorblock_remove:
        opts["sponsorblock_remove"] = [x.strip() for x in sponsorblock_remove.split(",") if x.strip()]

    # Remove None values because yt-dlp treats some None options as user-provided.
    return {k: v for k, v in opts.items() if v is not None}


def download(urls: list[str], ydl_opts: dict[str, Any], *, console: Console) -> None:
    if not urls:
        raise ValueError("No URL was provided.")
    if not ydl_opts.get("simulate"):
        ensure_ffmpeg(console)
        with DownloadProgress(console) as progress:
            ydl_opts = dict(ydl_opts)
            ydl_opts["progress_hooks"] = [progress.hook]
            import yt_dlp

            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download(urls)
    else:
        import yt_dlp

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download(urls)


def extract_info(url: str, *, flat: bool = False) -> dict[str, Any]:
    opts = {
        "quiet": True,
        "no_warnings": True,
        "skip_download": True,
        "extract_flat": "in_playlist" if flat else False,
    }
    import yt_dlp

    with yt_dlp.YoutubeDL(opts) as ydl:
        info = ydl.extract_info(url, download=False)
        if info is None:
            raise RuntimeError("yt-dlp returned no info for this URL.")
        return info


def print_info(url: str, console: Console, *, raw_json: bool = False) -> None:
    info = extract_info(url, flat=False)
    if raw_json:
        console.print_json(json.dumps(info, ensure_ascii=False, default=str))
        return

    table = Table(title="Video information", show_lines=False)
    table.add_column("Field", style="bold")
    table.add_column("Value")
    fields = [
        ("Title", info.get("title")),
        ("Uploader", info.get("uploader") or info.get("channel")),
        ("Duration", _format_duration(info.get("duration"))),
        ("View count", _format_number(info.get("view_count"))),
        ("Upload date", info.get("upload_date")),
        ("Live status", info.get("live_status")),
        ("Webpage URL", info.get("webpage_url")),
    ]
    for key, value in fields:
        table.add_row(key, str(value) if value is not None else "-")
    console.print(table)


def print_formats(url: str, console: Console) -> None:
    info = extract_info(url, flat=False)
    formats = info.get("formats") or []
    table = Table(title=f"Available formats: {info.get('title', 'video')}", show_lines=False)
    for column in ["ID", "Ext", "Resolution", "FPS", "Size", "Video", "Audio", "Note"]:
        table.add_column(column)

    for fmt in formats:
        height = fmt.get("height")
        width = fmt.get("width")
        resolution = fmt.get("resolution") or (f"{width}x{height}" if width and height else "audio only" if fmt.get("vcodec") == "none" else "-")
        filesize = fmt.get("filesize") or fmt.get("filesize_approx")
        table.add_row(
            str(fmt.get("format_id", "-")),
            str(fmt.get("ext", "-")),
            str(resolution),
            str(fmt.get("fps") or "-"),
            _format_bytes(filesize),
            str(fmt.get("vcodec") or "-"),
            str(fmt.get("acodec") or "-"),
            str(fmt.get("format_note") or fmt.get("format") or "-")[:60],
        )
    console.print(table)


def _format_bytes(value: int | float | None) -> str:
    if not value:
        return "-"
    value = float(value)
    units = ["B", "KiB", "MiB", "GiB", "TiB"]
    idx = 0
    while value >= 1024 and idx < len(units) - 1:
        value /= 1024
        idx += 1
    return f"{value:.1f} {units[idx]}"


def _format_duration(seconds: int | float | None) -> str | None:
    if seconds is None:
        return None
    seconds = int(seconds)
    h, rem = divmod(seconds, 3600)
    m, s = divmod(rem, 60)
    if h:
        return f"{h}:{m:02d}:{s:02d}"
    return f"{m}:{s:02d}"


def _format_number(value: int | None) -> str | None:
    if value is None:
        return None
    return f"{value:,}"
