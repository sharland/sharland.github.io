import difflib

import pytest

import workyml
from conftest import KINDS, REPO, WORK

KIND_IDS = ["mapping", "template", "analysis", "tool"]
ENTRY = {"title": "A mapping", "kind": "mapping", "year": "2026",
         "url": "/notes/a-good-note/", "meta": "Working draft, 2026.",
         "summary": "One plain sentence. And a second one that is long enough to need "
                    "wrapping onto another line of the file."}


def added_lines(before: str, after: str) -> list[str]:
    diff = difflib.ndiff(before.splitlines(), after.splitlines())
    changed = [d for d in diff if d[:1] in "+-"]
    assert all(d.startswith("+") for d in changed), "an existing line was changed or removed"
    return [d[2:] for d in changed]


def test_parse_reads_entries_and_folded_summaries():
    listing = workyml.parse(WORK)
    assert not listing.errors
    assert [b.data["title"] for b in listing.blocks] == ["next-task", "cairoX"]
    assert listing.blocks[0].data["summary"] == (
        "A local task tracker built around a dependency graph, with atomic writes and tests.")
    assert listing.blocks[0].lines["kind"] == 5
    assert "meta" not in listing.blocks[1].data


def test_kind_ids_in_file_order():
    assert workyml.kind_ids(KINDS) == KIND_IDS


def test_the_real_files_parse_cleanly():
    listing = workyml.parse((REPO / "_data" / "work.yml").read_text(encoding="utf-8"))
    assert not listing.errors and listing.blocks
    assert workyml.kind_ids((REPO / "_data" / "kinds.yml").read_text(encoding="utf-8"))


def test_new_kind_goes_before_groups_that_come_later():
    after = workyml.insert(WORK, ENTRY, KIND_IDS)
    added = added_lines(WORK, after)
    assert "- title: A mapping" in added
    assert added.count("") == 1
    assert len(added) == len(workyml.render(ENTRY).splitlines()) + 1
    titles = [b.data["title"] for b in workyml.parse(after).blocks]
    assert titles == ["A mapping", "next-task", "cairoX"]
    assert after.startswith("# One entry per published piece of work.")


def test_same_kind_goes_first_in_its_group():
    entry = dict(ENTRY, title="newer-tool", kind="tool", url="https://example.org/t")
    with_mapping = workyml.insert(WORK, ENTRY, KIND_IDS)
    after = workyml.insert(with_mapping, entry, KIND_IDS)
    added_lines(with_mapping, after)
    titles = [b.data["title"] for b in workyml.parse(after).blocks]
    assert titles == ["A mapping", "newer-tool", "next-task", "cairoX"]


def test_last_kind_goes_at_the_end():
    only_mapping = workyml.insert("# header\n", ENTRY, KIND_IDS)
    entry = dict(ENTRY, title="a-tool", kind="tool", url="https://example.org/t")
    after = workyml.insert(only_mapping, entry, KIND_IDS)
    titles = [b.data["title"] for b in workyml.parse(after).blocks]
    assert titles == ["A mapping", "a-tool"]
    assert after.endswith("\n") and not after.endswith("\n\n")
    assert "\n\n\n" not in after


def test_round_trip_and_wrapping():
    after = workyml.insert(WORK, ENTRY, KIND_IDS)
    block = workyml.parse(after).blocks[0]
    assert block.data == ENTRY
    assert all(len(line) <= 84 for line in workyml.render(ENTRY).splitlines())


def test_crlf_is_preserved():
    after = workyml.insert(WORK.replace("\n", "\r\n"), ENTRY, KIND_IDS)
    assert "\r\n" in after and "\n" not in after.replace("\r\n", "")


@pytest.mark.parametrize("title", ["ISO 42001: a map", "true", "2026", "#hash", "- dash"])
def test_awkward_titles_are_quoted_and_survive(title):
    after = workyml.insert(WORK, dict(ENTRY, title=title), KIND_IDS)
    listing = workyml.parse(after)
    assert not listing.errors
    assert listing.blocks[0].data["title"] == title


def test_refuses_to_edit_a_file_it_cannot_read():
    with pytest.raises(ValueError):
        workyml.insert(WORK + "stray line\n", ENTRY, KIND_IDS)
