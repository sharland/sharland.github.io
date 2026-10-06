import pytest

import checks
from conftest import NOTE, WORK, make_note, messages


def run(root, today, slug=None):
    return checks.run(root, today, slug=slug)


def errors(root, today, slug=None):
    return messages(run(root, today, slug), "E")


def warnings(root, today, slug=None):
    return messages(run(root, today, slug), "W")


def has(found, fragment):
    return any(fragment in message for message in found)


def test_a_good_draft_and_good_work_file_are_clean(root, today):
    make_note(root)
    assert run(root, today) == []
    assert run(root, today, slug="a-good-note") == []


def test_unknown_slug(root, today):
    assert has(errors(root, today, slug="nope"), "no note with slug")


# --- filename and slug ---

@pytest.mark.parametrize("name", ["a-good-note.md", "2026-10-06-a-good-note.md",
                                  "2026-10-A-Good-Note.md", "2026-10-a_good_note.md"])
def test_bad_filenames(root, today, name):
    make_note(root, name=name)
    found = errors(root, today)
    assert has(found, "filename is not YYYY-MM-slug.md") or has(found, "does not match the filename") \
        or has(found, "day of the month")


def test_slug_must_match_filename(root, today):
    make_note(root, slug="something-else")
    assert has(errors(root, today), "does not match the filename")


def test_slug_is_required(root, today):
    make_note(root, slug=None)
    assert has(errors(root, today), "missing 'slug'")


def test_duplicate_slug(root, today):
    make_note(root)
    make_note(root, name="2026-09-a-good-note.md")
    assert has(errors(root, today), "used by more than one note")


# --- front matter ---

@pytest.mark.parametrize("key", ["title", "date", "updated", "status", "version", "published"])
def test_required_fields(root, today, key):
    make_note(root, **{key: None})
    assert has(errors(root, today), f"missing {key!r}")


@pytest.mark.parametrize("replace, fragment", [
    ({"published": "yes"}, "published must be true or false"),
    ({"date": "5 October 2026"}, "date is not a real date"),
    ({"date": "2026-02-30"}, "date is not a real date"),
    ({"updated": "2026-09-01"}, "updated is earlier than date"),
    ({"version": "0.1"}, "version must be quoted"),
    ({"version": '"v1"'}, 'version must look like'),
])
def test_front_matter_errors(root, today, replace, fragment):
    make_note(root, **replace)
    assert has(errors(root, today), fragment)


def test_future_date_only_matters_once_published(root, today):
    make_note(root, date="2026-12-01", updated="2026-12-01")
    assert errors(root, today) == []
    assert has(errors(root, today, slug="a-good-note"), "date is in the future")


def test_front_matter_warnings(root, today):
    make_note(root, text=NOTE.replace("published: false", "layout: note\npublished: false"),
              status="nearly done")
    found = warnings(root, today)
    assert has(found, "status 'nearly done'") and has(found, "unknown front matter key 'layout'")


def test_long_description_warns(root, today):
    make_note(root, text=NOTE.replace("One sentence that says", "word " * 70))
    assert has(warnings(root, today), "description is")


def test_sources_must_be_public_urls(root, today):
    make_note(root, text=NOTE.replace("published: false",
                                      "sources:\n  - https://ok.example/\n  - C:\\mail\\tldr.eml\npublished: false"))
    assert has(errors(root, today), "source is not a public URL")


# --- drafting markers ---

MARKED = NOTE + "\nA claim (verify).\n\n[Brian: say why.]\n\n{% comment %}\nEDITOR'S CHECKLIST\n{% endcomment %}\n\nTODO tidy\n"


def test_markers_are_counted_on_a_draft_and_block_a_published_note(root, today):
    make_note(root, text=MARKED)
    draft = run(root, today)
    assert messages(draft, "E") == []
    assert has(messages(draft, "I"), "4 drafting markers")
    assert has(messages(draft, "W"), "TODO or TK")

    found = errors(root, today, slug="a-good-note")
    for fragment in ("marked (verify)", "[Brian: ...] prompt", "editor's checklist", "Liquid comment"):
        assert has(found, fragment)


def test_markers_block_an_already_published_note(root, today):
    make_note(root, text=MARKED, published="true")
    assert has(errors(root, today), "marked (verify)")


# --- headings ---

def test_h1_in_body_is_an_error_but_not_inside_code(root, today):
    make_note(root, text=NOTE + "\n```\n# a comment in code\n```\n")
    assert errors(root, today) == []
    make_note(root, text=NOTE + "\n# Second title\n")
    assert has(errors(root, today), "a # heading in the body")


def test_heading_order_warnings(root, today):
    make_note(root, text=NOTE.replace("## First heading", "### First heading"))
    assert has(warnings(root, today), "first heading is not ##")
    make_note(root, text=NOTE.replace("### A sub-heading", "#### A sub-heading"))
    assert has(warnings(root, today), "jumps from level 2 to level 4")


# --- links ---

@pytest.mark.parametrize("link, severity, fragment", [
    ("[x]()", "E", "empty target"),
    ("[x](/notes/missing/)", "E", "note that does not exist"),
    ("[x](/assets/img/nope.png)", "E", "file that does not exist"),
    ('<a href="/assets/img/nope.png">x</a>', "E", "file that does not exist"),
    ("[x](other.md)", "W", "relative link"),
    ("[x](http://example.org/)", "W", "plain http link"),
])
def test_link_problems(root, today, link, severity, fragment):
    make_note(root, text=NOTE + f"\n{link}\n")
    assert has(messages(run(root, today), severity), fragment)


def test_links_that_are_fine(root, today):
    body = ("\n[a](/assets/img/og.jpg) [b](/notes/) [c](#first-heading) [d](https://x.example/)"
            " [e](mailto:a@b.example) `[f](/assets/nope)`\n")
    make_note(root, text=NOTE + body)
    assert run(root, today) == []


def test_link_to_an_unpublished_note_blocks_only_a_published_one(root, today):
    make_note(root)
    make_note(root, name="2026-10-second.md",
              text=NOTE.replace("a-good-note", "second") + "\n[first](/notes/a-good-note/)\n")
    assert errors(root, today) == []
    assert has(errors(root, today, slug="second"), "note that is not published")


# --- work.yml ---

def write_work(root, text):
    (root / "_data" / "work.yml").write_text(text, encoding="utf-8", newline="")


@pytest.mark.parametrize("old, new, fragment", [
    ("  kind: tool\n  year: 2026", "  kind: gadget\n  year: 2026", "not an id in _data/kinds.yml"),
    ("  year: 2026", "  year: 26", "year must be four digits"),
    ("  year: 2026", "  year: 2031", "year is in the future"),
    ("  year: 2026\n", "", "missing 'year'"),
    ("https://github.com/sharland/next-task", "github.com/sharland/next-task", "url must start with"),
    ("https://github.com/sharland/next-task", "/notes/missing/", "note that does not exist"),
    ("https://github.com/sharland/next-task", "/assets/nope.pdf", "file that does not exist"),
    ("https://github.com/sharland/cairoX", "https://github.com/sharland/next-task", "same url"),
    ("- title: cairoX", "- title: next-task", "same title"),
    ("  kind: tool\n  year: 2026", "kind: tool\n  year: 2026", "unsupported line"),
])
def test_work_errors(root, today, old, new, fragment):
    assert old in WORK
    write_work(root, WORK.replace(old, new, 1))
    assert has(errors(root, today), fragment)


def test_work_warnings(root, today):
    write_work(root, WORK.replace("meta: Python, 2026.", "meta: Python, 2026")
               .replace("year: 2025", "year: 2026").replace("year: 2026", "year: 2024", 1)
               .replace("  kind: tool\n", "  kind: tool\n  colour: red\n", 1))
    found = warnings(root, today)
    assert has(found, "meta does not end with a full stop")
    assert has(found, "newest first")
    assert has(found, "unknown key 'colour'")


def test_work_link_to_a_draft_note_is_an_error_until_it_is_published(root, today):
    make_note(root)
    write_work(root, WORK.replace("https://github.com/sharland/next-task", "/notes/a-good-note/"))
    assert has(errors(root, today), "note that is not published")
    assert errors(root, today, slug="a-good-note") == []
    make_note(root, published="true")
    assert errors(root, today) == []
