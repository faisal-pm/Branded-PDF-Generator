"""Release criterion: a 10-page document renders in under 2 seconds."""

import subprocess
import sys
import textwrap
from pathlib import Path

EXAMPLE = Path(__file__).resolve().parent.parent / "examples" / "kestrel-labs"


def test_ten_page_document_renders_in_under_two_seconds() -> None:
    # A fresh interpreter, so font loading and imports count, as they would for a CLI user.
    script = textwrap.dedent(
        f"""
        import io, time
        from pathlib import Path
        start = time.perf_counter()
        from brandpdf import load_brand, render
        from pypdf import PdfReader
        kit = Path({str(EXAMPLE)!r})
        source = (kit / "test-programme-report.md").read_text(encoding="utf-8")
        body = source.split("---", 2)[2]
        markdown = source + "".join(body.replace("## ", "### ") for _ in range(4))
        pdf = render(markdown, load_brand(kit / "brand.yaml"), base_dir=kit)
        elapsed = time.perf_counter() - start
        print(len(PdfReader(io.BytesIO(pdf)).pages), elapsed)
        """
    )
    result = subprocess.run(
        [sys.executable, "-c", script], capture_output=True, text=True, check=True
    )
    pages, seconds = result.stdout.split()

    assert int(pages) >= 10
    assert float(seconds) < 2.0
