# sharland.github.io

Brian Sharland's site: a short page about his work in AI governance and
information security, with room for the documents he publishes. It is built
by GitHub Pages with Jekyll; nothing else runs anywhere.

## How it is put together

```
_config.yml          site settings, collections, plugins
_data/kinds.yml      the Work groups and their order
_data/work.yml       one entry per piece of published work
_notes/              Markdown notes; each becomes /notes/<slug>/
_layouts/            default.html (page frame), note.html (a note)
_includes/           head, side (disc, name, menu), menu (section links,
                     used by the sidebar and the sticky bar), glyph, footer
index.html           the front page
notes/index.html     list of notes at /notes/
404.html             not-found page
assets/css/site.css  all styles; colours and type live in :root
assets/js/disc.js    the drawing in the sidebar
assets/js/nav.js     marks the current section in the menu
assets/fonts/        Literata and Public Sans (both SIL Open Font License)
assets/img/          og.jpg (link preview), disc-fallback.webp (no-JS), favicons
```

## Adding a piece of work

Append an entry to `_data/work.yml`:

```yaml
- title: ISO/IEC 42001 mapped to the NIST AI RMF and the EU AI Act
  kind: mapping          # mapping | template | analysis | tool  (see _data/kinds.yml)
  year: 2026
  url: /notes/iso-42001-nist-ai-rmf-eu-ai-act/   # or a repository, or a PDF in assets/
  meta: Working draft, 2026.                     # optional, shown after the title
  summary: >-
    One or two plain sentences. Full stops, no bullet fragments.
```

Groups appear on the front page in the order given in `_data/kinds.yml` and
only when they have at least one entry, so an empty group costs nothing.

## Adding a note

Create `_notes/YYYY-MM-slug.md`:

```yaml
---
title: "The title"
date: 2026-10-05            # first published
updated: 2026-10-05         # last reviewed; shown in the document-control line
status: working draft       # free text: working draft, reviewed, final
version: "0.1"
description: >-
  One or two sentences. Used on the notes list and as the page's meta description.
published: false            # flip to true when it is ready
---

Body in Markdown. Tables work (GFM). Headings start at `##`.
```

The slug in the URL comes from the filename with the date prefix removed.
Notes with `published: false` are not built at all, so a draft can live in the
repository without appearing anywhere. The Notes section on the front page and
the `/notes/` list only show once a note is published. Published notes are also
syndicated at `/feed.xml`.

The seed note in `_notes/` was drafted offline and every reference in it is
marked "(verify)". Its editor's checklist is in a Liquid comment at the top of
the file and never renders.

## Previewing

The `Gemfile` pins the `github-pages` gem, so a local build is the same build
Pages runs.

With Ruby 3.x installed:

```sh
bundle install
bundle exec jekyll serve --livereload
# then open http://127.0.0.1:4000/
```

With Docker and no Ruby (untested here; the image installs the Gemfile on start):

```sh
docker run --rm -p 4000:4000 -v "$PWD":/srv/jekyll jekyll/jekyll:pages jekyll serve --watch --force_polling
```

Without either: push to a branch and read the build log under the repository's
Actions tab ("pages build and deployment"). The site itself only changes when
`master` changes.

To see unpublished notes locally, add `--unpublished` to the serve command.

## Deploying

This is a GitHub Pages user site, so it publishes from the root of `master`.
Merge to `master` and the build runs on its own; check the Actions tab if the
site does not change within ten minutes (Pages caches for that long). A Jekyll
error leaves the previous site in place and reports the error there.

If the Pages source has ever been changed in Settings to a `docs/` folder or a
different branch, this layout will not deploy until it is set back to
`master` and `/ (root)`.

## Design notes

- **Layout.** On screens 64rem and wider the left column is pinned: the disc, the
  name, the section menu and the two contact links stay in view while the text
  scrolls beside them. Below that width the menu becomes a bar that sticks to the
  top of the screen. The current section is marked by `assets/js/nav.js`; without
  JavaScript the menu still works as ordinary anchor links.
- **The disc.** `assets/js/disc.js` draws one of eight pieces into a canvas each
  visit: three ribbon pieces (translucent sheets between two curves), two ring
  pieces (drifting concentric circles that produce moiré), a radial burst, black
  sheets, and a black mesh. Which piece is drawn is chosen by the date, or pinned
  with `disc:` in `_config.yml`. Add `?disc=ribbons-lime` (or any other piece
  name) to the address to preview a piece on any day. The geometry inside a piece
  also changes daily.
- **Colour.** Each piece carries its own plate colour and line colours, and sets the
  page accent (links, menu highlight, heading rules) so the page always matches
  the drawing. All of it lives in the block of `html[data-disc=...]` rules at the
  top of `assets/css/site.css`; adding a piece is one CSS rule plus a name in the
  list in `_includes/head.html`, and a builder in `disc.js` if it needs a new kind
  of drawing. The light ground is cream, the dark ground is near-black, following
  the system setting.
- **Type.** Literata, a variable font with optical sizes, self-hosted from
  `assets/fonts/`. Monospace is the system stack and is only used for repository
  names.
- **Privacy.** The footer's claim that the page sets no cookies and loads nothing
  from third parties is true because the fonts are self-hosted and there is no
  analytics. Keep it true, or change the sentence.
- **Long notes.** For a table of contents inside a note, put `* TOC` on one line
  and `{:toc}` on the next where you want it; kramdown builds the list from the
  headings.
