# Brand kit reference

A brand kit is a YAML file, usually `brand.yaml`, that every document rendered with it inherits.
Run `brandpdf init` to get a commented starter kit.

Paths in the kit are relative to the kit file, so a kit and its assets can live in one folder and
move together. Hex colours must be quoted, because in YAML a bare `#` starts a comment.

```yaml
name: Fernleaf Studio

colors:
  primary: "#2E5E4E"
  secondary: "#8FB9A8"
  accent: "#E08A3C"
  text: "#1F2A24"        # optional
  background: "#FFFFFF"  # optional

fonts:
  heading: fonts/DMSerifDisplay-Regular.ttf
  body: Helvetica

logo: logo.png

contact:
  address: |
    12 Willow Lane
    Brookfield BF4 2LT
  phone: "+00 1632 960 418"
  email: hello@fernleaf.example
  website: fernleaf.example

page:
  size: A4
  margins_mm: {top: 25, right: 20, bottom: 22, left: 20}

letterhead:
  first_page: letterhead.pdf
  continuation: letterhead-continuation.pdf
```

## Keys

| Key | Required | Default | What it does |
|:--|:--|:--|:--|
| `name` | yes | | Organisation name. Used in the generated letterhead, the PDF author field, and as the title when a document has none. |
| `colors.primary` | yes | | Headings, the letterhead band, table header rows, note callouts, links. |
| `colors.secondary` | yes | | Rules, table row stripes and separators, tip callouts, quote bars. |
| `colors.accent` | yes | | Bullets and list numbers, checklist boxes, warning callouts. |
| `colors.text` | no | `#1A1A1A` | Body text. |
| `colors.background` | no | `#FFFFFF` | Page colour for pages without a letterhead file. |
| `fonts.heading` | no | `Helvetica-Bold` | Headings, the document title, table headers, callout labels. |
| `fonts.body` | no | `Helvetica` | Everything else. |
| `logo` | no | | PNG or JPEG. Replaces the name in the generated letterhead. |
| `contact.address` | no | | Multi-line address for the generated letterhead. |
| `contact.phone`, `contact.email`, `contact.website` | no | | Shown in the generated letterhead and its footer line. |
| `page.size` | no | `A4` | `A4`, `A5`, `Letter` or `Legal`. |
| `page.margins_mm` | no | 20 on each side | `top`, `right`, `bottom` and `left`, in millimetres. |
| `letterhead.first_page` | no | | PDF, PNG or JPEG drawn behind page 1. Setting it switches off the generated letterhead. |
| `letterhead.continuation` | no | `first_page` | Drawn behind pages 2 onwards. |

## Fonts

A font is either a built-in PDF font or a path to a `.ttf` file:

- **Built-in:** `Helvetica`, `Times-Roman` and `Courier`, each with `-Bold` and `-Oblique` (or
  `-Italic` for Times) variants. They need no files and have real bold and italic faces.
- **TrueType:** any static `.ttf` file, embedded in the PDF. Variable fonts (file names with
  `[wght]` in them) are not supported; download the static weights instead. A single file has one
  face, so `**bold**` and `*italic*` in body text look the same as normal text.

The [examples](../examples) use fonts under the SIL Open Font License, with each licence beside
its font.

## Letterheads

**Generated** (no `letterhead` key): page 1 gets a colour band, the logo or name, and the contact
block; later pages get a slim header with the name and document title. Every page gets a footer
with the website, email and phone, and "Page 2 of 5". The header and footer reserve space of their
own (38 mm at the top of page 1, 21 mm on later pages, 20 mm at the bottom), so margins smaller
than that are increased.

**Supplied** (`letterhead.first_page` set): the file is scaled to fill each page and drawn behind
the text. PDF letterheads use their first page. Set the margins so text clears the artwork; the
page number sits just below the text area.

## Validation

Every problem in a kit is reported at once, in terms of the YAML:

```text
Invalid brand kit brand.yaml:
  - colors.primary: '#2E5E4' is not a hex colour (expected "#RRGGBB" or "#RGB")
  - fonts.heading: file not found: /work/fonts/Heading.ttf
  - unknown key 'logo_path' (did you mean 'logo'?)
```

Fonts, images and letterhead PDFs are opened when the kit loads, so a corrupt file is caught
before any rendering starts.
