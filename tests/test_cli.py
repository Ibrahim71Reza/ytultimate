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


def test_download_help_mentions_output_alias():
    result = CliRunner().invoke(app, ["download", "--help"])
    assert result.exit_code == 0
    assert "--output" in result.output
    # Rich help truncates long combined aliases visually, so direct invocation tests
    # guarantee the aliases are actually accepted.
    for alias in ("--output", "--output-dir", "-o"):
        alias_result = CliRunner().invoke(app, ["download", "VIDEO_URL", alias, "/tmp", "--dry-run"])
        assert alias_result.exit_code != 2


def test_paths_command_works():
    result = CliRunner().invoke(app, ["paths"])
    assert result.exit_code == 0
    assert "Default output directory" in result.output
    assert "Filename template" in result.output
