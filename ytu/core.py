from __future__ import annotations

import json
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any, Iterable

from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from .config import expand_path
from .formats import (
    available_video_heights,
    build_audio_format,
    build_video_format,
    count_formats_by_height,
    smart_default_quality,
)
from .progress import DownloadProgress, FinalPathReporter, RichLogger

SUPPORTED_CONTAINERS = {"mp4", "mkv", "webm", "mov", "flv", "avi"}
SUPPORTED_AUDIO_FORMATS = {"best", "aac", "alac", "flac", "m4a", "mp3", "opus", "vorbis", "wav"}
SPONSORBLOCK_CATEGORIES = {
    "sponsor",
    "intro",
    "outro",
    "selfpromo",
    "preview",
    "interaction",
    "music_offtopic",
    "poi_highlight",
    "chapter",
    "all",
}


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


def parse_csv(value: str | None) -> list[str]:
    return [x.strip() for x in (value or "").split(",") if x.strip()]


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
    sponsorblock_mark: str | None = None,
    dry_run: bool = False,
    audio_only: bool = False,
    audio_format: str = "mp3",
    audio_quality: str = "0",
    fallback: str = "lower",
    format_sort: str | None = None,
    format_sort_force: bool = False,
    write_info_json: bool = False,
    write_description: bool = False,
    keep_video: bool = False,
    no_overwrites: bool = True,
    sleep_interval: float | None = None,
    max_sleep_interval: float | None = None,
    socket_timeout: float | None = None,
    print_filename: bool = False,
    remote_components: str | None = None,
    console: Console | None = None,
) -> dict[str, Any]:
    output_dir.mkdir(parents=True, exist_ok=True)
    template_path = Path(output_template).expanduser()
    template_is_absolute = template_path.is_absolute()
    outtmpl = str(template_path) if template_is_absolute else output_template

    if container not in SUPPORTED_CONTAINERS:
        raise ValueError(
            f"Unsupported container '{container}'. Use one of: {', '.join(sorted(SUPPORTED_CONTAINERS))}"
        )
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

    remove_categories = parse_csv(sponsorblock_remove)
    mark_categories = parse_csv(sponsorblock_mark)
    for category in remove_categories + mark_categories:
        if category not in SPONSORBLOCK_CATEGORIES:
            raise ValueError(
                f"Unsupported SponsorBlock category '{category}'. "
                f"Use one of: {', '.join(sorted(SPONSORBLOCK_CATEGORIES))}"
            )

    opts: dict[str, Any] = {
        "format": build_audio_format(format_id)
        if audio_only
        else build_video_format(
            quality,
            exact=exact_quality,
            format_id=format_id,
            compat=compat,
            fallback=fallback,
        ),
        "outtmpl": {"default": outtmpl},
        "merge_output_format": container,
        "noplaylist": not playlist,
        "playlist_items": playlist_items,
        "writesubtitles": subtitles,
        "writeautomaticsub": auto_subtitles,
        "embedsubtitles": embed_subtitles,
        "subtitleslangs": parse_csv(sub_langs),
        "writethumbnail": thumbnail or embed_thumbnail,
        "writeinfojson": write_info_json,
        "writedescription": write_description,
        "restrictfilenames": safe_names,
        "retries": retries,
        "fragment_retries": fragment_retries,
        "concurrent_fragment_downloads": concurrent_fragments,
        "ratelimit": rate_limit,
        "ignoreerrors": False,
        "continuedl": True,
        "overwrites": not no_overwrites,
        "nopart": False,
        "quiet": False,
        "no_warnings": False,
        "simulate": dry_run,
        "skip_download": dry_run,
        "keepvideo": keep_video,
        "postprocessors": postprocessors,
        "format_sort": parse_csv(format_sort),
        "format_sort_force": format_sort_force,
        "sleep_interval": sleep_interval,
        "max_sleep_interval": max_sleep_interval,
        "socket_timeout": socket_timeout,
        "print_to_file": None,
        "forceprint": {"video": ["filename"]} if print_filename else None,
        "logger": RichLogger(console or Console()),
        "remote_components": parse_csv(remote_components),
    }

    if not template_is_absolute:
        opts["paths"] = {"home": str(output_dir)}
    if archive:
        opts["download_archive"] = str(archive_path or (output_dir / ".download-archive.txt"))
    if cookies_from_browser:
        opts["cookiesfrombrowser"] = parse_cookies_from_browser(cookies_from_browser)
    if ffmpeg_location:
        opts["ffmpeg_location"] = ffmpeg_location
    if remove_categories:
        opts["sponsorblock_remove"] = remove_categories
    if mark_categories:
        opts["sponsorblock_mark"] = mark_categories

    # Remove None/empty-list values because yt-dlp treats some None options as user-provided.
    cleaned: dict[str, Any] = {}
    for key, value in opts.items():
        if value is None:
            continue
        if value == []:
            continue
        cleaned[key] = value
    return cleaned


def download(urls: list[str], ydl_opts: dict[str, Any], *, console: Console) -> None:
    if not urls:
        raise ValueError("No URL was provided.")
    if not ydl_opts.get("simulate"):
        ensure_ffmpeg(console)
        with DownloadProgress(console) as progress:
            ydl_opts = dict(ydl_opts)
            reporter = FinalPathReporter(console)
            ydl_opts["progress_hooks"] = [progress.hook]
            ydl_opts["postprocessor_hooks"] = [reporter.hook]
            import yt_dlp

            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download(urls)
            reporter.print_summary()
            output_home = ydl_opts.get("paths", {}).get("home")
            if output_home:
                console.print(f"[cyan]Output directory:[/cyan] {output_home}")
    else:
        import yt_dlp

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download(urls)


def extract_info(
    url: str,
    *,
    flat: bool = False,
    cookies_from_browser: str | None = None,
    playlist: bool = False,
) -> dict[str, Any]:
    opts: dict[str, Any] = {
        "quiet": True,
        "no_warnings": True,
        "skip_download": True,
        "extract_flat": "in_playlist" if flat else False,
        "noplaylist": not playlist,
    }
    cookies = parse_cookies_from_browser(cookies_from_browser)
    if cookies:
        opts["cookiesfrombrowser"] = cookies
    import yt_dlp

    with yt_dlp.YoutubeDL(opts) as ydl:
        info = ydl.extract_info(url, download=False)
        if info is None:
            raise RuntimeError("yt-dlp returned no info for this URL.")
        return info


def print_info(
    url: str,
    console: Console,
    *,
    raw_json: bool = False,
    cookies_from_browser: str | None = None,
) -> None:
    info = extract_info(url, flat=False, cookies_from_browser=cookies_from_browser)
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
        ("Upload date", _format_date(info.get("upload_date"))),
        ("Live status", info.get("live_status")),
        ("Availability", info.get("availability")),
        ("Webpage URL", info.get("webpage_url")),
    ]
    for key, value in fields:
        table.add_row(key, str(value) if value is not None else "-")
    console.print(table)


def print_formats(url: str, console: Console, *, cookies_from_browser: str | None = None, remote_components: str | None = None) -> None:
    info = extract_info(url, flat=False, cookies_from_browser=cookies_from_browser)
    formats = info.get("formats") or []
    table = Table(title=f"Available formats: {info.get('title', 'video')}", show_lines=False)
    for column in ["ID", "Ext", "Resolution", "FPS", "Size", "VCodec", "ACodec", "Bitrate", "Note"]:
        table.add_column(column)

    for fmt in formats:
        height = fmt.get("height")
        width = fmt.get("width")
        resolution = fmt.get("resolution") or (
            f"{width}x{height}"
            if width and height
            else "audio only"
            if fmt.get("vcodec") == "none"
            else "-"
        )
        filesize = fmt.get("filesize") or fmt.get("filesize_approx")
        tbr = fmt.get("tbr") or fmt.get("vbr") or fmt.get("abr")
        table.add_row(
            str(fmt.get("format_id", "-")),
            str(fmt.get("ext", "-")),
            str(resolution),
            str(fmt.get("fps") or "-"),
            _format_bytes(filesize),
            str(fmt.get("vcodec") or "-"),
            str(fmt.get("acodec") or "-"),
            f"{tbr:g}k" if isinstance(tbr, (int, float)) else "-",
            str(fmt.get("format_note") or fmt.get("format") or "-")[:60],
        )
    console.print(table)


def print_plan(url: str, console: Console, *, cookies_from_browser: str | None = None, remote_components: str | None = None) -> None:
    info = extract_info(url, flat=False, cookies_from_browser=cookies_from_browser)
    heights = available_video_heights(info)
    counts = count_formats_by_height(info)
    default_quality = smart_default_quality(heights)

    console.print(
        Panel(
            f"[bold]{info.get('title', 'video')}[/bold]\n"
            f"Uploader: {info.get('uploader') or info.get('channel') or '-'}\n"
            f"Duration: {_format_duration(info.get('duration')) or '-'}\n"
            f"Recommended default: [green]{default_quality}[/green] with --fallback lower",
            title="Download plan",
            border_style="cyan",
        )
    )

    quality_table = Table(title="Detected video quality ladder")
    quality_table.add_column("Quality")
    quality_table.add_column("Format count")
    quality_table.add_column("Command")
    if not counts:
        quality_table.add_row("-", "0", "No video formats detected")
    for height, count in counts.items():
        quality_table.add_row(
            f"{height}p",
            str(count),
            f'ytdown download "{url}" --quality {height}p --fallback lower',
        )
    console.print(quality_table)

    console.print("Useful commands:")
    console.print(f'  ytdown download "{url}" --quality {default_quality}')
    console.print(f'  ytdown wizard "{url}"')
    console.print(f'  ytdown formats "{url}"')


def update_engine(pre_release: bool = False) -> int:
    cmd = [sys.executable, "-m", "pip", "install", "-U"]
    if pre_release:
        cmd.append("--pre")
    cmd.append("yt-dlp")
    return subprocess.call(cmd)


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


def _format_date(value: str | None) -> str | None:
    if not value or len(value) != 8:
        return value
    return f"{value[:4]}-{value[4:6]}-{value[6:8]}"


def _format_number(value: int | None) -> str | None:
    if value is None:
        return None
    return f"{value:,}"
