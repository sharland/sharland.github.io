import json
import shutil

import pytest

import checks
import frontmatter
import sitetool
import workyml
from conftest import NOTE, REPO, WORK, make_note


def run(root, *argv):
    argv = list(argv)
    if "--today" not in argv:
        argv = ["--today", "2026-10-06", *argv]
    return sitetool.main(["--root", str(root), *argv])


def note_text(root, name="2026-10-a-good-note.md"):
    return (root / "_notes" / name).read_text(encoding="utf-8", newline="")


# --- new ---

def test_new_writes_a_draft_that_passes_check(root, capsys):
    assert run(root, "new", "--title", "Café rules: a second look!", "--json",
               "--source", "https://example.org/a", "--source", "https://example.org/b") == 0
    result = json.loads(capsys.readouterr().out)
    assert result == {"path": "_notes/2026-10-cafe-rules-a-second-look.md",
                      "slug": "cafe-rules-a-second-look",
                      "url": "https://sharland.github.io/notes/cafe-rules-a-second-look/"}
    front = frontmatter.parse(note_text(root, "2026-10-cafe-rules-a-second-look.md"))
    assert front.data["title"] == "Café rules: a second look!"
    assert front.data["published"] == "false"
    assert front.data["version"] == "0.1" and "version" in front.quoted
    assert front.data["sources"] == ["https://example.org/a", "https://example.org/b"]
    assert run(root, "check") == 0


def test_new_leaves_prompts_not_prose(root):
    run(root, "new", "--title", "Plain")
    front = frontmatter.parse(note_text(root, "2026-10-plain.md"))
    assert front.data["description"].startswith("[Brian:")
    body = [line for line in front.body.split("\n") if line.strip()]
    assert all("[Brian:" in line for line in body)
    assert run(root, "check", "plain") == 1


def test_new_refuses_an_existing_slug_and_bad_input(root, capsys):
    make_note(root)
    assert run(root, "new", "--title", "A good note") == 1
    assert run(root, "new", "--title", "X", "--slug", "Not A Slug") == 2
    assert run(root, "new", "--title", "10 things") == 2
    assert run(root, "new", "--title", "Y", "--source", "C:\\mail.eml") == 2
    assert sorted(p.name for p in (root / "_notes").iterdir()) == ["2026-10-a-good-note.md"]


def test_new_uses_the_repos_line_endings(root):
    (root / "_config.yml").write_text('url: "https://sharland.github.io"\r\n', newline="")
    run(root, "new", "--title", "Endings")
    text = note_text(root, "2026-10-endings.md")
    assert "\r\n" in text and "\n" not in text.replace("\r\n", "")


# --- work add ---

def test_work_add_inserts_and_reports(root):
    assert run(root, "work", "add", "--title", "newer-tool", "--kind", "tool",
               "--url", "https://example.org/t", "--summary", "A thing.") == 0
    blocks = workyml.parse((root / "_data" / "work.yml").read_text(encoding="utf-8")).blocks
    assert [b.data["title"] for b in blocks] == ["newer-tool", "next-task", "cairoX"]
    assert blocks[0].data["year"] == "2026"


def test_work_add_changes_nothing_when_the_entry_is_wrong(root):
    assert run(root, "work", "add", "--title", "x", "--kind", "gadget",
               "--url", "https://example.org/", "--summary", "A thing.") == 2
    assert run(root, "work", "add", "--title", "A map", "--kind", "mapping",
               "--url", "/notes/missing/", "--summary", "A thing.") == 1
    assert run(root, "work", "add", "--title", "next-task", "--kind", "tool",
               "--url", "https://example.org/t", "--summary", "A thing.") == 1
    assert (root / "_data" / "work.yml").read_text(encoding="utf-8", newline="") == WORK


def test_work_add_may_point_at_a_note_about_to_be_published(root):
    make_note(root)
    args = ["work", "add", "--title", "A map", "--kind", "mapping",
            "--url", "/notes/a-good-note/", "--summary", "A thing."]
    assert run(root, *args) == 1
    assert run(root, *args, "--assume-published", "a-good-note") == 0


# --- publish ---

def test_publish_sets_the_fields_and_nothing_else(root):
    make_note(root)
    assert run(root, "publish", "a-good-note", "--no-build") == 0
    before, after = NOTE.split("\n"), note_text(root).split("\n")
    changed = {a for a, b in zip(after, before) if a != b}
    assert changed == {"date: 2026-10-06", "updated: 2026-10-06", "published: true"}
    assert run(root, "check") == 0


def test_publish_options(root):
    make_note(root)
    assert run(root, "publish", "a-good-note", "--no-build", "--keep-date",
               "--version", "1.0", "--status", "reviewed") == 0
    data = frontmatter.parse(note_text(root)).data
    assert (data["date"], data["updated"]) == ("2026-10-01", "2026-10-06")
    assert (data["version"], data["status"]) == ("1.0", "reviewed")


def test_republishing_keeps_the_first_date(root):
    make_note(root, published="true")
    assert run(root, "publish", "a-good-note", "--no-build") == 0
    data = frontmatter.parse(note_text(root)).data
    assert (data["date"], data["updated"]) == ("2026-10-01", "2026-10-06")


def test_publish_refuses_a_note_with_markers_and_leaves_it_alone(root, capsys):
    text = NOTE + "\nA claim (verify).\n"
    make_note(root, text=text)
    assert run(root, "publish", "a-good-note", "--no-build") == 1
    assert note_text(root) == text
    assert "Nothing was changed" in capsys.readouterr().out
    assert run(root, "publish", "nope", "--no-build") == 1


def test_publish_puts_the_note_back_when_the_build_fails(root, monkeypatch):
    make_note(root)
    monkeypatch.setattr(checks, "check_build",
                        lambda *a, **k: [checks.Finding("E", "build", 0, "boom")])
    assert run(root, "publish", "a-good-note") == 1
    assert note_text(root) == NOTE


# --- handover ---

def test_handover_is_the_authors_words_and_the_link(root, capsys):
    make_note(root, published="true")
    assert run(root, "handover", "a-good-note", "--no-clip") == 0
    assert capsys.readouterr().out.strip() == (
        "A good note\n\n"
        "One sentence that says what the note is for, wrapped over two lines.\n\n"
        "https://sharland.github.io/notes/a-good-note/")
    assert run(root, "handover", "a-good-note", "--json") == 0
    info = json.loads(capsys.readouterr().out)
    assert info["url"].endswith("/notes/a-good-note/") and info["published"] is True


def test_handover_warns_about_a_draft(root, capsys):
    make_note(root)
    assert run(root, "handover", "a-good-note", "--no-clip") == 0
    assert "not published" in capsys.readouterr().err


# --- check, and the real thing ---

def test_check_exit_status_and_no_command(root, capsys):
    make_note(root)
    assert run(root, "check") == 0
    make_note(root, slug="wrong")
    assert run(root, "check") == 1
    assert run(root) == 2


def test_slugify():
    assert sitetool.slugify("ISO/IEC 42001, the NIST AI RMF & the EU AI Act") == \
        "iso-iec-42001-the-nist-ai-rmf-the-eu-ai-act"


def test_the_real_repo_has_no_errors_as_it_stands(today):
    found = [f for f in checks.run(REPO, today) if f.severity == "E"]
    assert found == [], "\n".join(str(f) for f in found)


@pytest.mark.slow
def test_real_build_is_clean_and_leaks_no_tooling(today):
    if checks.find_bundle() is None:
        pytest.skip("bundle is not installed")
    notes = checks.load_notes(REPO)
    found = checks.check_build(REPO, [n.slug for n in notes if n.slug], unpublished=True)
    assert found == [], "\n".join(str(f) for f in found)


# --- save ---

def test_save_creates_then_overwrites_a_draft(root, capsys):
    body = root / "body.md"
    body.write_text("## Heading\n\nText.\n", encoding="utf-8")
    assert run(root, "save", "--slug", "my-view", "--title", "My view", "--description", "One line.",
               "--body-file", str(body), "--source", "https://example.org/a", "--json") == 0
    out = json.loads(capsys.readouterr().out)
    assert out == {"path": "_notes/2026-10-my-view.md", "slug": "my-view",
                   "url": "https://sharland.github.io/notes/my-view/", "created": True}
    text = note_text(root, "2026-10-my-view.md")
    front = frontmatter.parse(text)
    assert front.data["published"] == "false" and front.data["status"] == "final"
    assert front.data["version"] == "1.0" and front.data["sources"] == ["https://example.org/a"]
    assert front.body.strip() == "## Heading\n\nText."
    assert run(root, "check") == 0
    capsys.readouterr()  # discard the check report so the next --json read is clean

    body.write_text("## Changed\n", encoding="utf-8")
    assert run(root, "--today", "2026-11-01", "save", "--slug", "my-view", "--title", "My view 2",
               "--description", "Two.", "--body-file", str(body), "--json") == 0
    out = json.loads(capsys.readouterr().out)
    assert out["created"] is False and out["path"] == "_notes/2026-10-my-view.md"
    front = frontmatter.parse(note_text(root, "2026-10-my-view.md"))
    assert front.data["date"] == "2026-10-06" and front.data["updated"] == "2026-11-01"
    assert front.data["title"] == "My view 2" and "Changed" in front.body


def test_save_refuses_a_published_note(root):
    make_note(root, published="true")
    body = root / "body.md"
    body.write_text("## X\n", encoding="utf-8")
    assert run(root, "save", "--slug", "a-good-note", "--title", "T", "--description", "D",
               "--body-file", str(body)) == 1
    assert note_text(root) == NOTE.replace("published: false", "published: true")


def test_save_rejects_bad_input(root):
    body = root / "body.md"
    body.write_text("x", encoding="utf-8")
    assert run(root, "save", "--slug", "Bad Slug", "--title", "T", "--description", "D", "--body-file", str(body)) == 2
    assert run(root, "save", "--slug", "ok", "--title", "T", "--description", "", "--body-file", str(body)) == 2
    assert run(root, "save", "--slug", "ok", "--title", "T", "--description", "D", "--body-file", str(root / "none.md")) == 2
