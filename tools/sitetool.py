"""Create, check and publish the notes and work entries on this site.

    python tools/sitetool.py new --title "..."        start a draft note
    python tools/sitetool.py work add ...             add an entry to _data/work.yml
    python tools/sitetool.py check [slug]             check everything; with a slug,
                                                      judge that note as if published
    python tools/sitetool.py publish <slug>           mark a note published, after checks
    python tools/sitetool.py handover <slug>          title, summary and link, ready to paste
    python tools/sitetool.py live <slug>              wait for GitHub Pages, then look

Nothing here commits, pushes or posts. Those stay deliberate, separate steps.
Exit status: 0 clean, 1 problems found, 2 wrong usage.
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import re
import subprocess
import sys
import textwrap
import time
import unicodedata
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import checks  # noqa: E402
import frontmatter  # noqa: E402
import workyml  # noqa: E402

DEFAULT_ROOT = Path(__file__).resolve().parent.parent
REPO = "sharland/sharland.github.io"


def site_url(root: Path) -> str:
    config = root / "_config.yml"
    if config.is_file():
        m = re.search(r'^url:\s*"?([^"\s#]+)"?', config.read_text(encoding="utf-8"), re.M)
        if m:
            return m.group(1).rstrip("/")
    return "https://sharland.github.io"


def repo_newline(root: Path) -> str:
    config = root / "_config.yml"
    if config.is_file():
        return frontmatter.detect_newline(config.read_text(encoding="utf-8", newline=""))
    return "\n"


def slugify(title: str) -> str:
    folded = unicodedata.normalize("NFKD", title).encode("ascii", "ignore").decode("ascii")
    return re.sub(r"[^a-z0-9]+", "-", folded.lower()).strip("-")


def report(findings: list, out=None) -> int:
    out = out or sys.stdout
    order = {"E": 0, "W": 1, "I": 2}
    for finding in sorted(findings, key=lambda f: (order[f.severity], f.path, f.line)):
        print(finding, file=out)
    errors = sum(1 for f in findings if f.severity == "E")
    warnings = sum(1 for f in findings if f.severity == "W")
    print(f"{errors} error(s), {warnings} warning(s).", file=out)
    return 1 if errors else 0


def write(path: Path, text: str) -> None:
    path.write_text(text, encoding="utf-8", newline="")


# --- check ----------------------------------------------------------------

def cmd_check(args) -> int:
    root, today = args.root, args.today
    findings = checks.run(root, today, slug=args.slug)
    notes = checks.load_notes(root)
    target = checks.find_note(notes, args.slug) if args.slug else None
    if args.build and not any(f.severity == "E" and f.path == "_notes" for f in findings):
        expect = [n.slug for n in notes if n.published and n.slug]
        if target and target.slug not in expect:
            expect.append(target.slug)
        findings += checks.check_build(root, expect,
                                       unpublished=bool(target and not target.published))
    if args.links:
        scope = [target] if target else notes
        findings += checks.check_external(checks.external_urls(root, scope))
    return report(findings)


# --- new ------------------------------------------------------------------

def front_matter(title, slug, date, updated, status, version, description, sources, published) -> list:
    lines = [
        "---",
        f"title: {frontmatter.quote(title)}",
        f"slug: {slug}",
        f"date: {date.isoformat()}",
        f"updated: {updated.isoformat()}",
        f"status: {status}",
        f"version: {frontmatter.quote(version)}",
        "description: >-",
    ]
    lines += ["  " + part for part in textwrap.wrap(" ".join(description.split()), width=78,
                                                   break_long_words=False, break_on_hyphens=False)]
    if sources:
        lines.append("sources:")
        lines += [f"  - {url}" for url in sources]
    lines += [f"published: {'true' if published else 'false'}", "---"]
    return lines


def cmd_new(args) -> int:
    root, today = args.root, args.today
    slug = args.slug or slugify(args.title)
    if not re.fullmatch(r"[a-z0-9]+(-[a-z0-9]+)*", slug) or re.match(r"^\d{1,2}-", slug):
        print(f"cannot use {slug!r} as a slug: lower-case letters, digits and hyphens, "
              "and not starting like a day of the month", file=sys.stderr)
        return 2
    notes = checks.load_notes(root)
    if checks.find_note(notes, slug):
        print(f"a note with slug {slug!r} already exists", file=sys.stderr)
        return 1
    for url in args.source or []:
        if not re.match(r"^https?://\S+$", url):
            print(f"not a public URL: {url!r}", file=sys.stderr)
            return 2
    description = args.description or "[Brian: one or two sentences. Used on the notes list and as the page's meta description.]"
    lines = front_matter(args.title, slug, today, today, "working draft", "0.1", description,
                         args.source or [], False)
    lines += [
        "",
        "## [Brian: first heading]",
        "",
        "[Brian: write the note here. Headings start at ##.]",
        "",
    ]
    newline = repo_newline(root)
    path = root / "_notes" / f"{today:%Y-%m}-{slug}.md"
    path.parent.mkdir(exist_ok=True)
    write(path, newline.join(lines))
    result = {"path": path.relative_to(root).as_posix(), "slug": slug,
              "url": f"{site_url(root)}/notes/{slug}/"}
    if args.json:
        print(json.dumps(result))
    else:
        print(f"Created {result['path']}")
        print(f"It will be published at {result['url']}")
        print("Preview drafts with: serve --unpublished")
    return 0


def cmd_save(args) -> int:
    root, today = args.root, args.today
    slug = args.slug.strip()
    if not re.fullmatch(r"[a-z0-9]+(-[a-z0-9]+)*", slug) or re.match(r"^\d{1,2}-", slug):
        print("slug may contain only lower-case letters, digits and hyphens, and must not start like a day",
              file=sys.stderr)
        return 2
    if not args.title.strip() or not args.description.strip():
        print("a note needs a title and a description", file=sys.stderr)
        return 2
    try:
        body = Path(args.body_file).read_text(encoding="utf-8")
    except OSError as error:
        print(f"cannot read the body: {error}", file=sys.stderr)
        return 2
    for url in args.source or []:
        if not re.match(r"^https?://\S+$", url):
            print(f"not a public URL: {url!r}", file=sys.stderr)
            return 2
    status = args.status or "final"
    version = args.version or "1.0"
    if not checks.VERSION_RE.match(version):
        print('version must look like "1.0"', file=sys.stderr)
        return 2

    existing = checks.find_note(checks.load_notes(root), slug)
    if existing is not None and existing.published:
        print(f"{existing.rel} is published; the page does not rewrite live notes", file=sys.stderr)
        return 1
    newline = repo_newline(root)
    if existing is not None:
        path = existing.path
        date = checks._parse_date(str(existing.front.data.get("date", ""))) or today
    else:
        path = root / "_notes" / f"{today:%Y-%m}-{slug}.md"
        date = today
    body = body.replace("\r\n", "\n").strip("\n") + "\n"
    lines = front_matter(args.title.strip(), slug, date, today, status, version,
                         args.description, args.source or [], False)
    text = newline.join(lines) + newline + newline + body.replace("\n", newline)
    path.parent.mkdir(exist_ok=True)
    write(path, text)
    result = {"path": path.relative_to(root).as_posix(), "slug": slug,
              "url": f"{site_url(root)}/notes/{slug}/", "created": existing is None}
    if args.json:
        print(json.dumps(result))
    else:
        print(f"{'Created' if existing is None else 'Updated'} {result['path']} (unpublished)")
    return 0


# --- work add -------------------------------------------------------------

def cmd_work_add(args) -> int:
    root, today = args.root, args.today
    work_path = root / "_data" / "work.yml"
    kinds = workyml.kind_ids((root / "_data" / "kinds.yml").read_text(encoding="utf-8"))
    if args.kind not in kinds:
        print(f"kind must be one of: {', '.join(kinds)}", file=sys.stderr)
        return 2
    entry = {"title": args.title, "kind": args.kind, "year": str(args.year or today.year),
             "url": args.url, "meta": args.meta, "summary": args.summary}
    original = work_path.read_text(encoding="utf-8", newline="")
    try:
        updated = workyml.insert(original, entry, kinds)
    except ValueError as error:
        print(error, file=sys.stderr)
        return 1
    write(work_path, updated)
    notes = checks.load_notes(root)
    findings = checks.check_work(root, notes, today,
                                 assume_published=set(args.assume_published or []))
    if any(f.severity == "E" for f in findings):
        write(work_path, original)
        report(findings, sys.stderr)
        print("Nothing was changed.", file=sys.stderr)
        return 1
    print(f"Added {args.title!r} to _data/work.yml under {args.kind}.")
    return report(findings)


# --- publish --------------------------------------------------------------

def cmd_publish(args) -> int:
    root, today = args.root, args.today
    notes = checks.load_notes(root)
    note = checks.find_note(notes, args.slug)
    if note is None:
        print(f"no note with slug {args.slug!r}", file=sys.stderr)
        return 1
    if args.version and not checks.VERSION_RE.match(args.version):
        print('version must look like "1.0"', file=sys.stderr)
        return 2
    original = note.text
    first_time = not note.published
    text = original
    try:
        text = frontmatter.set_field(text, "published", "true")
        text = frontmatter.set_field(text, "updated", today.isoformat())
        if first_time and not args.keep_date:
            text = frontmatter.set_field(text, "date", today.isoformat())
        if args.version:
            text = frontmatter.set_field(text, "version", frontmatter.quote(args.version))
        if args.status:
            text = frontmatter.set_field(text, "status", args.status)
    except ValueError as error:
        print(f"{note.rel}: {error}", file=sys.stderr)
        return 1

    findings = checks.run(root, today, slug=note.slug or args.slug, overrides={note.path: text})
    if any(f.severity == "E" for f in findings):
        report(findings)
        print("Not published. Nothing was changed.")
        return 1

    write(note.path, text)
    if not args.no_build:
        expect = [n.slug for n in checks.load_notes(root) if n.published and n.slug]
        build = checks.check_build(root, expect)
        findings += build
        if any(f.severity == "E" for f in build):
            write(note.path, original)
            report(findings)
            print("Not published. The note was put back as it was.")
            return 1
    report(findings)
    print(f"{note.rel} is marked published. Nothing is committed or pushed yet.")
    print("Next: preview it, then commit and push when you are ready.")
    return 0


# --- handover -------------------------------------------------------------

def cmd_handover(args) -> int:
    root = args.root
    note = checks.find_note(checks.load_notes(root), args.slug)
    if note is None:
        print(f"no note with slug {args.slug!r}", file=sys.stderr)
        return 1
    data = note.front.data
    url = f"{site_url(root)}/notes/{note.slug}/"
    info = {"title": data.get("title", ""), "description": data.get("description", ""),
            "url": url, "slug": note.slug, "status": data.get("status", ""),
            "version": data.get("version", ""), "date": data.get("date", ""),
            "updated": data.get("updated", ""), "published": note.published}
    info["text"] = f"{info['title']}\n\n{info['description']}\n\n{url}"
    if not note.published:
        print("warning: this note is not published, so the link will not work yet", file=sys.stderr)
    if args.json:
        print(json.dumps(info, ensure_ascii=False))
        return 0
    print(info["text"])
    if not args.no_clip and sys.platform == "win32":
        try:
            subprocess.run(["clip"], input=("﻿" + info["text"]).encode("utf-16-le"), check=True)
            print("\n(copied to the clipboard)", file=sys.stderr)
        except (OSError, subprocess.CalledProcessError):
            pass
    return 0


# --- live -----------------------------------------------------------------

def _fetch(url: str) -> tuple[int, str]:
    request = urllib.request.Request(url, headers={"Cache-Control": "no-cache"})
    try:
        with urllib.request.urlopen(request, timeout=20) as response:
            return response.status, response.read().decode("utf-8", errors="replace")
    except Exception as error:
        return getattr(error, "code", 0), ""


def cmd_live(args) -> int:
    root = args.root
    note = checks.find_note(checks.load_notes(root), args.slug)
    if note is None:
        print(f"no note with slug {args.slug!r}", file=sys.stderr)
        return 1
    head = subprocess.run(["git", "rev-parse", "HEAD"], cwd=root, capture_output=True,
                          text=True).stdout.strip()
    deadline = time.monotonic() + args.timeout
    status = commit = ""
    while True:
        result = subprocess.run(["gh", "api", f"repos/{REPO}/pages/builds/latest"],
                                cwd=root, capture_output=True, text=True)
        if result.returncode == 0:
            build = json.loads(result.stdout)
            status, commit = build.get("status", ""), build.get("commit", "")
            if commit == head and status in ("built", "errored"):
                break
        if time.monotonic() > deadline:
            print(f"Timed out. Latest Pages build is {status or 'unknown'} for "
                  f"{commit[:7] or 'unknown'}; HEAD is {head[:7]}. Has HEAD been pushed?")
            return 1
        time.sleep(10)
    if status == "errored":
        print(f"The Pages build for {head[:7]} failed: {build.get('error', {}).get('message')}")
        return 1
    url = f"{site_url(root)}/notes/{note.slug}/"
    code, page = _fetch(url)
    if code != 200:
        print(f"Pages built {head[:7]}, but {url} answered {code}. "
              "Pages can serve a cached copy for up to ten minutes; try again shortly.")
        return 1
    _, feed = _fetch(f"{site_url(root)}/feed.xml")
    print(f"Pages built {head[:7]}. {url} is live.")
    print("In the feed." if url in feed else "Not in the feed yet; it may still be cached.")
    return 0


# --- command line ---------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="site", description=__doc__.split("\n\n")[0],
                                     epilog="Run a command with -h for its options.")
    parser.add_argument("--root", type=Path, default=DEFAULT_ROOT, help=argparse.SUPPRESS)
    parser.add_argument("--today", type=dt.date.fromisoformat, default=None, help=argparse.SUPPRESS)
    sub = parser.add_subparsers(dest="command", metavar="command")

    p = sub.add_parser("new", help="start a draft note in _notes/")
    p.add_argument("--title", required=True)
    p.add_argument("--description", help="one or two sentences; a prompt is left if omitted")
    p.add_argument("--slug", help="the address under /notes/; made from the title if omitted")
    p.add_argument("--source", action="append", metavar="URL",
                   help="a public URL the note draws on; repeatable")
    p.add_argument("--json", action="store_true", help="print path, slug and url as JSON")
    p.set_defaults(func=cmd_new)

    p = sub.add_parser("save", help="write a draft note from a title, description and body file")
    p.add_argument("--slug", required=True)
    p.add_argument("--title", required=True)
    p.add_argument("--description", required=True)
    p.add_argument("--body-file", required=True, help="a file holding the Markdown body")
    p.add_argument("--source", action="append", metavar="URL")
    p.add_argument("--status", help="defaults to final")
    p.add_argument("--version", help="defaults to 1.0")
    p.add_argument("--json", action="store_true")
    p.set_defaults(func=cmd_save)

    p = sub.add_parser("work", help="edit _data/work.yml")
    wsub = p.add_subparsers(dest="work_command", metavar="add", required=True)
    a = wsub.add_parser("add", help="add an entry at the top of its group")
    a.add_argument("--title", required=True)
    a.add_argument("--kind", required=True, help="an id from _data/kinds.yml")
    a.add_argument("--year", type=int, help="defaults to this year")
    a.add_argument("--url", required=True, help="a repository, /notes/<slug>/ or a file in assets/")
    a.add_argument("--meta", help='short clause after the title, e.g. "Python, 2026."')
    a.add_argument("--summary", required=True, help="one or two plain sentences")
    a.add_argument("--assume-published", action="append", metavar="SLUG",
                   help="allow a link to a note you are about to publish")
    a.set_defaults(func=cmd_work_add)

    p = sub.add_parser("check", help="check notes and work entries")
    p.add_argument("slug", nargs="?", help="judge this note as if it were published")
    p.add_argument("--build", action="store_true", help="also run a real Jekyll build and inspect it")
    p.add_argument("--links", action="store_true", help="also ask each external link whether it answers")
    p.set_defaults(func=cmd_check)

    p = sub.add_parser("publish", help="mark a note published once it passes every check")
    p.add_argument("slug")
    p.add_argument("--version", help='set a new version, e.g. "1.0"')
    p.add_argument("--status", help="set a new status, e.g. reviewed")
    p.add_argument("--keep-date", action="store_true",
                   help="keep the drafting date as the publication date")
    p.add_argument("--no-build", action="store_true", help="skip the Jekyll build check")
    p.set_defaults(func=cmd_publish)

    p = sub.add_parser("handover", help="title, description and link, ready to paste elsewhere")
    p.add_argument("slug")
    p.add_argument("--json", action="store_true")
    p.add_argument("--no-clip", action="store_true", help="do not copy to the clipboard")
    p.set_defaults(func=cmd_handover)

    p = sub.add_parser("live", help="wait for GitHub Pages to build HEAD, then fetch the note")
    p.add_argument("slug")
    p.add_argument("--timeout", type=int, default=300, help="seconds to wait (default 300)")
    p.set_defaults(func=cmd_live)
    return parser


def main(argv: list[str] | None = None) -> int:
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8", errors="replace")
    parser = build_parser()
    args = parser.parse_args(argv)
    if not getattr(args, "func", None):
        parser.print_help()
        return 2
    args.root = args.root.resolve()
    args.today = args.today or dt.date.today()
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
