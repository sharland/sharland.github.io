"""Read _data/work.yml and _data/kinds.yml, and add an entry to work.yml.

Both files are a list of small maps. They are handled as text, block by
block, so the comments and layout a person wrote survive an edit untouched.
No YAML library is involved.
"""

from __future__ import annotations

import re
import textwrap
from dataclasses import dataclass, field

from frontmatter import BLOCK_INDICATORS, detect_newline, quote, scalar, split_comment

START_RE = re.compile(r"^- ([A-Za-z_][\w-]*):(.*)$")
FIELD_RE = re.compile(r"^  ([A-Za-z_][\w-]*):(.*)$")
WORK_FIELDS = ["title", "kind", "year", "url", "meta", "summary"]
WORK_REQUIRED = ["title", "kind", "year", "url", "summary"]


@dataclass
class Block:
    start: int                 # index of the '- key:' line
    end: int                   # index after the block's last non-blank line
    data: dict = field(default_factory=dict)
    lines: dict = field(default_factory=dict)   # key -> 1-based line number


@dataclass
class Listing:
    blocks: list
    errors: list               # (line number, message)


def parse(text: str) -> Listing:
    lines = text.splitlines()
    blocks: list[Block] = []
    errors: list[tuple[int, str]] = []
    current: Block | None = None
    i = 0
    while i < len(lines):
        line = lines[i]
        number = i + 1
        if not line.strip() or line.lstrip().startswith("#"):
            i += 1
            continue
        start = START_RE.match(line)
        fld = FIELD_RE.match(line)
        if start:
            current = Block(start=i, end=i + 1)
            blocks.append(current)
            key, rest = start.group(1), start.group(2)
        elif fld and current is not None:
            key, rest = fld.group(1), fld.group(2)
        else:
            errors.append((number, f"unsupported line: {line.strip()!r}"))
            i += 1
            continue
        if key in current.data:
            errors.append((number, f"duplicate key {key!r} in one entry"))
        current.lines[key] = number
        bare = split_comment(rest)[0].strip()
        if bare in BLOCK_INDICATORS:
            parts = []
            i += 1
            while i < len(lines) and (not lines[i].strip() or lines[i].startswith("    ")):
                if lines[i].strip():
                    parts.append(lines[i].strip())
                    current.end = i + 1
                elif parts and i + 1 < len(lines) and lines[i + 1].startswith("    "):
                    parts.append("")
                else:
                    break
                i += 1
            joiner = " " if bare.startswith(">") else "\n"
            current.data[key] = joiner.join(p for p in parts if p)
            continue
        value, _, error = scalar(rest)
        if error:
            errors.append((number, error))
        current.data[key] = value
        current.end = i + 1
        i += 1
    return Listing(blocks, errors)


def kind_ids(kinds_text: str) -> list[str]:
    return [b.data["id"] for b in parse(kinds_text).blocks if b.data.get("id")]


def _plain_or_quoted(value: str) -> str:
    risky = (
        value == ""
        or value != value.strip()
        or ": " in value
        or " #" in value
        or value.endswith(":")
        or value[0] in "!&*-?|>'\"%@`#[]{},"
        or value.lower() in {"true", "false", "yes", "no", "null", "on", "off", "~"}
        or re.fullmatch(r"[-+]?[\d.]+", value) is not None
    )
    return quote(value) if risky else value


def render(entry: dict, newline: str = "\n") -> str:
    """One entry as text, ending with a newline, in the file's house style."""
    out = [f"- title: {_plain_or_quoted(str(entry['title']))}"]
    out.append(f"  kind: {entry['kind']}")
    out.append(f"  year: {entry['year']}")
    out.append(f"  url: {_plain_or_quoted(str(entry['url']))}")
    if entry.get("meta"):
        out.append(f"  meta: {_plain_or_quoted(str(entry['meta']))}")
    out.append("  summary: >-")
    summary = " ".join(str(entry["summary"]).split())
    out.extend("    " + part for part in textwrap.wrap(summary, width=80,
                                                       break_long_words=False,
                                                       break_on_hyphens=False))
    return newline.join(out) + newline


def insert(text: str, entry: dict, kinds: list[str]) -> str:
    """Return work.yml with `entry` placed first in its group.

    With no entry of that kind yet, it goes before the first entry whose kind
    comes later in kinds.yml, or at the end.
    """
    newline = detect_newline(text)
    listing = parse(text)
    if listing.errors:
        raise ValueError("work.yml has problems; run check first")
    lines = text.splitlines(keepends=True)
    if lines and not lines[-1].endswith(("\n", "\r")):
        lines[-1] += newline
    block_text = render(entry, newline)

    order = {k: n for n, k in enumerate(kinds)}
    rank = order.get(entry["kind"], len(order))
    target = next((b for b in listing.blocks if b.data.get("kind") == entry["kind"]), None)
    if target is None:
        target = next((b for b in listing.blocks
                       if order.get(b.data.get("kind"), len(order)) > rank), None)
    if target is not None:
        return "".join(lines[:target.start]) + block_text + newline + "".join(lines[target.start:])
    body = "".join(lines)
    if listing.blocks:
        body = body.rstrip("\r\n") + newline + newline
    elif body and not body.endswith(newline * 2):
        body = body.rstrip("\r\n") + newline + newline
    return body + block_text
