"""Brand kit loading and validation (F1, F2)."""

import shutil
from pathlib import Path

import pytest
import reportlab
from PIL import Image

from brandpdf.brand import Brand, BrandError, load_brand, parse_brand

VERA = Path(reportlab.__file__).parent / "fonts"

MINIMAL = """\
name: Fernleaf Studio
colors:
  primary: "#2E5E4E"
  secondary: "#8FB9A8"
  accent: "#F4A259"
"""


@pytest.fixture
def kit_dir(tmp_path: Path) -> Path:
    """A folder with real assets that a full brand kit can point at."""
    fonts = tmp_path / "fonts"
    fonts.mkdir()
    shutil.copy(VERA / "VeraBd.ttf", fonts / "Heading.ttf")
    shutil.copy(VERA / "Vera.ttf", fonts / "Body.ttf")
    Image.new("RGB", (40, 20), "#2E5E4E").save(tmp_path / "logo.png")
    Image.new("RGB", (60, 85), "white").save(tmp_path / "letterhead.png")
    (tmp_path / "notes.txt").write_text("not a letterhead")
    (tmp_path / "fonts" / "Broken.ttf").write_bytes(b"definitely not a font")
    return tmp_path


def write_kit(folder: Path, text: str) -> Path:
    path = folder / "brand.yaml"
    path.write_text(text, encoding="utf-8")
    return path


def load_error(folder: Path, text: str) -> str:
    with pytest.raises(BrandError) as excinfo:
        load_brand(write_kit(folder, text))
    return str(excinfo.value)


def test_minimal_kit_fills_in_defaults(tmp_path: Path) -> None:
    brand = load_brand(write_kit(tmp_path, MINIMAL))

    assert brand.name == "Fernleaf Studio"
    assert brand.colors.primary == "#2E5E4E"
    assert brand.colors.text == "#1A1A1A"
    assert brand.colors.background == "#FFFFFF"
    assert brand.fonts.heading == "Helvetica-Bold"
    assert brand.fonts.body == "Helvetica"
    assert brand.logo is None
    assert brand.page.size == "A4"
    assert brand.page.margins_mm.top == 20
    assert brand.letterhead.first_page is None


def test_full_kit_resolves_paths_relative_to_the_kit_file(
    kit_dir: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    path = write_kit(
        kit_dir,
        MINIMAL
        + """\
fonts:
  heading: fonts/Heading.ttf
  body: fonts/Body.ttf
logo: logo.png
contact:
  address: |
    12 Willow Lane
    Brookfield
  phone: "+00 1234 5678"
  email: hello@fernleaf.example
  website: fernleaf.example
page:
  size: Letter
  margins_mm: {top: 30, right: 18, bottom: 25, left: 18}
letterhead:
  first_page: letterhead.png
""",
    )
    monkeypatch.chdir(kit_dir.parent)  # paths must not depend on the working directory

    brand = load_brand(path)

    assert brand.fonts.heading == kit_dir.resolve() / "fonts" / "Heading.ttf"
    assert brand.fonts.body == kit_dir.resolve() / "fonts" / "Body.ttf"
    assert brand.logo == kit_dir.resolve() / "logo.png"
    assert brand.letterhead.first_page == kit_dir.resolve() / "letterhead.png"
    assert brand.letterhead.continuation is None
    assert brand.contact.address == "12 Willow Lane\nBrookfield\n"
    assert brand.contact.email == "hello@fernleaf.example"
    assert brand.page.size == "Letter"
    assert brand.page.margins_mm.top == 30


def test_short_and_lowercase_hex_colours_are_normalised(tmp_path: Path) -> None:
    brand = load_brand(write_kit(tmp_path, MINIMAL.replace('"#2E5E4E"', '"#2e5"')))

    assert brand.colors.primary == "#22EE55"


def test_unquoted_numbers_in_text_fields_are_kept_as_text(tmp_path: Path) -> None:
    brand = load_brand(write_kit(tmp_path, MINIMAL + "contact:\n  phone: 5550123\n"))

    assert brand.contact.phone == "5550123"


def test_brand_is_immutable(tmp_path: Path) -> None:
    brand = load_brand(write_kit(tmp_path, MINIMAL))

    with pytest.raises(ValueError):
        brand.name = "Something else"  # type: ignore[misc]


def test_parse_brand_accepts_a_mapping(kit_dir: Path) -> None:
    data = {
        "name": "Fernleaf Studio",
        "colors": {"primary": "#2E5E4E", "secondary": "#8FB9A8", "accent": "#F4A259"},
        "logo": "logo.png",
    }

    brand = parse_brand(data, base_dir=kit_dir)

    assert isinstance(brand, Brand)
    assert brand.logo == kit_dir.resolve() / "logo.png"


@pytest.mark.parametrize(
    ("change", "expected"),
    [
        pytest.param(
            ('"#2E5E4E"', '"#2E5E4"'),
            ["colors.primary", "'#2E5E4' is not a hex colour"],
            id="bad-hex",
        ),
        pytest.param(
            ('"#2E5E4E"', "#2E5E4E"),
            ["colors.primary", 'quote hex colours, e.g. "#1F4E79"'],
            id="unquoted-hex",
        ),
        pytest.param(
            ("colors:", "colours:"),
            ["unknown key 'colours' (did you mean 'colors'?)"],
            id="unknown-top-level-key",
        ),
        pytest.param(
            ("primary:", "primay:"),
            ["colors: unknown key 'primay' (did you mean 'primary'?)"],
            id="unknown-nested-key",
        ),
        pytest.param(
            ("name: Fernleaf Studio\n", ""),
            ["name: required key missing"],
            id="missing-name",
        ),
        pytest.param(
            ("", "fonts:\n  body: fonts/Missing.ttf\n"),
            ["fonts.body: file not found:", "Missing.ttf"],
            id="missing-font-file",
        ),
        pytest.param(
            ("", "fonts:\n  heading: fonts/Broken.ttf\n"),
            ["fonts.heading:", "is not a valid TrueType font"],
            id="corrupt-font-file",
        ),
        pytest.param(
            ("", "fonts:\n  heading: Comic Sans\n"),
            ["fonts.heading: 'Comic Sans' is not a built-in font or a .ttf file", "Helvetica"],
            id="unknown-font-name",
        ),
        pytest.param(
            ("", "logo: missing-logo.png\n"),
            ["logo: file not found:", "missing-logo.png"],
            id="missing-logo",
        ),
        pytest.param(
            ("", "letterhead:\n  first_page: notes.txt\n"),
            ["letterhead.first_page: 'notes.txt' must be a .pdf, .png, .jpg or .jpeg file"],
            id="wrong-letterhead-type",
        ),
        pytest.param(
            ("", "page:\n  size: Tabloid\n"),
            ["page.size: 'Tabloid' is not one of 'A4', 'A5', 'Letter' or 'Legal'"],
            id="unknown-page-size",
        ),
        pytest.param(
            ("", "page:\n  margins_mm: {top: -5}\n"),
            ["page.margins_mm.top: must be at least 0 (got -5)"],
            id="negative-margin",
        ),
        pytest.param(
            ("", "page:\n  margins_mm: {top: wide}\n"),
            ["page.margins_mm.top: expected a number, got 'wide'"],
            id="non-numeric-margin",
        ),
        pytest.param(
            ("", "contact: hello@fernleaf.example\n"),
            ["contact: expected a section of keys (address, phone, email, website)"],
            id="section-given-as-value",
        ),
        pytest.param(
            ("", "page:\n  margins_mm: {left: 120, right: 100}\n"),
            ["page: left and right margins (220 mm) leave no room on A4 (210 mm wide)"],
            id="margins-too-wide",
        ),
    ],
)
def test_invalid_kit_gives_a_readable_error(
    kit_dir: Path, change: tuple[str, str], expected: list[str]
) -> None:
    old, new = change
    text = MINIMAL + new if old == "" else MINIMAL.replace(old, new)

    message = load_error(kit_dir, text)

    assert message.startswith(f"Invalid brand kit {kit_dir / 'brand.yaml'}:")
    for fragment in expected:
        assert fragment in message


def test_parse_brand_error_without_a_source_file() -> None:
    with pytest.raises(BrandError) as excinfo:
        parse_brand({"name": "Fernleaf Studio"})

    assert str(excinfo.value) == "Invalid brand kit:\n  - colors: required key missing"


def test_every_problem_is_reported_at_once(tmp_path: Path) -> None:
    text = MINIMAL.replace('"#2E5E4E"', '"green"') + "page:\n  size: Tabloid\n"

    with pytest.raises(BrandError) as excinfo:
        load_brand(write_kit(tmp_path, text))

    assert len(excinfo.value.problems) == 2
    assert "colors.primary" in str(excinfo.value)
    assert "page.size" in str(excinfo.value)


def test_missing_kit_file(tmp_path: Path) -> None:
    with pytest.raises(BrandError, match="Brand kit not found: .*nope.yaml"):
        load_brand(tmp_path / "nope.yaml")


def test_yaml_syntax_error_points_at_the_line(tmp_path: Path) -> None:
    message = load_error(tmp_path, "name: Fernleaf\ncolors: [unclosed\n")

    assert "is not valid YAML" in message
    assert "line 3" in message


def test_top_level_must_be_a_mapping(tmp_path: Path) -> None:
    message = load_error(tmp_path, "- just\n- a list\n")

    assert "expected keys such as 'name' and 'colors' at the top level" in message
