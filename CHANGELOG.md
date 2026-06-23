# Changelog

## 1.0.2 - README polish

- Reworked README into a cleaner GitHub-style guide.
- Added a faster quick-start path, clearer quality behavior table, and easier command examples.
- Improved sections for queue workflow, playlists, subtitles, audio, config, maintenance, and GitHub publishing.

## 1.0.1 - Command rename

- Added `ytdown` as the recommended primary command.
- Added `yt-down` as a readable alias.
- Kept `ytu` and `ytultimate` as backward-compatible aliases.
- Updated README examples and internal user-facing guidance to prefer `ytdown`.

## 1.0.0 - Ultimate CLI upgrade

- Added interactive `ytu wizard` downloader.
- Added `ytu plan` to inspect a URL and generate practical download commands.
- Added persistent queue commands: `ytu queue add`, `ytu queue list`, `ytu queue run`, `ytu queue clear`.
- Added smart quality fallback policies: `lower`, `exact`, `higher`, `nearest`, `any`.
- Added presets: `max`, `mp4`, `720p`, `1080p`, `mobile`, `lecture`, `archive`.
- Added friendly error explanations with likely fixes.
- Added `ytu doctor` and `ytu update-engine` maintenance commands.
- Added info JSON and description writing options.
- Added format sort, sleep interval, socket timeout, overwrite, keep-video, and print-filename controls.
- Added SponsorBlock mark/remove category validation.
- Expanded README with complete workflows.
- Expanded tests for format selection, queue persistence, and CLI help.

## 0.1.0 - Initial CLI

- Basic download, audio, formats, info, config, and selfcheck commands.
- Resolution selection and batch URL support.
