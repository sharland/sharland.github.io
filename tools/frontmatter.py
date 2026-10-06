"""Read and edit the front matter at the top of a note.

A deliberately small subset of YAML, so that nothing here can disagree with
what Jekyll reads without saying so:

    key: plain value            # trailing comment
    key: "quoted value"
    key: >-                     folded block, indented lines follow
    key:                        list, '  - item' lines follow

Anything else is reported as an error rather than guessed at. Edits change
one line and leave every other byte, including line endings, alone.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field

KEY_RE = re.compile(r"^([A-Za-z_][\w-]*):(.*)$")
ITEM_RE = re.compile(r"^\s+-\s+(.*)$")
BLOCK_INDICATORS = {">", ">-", "|", "|-"}


@dataclass
class Front:
    has_front: bool = False
    data: dict = field(default_factory=dict)      # key -> str or list[str]
    lines: dict = field(default_factory=dict)     # key -> 1-based line number
    quoted: set = field(default_factory=set)      # keys whose scalar was quoted
    errors: list = field(default_factory=list)    # (line number, message)
    body: str = ""
    body_line: int = 1                            # line number of the body's first line


def detect_newline(text: str) -> str:
    return "\r\n" if "\r\n" in text else "\n"


def split_comment(rest: str) -> tuple[str, str]:
    """Split 'value   # comment' into ('value', '   # comment'), respecting quotes."""
    stripped = rest.lstrip()
    lead = len(rest) - len(stripped)
    if stripped[:1] in ('"', "'"):
        quote = stripped[0]
        i = 1
        while i < len(stripped):
            ch = stripped[i]
            if quote == '"' and ch == "\\":
                i += 2
                continue
            if ch == quote:
                if quote == "'" and stripped[i + 1:i + 2] == "'":
                    i += 2
                    continue
                end = lead + i + 1
                return rest[:end], rest[end:]
            i += 1
        return rest, ""
    m = re.search(r"\s+#", rest)
    if m:
        return rest[:m.start()], rest[m.start():]
    return rest.rstrip(), rest[len(rest.rstrip()):]


def scalar(rest: str) -> tuple[str, bool, str | None]:
    """Return (value, was_quoted, error) for the text after 'key:'."""
    value, comment = split_comment(rest)
    value = value.strip()
    if comment.strip() and not comment.strip().startswith("#"):
        return value, False, "unexpected text after a quoted value"
    if value[:1] == '"':
        if len(value) < 2 or not value.endswith('"'):
            return value, True, "unterminated double-quoted value"
        return value[1:-1].replace('\\"', '"').replace("\\\\", "\\"), True, None
    if value[:1] == "'":
        if len(value) < 2 or not value.endswith("'"):
            return value, True, "unterminated single-quoted value"
        return value[1:-1].replace("''", "'"), True, None
    if value[:1] in ("[", "{", "&", "*", "!", "%", "@", "`"):
        return value, False, f"unsupported YAML value starting with {value[:1]!r}"
    return value, False, None


def parse(text: str) -> Front:
    front = Front()
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        front.body = text
        return front
    close = None
    for i in range(1, len(lines)):
        if lines[i].strip() == "---":
            close = i
            break
    if close is None:
        front.errors.append((1, "front matter is not closed with a line of ---"))
        front.body = ""
        return front
    front.has_front = True
    front.body_line = close + 2
    front.body = "\n".join(lines[close + 1:])

    i = 1
    while i < close:
        line = lines[i]
        number = i + 1
        if not line.strip() or line.lstrip().startswith("#"):
            i += 1
            continue
        m = KEY_RE.match(line)
        if not m:
            front.errors.append((number, f"unsupported front matter line: {line.strip()!r}"))
            i += 1
            continue
        key, rest = m.group(1), m.group(2)
        if key in front.data:
            front.errors.append((number, f"duplicate key {key!r}"))
        front.lines[key] = number
        bare = split_comment(rest)[0].strip()
        if bare in BLOCK_INDICATORS:
            block = []
            i += 1
            while i < close and (not lines[i].strip() or lines[i][:1] in (" ", "\t")):
                block.append(lines[i].strip())
                i += 1
            while block and not block[-1]:
                block.pop()
            if bare.startswith(">"):
                paragraphs, current = [], []
                for part in block:
                    if part:
                        current.append(part)
                    elif current:
                        paragraphs.append(" ".join(current))
                        current = []
                if current:
                    paragraphs.append(" ".join(current))
                front.data[key] = "\n".join(paragraphs)
            else:
                front.data[key] = "\n".join(block)
            continue
        if bare == "":
            items = []
            i += 1
            while i < close and (ITEM_RE.match(lines[i]) or not lines[i].strip()):
                item = ITEM_RE.match(lines[i])
                if item:
                    value, _, error = scalar(item.group(1))
                    if error:
                        front.errors.append((i + 1, error))
                    items.append(value)
                i += 1
            front.data[key] = items if items else ""
            continue
        value, was_quoted, error = scalar(rest)
        if error:
            front.errors.append((number, error))
        if was_quoted:
            front.quoted.add(key)
        front.data[key] = value
        i += 1
    return front


def set_field(text: str, key: str, value: str) -> str:
    """Set a one-line scalar. `value` is written as given, so quote it if needed.

    Only the one line changes. A missing key is added as the last line of the
    front matter. A key holding a block or a list is refused.
    """
    newline = detect_newline(text)
    lines = text.splitlines(keepends=True)
    if not lines or lines[0].strip() != "---":
        raise ValueError("no front matter")
    close = next((i for i in range(1, len(lines)) if lines[i].strip() == "---"), None)
    if close is None:
        raise ValueError("front matter is not closed")
    for i in range(1, close):
        m = KEY_RE.match(lines[i].rstrip("\r\n"))
        if not m or m.group(1) != key:
            continue
        rest = m.group(2)
        current, comment = split_comment(rest)
        if current.strip() in BLOCK_INDICATORS or current.strip() == "":
            raise ValueError(f"{key!r} is a block or list; edit it by hand")
        ending = lines[i][len(lines[i].rstrip("\r\n")):]
        lines[i] = f"{key}: {value}{comment}{ending}"
        return "".join(lines)
    lines.insert(close, f"{key}: {value}{newline}")
    return "".join(lines)


def quote(value: str) -> str:
    """A double-quoted YAML scalar."""
    return '"' + value.replace("\\", "\\\\").replace('"', '\\"') + '"'
