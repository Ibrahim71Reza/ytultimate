from __future__ import annotations

from pathlib import Path
from typing import Any

from rich.console import Console
from rich.progress import (
    BarColumn,
    DownloadColumn,
    Progress,
    SpinnerColumn,
    TaskID,
    TextColumn,
    TimeRemainingColumn,
    TransferSpeedColumn,
)


class RichLogger:
    def __init__(self, console: Console) -> None:
        self.console = console

    def debug(self, msg: str) -> None:
        # yt-dlp sends many debug lines; keep the UI clean.
        return None

    def info(self, msg: str) -> None:
        if msg:
            self.console.print(msg)

    def warning(self, msg: str) -> None:
        self.console.print(f"[yellow]warning:[/yellow] {msg}")

    def error(self, msg: str) -> None:
        self.console.print(f"[red]error:[/red] {msg}")


class DownloadProgress:
    def __init__(self, console: Console) -> None:
        self.console = console
        self.progress = Progress(
            SpinnerColumn(),
            TextColumn("[bold blue]{task.description}"),
            BarColumn(),
            DownloadColumn(),
            TransferSpeedColumn(),
            TimeRemainingColumn(),
            console=console,
            transient=False,
        )
        self.tasks: dict[str, TaskID] = {}

    def __enter__(self) -> "DownloadProgress":
        self.progress.start()
        return self

    def __exit__(self, exc_type: object, exc: object, tb: object) -> None:
        self.progress.stop()

    def hook(self, data: dict[str, Any]) -> None:
        status = data.get("status")
        filename = data.get("filename") or data.get("tmpfilename") or "download"
        key = str(filename)
        name = Path(key).name
        if len(name) > 70:
            name = f"{name[:67]}..."

        task_id = self.tasks.get(key)
        if task_id is None:
            task_id = self.progress.add_task(name, total=1)
            self.tasks[key] = task_id

        if status == "downloading":
            downloaded = int(data.get("downloaded_bytes") or 0)
            total = data.get("total_bytes") or data.get("total_bytes_estimate") or 0
            total = int(total or max(downloaded, 1))
            self.progress.update(task_id, total=total, completed=min(downloaded, total))
        elif status == "finished":
            total = data.get("total_bytes") or data.get("downloaded_bytes") or 1
            total = int(total or 1)
            self.progress.update(task_id, total=total, completed=total)
            self.console.print(f"[green]downloaded:[/green] {Path(key).name}")
        elif status == "error":
            self.console.print(f"[red]failed:[/red] {name}")


class FinalPathReporter:
    """Collect and print final post-processed output paths reported by yt-dlp."""

    def __init__(self, console: Console) -> None:
        self.console = console
        self._paths: set[str] = set()

    def hook(self, data: dict[str, Any]) -> None:
        if data.get("status") != "finished":
            return
        info = data.get("info_dict") or {}
        candidates = [
            info.get("filepath"),
            info.get("_filename"),
            data.get("filepath"),
            data.get("filename"),
        ]
        for candidate in candidates:
            if candidate:
                self._paths.add(str(candidate))
                return

    def print_summary(self) -> None:
        if not self._paths:
            return
        for path in sorted(self._paths):
            self.console.print(f"[bold green]saved:[/bold green] {path}")
