from __future__ import annotations

from pathlib import Path
from typing import Optional

import typer
from rich.console import Console

from . import __version__
from .config import CONFIG_PATH, expand_path, load_config, write_default_config
from .core import build_ydl_opts, download as run_download, normalize_urls, print_formats, print_info

app = typer.Typer(
    help="YT Ultimate: a polished CLI for authorized YouTube/video downloads with precise quality control.",
    no_args_is_help=True,
)
console = Console()


def _version_callback(value: bool) -> None:
    if value:
        console.print(f"ytultimate {__version__}")
        raise typer.Exit()


@app.callback()
def main(
    version: bool = typer.Option(False, "--version", callback=_version_callback, is_eager=True, help="Show version and exit."),
) -> None:
    return None


@app.command("download")
def download_video(
    urls: list[str] = typer.Argument(None, help="One or more video URLs."),
    file: Optional[Path] = typer.Option(None, "--file", "-a", help="Text file with one URL per line."),
    quality: Optional[str] = typer.Option(None, "--quality", "-q", help="best, 720p, 1080p, 1440p, 2160p, etc."),
    exact_quality: bool = typer.Option(False, "--exact-quality", help="Require exact height instead of best <= height."),
    format_id: Optional[str] = typer.Option(None, "--format-id", "-f", help="Manual yt-dlp format ID/selector. Overrides --quality."),
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
    safe_names: Optional[bool] = typer.Option(None, "--safe-names/--normal-names", help="Use filesystem-safe ASCII filenames."),
    archive: bool = typer.Option(False, "--archive", help="Skip files already downloaded before."),
    archive_path: Optional[Path] = typer.Option(None, "--archive-path", help="Custom archive file path."),
    rate_limit: Optional[str] = typer.Option(None, "--rate-limit", help="Limit speed, e.g. 2M or 500K."),
    retries: Optional[int] = typer.Option(None, "--retries", help="Network retry count."),
    fragment_retries: Optional[int] = typer.Option(None, "--fragment-retries", help="Fragment retry count."),
    concurrent_fragments: Optional[int] = typer.Option(None, "--fragments", help="Concurrent fragments."),
    cookies_from_browser: Optional[str] = typer.Option(None, "--cookies-from-browser", help="Use browser cookies, e.g. chrome or firefox. Only for videos you are allowed to access."),
    ffmpeg_location: Optional[str] = typer.Option(None, "--ffmpeg-location", help="Custom ffmpeg/ffprobe location."),
    sponsorblock_remove: Optional[str] = typer.Option(None, "--sponsorblock-remove", help="Comma-separated SponsorBlock categories to remove."),
    dry_run: bool = typer.Option(False, "--dry-run", help="Preview extraction without downloading."),
    config: Optional[Path] = typer.Option(None, "--config", help=f"Config path. Default: {CONFIG_PATH}"),
) -> None:
    """Download video with exact or capped resolution control."""
    try:
        cfg = load_config(config)
        final_urls = normalize_urls(urls or [], file)
        opts = build_ydl_opts(
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
            archive=archive,
            archive_path=archive_path,
            rate_limit=rate_limit,
            retries=retries if retries is not None else int(cfg["retries"]),
            fragment_retries=fragment_retries if fragment_retries is not None else int(cfg["fragment_retries"]),
            concurrent_fragments=concurrent_fragments if concurrent_fragments is not None else int(cfg["concurrent_fragments"]),
            cookies_from_browser=cookies_from_browser,
            ffmpeg_location=ffmpeg_location,
            sponsorblock_remove=sponsorblock_remove,
            dry_run=dry_run,
            console=console,
        )
        run_download(final_urls, opts, console=console)
        console.print("[bold green]Done.[/bold green]")
    except Exception as exc:
        console.print(f"[bold red]Error:[/bold red] {exc}")
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
    archive: bool = typer.Option(False, "--archive", help="Skip files already downloaded before."),
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
            archive=archive,
            archive_path=None,
            rate_limit=None,
            retries=int(cfg["retries"]),
            fragment_retries=int(cfg["fragment_retries"]),
            concurrent_fragments=int(cfg["concurrent_fragments"]),
            cookies_from_browser=cookies_from_browser,
            ffmpeg_location=None,
            sponsorblock_remove=None,
            dry_run=False,
            audio_only=True,
            audio_format=audio_format,
            audio_quality=audio_quality,
            console=console,
        )
        run_download(final_urls, opts, console=console)
        console.print("[bold green]Done.[/bold green]")
    except Exception as exc:
        console.print(f"[bold red]Error:[/bold red] {exc}")
        raise typer.Exit(code=1) from exc


@app.command("formats")
def formats(url: str = typer.Argument(..., help="Video URL.")) -> None:
    """List all available video/audio formats before downloading."""
    try:
        print_formats(url, console)
    except Exception as exc:
        console.print(f"[bold red]Error:[/bold red] {exc}")
        raise typer.Exit(code=1) from exc


@app.command("info")
def info(
    url: str = typer.Argument(..., help="Video URL."),
    json_output: bool = typer.Option(False, "--json", help="Print raw JSON metadata."),
) -> None:
    """Show video metadata."""
    try:
        print_info(url, console, raw_json=json_output)
    except Exception as exc:
        console.print(f"[bold red]Error:[/bold red] {exc}")
        raise typer.Exit(code=1) from exc


@app.command("init-config")
def init_config(
    path: Optional[Path] = typer.Option(None, "--path", help=f"Config path. Default: {CONFIG_PATH}"),
    force: bool = typer.Option(False, "--force", help="Overwrite existing config."),
) -> None:
    """Create a default config file."""
    target = write_default_config(path, overwrite=force)
    console.print(f"[green]Config ready:[/green] {target}")


@app.command("selfcheck")
def selfcheck() -> None:
    """Check required external tools."""
    import shutil
    import yt_dlp

    console.print(f"ytultimate: [green]{__version__}[/green]")
    console.print(f"yt-dlp: [green]{yt_dlp.version.__version__}[/green]")
    console.print(f"ffmpeg: {'[green]found[/green]' if shutil.which('ffmpeg') else '[red]missing[/red]'}")
    console.print(f"config: {CONFIG_PATH}")
