from pathlib import Path

from ytu.queue import QueueItem, append_queue, clear_queue, read_queue, write_queue


def test_queue_roundtrip(tmp_path: Path):
    path = tmp_path / "queue.jsonl"
    item = QueueItem.create("https://example.com/video", quality="720p", fallback="nearest", compat=True)
    write_queue([item], path)
    loaded = read_queue(path)
    assert len(loaded) == 1
    assert loaded[0].url == item.url
    assert loaded[0].quality == "720p"
    assert loaded[0].fallback == "nearest"
    assert loaded[0].compat is True


def test_queue_append_and_clear(tmp_path: Path):
    path = tmp_path / "queue.jsonl"
    append_queue([QueueItem.create("https://example.com/1")], path)
    append_queue([QueueItem.create("https://example.com/2")], path)
    assert len(read_queue(path)) == 2
    clear_queue(path)
    assert read_queue(path) == []
