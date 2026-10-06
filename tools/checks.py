"""The rules a note and a work entry must meet, each one written down as code.

Severity:
    E  error    blocks publishing
    W  warning  reported, does not block
    I  info     a count worth knowing, nothing to fix yet

What is *not* here is anything that needs judgment: whether a reference says
what the note claims, tone, argument, or when a draft has earned a new status.
Those stay with the author.
"""

from __future__ import annotations

import datetime as dt
import html.parser
import os
import re
import shutil
import subprocess
import tempfile
import urllib.error
import urllib.request
from dataclasses import dataclass
from pathlib import Path

import frontmatter
import workyml

FILENAME_RE = re.compile(r"^(\d{4})-(\d{2})-([a-z0-9]+(?:-[a-z0-9]+)*)\.md$")
DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
VERSION_RE = re.compile(r"^\d+\.\d+$")
REQUIRED = ["title", "slug", "date", "updated", "status", "version", "description", "published"]
OPTIONAL = ["sources"]
STATUSES = ["working draft", "reviewed", "final"]
DESCRIPTION_MAX = 300
BLOCKING_MARKERS = [
    ("(verify)", "an unchecked reference, marked (verify)"),
    ("[Brian:", "an unanswered [Brian: ...] prompt"),
    ("EDITOR'S CHECKLIST", "the editor's checklist"),
    ("{% comment %}", "a Liquid comment block"),
]
SOFT_MARKER_RE = re.compile(r"\b(TODO|TK)\b")
MD_LINK_RE = re.compile(r"\[[^\]]*\]\(\s*([^)\s]*)(?:\s+\"[^\"]*\")?\s*\)")
HREF_RE = re.compile(r"""(?:href|src)\s*=\s*["']([^"']*)["']""")
HEADING_RE = re.compile(r"^(#{1,6})\s+\S")
FENCE_RE = re.compile(r"^\s*(```|~~~)")
KNOWN_PAGES = {"/", "/notes/", "/feed.xml", "/sitemap.xml", "/robots.txt"}
LEAKS = ["tools", "tests", "design", "CLAUDE.md", "CLAUDE.html", "pytest.ini",
         "requirements-dev.txt", "Gemfile", "README.md", "README.html"]
RUBY_BIN = r"C:\Ruby33-x64\bin"


@dataclass(frozen=True)
class Finding:
    severity: str
    path: str
    line: int
    message: str

    def __str__(self) -> str:
        where = f"{self.path}:{self.line}" if self.line else self.path
        return f"{self.severity}  {where}  {self.message}"


@dataclass
class Note:
    path: Path
    rel: str
    text: str
    front: frontmatter.Front

    @property
    def slug(self) -> str:
        return str(self.front.data.get("slug", ""))

    @property
    def published(self) -> bool:
        return self.front.data.get("published") == "true"

    def body_lines(self):
        """(line number, text, in_code_fence) for each line of the body."""
        fenced = False
        for offset, line in enumerate(self.front.body.split("\n")):
            if FENCE_RE.match(line):
                fenced = not fenced
                yield self.front.body_line + offset, line, True
                continue
            yield self.front.body_line + offset, line, fenced


def load_notes(root: Path, overrides: dict | None = None) -> list[Note]:
    """Every note in _notes/. `overrides` maps a path to text to use instead of the file."""
    overrides = {Path(k).resolve(): v for k, v in (overrides or {}).items()}
    notes = []
    folder = root / "_notes"
    for path in sorted(folder.glob("*.md")) if folder.is_dir() else []:
        text = overrides.get(path.resolve())
        if text is None:
            text = path.read_text(encoding="utf-8", newline="")
        notes.append(Note(path, path.relative_to(root).as_posix(), text, frontmatter.parse(text)))
    return notes


def find_note(notes: list[Note], slug: str) -> Note | None:
    for note in notes:
        if note.slug == slug or note.path.stem == slug:
            return note
        m = FILENAME_RE.match(note.path.name)
        if m and m.group(3) == slug:
            return note
    return None


def _strip_code_spans(line: str) -> str:
    return re.sub(r"`[^`]*`", lambda m: " " * len(m.group(0)), line)


def _parse_date(value: str) -> dt.date | None:
    if not DATE_RE.match(value or ""):
        return None
    try:
        return dt.date.fromisoformat(value)
    except ValueError:
        return None


def check_note(note: Note, notes: list[Note], root: Path, today: dt.date,
               as_published: bool = False) -> list[Finding]:
    out: list[Finding] = []
    front = note.front
    data = front.data
    live = note.published or as_published

    def add(severity, line, message):
        out.append(Finding(severity, note.rel, line, message))

    # Filename and slug
    name = FILENAME_RE.match(note.path.name)
    if not name:
        add("E", 0, "filename is not YYYY-MM-slug.md in lower case with hyphens")
    if not front.has_front:
        add("E", 1, "no front matter")
        return out
    for line, message in front.errors:
        add("E", line, message)

    slug = data.get("slug", "")
    if name and slug and slug != name.group(3):
        add("E", front.lines["slug"], f"slug {slug!r} does not match the filename ({name.group(3)!r})")
    if slug and re.match(r"^\d{1,2}-", str(slug)):
        add("E", front.lines["slug"], "slug starts like a day of the month; Jekyll would read the filename as a date")
    if slug and sum(1 for other in notes if other.slug == slug) > 1:
        add("E", front.lines["slug"], f"slug {slug!r} is used by more than one note")

    # Front matter
    for key in REQUIRED:
        if key not in data or data[key] == "" or data[key] == []:
            add("E", front.lines.get(key, 1), f"front matter is missing {key!r}")
    for key in data:
        if key not in REQUIRED and key not in OPTIONAL:
            add("W", front.lines[key], f"unknown front matter key {key!r}")

    if "published" in data and data["published"] not in ("true", "false"):
        add("E", front.lines["published"], "published must be true or false")

    date = updated = None
    for key in ("date", "updated"):
        if data.get(key):
            parsed = _parse_date(str(data[key]))
            if parsed is None:
                add("E", front.lines[key], f"{key} is not a real date written YYYY-MM-DD")
            elif live and parsed > today:
                add("E", front.lines[key], f"{key} is in the future; Jekyll lists the note but does not build its page")
            if key == "date":
                date = parsed
            else:
                updated = parsed
    if date and updated and updated < date:
        add("E", front.lines["updated"], "updated is earlier than date")

    if data.get("version"):
        if not VERSION_RE.match(str(data["version"])):
            add("E", front.lines["version"], 'version must look like "0.1"')
        elif "version" not in front.quoted:
            add("E", front.lines["version"], 'version must be quoted, or YAML reads "1.10" as 1.1')
    if data.get("status") and data["status"] not in STATUSES:
        add("W", front.lines["status"], f"status {data['status']!r} is not one of: {', '.join(STATUSES)}")
    if isinstance(data.get("description"), str) and len(data["description"]) > DESCRIPTION_MAX:
        add("W", front.lines["description"],
            f"description is {len(data['description'])} characters; over {DESCRIPTION_MAX} is long for a list entry")

    sources = data.get("sources", [])
    if sources and not isinstance(sources, list):
        add("E", front.lines["sources"], "sources must be a list of URLs")
    elif sources:
        for url in sources:
            if not re.match(r"^https?://\S+$", url):
                add("E", front.lines["sources"], f"source is not a public URL: {url!r}")

    # Markers left from drafting
    marker_count = 0
    for marker, meaning in BLOCKING_MARKERS:
        hits = [n for n, line, _ in note.body_lines() if marker in line]
        marker_count += len(hits)
        if live:
            for n in hits:
                add("E", n, f"still contains {meaning}")
    for n, line, fenced in note.body_lines():
        if not fenced and SOFT_MARKER_RE.search(_strip_code_spans(line)):
            add("W", n, "contains TODO or TK")
    if marker_count and not live:
        add("I", 0, f"draft: {marker_count} drafting markers to clear before publishing")

    # Headings
    previous = None
    for n, line, fenced in note.body_lines():
        if fenced:
            continue
        m = HEADING_RE.match(line)
        if not m:
            continue
        level = len(m.group(1))
        if level == 1:
            add("E", n, "a # heading in the body; the title is the page's only h1, so start at ##")
        elif previous is None and level != 2:
            add("W", n, "the first heading is not ##")
        elif previous is not None and level > previous + 1:
            add("W", n, f"heading jumps from level {previous} to level {level}")
        previous = level

    # Links
    by_slug = {other.slug: other for other in notes if other.slug}
    for n, line, fenced in note.body_lines():
        if fenced:
            continue
        clean = _strip_code_spans(line)
        targets = MD_LINK_RE.findall(clean) + HREF_RE.findall(clean)
        for target in targets:
            for finding in _check_target(target, by_slug, root, live):
                add(finding[0], n, finding[1])
    return out


def _check_target(target: str, by_slug: dict, root: Path, live: bool):
    if "{{" in target or "{%" in target:
        return
    if target == "":
        yield "E", "a link with an empty target"
        return
    if target.startswith(("#", "mailto:")):
        return
    if target.startswith("http://"):
        yield "W", f"plain http link: {target}"
        return
    if target.startswith("https://"):
        return
    path = target.split("#")[0].split("?")[0]
    if not path.startswith("/"):
        yield "W", f"relative link {target!r}; start internal links with /"
        return
    m = re.match(r"^/notes/([^/]+)/?$", path)
    if m:
        other = by_slug.get(m.group(1))
        if other is None:
            yield "E", f"links to a note that does not exist: {path}"
        elif live and not other.published:
            yield "E", f"links to a note that is not published: {path}"
        return
    if path in KNOWN_PAGES:
        return
    if not (root / path.lstrip("/")).is_file():
        yield "E", f"links to a file that does not exist: {path}"


def check_work(root: Path, notes: list[Note], today: dt.date,
               assume_published: set | None = None) -> list[Finding]:
    out: list[Finding] = []
    rel = "_data/work.yml"
    work_path = root / "_data" / "work.yml"
    kinds_path = root / "_data" / "kinds.yml"
    if not work_path.is_file():
        return [Finding("E", rel, 0, "file is missing")]
    kinds = workyml.kind_ids(kinds_path.read_text(encoding="utf-8")) if kinds_path.is_file() else []
    listing = workyml.parse(work_path.read_text(encoding="utf-8"))
    assume_published = assume_published or set()
    by_slug = {n.slug: n for n in notes if n.slug}

    def add(severity, line, message):
        out.append(Finding(severity, rel, line, message))

    for line, message in listing.errors:
        add("E", line, message)

    seen_titles: dict = {}
    seen_urls: dict = {}
    last_year: dict = {}
    for block in listing.blocks:
        data, lines = block.data, block.lines
        first = block.start + 1
        for key in workyml.WORK_REQUIRED:
            if not data.get(key):
                add("E", lines.get(key, first), f"entry is missing {key!r}")
        for key in data:
            if key not in workyml.WORK_FIELDS:
                add("W", lines[key], f"unknown key {key!r}")
        kind = data.get("kind")
        if kind and kind not in kinds:
            add("E", lines["kind"], f"kind {kind!r} is not an id in _data/kinds.yml")
        year = data.get("year", "")
        if year:
            if not re.match(r"^\d{4}$", year):
                add("E", lines["year"], "year must be four digits")
            elif int(year) > today.year:
                add("E", lines["year"], "year is in the future")
            elif kind:
                if kind in last_year and int(year) > last_year[kind]:
                    add("W", lines["year"], "entries in a group should run newest first")
                last_year[kind] = int(year)
        url = data.get("url", "")
        if url:
            if url.startswith("/"):
                path = url.split("#")[0]
                m = re.match(r"^/notes/([^/]+)/?$", path)
                if m:
                    note = by_slug.get(m.group(1))
                    if note is None:
                        add("E", lines["url"], f"points at a note that does not exist: {path}")
                    elif not note.published and note.slug not in assume_published:
                        add("E", lines["url"], f"points at a note that is not published: {path}")
                    elif not path.endswith("/"):
                        add("W", lines["url"], "note addresses end with a slash")
                elif path not in KNOWN_PAGES and not (root / path.lstrip("/")).is_file():
                    add("E", lines["url"], f"points at a file that does not exist: {path}")
            elif not re.match(r"^https?://\S+$", url):
                add("E", lines["url"], "url must start with https://, http:// or /")
            if url in seen_urls:
                add("E", lines["url"], f"same url as the entry on line {seen_urls[url]}")
            seen_urls.setdefault(url, first)
        title = data.get("title", "")
        if title:
            if title in seen_titles:
                add("E", lines["title"], f"same title as the entry on line {seen_titles[title]}")
            seen_titles.setdefault(title, first)
        for key in ("meta", "summary"):
            if data.get(key) and not data[key].rstrip().endswith((".", "?", "!")):
                add("W", lines[key], f"{key} does not end with a full stop")
    return out


def run(root: Path, today: dt.date, slug: str | None = None,
        overrides: dict | None = None) -> list[Finding]:
    """All static checks. With `slug`, that note is judged as if it were published."""
    notes = load_notes(root, overrides)
    out: list[Finding] = []
    target = find_note(notes, slug) if slug else None
    if slug and target is None:
        return [Finding("E", "_notes", 0, f"no note with slug {slug!r}")]
    for note in notes:
        out.extend(check_note(note, notes, root, today, as_published=note is target))
    out.extend(check_work(root, notes, today,
                          assume_published={target.slug} if target else None))
    return out


# --- The real build -------------------------------------------------------

class _Page(html.parser.HTMLParser):
    def __init__(self):
        super().__init__()
        self.ids: set = set()
        self.links: list = []

    def handle_starttag(self, tag, attrs):
        for key, value in attrs:
            if value is None:
                continue
            if key in ("id", "name"):
                self.ids.add(value)
            elif key in ("href", "src"):
                self.links.append(value)


def find_bundle() -> str | None:
    found = shutil.which("bundle")
    if found:
        return found
    candidate = Path(RUBY_BIN) / "bundle.bat"
    return str(candidate) if candidate.is_file() else None


def check_build(root: Path, expect_slugs: list[str], unpublished: bool = False) -> list[Finding]:
    """Build the site into a temporary folder and inspect what came out."""
    bundle = find_bundle()
    if bundle is None:
        return [Finding("E", "build", 0, "bundle was not found; see Previewing in README.md")]
    env = dict(os.environ)
    env["PATH"] = str(Path(bundle).parent) + os.pathsep + env.get("PATH", "")
    out: list[Finding] = []
    with tempfile.TemporaryDirectory(prefix="site-check-") as tmp:
        dest = Path(tmp) / "site"
        command = [bundle, "exec", "jekyll", "build", "--strict_front_matter",
                   "--destination", str(dest)]
        if unpublished:
            command.append("--unpublished")
        result = subprocess.run(command, cwd=root, env=env, capture_output=True,
                                text=True, encoding="utf-8", errors="replace")
        log = (result.stdout or "") + (result.stderr or "")
        if result.returncode != 0:
            tail = " | ".join(line.strip() for line in log.strip().splitlines()[-4:])
            return [Finding("E", "build", 0, f"jekyll build failed: {tail}")]
        for line in log.splitlines():
            if re.search(r"Liquid (Warning|Exception)|\bError:", line):
                out.append(Finding("E", "build", 0, line.strip()))

        for slug in expect_slugs:
            if not (dest / "notes" / slug / "index.html").is_file():
                out.append(Finding("E", "build", 0, f"no page was built at /notes/{slug}/"))
        for name in LEAKS:
            if (dest / name).exists():
                out.append(Finding("E", "build", 0, f"{name} was copied into the built site; add it to exclude in _config.yml"))
        for leaked in dest.glob("*.bat"):
            out.append(Finding("E", "build", 0, f"{leaked.name} was copied into the built site; add it to exclude in _config.yml"))

        pages = {}
        for path in dest.rglob("*.html"):
            page = _Page()
            page.feed(path.read_text(encoding="utf-8", errors="replace"))
            pages[path] = page
        for path, page in pages.items():
            rel = "/" + path.relative_to(dest).as_posix()
            for link in page.links:
                if link.startswith(("http:", "https:", "mailto:", "//", "data:", "javascript:")):
                    continue
                target, _, fragment = link.partition("#")
                target = target.split("?")[0]
                if target == "":
                    target_file = path
                elif target.startswith("/"):
                    target_file = dest / target.lstrip("/")
                else:
                    target_file = path.parent / target
                if target_file.is_dir():
                    target_file = target_file / "index.html"
                if not target_file.is_file():
                    out.append(Finding("E", "build", 0, f"{rel} links to {link}, which was not built"))
                elif (fragment and fragment != "top"   # browsers scroll to the top for #top
                      and target_file in pages and fragment not in pages[target_file].ids):
                    out.append(Finding("E", "build", 0, f"{rel} links to {link}, but no element has that id"))
    return list(dict.fromkeys(out))


# --- External links -------------------------------------------------------

def external_urls(root: Path, notes: list[Note]) -> list[tuple[str, int, str]]:
    found = []
    for note in notes:
        for url in note.front.data.get("sources", []) or []:
            found.append((note.rel, note.front.lines.get("sources", 0), url))
        for n, line, fenced in note.body_lines():
            if fenced:
                continue
            clean = _strip_code_spans(line)
            for target in MD_LINK_RE.findall(clean) + HREF_RE.findall(clean):
                if target.startswith(("http://", "https://")):
                    found.append((note.rel, n, target))
    return found


def check_external(urls: list[tuple[str, int, str]], timeout: float = 10.0) -> list[Finding]:
    """Ask each address whether it answers. Warnings only: many sites refuse scripts."""
    out = []
    cache: dict = {}
    for rel, line, url in urls:
        if url not in cache:
            cache[url] = _probe(url, timeout)
        if cache[url]:
            out.append(Finding("W", rel, line, f"{url} -> {cache[url]}"))
    return out


def _probe(url: str, timeout: float) -> str:
    headers = {"User-Agent": "Mozilla/5.0 (sharland.github.io link check)"}
    last = "no answer"
    for method in ("HEAD", "GET"):
        try:
            request = urllib.request.Request(url, method=method, headers=headers)
            with urllib.request.urlopen(request, timeout=timeout) as response:
                if response.status < 400:
                    return ""
        except urllib.error.HTTPError as error:
            last = f"HTTP {error.code}"
        except Exception as error:  # DNS, TLS, timeout: all just "did not answer"
            last = type(error).__name__
    return last
