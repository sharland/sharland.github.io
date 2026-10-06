# sharland.github.io

Brian Sharland's site: a short page about his work in AI governance and
information security, with room for the documents he publishes. It is built
by GitHub Pages with Jekyll; nothing else runs anywhere. The scripts in
`tools/` are for writing and checking on the author's machine and are not part
of the published site.

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
favicon.ico          the disc icon at 16, 32 and 48 px, for browsers that ask for this path
assets/css/site.css  all styles; colours and type live in :root
assets/js/disc.js    the drawing in the sidebar
assets/js/nav.js     marks the current section in the menu
assets/fonts/        Literata and Public Sans (both SIL Open Font License)
assets/img/          og.jpg (link preview), disc-fallback.webp (no-JS), favicons

Not published (listed under exclude in _config.yml):
tools/               sitetool.py and its modules: create, check and publish notes
tests/               pytest tests for the tools
site.bat, serve.bat  Windows shortcuts for the tools and the local preview
CLAUDE.md            working rules for AI-assisted sessions in this repository
```

## Adding a piece of work

Add an entry to `_data/work.yml`, first in its group, since entries appear in
file order and the newest belongs at the top. `site work add` does this and
checks the result (see Tools below). By hand:

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

`site new --title "The title"` creates the file below with today's date. By
hand, create `_notes/YYYY-MM-slug.md`:

```yaml
---
title: "The title"
slug: the-title             # the address: /notes/the-title/. Same as the filename after YYYY-MM-
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

The address comes from `slug:`, not from the filename. Jekyll only strips a
filename date that includes the day, so without `slug:` a file named
`2026-10-the-title.md` would be published at `/notes/2026-10-the-title/`. Once
a note is published its slug should never change. An optional `sources:` list
of public URLs records what a note draws on; it is not shown on the page.

Notes with `published: false` are not built at all, so a draft can live in the
repository without appearing on the site. The repository itself is public, so
a draft is still readable on GitHub. The Notes section on the front page and
the `/notes/` list only show once a note is published. Published notes are also
syndicated at `/feed.xml`.

The seed note in `_notes/` was drafted offline and every reference in it is
marked "(verify)". Its editor's checklist is in a Liquid comment at the top of
the file and never renders.

## Tools

`tools/sitetool.py` creates, checks and publishes notes and work entries. It
uses only the Python standard library. On Windows, `site.bat` runs it, so the
commands below can be typed as `site ...` from this folder. Nothing in it
commits, pushes or posts anywhere.

```sh
python tools/sitetool.py new --title "The title"      # start a draft note
python tools/sitetool.py check                        # check every note and work entry
python tools/sitetool.py check the-title --links      # is this note ready to publish?
python tools/sitetool.py publish the-title            # all checks, a real build, then published: true
python tools/sitetool.py work add --title "..." --kind mapping --url /notes/the-title/ --summary "..."
python tools/sitetool.py handover the-title           # title, description and link, ready to paste
python tools/sitetool.py live the-title               # wait for Pages, then fetch the live note
```

`check` reports errors, which block publishing, and warnings, which do not. A
note being published must have no `(verify)` markers, `[Brian: ...]` prompts or
editor's checklist left in it, a slug that matches its filename, sound dates, a
quoted version, headings that start at `##`, and internal links that resolve.
Work entries must have a known `kind` and a `url` that leads somewhere. With
`--build` it runs a real Jekyll build and inspects the result, including that
none of the tooling leaked into the site. What it cannot judge is left to the
author: whether a reference says what the note claims, and when a draft has
earned a new status.

`publish` sets `published: true` and `updated`, and on first publication sets
`date` to the day (`--keep-date` keeps the drafting date). Committing and
pushing remain separate, deliberate steps; see Deploying.

The tests need pytest (`pip install -r requirements-dev.txt`) and run with
`python -m pytest`. One test runs a real Jekyll build; skip it with
`-m "not slow"`.

## Previewing

The `Gemfile` pins the `github-pages` gem, so a local build is the same build
Pages runs.

With Ruby 3.x installed:

```sh
bundle install
bundle exec jekyll serve --livereload
# then open http://127.0.0.1:4000/
```

On Windows, starting with no Ruby (tested with Ruby 3.3, the version Pages
builds with):

```powershell
# 1. Ruby with the MSYS2 development kit; a few gems compile native code.
winget install --id RubyInstallerTeam.RubyWithDevKit.3.3 --source winget --scope user

# 2. Open a new terminal so Ruby is on the PATH, then from this folder:
bundle install
bundle exec jekyll serve --livereload
```

The `Gemfile` carries two Windows-only gems that make this work, and neither
is installed on any other platform. `tzinfo-data` supplies the timezone
database Windows lacks; without it Jekyll stops with "No source of timezone
data could be found" because `_config.yml` sets a timezone. `wdm` lets the
server watch for file changes through the Windows API instead of polling.

To keep the gems inside the project instead of the Ruby install, run
`bundle config set --local path vendor/bundle` before `bundle install`. Both
`vendor/` and `.bundle/` are ignored by git and by Jekyll.

With Docker and no Ruby (untested here; the image installs the Gemfile on start):

```sh
docker run --rm -p 4000:4000 -v "$PWD":/srv/jekyll jekyll/jekyll:pages jekyll serve --watch --force_polling
```

Without either: push to a branch and read the build log under the repository's
Actions tab ("pages build and deployment"). The site itself only changes when
`master` changes.

To see unpublished notes locally, add `--unpublished` to the serve command.

On Windows, `serve.bat` does the above in one step: it installs any missing
gems, starts the server and opens the browser. `serve --unpublished` shows drafts.

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
  the system setting unless the Light/Dark switch says otherwise.
- **Type.** Two faces, both self-hosted from `assets/fonts/`: Literata (serif,
  variable, optical sizes) and Public Sans (sans, variable). `type_pairing` in
  `_config.yml` decides which sets headings and which sets text: `b`, the current
  setting, is Public Sans headings with Literata text; `a` is the reverse. Add
  `?type=a` or `?type=b` to the address to compare them on the live site.
  Monospace is the system stack and is only used for repository names and the
  piece name under the disc.
- **Switches.** Clicking the disc, or the arrows beneath it, steps through the
  pieces; the choice lasts for the browser session and is written into the
  address as `?disc=<name>` so a particular piece can be linked to. Light/Dark
  overrides the system theme and is remembered in the browser. Both controls are
  hidden when JavaScript is off. The logic is in `assets/js/controls.js`.
- **Privacy.** The footer's claim that the page sets no cookies and loads nothing
  from third parties is true because the fonts are self-hosted and there is no
  analytics. Keep it true, or change the sentence.
- **Long notes.** For a table of contents inside a note, put `* TOC` on one line
  and `{:toc}` on the next where you want it; kramdown builds the list from the
  headings.
