from __future__ import annotations

from pathlib import Path
from typing import Optional

import typer
from rich.console import Console
from rich.prompt import Confirm, Prompt
from rich.table import Table

from . import __version__
from .config import CONFIG_PATH, PRESETS, apply_preset, expand_path, load_config, write_default_config
from .core import (
    build_ydl_opts,
    download as run_download,
    extract_info,
    normalize_urls,
    print_formats,
    print_info,
    print_plan,
    update_engine,
)
from .errors import render_error
from .formats import available_video_heights, smart_default_quality
from .queue import QUEUE_PATH, QueueItem, append_queue, clear_queue, read_queue, write_queue

app = typer.Typer(
    help="YT Ultimate: a Linux-first CLI for authorized YouTube/video downloads with precise quality control.",
    no_args_is_help=True,
)
queue_app = typer.Typer(help="Persistent download queue commands.", no_args_is_help=True)
app.add_typer(queue_app, name="queue")
console = Console()


def _version_callback(value: bool) -> None:
    if value:
        console.print(f"ytultimate {__version__}")
        raise typer.Exit()


@app.callback()
def main(
    version: bool = typer.Option(
        False,
        "--version",
        callback=_version_callback,
        is_eager=True,
        help="Show version and exit.",
    ),
) -> None:
    return None


def _configured(config: Path | None, preset: str | None) -> dict:
    return apply_preset(load_config(config), preset)


def _common_opts(
    *,
    cfg: dict,
    output_dir: Optional[Path],
    output_template: Optional[str],
    quality: Optional[str],
    exact_quality: bool,
    format_id: Optional[str],
    compat: Optional[bool],
    container: Optional[str],
    playlist: Optional[bool],
    playlist_items: Optional[str],
    subtitles: bool,
    auto_subtitles: bool,
    embed_subtitles: bool,
    sub_langs: Optional[str],
    thumbnail: bool,
    embed_thumbnail: bool,
    metadata: Optional[bool],
    safe_names: Optional[bool],
    archive: Optional[bool],
    archive_path: Optional[Path],
    rate_limit: Optional[str],
    retries: Optional[int],
    fragment_retries: Optional[int],
    concurrent_fragments: Optional[int],
    cookies_from_browser: Optional[str],
    ffmpeg_location: Optional[str],
    sponsorblock_remove: Optional[str],
    sponsorblock_mark: Optional[str],
    dry_run: bool,
    fallback: Optional[str],
    format_sort: Optional[str],
    format_sort_force: Optional[bool],
    write_info_json: Optional[bool],
    write_description: Optional[bool],
    keep_video: bool,
    overwrite: bool,
    sleep_interval: Optional[float],
    max_sleep_interval: Optional[float],
    socket_timeout: Optional[float],
    print_filename: bool,
) -> dict:
    return build_ydl_opts(
        output_dir=expand_path(output_dir or cfg["output_dir"]),
        output_template=output_template or cfg["output_template"],
        quality=quality or cfg["quality"],
        exact_quality=exact_quality,
        format_id=format_id,
        compat=cfg["compat"] if compat is None else compat,
        container=container or cfg["container"],
        playlist=cfg["playlist"] if playlist is None else playlist,
        playlist_items=playlist_items,
        subtitles=subtitles,
        auto_subtitles=auto_subtitles,
        embed_subtitles=embed_subtitles,
        sub_langs=sub_langs or cfg["sub_langs"],
        thumbnail=thumbnail,
        embed_thumbnail=embed_thumbnail,
        metadata=cfg["write_metadata"] if metadata is None else metadata,
        safe_names=cfg["safe_names"] if safe_names is None else safe_names,
        archive=cfg.get("archive", False) if archive is None else archive,
        archive_path=archive_path,
        rate_limit=rate_limit,
        retries=retries if retries is not None else int(cfg["retries"]),
        fragment_retries=fragment_retries
        if fragment_retries is not None
        else int(cfg["fragment_retries"]),
        concurrent_fragments=concurrent_fragments
        if concurrent_fragments is not None
        else int(cfg["concurrent_fragments"]),
        cookies_from_browser=cookies_from_browser,
        ffmpeg_location=ffmpeg_location,
        sponsorblock_remove=sponsorblock_remove if sponsorblock_remove is not None else cfg.get("sponsorblock_remove", ""),
        sponsorblock_mark=sponsorblock_mark if sponsorblock_mark is not None else cfg.get("sponsorblock_mark", ""),
        dry_run=dry_run,
        fallback=fallback or cfg.get("fallback", "lower"),
        format_sort=format_sort if format_sort is not None else cfg.get("format_sort", ""),
        format_sort_force=cfg.get("format_sort_force", False)
        if format_sort_force is None
        else format_sort_force,
        write_info_json=cfg.get("write_info_json", False)
        if write_info_json is None
        else write_info_json,
        write_description=cfg.get("write_description", False)
        if write_description is None
        else write_description,
        keep_video=keep_video,
        no_overwrites=not overwrite,
        sleep_interval=sleep_interval if sleep_interval is not None else cfg.get("sleep_interval"),
        max_sleep_interval=max_sleep_interval
        if max_sleep_interval is not None
        else cfg.get("max_sleep_interval"),
        socket_timeout=socket_timeout if socket_timeout is not None else cfg.get("socket_timeout"),
        print_filename=print_filename,
        console=console,
    )


@app.command("download")
def download_video(
    urls: list[str] = typer.Argument(None, help="One or more video URLs."),
    file: Optional[Path] = typer.Option(None, "--file", "-a", help="Text file with one URL per line."),
    preset: Optional[str] = typer.Option(None, "--preset", help=f"Preset: {', '.join(sorted(PRESETS))}."),
    quality: Optional[str] = typer.Option(
        None,
        "--quality",
        "-q",
        help="best, 720p, 1080p, 1440p, 2160p, etc.",
    ),
    exact_quality: bool = typer.Option(
        False,
        "--exact-quality",
        help="Require exact height instead of best <= height.",
    ),
    fallback: Optional[str] = typer.Option(
        None,
        "--fallback",
        help="Quality fallback: lower, exact, higher, nearest, any.",
    ),
    format_id: Optional[str] = typer.Option(
        None,
        "--format-id",
        "-f",
        help="Manual yt-dlp format ID/selector. Overrides --quality.",
    ),
    output_dir: Optional[Path] = typer.Option(None, "--output-dir", "-o", help="Download directory."),
    output_template: Optional[str] = typer.Option(None, "--template", help="yt-dlp output template."),
    container: Optional[str] = typer.Option(None, "--container", help="Merge container: mp4, mkv, webm, mov, flv, avi."),
    compat: Optional[bool] = typer.Option(None, "--compat/--no-compat", help="Prefer MP4/M4A-friendly formats first."),
    playlist: Optional[bool] = typer.Option(None, "--playlist/--single", help="Allow playlist/channel downloads, or force a single video."),
    playlist_items: Optional[str] = typer.Option(None, "--playlist-items", help="Playlist items, e.g. 1:5,7,-3::."),
    subtitles: bool = typer.Option(False, "--subs", help="Download human-created subtitles."),
    auto_subtitles: bool = typer.Option(False, "--auto-subs", help="Download auto-generated subtitles."),
    embed_subtitles: bool = typer.Option(False, "--embed-subs", help="Embed subtitles into the video when possible."),
    sub_langs: Optional[str] = typer.Option(None, "--sub-langs", help="Subtitle languages, comma-separated, e.g. en.*,bn."),
    thumbnail: bool = typer.Option(False, "--thumbnail", help="Write thumbnail image."),
    embed_thumbnail: bool = typer.Option(False, "--embed-thumbnail", help="Embed thumbnail into media file when possible."),
    metadata: Optional[bool] = typer.Option(None, "--metadata/--no-metadata", help="Write metadata/chapters using ffmpeg."),
    write_info_json: Optional[bool] = typer.Option(None, "--write-info-json/--no-info-json", help="Save yt-dlp info JSON."),
    write_description: Optional[bool] = typer.Option(None, "--write-description/--no-description", help="Save video description text."),
    safe_names: Optional[bool] = typer.Option(None, "--safe-names/--normal-names", help="Use filesystem-safe ASCII filenames."),
    archive: Optional[bool] = typer.Option(None, "--archive/--no-archive", help="Skip files already downloaded before."),
    archive_path: Optional[Path] = typer.Option(None, "--archive-path", help="Custom archive file path."),
    rate_limit: Optional[str] = typer.Option(None, "--rate-limit", help="Limit speed, e.g. 2M or 500K."),
    retries: Optional[int] = typer.Option(None, "--retries", help="Network retry count."),
    fragment_retries: Optional[int] = typer.Option(None, "--fragment-retries", help="Fragment retry count."),
    concurrent_fragments: Optional[int] = typer.Option(None, "--fragments", help="Concurrent fragments."),
    cookies_from_browser: Optional[str] = typer.Option(None, "--cookies-from-browser", help="Use browser cookies, e.g. chrome or firefox, only for content you are allowed to access."),
    ffmpeg_location: Optional[str] = typer.Option(None, "--ffmpeg-location", help="Custom ffmpeg/ffprobe location."),
    sponsorblock_remove: Optional[str] = typer.Option(None, "--sponsorblock-remove", help="Comma-separated SponsorBlock categories to remove."),
    sponsorblock_mark: Optional[str] = typer.Option(None, "--sponsorblock-mark", help="Comma-separated SponsorBlock categories to mark as chapters."),
    format_sort: Optional[str] = typer.Option(None, "--format-sort", help="yt-dlp format sort, e.g. res:720,ext:mp4:m4a."),
    format_sort_force: Optional[bool] = typer.Option(None, "--format-sort-force/--no-format-sort-force", help="Force custom format sort order."),
    keep_video: bool = typer.Option(False, "--keep-video", help="Keep original video after audio extraction/post-processing."),
    overwrite: bool = typer.Option(False, "--overwrite", help="Overwrite existing files."),
    sleep_interval: Optional[float] = typer.Option(None, "--sleep", help="Seconds to sleep between downloads."),
    max_sleep_interval: Optional[float] = typer.Option(None, "--max-sleep", help="Upper bound for random sleep interval."),
    socket_timeout: Optional[float] = typer.Option(None, "--socket-timeout", help="Network socket timeout in seconds."),
    print_filename: bool = typer.Option(False, "--print-filename", help="Print final filename selected by yt-dlp."),
    dry_run: bool = typer.Option(False, "--dry-run", help="Preview extraction without downloading."),
    config: Optional[Path] = typer.Option(None, "--config", help=f"Config path. Default: {CONFIG_PATH}"),
) -> None:
    """Download video with exact, capped, nearest, or best-available quality control."""
    try:
        cfg = _configured(config, preset)
        final_urls = normalize_urls(urls or [], file)
        opts = _common_opts(
            cfg=cfg,
            output_dir=output_dir,
            output_template=output_template,
            quality=quality,
            exact_quality=exact_quality,
            format_id=format_id,
            compat=compat,
            container=container,
            playlist=playlist,
            playlist_items=playlist_items,
            subtitles=subtitles,
            auto_subtitles=auto_subtitles,
            embed_subtitles=embed_subtitles,
            sub_langs=sub_langs,
            thumbnail=thumbnail,
            embed_thumbnail=embed_thumbnail,
            metadata=metadata,
            safe_names=safe_names,
            archive=archive,
            archive_path=archive_path,
            rate_limit=rate_limit,
            retries=retries,
            fragment_retries=fragment_retries,
            concurrent_fragments=concurrent_fragments,
            cookies_from_browser=cookies_from_browser,
            ffmpeg_location=ffmpeg_location,
            sponsorblock_remove=sponsorblock_remove,
            sponsorblock_mark=sponsorblock_mark,
            dry_run=dry_run,
            fallback=fallback,
            format_sort=format_sort,
            format_sort_force=format_sort_force,
            write_info_json=write_info_json,
            write_description=write_description,
            keep_video=keep_video,
            overwrite=overwrite,
            sleep_interval=sleep_interval,
            max_sleep_interval=max_sleep_interval,
            socket_timeout=socket_timeout,
            print_filename=print_filename,
        )
        run_download(final_urls, opts, console=console)
        console.print("[bold green]Done.[/bold green]")
    except Exception as exc:
        render_error(console, exc)
        raise typer.Exit(code=1) from exc


@app.command("audio")
def download_audio(
    urls: list[str] = typer.Argument(None, help="One or more video URLs."),
    file: Optional[Path] = typer.Option(None, "--file", "-a", help="Text file with one URL per line."),
    audio_format: str = typer.Option("mp3", "--audio-format", help="mp3, m4a, opus, flac, wav, best, etc."),
    audio_quality: str = typer.Option("0", "--audio-quality", help="0 best to 10 worst for VBR, or bitrate like 192K."),
    output_dir: Optional[Path] = typer.Option(None, "--output-dir", "-o", help="Download directory."),
    output_template: Optional[str] = typer.Option(None, "--template", help="yt-dlp output template."),
    playlist: Optional[bool] = typer.Option(None, "--playlist/--single", help="Allow playlist/channel downloads, or force a single video."),
    archive: Optional[bool] = typer.Option(None, "--archive/--no-archive", help="Skip files already downloaded before."),
    cookies_from_browser: Optional[str] = typer.Option(None, "--cookies-from-browser", help="Use browser cookies only for content you are allowed to access."),
    config: Optional[Path] = typer.Option(None, "--config", help=f"Config path. Default: {CONFIG_PATH}"),
) -> None:
    """Extract audio from authorized videos."""
    try:
        cfg = load_config(config)
        final_urls = normalize_urls(urls or [], file)
        opts = build_ydl_opts(
            output_dir=expand_path(output_dir or cfg["output_dir"]),
            output_template=output_template or cfg["output_template"],
            quality=cfg["quality"],
            exact_quality=False,
            format_id=None,
            compat=False,
            container=cfg["container"],
            playlist=cfg["playlist"] if playlist is None else playlist,
            playlist_items=None,
            subtitles=False,
            auto_subtitles=False,
            embed_subtitles=False,
            sub_langs=cfg["sub_langs"],
            thumbnail=False,
            embed_thumbnail=True,
            metadata=True,
            safe_names=cfg["safe_names"],
            archive=cfg.get("archive", False) if archive is None else archive,
            archive_path=None,
            rate_limit=None,
            retries=int(cfg["retries"]),
            fragment_retries=int(cfg["fragment_retries"]),
            concurrent_fragments=int(cfg["concurrent_fragments"]),
            cookies_from_browser=cookies_from_browser,
            ffmpeg_location=None,
            sponsorblock_remove=None,
            sponsorblock_mark=None,
            dry_run=False,
            audio_only=True,
            audio_format=audio_format,
            audio_quality=audio_quality,
            fallback=cfg.get("fallback", "lower"),
            socket_timeout=cfg.get("socket_timeout"),
            console=console,
        )
        run_download(final_urls, opts, console=console)
        console.print("[bold green]Done.[/bold green]")
    except Exception as exc:
        render_error(console, exc)
        raise typer.Exit(code=1) from exc


@app.command("wizard")
def wizard(
    url: str = typer.Argument(..., help="Video URL."),
    output_dir: Optional[Path] = typer.Option(None, "--output-dir", "-o", help="Download directory."),
    cookies_from_browser: Optional[str] = typer.Option(None, "--cookies-from-browser", help="Use browser cookies only for content you are allowed to access."),
    config: Optional[Path] = typer.Option(None, "--config", help=f"Config path. Default: {CONFIG_PATH}"),
) -> None:
    """Interactive downloader: inspect formats, choose quality, then download."""
    try:
        cfg = load_config(config)
        info = extract_info(url, cookies_from_browser=cookies_from_browser)
        heights = available_video_heights(info)
        default_quality = smart_default_quality(heights)
        choices = ["best"] + [f"{h}p" for h in heights] + ["manual"]

        console.print(f"[bold]{info.get('title', 'video')}[/bold]")
        console.print(f"Detected qualities: {', '.join([f'{h}p' for h in heights]) or 'none'}")
        selected = Prompt.ask("Choose quality", choices=choices, default=default_quality)
        if selected == "manual":
            selected = Prompt.ask("Type quality or format selector", default=default_quality)

        fallback = Prompt.ask(
            "Fallback policy",
            choices=["lower", "exact", "higher", "nearest", "any"],
            default=cfg.get("fallback", "lower"),
        )
        compat = Confirm.ask("Prefer MP4/M4A compatibility?", default=bool(cfg.get("compat", False)))
        archive = Confirm.ask("Use download archive to avoid duplicates?", default=bool(cfg.get("archive", False)))

        opts = build_ydl_opts(
            output_dir=expand_path(output_dir or cfg["output_dir"]),
            output_template=cfg["output_template"],
            quality=selected,
            exact_quality=fallback == "exact",
            format_id=None,
            compat=compat,
            container=cfg["container"],
            playlist=False,
            playlist_items=None,
            subtitles=False,
            auto_subtitles=False,
            embed_subtitles=False,
            sub_langs=cfg["sub_langs"],
            thumbnail=False,
            embed_thumbnail=False,
            metadata=cfg["write_metadata"],
            safe_names=cfg["safe_names"],
            archive=archive,
            archive_path=None,
            rate_limit=None,
            retries=int(cfg["retries"]),
            fragment_retries=int(cfg["fragment_retries"]),
            concurrent_fragments=int(cfg["concurrent_fragments"]),
            cookies_from_browser=cookies_from_browser,
            ffmpeg_location=None,
            sponsorblock_remove=cfg.get("sponsorblock_remove", ""),
            sponsorblock_mark=cfg.get("sponsorblock_mark", ""),
            dry_run=False,
            fallback=fallback,
            format_sort=cfg.get("format_sort", ""),
            format_sort_force=bool(cfg.get("format_sort_force", False)),
            write_info_json=bool(cfg.get("write_info_json", False)),
            write_description=bool(cfg.get("write_description", False)),
            socket_timeout=cfg.get("socket_timeout"),
            console=console,
        )
        run_download([url], opts, console=console)
        console.print("[bold green]Done.[/bold green]")
    except Exception as exc:
        render_error(console, exc)
        raise typer.Exit(code=1) from exc


@app.command("formats")
def formats(
    url: str = typer.Argument(..., help="Video URL."),
    cookies_from_browser: Optional[str] = typer.Option(None, "--cookies-from-browser", help="Use browser cookies only for content you are allowed to access."),
) -> None:
    """List all available video/audio formats before downloading."""
    try:
        print_formats(url, console, cookies_from_browser=cookies_from_browser)
    except Exception as exc:
        render_error(console, exc)
        raise typer.Exit(code=1) from exc


@app.command("plan")
def plan(
    url: str = typer.Argument(..., help="Video URL."),
    cookies_from_browser: Optional[str] = typer.Option(None, "--cookies-from-browser", help="Use browser cookies only for content you are allowed to access."),
) -> None:
    """Inspect a URL and print recommended commands without downloading."""
    try:
        print_plan(url, console, cookies_from_browser=cookies_from_browser)
    except Exception as exc:
        render_error(console, exc)
        raise typer.Exit(code=1) from exc


@app.command("info")
def info(
    url: str = typer.Argument(..., help="Video URL."),
    json_output: bool = typer.Option(False, "--json", help="Print raw JSON metadata."),
    cookies_from_browser: Optional[str] = typer.Option(None, "--cookies-from-browser", help="Use browser cookies only for content you are allowed to access."),
) -> None:
    """Show video metadata."""
    try:
        print_info(url, console, raw_json=json_output, cookies_from_browser=cookies_from_browser)
    except Exception as exc:
        render_error(console, exc)
        raise typer.Exit(code=1) from exc


@app.command("init-config")
def init_config(
    path: Optional[Path] = typer.Option(None, "--path", help=f"Config path. Default: {CONFIG_PATH}"),
    force: bool = typer.Option(False, "--force", help="Overwrite existing config."),
) -> None:
    """Create a default config file."""
    target = write_default_config(path, overwrite=force)
    console.print(f"[green]Config ready:[/green] {target}")


@app.command("doctor")
def doctor() -> None:
    """Check required external tools and show upgrade guidance."""
    import shutil

    table = Table(title="YT Ultimate doctor")
    table.add_column("Component")
    table.add_column("Status")
    table.add_column("Fix")

    try:
        import yt_dlp

        ytdlp_status = f"found {yt_dlp.version.__version__}"
        ytdlp_fix = "ytdown update-engine"
    except Exception:
        ytdlp_status = "missing"
        ytdlp_fix = "pip install -e ."

    table.add_row("ytultimate", __version__, "-")
    table.add_row("yt-dlp", ytdlp_status, ytdlp_fix)
    table.add_row("ffmpeg", "found" if shutil.which("ffmpeg") else "missing", "sudo apt install ffmpeg")
    table.add_row("ffprobe", "found" if shutil.which("ffprobe") else "missing", "sudo apt install ffmpeg")
    table.add_row("git", "found" if shutil.which("git") else "missing", "sudo apt install git")
    table.add_row("config", str(CONFIG_PATH), "ytdown init-config")
    table.add_row("queue", str(QUEUE_PATH), "ytdown queue add URL")
    console.print(table)


@app.command("selfcheck")
def selfcheck() -> None:
    """Alias for doctor."""
    doctor()


@app.command("update-engine")
def update_ytdlp(
    nightly: bool = typer.Option(False, "--nightly", help="Allow pre-release/nightly yt-dlp builds."),
) -> None:
    """Update the yt-dlp extraction engine installed in the current Python environment."""
    code = update_engine(pre_release=nightly)
    if code == 0:
        console.print("[green]yt-dlp update command completed.[/green]")
    else:
        console.print("[red]yt-dlp update command failed.[/red]")
        raise typer.Exit(code=code)


@queue_app.command("add")
def queue_add(
    urls: list[str] = typer.Argument(None, help="One or more video URLs."),
    file: Optional[Path] = typer.Option(None, "--file", "-a", help="Text file with one URL per line."),
    quality: str = typer.Option("best", "--quality", "-q", help="best, 720p, 1080p, etc."),
    fallback: str = typer.Option("lower", "--fallback", help="lower, exact, higher, nearest, any."),
    compat: bool = typer.Option(False, "--compat", help="Prefer MP4/M4A-friendly formats."),
    playlist: bool = typer.Option(False, "--playlist", help="Allow playlist/channel downloads."),
    queue_path: Optional[Path] = typer.Option(None, "--queue", help=f"Queue path. Default: {QUEUE_PATH}"),
) -> None:
    """Add URLs to the persistent queue."""
    try:
        final_urls = normalize_urls(urls or [], file)
        if not final_urls:
            raise ValueError("No URL was provided.")
        items = [
            QueueItem.create(
                url,
                quality=quality,
                fallback=fallback,
                compat=compat,
                playlist=playlist,
            )
            for url in final_urls
        ]
        target = append_queue(items, queue_path)
        console.print(f"[green]Added {len(items)} item(s) to queue:[/green] {target}")
    except Exception as exc:
        render_error(console, exc)
        raise typer.Exit(code=1) from exc


@queue_app.command("list")
def queue_list(
    queue_path: Optional[Path] = typer.Option(None, "--queue", help=f"Queue path. Default: {QUEUE_PATH}"),
) -> None:
    """Show queued, done, and failed items."""
    items = read_queue(queue_path)
    table = Table(title=f"Queue: {queue_path or QUEUE_PATH}")
    for column in ["ID", "Status", "Quality", "Fallback", "Compat", "Playlist", "URL", "Error"]:
        table.add_column(column)
    for item in items:
        table.add_row(
            item.id,
            item.status,
            item.quality,
            item.fallback,
            "yes" if item.compat else "no",
            "yes" if item.playlist else "no",
            item.url[:70],
            (item.error or "")[:50],
        )
    console.print(table)


@queue_app.command("run")
def queue_run(
    limit: Optional[int] = typer.Option(None, "--limit", help="Maximum queued items to run."),
    queue_path: Optional[Path] = typer.Option(None, "--queue", help=f"Queue path. Default: {QUEUE_PATH}"),
    output_dir: Optional[Path] = typer.Option(None, "--output-dir", "-o", help="Download directory."),
    config: Optional[Path] = typer.Option(None, "--config", help=f"Config path. Default: {CONFIG_PATH}"),
    continue_on_error: bool = typer.Option(True, "--continue/--stop-on-error", help="Continue queue after one item fails."),
) -> None:
    """Run queued downloads sequentially and save success/failure state."""
    cfg = load_config(config)
    items = read_queue(queue_path)
    pending = [item for item in items if item.status == "queued"]
    if limit is not None:
        pending = pending[:limit]
    if not pending:
        console.print("[yellow]No queued items to run.[/yellow]")
        return

    for item in pending:
        console.rule(f"Queue item {item.id}")
        try:
            opts = build_ydl_opts(
                output_dir=expand_path(output_dir or cfg["output_dir"]),
                output_template=cfg["output_template"],
                quality=item.quality,
                exact_quality=item.fallback == "exact",
                format_id=None,
                compat=item.compat,
                container=cfg["container"],
                playlist=item.playlist,
                playlist_items=None,
                subtitles=False,
                auto_subtitles=False,
                embed_subtitles=False,
                sub_langs=cfg["sub_langs"],
                thumbnail=False,
                embed_thumbnail=False,
                metadata=cfg["write_metadata"],
                safe_names=cfg["safe_names"],
                archive=True,
                archive_path=None,
                rate_limit=None,
                retries=int(cfg["retries"]),
                fragment_retries=int(cfg["fragment_retries"]),
                concurrent_fragments=int(cfg["concurrent_fragments"]),
                cookies_from_browser=None,
                ffmpeg_location=None,
                sponsorblock_remove=cfg.get("sponsorblock_remove", ""),
                sponsorblock_mark=cfg.get("sponsorblock_mark", ""),
                dry_run=False,
                fallback=item.fallback,
                format_sort=cfg.get("format_sort", ""),
                format_sort_force=bool(cfg.get("format_sort_force", False)),
                write_info_json=bool(cfg.get("write_info_json", False)),
                write_description=bool(cfg.get("write_description", False)),
                socket_timeout=cfg.get("socket_timeout"),
                console=console,
            )
            run_download([item.url], opts, console=console)
            item.mark("done")
            console.print(f"[green]Queue item done:[/green] {item.id}")
        except Exception as exc:  # noqa: PERF203 - state must be persisted per item
            item.mark("failed", str(exc))
            render_error(console, exc)
            if not continue_on_error:
                write_queue(items, queue_path)
                raise typer.Exit(code=1) from exc
        finally:
            write_queue(items, queue_path)

    console.print("[bold green]Queue run finished.[/bold green]")


@queue_app.command("clear")
def queue_clear(
    queue_path: Optional[Path] = typer.Option(None, "--queue", help=f"Queue path. Default: {QUEUE_PATH}"),
) -> None:
    """Clear the queue file."""
    target = clear_queue(queue_path)
    console.print(f"[green]Queue cleared:[/green] {target}")
