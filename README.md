# YT Ultimate CLI

A Linux-first command-line downloader for authorized YouTube/video downloads with clean progress UI, strong resolution control, batch support, subtitles, metadata, thumbnails, audio extraction, archive tracking, and local Git readiness.

> Use this tool only for videos you own, videos you have permission to download, or content whose license/platform rules allow downloading. This project does not bypass DRM or access controls.

## Why this design

YouTube extraction changes frequently, so this CLI wraps `yt-dlp` instead of trying to scrape YouTube directly. `yt-dlp` handles extraction, format listing, merging, subtitles, metadata, playlists, and many edge cases; this project adds a cleaner opinionated interface on top.

## Features

- Download best available video/audio.
- Download capped quality: `720p`, `1080p`, `1440p`, `2160p`, or custom height.
- Exact quality mode: require exactly `720p`, etc.
- Manual format ID mode after viewing `ytu formats`.
- MP4 compatibility preference mode.
- Batch URL download from a text file.
- Playlist/channel mode is opt-in using `--playlist`.
- Progress UI using Rich.
- Audio extraction to `mp3`, `m4a`, `opus`, `flac`, `wav`, etc.
- Subtitles and auto-subtitles.
- Thumbnail writing/embedding.
- Metadata and chapter embedding.
- Download archive to avoid duplicates.
- Browser cookie support for videos you are allowed to access.
- Local JSON config file.
- Git initialized for immediate remote push.

## Requirements

```bash
sudo apt update
sudo apt install -y python3 python3-venv python3-pip ffmpeg git
```

`ffmpeg` is important because high-quality YouTube streams are often split into separate video and audio files that must be merged.

## Install locally

From inside this project folder:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -e .
```

Now test:

```bash
ytu --version
ytu selfcheck
```

## Basic usage

Download best quality single video:

```bash
ytu download "https://www.youtube.com/watch?v=VIDEO_ID"
```

Download best video at or below 720p:

```bash
ytu download "https://www.youtube.com/watch?v=VIDEO_ID" --quality 720p
```

Require exactly 720p:

```bash
ytu download "https://www.youtube.com/watch?v=VIDEO_ID" --quality 720p --exact-quality
```

Prefer MP4/M4A-friendly formats:

```bash
ytu download "https://www.youtube.com/watch?v=VIDEO_ID" --quality 1080p --compat --container mp4
```

List all available formats:

```bash
ytu formats "https://www.youtube.com/watch?v=VIDEO_ID"
```

Use a specific format ID or custom yt-dlp selector:

```bash
ytu download "https://www.youtube.com/watch?v=VIDEO_ID" --format-id "137+140"
```

Download a playlist intentionally:

```bash
ytu download "PLAYLIST_URL" --playlist --quality 720p --archive
```

Download selected playlist items:

```bash
ytu download "PLAYLIST_URL" --playlist --playlist-items "1:5,8,10" --quality 720p
```

Batch download:

```bash
ytu download --file examples/urls.txt --quality 720p --archive
```

Extract audio:

```bash
ytu audio "https://www.youtube.com/watch?v=VIDEO_ID" --audio-format mp3 --audio-quality 0
```

Download subtitles:

```bash
ytu download "VIDEO_URL" --quality 720p --subs --embed-subs --sub-langs "en.*,bn"
```

Preview without downloading:

```bash
ytu download "VIDEO_URL" --quality 720p --dry-run
```

## Config file

Create config:

```bash
ytu init-config
```

Default path:

```text
~/.config/ytultimate/config.json
```

Example config:

```json
{
  "output_dir": "~/Videos/YTUltimate",
  "quality": "best",
  "container": "mp4",
  "output_template": "%(uploader|Unknown)s/%(title).180B [%(id)s].%(ext)s",
  "sub_langs": "en.*",
  "concurrent_fragments": 4,
  "retries": 10,
  "fragment_retries": 10,
  "playlist": false,
  "safe_names": false,
  "compat": false,
  "write_metadata": true
}
```

## Add to GitHub later

This folder is already initialized as a local Git repository with an initial commit. After you create an empty GitHub repo, run:

```bash
git remote add origin git@github.com:YOUR_USERNAME/YOUR_REPO.git
git branch -M main
git push -u origin main
```

Or with HTTPS:

```bash
git remote add origin https://github.com/YOUR_USERNAME/YOUR_REPO.git
git branch -M main
git push -u origin main
```

## Development

```bash
source .venv/bin/activate
python -m compileall ytu
python -m pytest
```

## Important quality behavior

- `--quality 720p` means best available video **at or below** 720p.
- `--quality 720p --exact-quality` means only exactly 720p is acceptable.
- `--format-id` overrides all automatic quality logic.
- `--compat` prefers MP4/M4A-friendly streams before falling back to other available streams.
