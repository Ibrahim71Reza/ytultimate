# YT Ultimate CLI

A Linux-first power CLI for **authorized** YouTube/video downloads with smart resolution control, interactive quality selection, queue management, batch downloads, playlist controls, metadata, subtitles, thumbnails, audio extraction, retry tuning, browser-cookie support, and local Git readiness.

> Use this tool only for videos you own, videos you have permission to download, or content whose license/platform rules allow downloading. This project does not bypass DRM, payment, private-video permissions, or platform access controls.

## Why this design

YouTube extraction changes frequently, so this CLI wraps `yt-dlp` instead of trying to scrape YouTube directly. `yt-dlp` handles extraction, format listing, merging, subtitles, metadata, playlists, SponsorBlock, and many edge cases; this project adds a cleaner, safer, more opinionated interface on top.

## Feature map

### Quality and format control

- Best available quality: `ytu download URL`
- Capped quality: `--quality 720p`, `--quality 1080p`, custom height, etc.
- Exact quality: `--quality 720p --exact-quality`
- Smart fallback: `--fallback lower|exact|higher|nearest|any`
- MP4/M4A compatibility preference: `--compat --container mp4`
- Manual format selector: `--format-id "137+140"`
- Format sorting passthrough: `--format-sort "res:720,ext:mp4:m4a"`
- Format listing: `ytu formats URL`
- Download planning: `ytu plan URL`

### Professional download workflow

- Interactive wizard: `ytu wizard URL`
- Batch URL file: `ytu download --file urls.txt`
- Persistent queue: `ytu queue add`, `ytu queue list`, `ytu queue run`, `ytu queue clear`
- Playlist opt-in: `--playlist`
- Playlist item ranges: `--playlist-items "1:5,8,10"`
- Download archive: `--archive`
- Resume partial downloads by default
- Retry and fragment retry controls
- Speed limit: `--rate-limit 2M`
- Sleep interval and socket timeout controls
- No overwrite by default; explicit `--overwrite` available

### Metadata, subtitles, thumbnails

- Human subtitles: `--subs`
- Auto subtitles: `--auto-subs`
- Embed subtitles: `--embed-subs`
- Subtitle languages: `--sub-langs "en.*,bn"`
- Write thumbnail: `--thumbnail`
- Embed thumbnail: `--embed-thumbnail`
- Embed metadata and chapters by default
- Write info JSON: `--write-info-json`
- Write description: `--write-description`
- SponsorBlock mark/remove support where available

### Audio

- Audio extraction command: `ytu audio URL`
- Supports `mp3`, `m4a`, `opus`, `flac`, `wav`, `best`, etc.
- Embeds thumbnail and metadata for audio downloads when possible

### Maintenance

- Dependency check: `ytu doctor`
- Alias: `ytu selfcheck`
- Update extraction engine: `ytu update-engine`
- Optional pre-release/nightly engine update: `ytu update-engine --nightly`
- Config file: `~/.config/ytultimate/config.json`
- Git initialized locally for later GitHub remote push

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
ytu doctor
```

## Fast examples

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

Try exact/lower/higher/best fallback automatically:

```bash
ytu download "VIDEO_URL" --quality 720p --fallback nearest
```

Prefer MP4/M4A-friendly output:

```bash
ytu download "VIDEO_URL" --quality 1080p --compat --container mp4
```

Plan before downloading:

```bash
ytu plan "VIDEO_URL"
```

Interactive mode:

```bash
ytu wizard "VIDEO_URL"
```

List all available formats:

```bash
ytu formats "VIDEO_URL"
```

Use a specific format ID or custom yt-dlp selector:

```bash
ytu download "VIDEO_URL" --format-id "137+140"
```

Batch download:

```bash
ytu download --file examples/urls.txt --quality 720p --archive
```

Download playlist intentionally:

```bash
ytu download "PLAYLIST_URL" --playlist --quality 720p --archive
```

Download selected playlist items:

```bash
ytu download "PLAYLIST_URL" --playlist --playlist-items "1:5,8,10" --quality 720p
```

Extract audio:

```bash
ytu audio "VIDEO_URL" --audio-format mp3 --audio-quality 0
```

Download subtitles:

```bash
ytu download "VIDEO_URL" --quality 720p --subs --embed-subs --sub-langs "en.*,bn"
```

Preview without downloading:

```bash
ytu download "VIDEO_URL" --quality 720p --dry-run
```

Use browser cookies for content you are allowed to access:

```bash
ytu download "VIDEO_URL" --cookies-from-browser chrome
```

## Queue workflow

Add URLs:

```bash
ytu queue add "VIDEO_URL_1" "VIDEO_URL_2" --quality 720p --fallback nearest --compat
```

Add from file:

```bash
ytu queue add --file examples/urls.txt --quality 1080p
```

List queue:

```bash
ytu queue list
```

Run queue:

```bash
ytu queue run
```

Stop on the first failed item:

```bash
ytu queue run --stop-on-error
```

Clear queue:

```bash
ytu queue clear
```

## Presets

```bash
ytu download "VIDEO_URL" --preset mobile
ytu download "VIDEO_URL" --preset lecture
ytu download "VIDEO_URL" --preset archive
ytu download "VIDEO_URL" --preset mp4
ytu download "VIDEO_URL" --preset max
```

Available presets:

- `max`: best available quality
- `mp4`: best available with MP4/M4A compatibility preference
- `720p`: 720p-compatible output
- `1080p`: 1080p-compatible output
- `mobile`: practical 720p MP4 mode
- `lecture`: 720p MP4 with metadata/info/description
- `archive`: best available with metadata/info/description/archive tracking

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
  "fallback": "lower",
  "container": "mp4",
  "output_template": "%(uploader|Unknown)s/%(title).180B [%(id)s].%(ext)s",
  "sub_langs": "en.*",
  "concurrent_fragments": 4,
  "retries": 10,
  "fragment_retries": 10,
  "playlist": false,
  "safe_names": false,
  "compat": false,
  "write_metadata": true,
  "write_info_json": false,
  "write_description": false,
  "format_sort": "",
  "format_sort_force": false,
  "sleep_interval": null,
  "max_sleep_interval": null,
  "socket_timeout": 30,
  "archive": false,
  "sponsorblock_remove": "",
  "sponsorblock_mark": ""
}
```

## Quality behavior

- `--quality 720p` means best available video **at or below** 720p.
- `--quality 720p --exact-quality` means only exactly 720p is acceptable.
- `--quality 720p --fallback nearest` tries exact 720p, then lower, then higher, then best available.
- `--quality 720p --fallback higher` chooses 720p or above.
- `--format-id` overrides all automatic quality logic.
- `--compat` prefers MP4/M4A-friendly streams before broader fallbacks.

## Add to GitHub later

This folder is initialized as a local Git repository. After you create an empty GitHub repo, run:

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

Current included unit tests cover quality parsing, format selector construction, smart fallback behavior, and queue persistence.

## Honest limitation

No downloader can guarantee every YouTube video forever. Videos may be private, removed, DRM-protected, region-limited, age-restricted, account-restricted, or blocked by platform policy. This CLI is designed to be powerful and maintainable while respecting permissions and access controls.
