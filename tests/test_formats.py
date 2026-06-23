import pytest

from ytu.formats import (
    available_video_heights,
    build_audio_format,
    build_video_format,
    normalize_fallback,
    parse_quality,
    smart_default_quality,
)


def test_parse_quality_best():
    assert parse_quality("best") is None
    assert parse_quality("original") is None
    assert parse_quality("auto") is None


def test_parse_quality_height():
    assert parse_quality("720p") == 720
    assert parse_quality("1080") == 1080


def test_parse_quality_rejects_bad_value():
    with pytest.raises(ValueError):
        parse_quality("huge")


def test_video_format_capped():
    selector = build_video_format("720p")
    assert "height<=720" in selector
    assert "+ba" in selector


def test_video_format_exact():
    selector = build_video_format("720p", exact=True)
    assert "height=720" in selector
    assert "height<=720" not in selector


def test_video_format_nearest():
    selector = build_video_format("720p", fallback="nearest")
    assert "height=720" in selector
    assert "height<=720" in selector
    assert "height>=720" in selector
    assert "bv*+ba/b" in selector


def test_video_format_higher():
    selector = build_video_format("1080p", fallback="higher")
    assert "height>=1080" in selector


def test_compat_selector_prefers_mp4_m4a():
    selector = build_video_format("720p", compat=True)
    assert "ext=mp4" in selector
    assert "ext=m4a" in selector


def test_normalize_fallback_aliases():
    assert normalize_fallback("closest") == "nearest"
    assert normalize_fallback("none") == "exact"


def test_format_id_overrides():
    assert build_video_format("720p", format_id="137+140") == "137+140"
    assert build_audio_format("251") == "251"


def test_available_heights_and_default_quality():
    info = {
        "formats": [
            {"height": 360, "vcodec": "avc1"},
            {"height": 720, "vcodec": "vp9"},
            {"height": 1080, "vcodec": "avc1"},
            {"vcodec": "none"},
        ]
    }
    heights = available_video_heights(info)
    assert heights == [1080, 720, 360]
    assert smart_default_quality(heights) == "1080p"
