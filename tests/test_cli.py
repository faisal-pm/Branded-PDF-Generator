from typer.testing import CliRunner

from brandpdf import __version__
from brandpdf.cli import app

runner = CliRunner()


def test_help_lists_commands() -> None:
    result = runner.invoke(app, ["--help"])

    assert result.exit_code == 0
    assert "build" in result.output
    assert "init" in result.output


def test_version_flag_prints_version() -> None:
    result = runner.invoke(app, ["--version"])

    assert result.exit_code == 0
    assert __version__ in result.output


def test_unimplemented_command_fails_cleanly() -> None:
    result = runner.invoke(app, ["init"])

    assert result.exit_code == 1
    assert "not implemented yet" in result.output
