from typer.testing import CliRunner

from ytu.cli import app


def test_help_works():
    result = CliRunner().invoke(app, ["--help"])
    assert result.exit_code == 0
    assert "YT Ultimate" in result.output


def test_download_help_works():
    result = CliRunner().invoke(app, ["download", "--help"])
    assert result.exit_code == 0
    assert "--fallback" in result.output
    assert "--preset" in result.output


def test_queue_help_works():
    result = CliRunner().invoke(app, ["queue", "--help"])
    assert result.exit_code == 0
    assert "Persistent download queue" in result.output
