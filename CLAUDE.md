# sharland.github.io

Brian Sharland's personal site: Jekyll on GitHub Pages, published from the root
of `master`. `README.md` describes the layout and design. This file is about
how to work here.

## Rules that are easy to break

- **A push to `master` is a live deploy.** Commit and push only when Brian asks.
  Small changes go straight to `master`; use a branch and pull request for
  anything larger, and say so.
- **Notes only.** The site carries formal working documents in `_notes/`. There
  is no blog or commentary section and none should be added; short commentary
  goes to LinkedIn, which the Notes area links to.
- **Opinion writing is Brian's alone.** For an opinion note or LinkedIn
  commentary, do not draft, rewrite, edit, tidy or suggest wording, even where
  that leaves errors in. He works in AI compliance and wants his opinions to be
  demonstrably his own. Help there is limited to mechanics he asks for:
  creating the empty file, running the rule-based checks, publishing.
- **Structured documents are different.** For crosswalks, mappings, templates
  and policy, assist normally: verify references against their sources and
  edit on request. If it is unclear which kind a piece is, ask. `site new`
  leaves `[Brian: ...]` prompts and never prose.
- **Personal only.** This is a personal project. Do not read from or write to
  employer systems or data (work Slack, Jira, Confluence, work mail or files)
  for anything here, and do not send project content to an external model API
  without asking first.
- **The repository is public, drafts included.** `published: false` hides a
  note from the site, not from GitHub. Put only public URLs in `sources:`;
  never newsletter text, mail links or anything private.
- **A slug is permanent once published.** It is the note's address. Changing it
  breaks links.
- **Pages builds with no custom plugins.** Anything beyond the `github-pages`
  gem set will work locally and fail live.

## Commands

`site.bat` wraps `python tools/sitetool.py`. Nothing in it commits, pushes or posts.

| Command | What it does |
|---|---|
| `site new --title "..." [--source URL]` | Start a draft in `_notes/YYYY-MM-<slug>.md` |
| `site save --slug ... --title ... --description ... --body-file F` | Write a draft from a body file; refuses to touch a published note. Used by the daily-briefing page |
| `site work add --title --kind --url --summary [--meta] [--year]` | Add an entry to `_data/work.yml`, first in its group |
| `site check` | Check every note and work entry as they stand |
| `site check <slug> [--build] [--links]` | Judge one note as if it were published |
| `site publish <slug> [--version] [--status] [--keep-date]` | Run every check and a real build, then mark the note published |
| `site handover <slug> [--json]` | Title, description and link, ready to paste into LinkedIn |
| `site live <slug>` | Wait for the Pages build of HEAD, then fetch the live note |
| `serve [--unpublished]` | Local preview with live reload; `--unpublished` shows drafts |

Tests: `python -m pytest` (add `-m "not slow"` to skip the real Jekyll build).

## Publishing a note

1. `site check <slug> --links`. Errors block publishing. Brian fixes them; verify
   references against their sources when he asks, and report per reference.
2. Brian decides the status, the version, and whether the note also gets a
   `work.yml` entry.
3. `site publish <slug>`, then `site work add ... --assume-published <slug>` if wanted.
4. Brian previews it with `serve`.
5. Show the diff, then commit the named files.
6. Push only on Brian's explicit go-ahead.
7. `site live <slug>`, then `site handover <slug>`. Brian posts to LinkedIn himself.

## What the checks do and do not cover

`tools/checks.py` holds every rule that can be written down: filename and slug,
front matter, leftover drafting markers, heading levels, internal links, and
the shape of `work.yml`. `--build` inspects a real Jekyll build.

Not in code, by design: whether a reference says what the note claims (Claude
researches, Brian decides), tone and argument, and when a draft has earned a
new status or version (Brian).

## Practical details

- Working files have CRLF line endings. The tools preserve whatever a file
  uses; do the same when editing by hand.
- A note's address comes from `slug:` in its front matter, not the filename.
  Jekyll only strips a filename date that includes the day.
- Ruby is at `C:\Ruby33-x64`; gems are in `vendor/bundle`. See Previewing in the README.
- `_config.yml` `exclude:` keeps tooling out of the built site. Add any new
  top-level tooling file there; `site check --build` fails if one leaks.
- After a push, `gh api repos/sharland/sharland.github.io/pages/builds/latest`
  shows whether Pages built it.
