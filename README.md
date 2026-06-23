# YT Ultimate CLI

**A clean, Linux-first command-line downloader for authorized YouTube/video downloads.**

`ytdown` gives you smart quality selection, interactive downloads, queues, batch files, playlists, subtitles, thumbnails, metadata, audio extraction, browser-cookie support, and FFmpeg-powered merging through one easy command.

> **Permission notice**
>
> Use this tool only for videos you own, have permission to download, or are allowed to save under the platform/license rules. This project does **not** bypass DRM, paid access, private-video permissions, copyright restrictions, or platform access controls.

---

## Why `ytdown`?

The main command is:

```bash
ytdown
```

It is short, lowercase, easy to type, and clearly means **YouTube download**.

Installed command aliases:

| Command | Purpose |
|---|---|
| `ytdown` | Recommended main command |
| `yt-down` | Readable hyphenated alias |
| `ytultimate` | Full project-name alias |
| `ytu` | Short legacy alias |

---

## What this tool is best for

- Downloading a single video in the quality you want.
- Downloading at or below `720p`, `1080p`, `1440p`, `2160p`, etc.
- Choosing a quality interactively before download.
- Downloading playlists intentionally.
- Running a persistent download queue.
- Downloading many URLs from a `.txt` file.
- Extracting audio as `mp3`, `m4a`, `opus`, `flac`, or `wav`.
- Saving subtitles, thumbnails, metadata, chapters, descriptions, and info JSON.
- Using browser cookies for videos your own account is allowed to access.
- Keeping the project Git-ready for later GitHub publishing.

Under the hood, this CLI uses the official `yt-dlp` Python package for extraction and your system-installed `ffmpeg`/`ffprobe` for media merging and post-processing.

---

## Requirements

Install the Linux system tools first:

```bash
sudo apt update
sudo apt install -y python3 python3-venv python3-pip ffmpeg git
```

Why FFmpeg matters: high-quality video platforms often provide video and audio as separate streams. FFmpeg merges them into one final media file.

---

## Installation

From inside the project folder:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -e .
```

Check that everything is ready:

```bash
ytdown --version
ytdown doctor
```

---

## Quick start

Download the best available quality:

```bash
ytdown download "VIDEO_URL"
```

Download the best available version at or below 720p:

```bash
ytdown download "VIDEO_URL" --quality 720p
```

Download exactly 720p only:

```bash
ytdown download "VIDEO_URL" --quality 720p --exact-quality
```

Choose quality interactively:

```bash
ytdown wizard "VIDEO_URL"
```

Preview a recommended download plan:

```bash
ytdown plan "VIDEO_URL"
```

List all available formats:

```bash
ytdown formats "VIDEO_URL"
```

Extract audio as MP3:

```bash
ytdown audio "VIDEO_URL" --audio-format mp3 --audio-quality 0
```

---

## Most useful examples

| Goal | Command |
|---|---|
| Best quality | `ytdown download "VIDEO_URL"` |
| 720p or lower | `ytdown download "VIDEO_URL" --quality 720p` |
| Exact 720p | `ytdown download "VIDEO_URL" --quality 720p --exact-quality` |
| 1080p MP4-friendly | `ytdown download "VIDEO_URL" --quality 1080p --compat --container mp4` |
| Choose interactively | `ytdown wizard "VIDEO_URL"` |
| Plan first | `ytdown plan "VIDEO_URL"` |
| List formats | `ytdown formats "VIDEO_URL"` |
| Manual format IDs | `ytdown download "VIDEO_URL" --format-id "137+140"` |
| Audio MP3 | `ytdown audio "VIDEO_URL" --audio-format mp3` |
| Dry run | `ytdown download "VIDEO_URL" --quality 720p --dry-run` |
| Browser cookies | `ytdown download "VIDEO_URL" --cookies-from-browser chrome` |

---

## Quality selection explained

`ytdown` is designed around practical quality control.

| Option | Meaning |
|---|---|
| `--quality 720p` | Best video at or below 720p |
| `--quality 1080p` | Best video at or below 1080p |
| `--quality best` | Best available quality |
| `--exact-quality` | Require the exact requested height |
| `--fallback lower` | Use requested quality or lower |
| `--fallback exact` | Use only the exact requested quality |
| `--fallback higher` | Use requested quality or higher |
| `--fallback nearest` | Try exact, then lower, then higher, then best |
| `--fallback any` | Use best available if the requested quality is unavailable |
| `--format-id` | Override automatic selection with a manual yt-dlp selector |

Recommended everyday command:

```bash
ytdown download "VIDEO_URL" --quality 720p --fallback nearest --compat
```

---

## Presets

Presets are shortcuts for common download styles.

```bash
ytdown download "VIDEO_URL" --preset mobile
ytdown download "VIDEO_URL" --preset lecture
ytdown download "VIDEO_URL" --preset archive
ytdown download "VIDEO_URL" --preset mp4
ytdown download "VIDEO_URL" --preset max
```

| Preset | Best for |
|---|---|
| `max` | Best available quality |
| `mp4` | MP4/M4A-friendly output |
| `720p` | 720p-compatible video |
| `1080p` | 1080p-compatible video |
| `mobile` | Practical 720p MP4 downloads |
| `lecture` | 720p MP4 with metadata, info JSON, and description |
| `archive` | Best quality with metadata and archive tracking |

---

## Batch downloads

Create a text file with one URL per line:

```text
https://www.youtube.com/watch?v=VIDEO_ID_1
https://www.youtube.com/watch?v=VIDEO_ID_2
https://www.youtube.com/watch?v=VIDEO_ID_3
```

Run:

```bash
ytdown download --file examples/urls.txt --quality 720p --archive
```

`--archive` helps avoid downloading the same video again later.

---

## Queue workflow

Use the queue when you want to collect URLs first and download them later in order.

Add URLs:

```bash
ytdown queue add "VIDEO_URL_1" "VIDEO_URL_2" --quality 720p --fallback nearest --compat
```

Add URLs from a file:

```bash
ytdown queue add --file examples/urls.txt --quality 1080p
```

See queued items:

```bash
ytdown queue list
```

Run the queue:

```bash
ytdown queue run
```

Stop when the first item fails:

```bash
ytdown queue run --stop-on-error
```

Clear the queue:

```bash
ytdown queue clear
```

---

## Playlists

Playlist downloads are opt-in so you do not accidentally download a full playlist.

Download a playlist:

```bash
ytdown download "PLAYLIST_URL" --playlist --quality 720p --archive
```

Download only selected playlist items:

```bash
ytdown download "PLAYLIST_URL" --playlist --playlist-items "1:5,8,10" --quality 720p
```

Force a single video from a playlist URL:

```bash
ytdown download "VIDEO_OR_PLAYLIST_URL" --single
```

---

## Subtitles, thumbnails, and metadata

Download human-created subtitles:

```bash
ytdown download "VIDEO_URL" --subs --sub-langs "en.*,bn"
```

Download and embed subtitles:

```bash
ytdown download "VIDEO_URL" --quality 720p --subs --embed-subs --sub-langs "en.*,bn"
```

Use auto-generated subtitles:

```bash
ytdown download "VIDEO_URL" --auto-subs --sub-langs "en.*"
```

Save thumbnail:

```bash
ytdown download "VIDEO_URL" --thumbnail
```

Embed thumbnail:

```bash
ytdown download "VIDEO_URL" --embed-thumbnail
```

Save extra metadata files:

```bash
ytdown download "VIDEO_URL" --write-info-json --write-description
```

---

## Audio extraction

Extract best-quality MP3:

```bash
ytdown audio "VIDEO_URL" --audio-format mp3 --audio-quality 0
```

Extract M4A:

```bash
ytdown audio "VIDEO_URL" --audio-format m4a
```

Extract from a URL file:

```bash
ytdown audio --file examples/urls.txt --audio-format mp3 --archive
```

Supported audio formats depend on FFmpeg and yt-dlp support, but common choices include:

```text
mp3, m4a, opus, flac, wav, best
```

---

## Browser cookies

Some videos require your logged-in browser session. For videos your account is allowed to access, use:

```bash
ytdown download "VIDEO_URL" --cookies-from-browser chrome
```

or:

```bash
ytdown download "VIDEO_URL" --cookies-from-browser firefox
```

This does not bypass private access controls. It only lets yt-dlp use your existing browser login where permitted.

---

## Config file

Create the default config:

```bash
ytdown init-config
```

Default location:

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

Use a custom config file:

```bash
ytdown download "VIDEO_URL" --config ./my-config.json
```

---

## Output folder and filenames

Set a custom output folder:

```bash
ytdown download "VIDEO_URL" --output-dir ~/Videos/Downloads
```

Use a custom filename template:

```bash
ytdown download "VIDEO_URL" --template "%(uploader)s/%(title).180B [%(id)s].%(ext)s"
```

Use safer ASCII filenames:

```bash
ytdown download "VIDEO_URL" --safe-names
```

Overwrite existing files only when you explicitly ask:

```bash
ytdown download "VIDEO_URL" --overwrite
```

---

## Maintenance

Check installed tools:

```bash
ytdown doctor
```

Update the yt-dlp extraction engine inside the current Python environment:

```bash
ytdown update-engine
```

Use nightly/pre-release yt-dlp builds only when you understand the risk:

```bash
ytdown update-engine --nightly
```

---

## Command overview

| Command | Description |
|---|---|
| `ytdown download` | Download video with smart quality control |
| `ytdown audio` | Extract audio from video URLs |
| `ytdown wizard` | Interactive guided downloader |
| `ytdown formats` | List all available formats |
| `ytdown plan` | Show recommended commands before downloading |
| `ytdown info` | Show video metadata |
| `ytdown init-config` | Create a config file |
| `ytdown doctor` | Check dependencies and setup |
| `ytdown selfcheck` | Alias for `doctor` |
| `ytdown update-engine` | Update yt-dlp |
| `ytdown queue add` | Add URLs to the queue |
| `ytdown queue list` | Show queue status |
| `ytdown queue run` | Run queued downloads |
| `ytdown queue clear` | Clear the queue |

---

## Add this project to GitHub

This folder is already initialized as a local Git repository.

After creating an empty GitHub repo, add your remote.

SSH:

```bash
git remote add origin git@github.com:YOUR_USERNAME/YOUR_REPO.git
git branch -M main
git push -u origin main
```

HTTPS:

```bash
git remote add origin https://github.com/YOUR_USERNAME/YOUR_REPO.git
git branch -M main
git push -u origin main
```

---

## Development

Activate the virtual environment:

```bash
source .venv/bin/activate
```

Run checks:

```bash
python -m compileall ytu
python -m pytest
```

The included tests cover quality parsing, format selector construction, fallback behavior, and queue persistence.

---

## Honest limitations

No downloader can guarantee every video forever. A video may be unavailable because it is:

- private,
- deleted,
- DRM-protected,
- region-restricted,
- account-restricted,
- age-restricted,
- paid-only,
- blocked by copyright or platform policy.

YT Ultimate CLI is designed to be powerful, clean, and maintainable while respecting permissions and access controls.

---

## License

MIT License. See [`LICENSE`](LICENSE) for details.
