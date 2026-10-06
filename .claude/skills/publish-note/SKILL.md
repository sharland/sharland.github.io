---
name: publish-note
description: Publish a note on sharland.github.io, or check whether one is ready. Use when Brian says a note is finished, asks to publish, release or put a note live, asks "is this note ready?", or wants the LinkedIn text for a note. Walks the checks, the publish step, the commit, the push and the live verification, stopping for his go-ahead before anything goes public.
---

# Publishing a note

A push to `master` deploys the site, and a published note's address is
permanent. So this is a sequence with gates, not a single command. Run the
tooling; leave the decisions and the writing to Brian.

Commands are run from the repository root as `python tools/sitetool.py ...`.

## 1. Find out whether it is ready

```
python tools/sitetool.py check <slug> --links
```

- **Errors** block publishing. Report them grouped by kind, with counts, not
  as a raw dump. Typical ones: `(verify)` markers, `[Brian: ...]` prompts, the
  editor's checklist block.
- **Warnings** from `--links` often mean a site refuses scripts, not that the
  link is dead. Open the doubtful ones before calling a link broken.
- Do not clear markers yourself. A `(verify)` marker comes off when Brian is
  satisfied the reference is right. If he asks you to verify references, check
  each against its source and report per reference: confirmed, wrong (with
  what the source says), or could not check. He removes the marker.
- Do not write or rewrite the note's prose unless he asks for an edit.

Stop here if there are errors.

## 2. Ask Brian for the decisions that are his

- Status: `working draft`, `reviewed` or `final`.
- Version, for example `1.0` on first publication.
- Whether the note also gets an entry on the front page under Work, and if so
  the kind (see `_data/kinds.yml`), the `meta` clause and the one or two
  sentence summary. The summary is his wording.
- First publication sets `date` to today. Pass `--keep-date` only if he wants
  the drafting date kept.

## 3. Publish locally

```
python tools/sitetool.py publish <slug> [--version X.Y] [--status ...] [--keep-date]
```

This re-runs every check, runs a real Jekyll build, and only then sets
`published: true` and `updated`. If the build fails it puts the note back.

If a work entry was agreed:

```
python tools/sitetool.py work add --title "..." --kind <kind> --url /notes/<slug>/ --meta "..." --summary "..." --assume-published <slug>
```

## 4. Let Brian read it

Ask him to run `serve` and read the page at `/notes/<slug>/`, the notes list
and the front page. Wait for him to say it is right.

## 5. Commit

Show `git diff --stat` and the front matter diff. Commit only the named files:
the note, and `_data/work.yml` if it changed.

## 6. Push, only on his go-ahead

Say plainly that the push makes the note public at its permanent address, and
wait for an explicit yes in this conversation. Then `git push origin master`.

## 7. Confirm it is live, then hand over

```
python tools/sitetool.py live <slug>
python tools/sitetool.py handover <slug>
```

`live` waits for the Pages build and fetches the note. If it reports a cached
copy, wait and run it again rather than assuming failure.

`handover` prints the title, description and link and copies them to the
clipboard. That text is Brian's own words; do not embellish it. He posts to
LinkedIn himself.
