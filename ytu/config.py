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
}


def expand_path(value: str | Path) -> Path:
    return Path(value).expanduser().resolve()


def load_config(config_path: Path | None = None) -> dict[str, Any]:
    path = config_path or CONFIG_PATH
    data = DEFAULT_CONFIG.copy()
    if path.exists():
        with path.open("r", encoding="utf-8") as f:
            loaded = json.load(f)
        if not isinstance(loaded, dict):
            raise ValueError(f"Config file must contain a JSON object: {path}")
        data.update(loaded)
    return data


def write_default_config(path: Path | None = None, overwrite: bool = False) -> Path:
    target = path or CONFIG_PATH
    target.parent.mkdir(parents=True, exist_ok=True)
    if target.exists() and not overwrite:
        return target
    with target.open("w", encoding="utf-8") as f:
        json.dump(DEFAULT_CONFIG, f, indent=2)
        f.write("\n")
    return target
