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


@pytest.fixture
def project(tmp_path: Path) -> Path:
    """A folder with a starter brand kit and a short document."""
    runner.invoke(app, ["init", str(tmp_path / "brand.yaml")])
    (tmp_path / "doc.md").write_text("# Welcome\n\n- First item\n", encoding="utf-8")
    return tmp_path


def test_build_writes_a_pdf(project: Path) -> None:
    out = project / "out" / "welcome.pdf"

    result = runner.invoke(
        app,
        ["build", str(project / "doc.md"), "--brand", str(project / "brand.yaml"), "-o", str(out)],
    )

    assert result.exit_code == 0, result.output
    assert f"Wrote {out}" in result.output
    assert out.read_bytes().startswith(b"%PDF-")


def test_build_defaults_to_brand_yaml_and_a_pdf_beside_the_source(
    project: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.chdir(project)

    result = runner.invoke(app, ["build", "doc.md"])

    assert result.exit_code == 0, result.output
    assert (project / "doc.pdf").read_bytes().startswith(b"%PDF-")


def test_build_reports_brand_kit_problems(project: Path) -> None:
    (project / "brand.yaml").write_text("name: Broken\n", encoding="utf-8")

    result = runner.invoke(
        app, ["build", str(project / "doc.md"), "-b", str(project / "brand.yaml")]
    )

    assert result.exit_code == 1
    assert "colors: required key missing" in result.output
    assert not (project / "doc.pdf").exists()


def test_build_reports_a_missing_source(project: Path) -> None:
    result = runner.invoke(
        app, ["build", str(project / "nope.md"), "-b", str(project / "brand.yaml")]
    )

    assert result.exit_code == 1
    assert "Error: document not found:" in result.output
    assert "nope.md" in result.output


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
