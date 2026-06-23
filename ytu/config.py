from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from platformdirs import user_config_dir

APP_NAME = "ytultimate"
CONFIG_DIR = Path(user_config_dir(APP_NAME))
CONFIG_PATH = CONFIG_DIR / "config.json"

DEFAULT_CONFIG: dict[str, Any] = {
    "output_dir": "~/Videos/YTUltimate",
    "quality": "best",
    "fallback": "lower",
    "container": "mp4",
    "output_template": "%(uploader|Unknown)s/%(title).180B [%(id)s].%(ext)s",
    "sub_langs": "en.*",
    "concurrent_fragments": 4,
    "retries": 10,
    "fragment_retries": 10,
    "playlist": False,
    "safe_names": False,
    "compat": False,
    "write_metadata": True,
    "write_info_json": False,
    "write_description": False,
    "format_sort": "",
    "format_sort_force": False,
    "sleep_interval": None,
    "max_sleep_interval": None,
    "socket_timeout": 30,
    "archive": False,
    "sponsorblock_remove": "",
    "sponsorblock_mark": "",
}

PRESETS: dict[str, dict[str, Any]] = {
    "max": {"quality": "best", "fallback": "any", "compat": False},
    "mp4": {"quality": "best", "fallback": "any", "compat": True, "container": "mp4"},
    "720p": {"quality": "720p", "fallback": "lower", "compat": True, "container": "mp4"},
    "1080p": {"quality": "1080p", "fallback": "lower", "compat": True, "container": "mp4"},
    "mobile": {"quality": "720p", "fallback": "lower", "compat": True, "container": "mp4"},
    "lecture": {
        "quality": "720p",
        "fallback": "lower",
        "compat": True,
        "container": "mp4",
        "write_metadata": True,
        "write_info_json": True,
        "write_description": True,
    },
    "archive": {
        "quality": "best",
        "fallback": "any",
        "compat": False,
        "write_metadata": True,
        "write_info_json": True,
        "write_description": True,
        "archive": True,
    },
}


def expand_path(value: str | Path) -> Path:
    return Path(value).expanduser().resolve()


def apply_preset(config: dict[str, Any], preset: str | None) -> dict[str, Any]:
    data = config.copy()
    if not preset:
        return data
    key = preset.strip().lower()
    if key not in PRESETS:
        raise ValueError(f"Unknown preset '{preset}'. Use one of: {', '.join(sorted(PRESETS))}")
    data.update(PRESETS[key])
    return data


def load_config(config_path: Path | None = None) -> dict[str, Any]:
    path = config_path or CONFIG_PATH
    data = DEFAULT_CONFIG.copy()
    if path.exists():
        with path.expanduser().open("r", encoding="utf-8") as f:
            loaded = json.load(f)
        if not isinstance(loaded, dict):
            raise ValueError(f"Config file must contain a JSON object: {path}")
        data.update(loaded)
    return data


def write_default_config(path: Path | None = None, overwrite: bool = False) -> Path:
    target = path or CONFIG_PATH
    target = target.expanduser()
    target.parent.mkdir(parents=True, exist_ok=True)
    if target.exists() and not overwrite:
        return target
    with target.open("w", encoding="utf-8") as f:
        json.dump(DEFAULT_CONFIG, f, indent=2)
        f.write("\n")
    return target
