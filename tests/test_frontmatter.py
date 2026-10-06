import pytest

import frontmatter
from conftest import NOTE


def test_parses_scalars_blocks_and_line_numbers():
    front = frontmatter.parse(NOTE)
    assert front.has_front and not front.errors
    assert front.data["title"] == "A good note"
    assert front.data["version"] == "0.1"
    assert "version" in front.quoted and "date" not in front.quoted
    assert front.data["description"] == (
        "One sentence that says what the note is for, wrapped over two lines.")
    assert front.data["published"] == "false"
    assert front.lines["slug"] == 3
    assert front.body_line == 13
    assert front.body.split("\n")[1] == "## First heading"


def test_trailing_comments_are_dropped_but_hashes_in_quotes_kept():
    text = '---\ndate: 2026-10-05     # first published\ntitle: "C# and # signs"\n---\n'
    front = frontmatter.parse(text)
    assert front.data["date"] == "2026-10-05"
    assert front.data["title"] == "C# and # signs"


def test_lists_of_strings():
    text = "---\nsources:\n  - https://a.example/\n  - https://b.example/x\npublished: false\n---\n"
    front = frontmatter.parse(text)
    assert front.data["sources"] == ["https://a.example/", "https://b.example/x"]
    assert front.data["published"] == "false"


def test_escaped_quotes():
    front = frontmatter.parse('---\ntitle: "He said \\"no\\""\n---\n')
    assert front.data["title"] == 'He said "no"'
    assert frontmatter.quote('He said "no"') == '"He said \\"no\\""'


@pytest.mark.parametrize("line", ["tags: [a, b]", "  indented: thing", "not a key line"])
def test_unsupported_yaml_is_an_error_not_a_guess(line):
    front = frontmatter.parse(f"---\n{line}\n---\n")
    assert front.errors


def test_missing_or_unclosed_front_matter():
    assert not frontmatter.parse("just text\n").has_front
    assert frontmatter.parse("---\ntitle: x\n").errors


def test_crlf_parses_the_same():
    assert frontmatter.parse(NOTE.replace("\n", "\r\n")).data == frontmatter.parse(NOTE).data


@pytest.mark.parametrize("newline", ["\n", "\r\n"])
def test_set_field_changes_one_line_only(newline):
    text = NOTE.replace("\n", newline)
    changed = frontmatter.set_field(text, "published", "true")
    before, after = text.split(newline), changed.split(newline)
    assert len(before) == len(after)
    different = [i for i, (a, b) in enumerate(zip(before, after)) if a != b]
    assert different == [10]
    assert after[10] == "published: true"
    assert frontmatter.set_field(changed, "published", "false") == text


def test_set_field_keeps_a_trailing_comment():
    text = "---\ndate: 2026-10-05     # first published\n---\nbody\n"
    assert frontmatter.set_field(text, "date", "2026-11-01") == (
        "---\ndate: 2026-11-01     # first published\n---\nbody\n")


def test_set_field_adds_a_missing_key_and_refuses_blocks():
    text = "---\ntitle: x\ndescription: >-\n  words\n---\nbody\n"
    assert frontmatter.set_field(text, "slug", "x") == (
        "---\ntitle: x\ndescription: >-\n  words\nslug: x\n---\nbody\n")
    with pytest.raises(ValueError):
        frontmatter.set_field(text, "description", "new")
