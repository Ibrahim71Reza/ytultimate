<div align="center">
# 🎬 YT Ultimate CLI (`ytdown`)

![Platform](https://img.shields.io/badge/Platform-Linux-blue?style=flat-square&logo=linux)
![Python](https://img.shields.io/badge/Python-3.8%2B-FFE873?style=flat-square&logo=python&logoColor=blue)
![License](https://img.shields.io/badge/License-MIT-green?style=flat-square)

**A clean, Linux-first command-line downloader for authorized YouTube/video downloads.**

`ytdown` gives you smart quality selection, interactive downloads, queues, batch files, playlists, subtitles, thumbnails, metadata, audio extraction, browser-cookie support, and FFmpeg-powered merging through one easy command.

</div>

> ⚠️ **Permission notice**
>
> Use this tool only for videos you own, have permission to download, or are allowed to save under the platform/license rules. This project does **not** bypass DRM, paid access, private-video permissions, copyright restrictions, or platform access controls.

---

## 💡 Why `ytdown`?

The main command is:

```bash
ytdown
```

It is short, lowercase, easy to type, and clearly means **YouTube download**.

**Installed command aliases:**

| Command | Purpose |
|:---|:---|
| `ytdown` | Recommended main command |
| `yt-down` | Readable hyphenated alias |
| `ytultimate` | Full project-name alias |
| `ytu` | Short legacy alias |

---

## ✨ What this tool is best for

- Downloading a single video in the exact quality you want.
- Targeting precise resolutions like `2160p` (4K), `1440p` (2K), `1080p` (HD), or `720p`.
- Choosing a quality interactively before downloading.
- Running a persistent download queue or downloading many URLs from a `.txt` file.
- Downloading playlists intentionally.
- Extracting pure audio as `mp3`, `m4a`, `opus`, `flac`, or `wav`.
- Saving subtitles, thumbnails, metadata, chapters, descriptions, and info JSON.
- Using browser cookies for videos your own account is allowed to access.

*Under the hood, this CLI uses the official `yt-dlp` Python package for extraction and your system-installed `ffmpeg`/`ffprobe` for media merging and post-processing.*

---

## ⚙️ Requirements & Installation

Install the Linux system tools first. High-quality video platforms often provide video and audio as separate streams, so **FFmpeg** is required to merge them into one final media file.

```bash
sudo apt update
sudo apt install -y python3 python3-venv python3-pip ffmpeg git
```

**Install the CLI:**
From inside the project folder:

```bash
git clone https://github.com/Ibrahim71Reza/ytultimate.git
cd ytultimate
python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -e .
```

**Verify installation:**
```bash
ytdown --version
ytdown doctor
```

---

## ⚡ Quick start

> 💎 **Default = best available quality.**  
> Use `--quality 1080p`, `1440p`, or `2160p` when you want a specific HD/2K/4K cap.  
> Use `720p` mainly for smaller file size/mobile/bandwidth-saving downloads.

**Download the best available quality:**
```bash
ytdown download "VIDEO_URL"
```

**Download Full HD, if available:**
```bash
ytdown download "VIDEO_URL" --quality 1080p --fallback nearest
```

**Download 2K / QHD, if available:**
```bash
ytdown download "VIDEO_URL" --quality 1440p --fallback nearest
```

**Download 4K / Ultra HD, if available:**
```bash
ytdown download "VIDEO_URL" --quality 2160p --fallback nearest
```

**Download a smaller 720p version:**
```bash
ytdown download "VIDEO_URL" --quality 720p
```

**Choose quality interactively:**
```bash
ytdown wizard "VIDEO_URL"
```

**Preview a recommended download plan:**
```bash
ytdown plan "VIDEO_URL"
```

**List all available formats:**
```bash
ytdown formats "VIDEO_URL"
```

**See where downloads will be saved:**
```bash
ytdown paths
```

---

## 📚 Most useful examples

| Goal | Command |
|:---|:---|
| **Best available quality** | `ytdown download "VIDEO_URL"` |
| **Full HD / 1080p** | `ytdown download "VIDEO_URL" --quality 1080p --fallback nearest` |
| **2K / 1440p** | `ytdown download "VIDEO_URL" --quality 1440p --fallback nearest` |
| **4K / 2160p** | `ytdown download "VIDEO_URL" --quality 2160p --fallback nearest` |
| **Smaller 720p download** | `ytdown download "VIDEO_URL" --quality 720p` |
| **MP4-friendly 1080p** | `ytdown download "VIDEO_URL" --quality 1080p --compat --container mp4` |
| **Choose interactively** | `ytdown wizard "VIDEO_URL"` |
| **Plan first** | `ytdown plan "VIDEO_URL"` |
| **List formats** | `ytdown formats "VIDEO_URL"` |
| **Manual format IDs** | `ytdown download "VIDEO_URL" --format-id "137+140"` |
| **Audio MP3** | `ytdown audio "VIDEO_URL" --audio-format mp3` |
| **Dry run** | `ytdown download "VIDEO_URL" --quality 1080p --dry-run` |
| **Browser cookies** | `ytdown download "VIDEO_URL" --cookies-from-browser chrome` |
| **Custom output folder**| `ytdown download "VIDEO_URL" --output ~/Downloads` |

---

## 🎯 Quality selection explained

`ytdown` is designed around practical quality control.

| Option | Meaning |
|:---|:---|
| `--quality best` | Best available quality (Default) |
| `--quality 1080p` | Best video at or below 1080p |
| `--quality 2160p` | Best video at or below 4K / 2160p |
| `--exact-quality` | Require the exact requested height |
| `--fallback lower` | Use requested quality or lower |
| `--fallback nearest` | Try exact, then lower, then higher, then best |
| `--fallback any` | Use best available if the requested quality is unavailable |

**Recommended everyday command for high-quality downloads:**
```bash
ytdown download "VIDEO_URL" --quality 1080p --fallback nearest --compat
```

**Recommended maximum-quality command:**
```bash
ytdown download "VIDEO_URL" --quality best
```

**Recommended smaller-file command:**
```bash
ytdown download "VIDEO_URL" --quality 720p --fallback nearest --compat
```

---

## 📁 Where did my video go?

By default, downloads are saved here:
```text
~/Videos/YTUltimate
```

The default filename template creates an uploader folder, resulting in organized files like this:
```text
~/Videos/YTUltimate/CHANNEL_NAME/VIDEO_TITLE [VIDEO_ID].mp4
```

<details>
<summary><b>🔍 Click here for commands to find or move your downloads</b></summary>

Find your latest downloaded files:
```bash
find ~/Videos/YTUltimate -type f -printf "%TY-%Tm-%Td %TH:%TM  %p\n" | sort | tail -20
```

Search for one downloaded video by YouTube ID:
```bash
find ~/Videos/YTUltimate -type f -iname "*VIDEO_ID*"
```

Save to a custom folder:
```bash
ytdown download "VIDEO_URL" --output ~/Downloads
```
*(Note: `--output`, `--output-dir`, and `-o` all mean the download folder. Use `--template` only when you want to change the filename/folder pattern inside that output folder).*
</details>

---

## 🗂️ Advanced Workflows

### 📥 Batch downloads
Create a text file (`examples/urls.txt`) with one URL per line, then run:
```bash
ytdown download --file examples/urls.txt --quality 1080p --fallback nearest --archive
```
*(Note: `--archive` helps avoid downloading the same video again later).*

### ⏳ Queue workflow
Use the queue when you want to collect URLs first and download them later in order.

```bash
ytdown queue add "VIDEO_URL_1" "VIDEO_URL_2" --quality 1080p --fallback nearest --compat
ytdown queue add --file examples/urls.txt
ytdown queue list
ytdown queue run
```

### 📋 Playlists
Playlist downloads are opt-in so you do not accidentally download a massive list.

```bash
# Download a full playlist
ytdown download "PLAYLIST_URL" --playlist --quality 1080p --archive

# Download specific items
ytdown download "PLAYLIST_URL" --playlist --playlist-items "1:5,8,10"

# Force a single video from a playlist URL
ytdown download "VIDEO_OR_PLAYLIST_URL" --single
```

### 📝 Subtitles, thumbnails, and metadata

```bash
# Download and embed human-created subtitles
ytdown download "VIDEO_URL" --quality 1080p --subs --embed-subs --sub-langs "en.*,bn"

# Use auto-generated subtitles
ytdown download "VIDEO_URL" --auto-subs --sub-langs "en.*"

# Save and embed thumbnail
ytdown download "VIDEO_URL" --thumbnail --embed-thumbnail

# Save extra metadata files
ytdown download "VIDEO_URL" --write-info-json --write-description
```

---

## 🎵 Audio Extraction

Extract pure audio using standard formats (`mp3`, `m4a`, `opus`, `flac`, `wav`):

```bash
# Extract best-quality MP3
ytdown audio "VIDEO_URL" --audio-format mp3 --audio-quality 0

# Extract M4A
ytdown audio "VIDEO_URL" --audio-format m4a

# Batch extract MP3s from a text file
ytdown audio --file examples/urls.txt --audio-format mp3 --archive
```

---

## 🍪 Browser Cookies

Some videos require your logged-in browser session. For videos your account is allowed to access:

```bash
ytdown download "VIDEO_URL" --cookies-from-browser chrome
# or:
ytdown download "VIDEO_URL" --cookies-from-browser firefox
```
*This does not bypass private access controls. It only lets `yt-dlp` use your existing browser login where permitted.*

---

## 🛠️ Configuration & Maintenance

**Generate a default config file:**
```bash
ytdown init-config
```
*(Saved to `~/.config/ytultimate/config.json` by default. You can edit this file to set your default output dir, fallback preferences, language codes, etc.)*

**Check system dependencies:**
```bash
ytdown doctor
```

**Update the extraction engine:**
```bash
ytdown update-engine
```

---

## 🛑 Honest Limitations

No downloader can guarantee every video forever. A video may be unavailable because it is:
- private, deleted, or DRM-protected,
- region/account/age-restricted,
- paid-only, or blocked by copyright/platform policy.

YT Ultimate CLI is designed to be powerful, clean, and maintainable while respecting permissions and access controls.

---

## 📄 License
This project is licensed under the MIT License. See the [`LICENSE`](LICENSE) file for details.
