# Case study: brandpdf

**What it is:** an open-source Python library and command-line tool that turns a brand kit and
Markdown into consistently branded, multi-page PDFs.
**Stack:** Python 3.10+, ReportLab, markdown-it-py, pydantic, pypdf, Typer; pytest with pdfplumber
and PyMuPDF for testing.
**Links:** [GitHub](https://github.com/faisal-pm/Branded-PDF-Generator) ·
[examples](https://github.com/faisal-pm/Branded-PDF-Generator/tree/main/examples)

## The problem

Small organisations produce a steady stream of documents: checklists, letters, information sheets,
reports. Without a designer or a template system, each one is rebuilt by hand in a word processor
and drifts off-brand. Generating them from code is no easier: ReportLab is capable but low-level,
so every new document type means more layout code.

I had built branded document tooling for a training organisation and kept meeting the same need.
brandpdf is a clean, general version of that idea, written from scratch for anyone to use.

## The approach

Two inputs, one command:

- **A brand kit** (`brand.yaml`) holds everything visual: colours, fonts, logo, contact details,
  page setup and letterhead. It is written once.
- **Documents** are plain Markdown, with a few widely known extras: tables, `- [ ]` checklists, and
  GitHub-style `> [!WARNING]` callouts. People can write them, and so can AI assistants, without
  touching layout code.

`brandpdf build doc.md` combines the two.

## Design decisions

**Three small layers.** Markdown is parsed into plain, immutable data with no PDF types in it.
A second layer maps that data to ReportLab flowables using styles derived from the brand kit.
A third draws letterheads and footers on each page. Each layer is tested on its own.

**Errors written for the person editing the file.** The brand kit is validated with pydantic, but
its messages are rewritten in terms of the YAML: `colors.primary: '#2E5E4' is not a hex colour`,
`unknown key 'colours' (did you mean 'colors'?)`. Every problem is reported at once, and fonts,
images and letterhead PDFs are opened at load time, so a broken kit fails before rendering starts.
A bare `#` in YAML starts a comment and silently empties a colour; the error says to quote it.

**Deterministic output.** The same inputs produce a byte-identical PDF, which makes outputs safe to
commit, diff and cache.

**Two letterhead modes.** A letterhead can be generated from the kit (colour band, logo, contact
block, footer) or supplied as a designer's PDF or image. ReportLab can't import PDF pages, so
supplied PDFs are merged underneath each finished page with pypdf.

**"Page 2 of 5".** Page totals aren't known until layout finishes, so a custom canvas holds each
page and draws the footers once the count is in.

## Testing

About 140 tests, written before the code they cover:

- **Unit tests** for parsing and validation.
- **Content tests** that render a PDF and read it back with pdfplumber, checking text order, fonts,
  colours, positions, page numbers and repeated table headers.
- **Visual snapshots:** each page is rasterised with PyMuPDF and compared with a committed reference
  image within a small pixel tolerance. Accepting a new snapshot is a deliberate step.

CI runs on Linux, macOS and Windows with Python 3.10 and 3.13.

Testing caught real layout bugs. For example, a heading marked "keep with next" dragged a
60-row table onto the next page and left page 1 blank. Headings now use a conditional page break
instead.

## Results

- A 10-page document renders in about 0.1 seconds, under 1 second from a cold start.
- From `pip install` to a first branded PDF takes a few minutes with the README quickstart.
- Three fictional example brands cover every letterhead mode, page size and content feature.

## What's next

A browser UI, and a generator that builds a brand kit from an existing website or style guide.
