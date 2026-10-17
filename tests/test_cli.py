from pathlib import Path

import pytest
from typer.testing import CliRunner

from brandpdf import __version__
from brandpdf.brand import load_brand
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
    result = runner.invoke(app, ["build", "doc.md", "--brand", "brand.yaml", "-o", "out.pdf"])

    assert result.exit_code == 1
    assert "not implemented yet" in result.output


def test_init_writes_a_starter_kit_that_loads(tmp_path: Path) -> None:
    target = tmp_path / "brand.yaml"

    result = runner.invoke(app, ["init", str(target)])

    assert result.exit_code == 0
    assert f"Wrote starter brand kit to {target}" in result.output
    brand = load_brand(target)
    assert brand.name == "Your Organisation"


def test_init_defaults_to_brand_yaml_in_the_current_folder(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.chdir(tmp_path)

    result = runner.invoke(app, ["init"])

    assert result.exit_code == 0
    assert (tmp_path / "brand.yaml").is_file()


def test_init_refuses_to_overwrite_without_force(tmp_path: Path) -> None:
    target = tmp_path / "brand.yaml"
    target.write_text("name: Keep me\n")

    result = runner.invoke(app, ["init", str(target)])

    assert result.exit_code == 1
    assert "already exists" in result.output
    assert "--force" in result.output
    assert target.read_text() == "name: Keep me\n"


def test_init_force_overwrites(tmp_path: Path) -> None:
    target = tmp_path / "brand.yaml"
    target.write_text("name: Replace me\n")

    result = runner.invoke(app, ["init", str(target), "--force"])

    assert result.exit_code == 0
    assert load_brand(target).name == "Your Organisation"
