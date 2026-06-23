from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable
from uuid import uuid4

from .config import CONFIG_DIR

QUEUE_PATH = CONFIG_DIR / "queue.jsonl"
VALID_STATUSES = {"queued", "done", "failed", "skipped"}


@dataclass(slots=True)
class QueueItem:
    id: str
    url: str
    status: str = "queued"
    quality: str = "best"
    fallback: str = "lower"
    compat: bool = False
    playlist: bool = False
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    updated_at: str | None = None
    error: str | None = None

    @classmethod
    def create(
        cls,
        url: str,
        *,
        quality: str = "best",
        fallback: str = "lower",
        compat: bool = False,
        playlist: bool = False,
    ) -> "QueueItem":
        return cls(
            id=uuid4().hex[:12],
            url=url,
            quality=quality,
            fallback=fallback,
            compat=compat,
            playlist=playlist,
        )

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "QueueItem":
        status = str(data.get("status", "queued"))
        if status not in VALID_STATUSES:
            status = "queued"
        return cls(
            id=str(data.get("id") or uuid4().hex[:12]),
            url=str(data["url"]),
            status=status,
            quality=str(data.get("quality", "best")),
            fallback=str(data.get("fallback", "lower")),
            compat=bool(data.get("compat", False)),
            playlist=bool(data.get("playlist", False)),
            created_at=str(data.get("created_at") or datetime.now(timezone.utc).isoformat()),
            updated_at=data.get("updated_at"),
            error=data.get("error"),
        )

    def mark(self, status: str, error: str | None = None) -> None:
        if status not in VALID_STATUSES:
            raise ValueError(f"Invalid queue status: {status}")
        self.status = status
        self.error = error
        self.updated_at = datetime.now(timezone.utc).isoformat()


def read_queue(path: Path | None = None) -> list[QueueItem]:
    target = path or QUEUE_PATH
    if not target.exists():
        return []
    items: list[QueueItem] = []
    with target.expanduser().open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            items.append(QueueItem.from_dict(json.loads(line)))
    return items


def write_queue(items: Iterable[QueueItem], path: Path | None = None) -> Path:
    target = path or QUEUE_PATH
    target = target.expanduser()
    target.parent.mkdir(parents=True, exist_ok=True)
    with target.open("w", encoding="utf-8") as f:
        for item in items:
            f.write(json.dumps(asdict(item), ensure_ascii=False) + "\n")
    return target


def append_queue(items: Iterable[QueueItem], path: Path | None = None) -> Path:
    target = path or QUEUE_PATH
    target = target.expanduser()
    target.parent.mkdir(parents=True, exist_ok=True)
    with target.open("a", encoding="utf-8") as f:
        for item in items:
            f.write(json.dumps(asdict(item), ensure_ascii=False) + "\n")
    return target


def clear_queue(path: Path | None = None) -> Path:
    target = path or QUEUE_PATH
    target = target.expanduser()
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text("", encoding="utf-8")
    return target
