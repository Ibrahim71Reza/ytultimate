from ytu.formats import build_audio_format, build_video_format, parse_quality


def test_parse_quality_best():
    assert parse_quality("best") is None
    assert parse_quality("original") is None


def test_parse_quality_height():
    assert parse_quality("720p") == 720
    assert parse_quality("1080") == 1080


def test_video_format_capped():
    selector = build_video_format("720p")
    assert "height<=720" in selector
    assert "+ba" in selector


def test_video_format_exact():
    selector = build_video_format("720p", exact=True)
    assert "height=720" in selector


def test_format_id_overrides():
    assert build_video_format("720p", format_id="137+140") == "137+140"
    assert build_audio_format("251") == "251"
