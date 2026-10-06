import datetime as dt
import shutil
import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO / "tools"))

TODAY = dt.date(2026, 10, 6)

KINDS = """\
# Work groups.
- id: mapping
  label: Framework mappings
- id: template
  label: Templates and tooling
- id: analysis
  label: Analyses
- id: tool
  label: Tools
  mono: true
"""

WORK = """\
# One entry per published piece of work.
#   title    what the link says

- title: next-task
  kind: tool
  year: 2026
  url: https://github.com/sharland/next-task
  meta: Python, 2026.
  summary: >-
    A local task tracker built around a dependency graph, with
    atomic writes and tests.

- title: cairoX
  kind: tool
  year: 2025
  url: https://github.com/sharland/cairoX
  summary: >-
    A small helper library for pycairo.
"""

NOTE = """\
---
title: "A good note"
slug: a-good-note
date: 2026-10-01
updated: 2026-10-02
status: working draft
version: "0.1"
description: >-
  One sentence that says what the note is for,
  wrapped over two lines.
published: false
---

## First heading

Some text with a [link](https://example.org/) in it.

### A sub-heading

More text.
"""


def make_note(root: Path, name: str = "2026-10-a-good-note.md", text: str = NOTE,
              **replace) -> Path:
    """Write a note. Keyword arguments replace whole front matter lines, or remove them with None."""
    for key, value in replace.items():
        lines = []
        for line in text.split("\n"):
            if line.startswith(f"{key}:"):
                if value is not None:
                    lines.append(f"{key}: {value}")
            else:
                lines.append(line)
        text = "\n".join(lines)
    path = root / "_notes" / name
    path.write_text(text, encoding="utf-8", newline="")
    return path


@pytest.fixture
def root(tmp_path: Path) -> Path:
    (tmp_path / "_notes").mkdir()
    (tmp_path / "_data").mkdir()
    (tmp_path / "assets" / "img").mkdir(parents=True)
    (tmp_path / "assets" / "img" / "og.jpg").write_bytes(b"x")
    (tmp_path / "_data" / "kinds.yml").write_text(KINDS, encoding="utf-8", newline="")
    (tmp_path / "_data" / "work.yml").write_text(WORK, encoding="utf-8", newline="")
    (tmp_path / "_config.yml").write_text('url: "https://sharland.github.io"\n',
                                          encoding="utf-8", newline="")
    return tmp_path


@pytest.fixture
def today() -> dt.date:
    return TODAY


def messages(findings, severity=None):
    return [f.message for f in findings if severity is None or f.severity == severity]
