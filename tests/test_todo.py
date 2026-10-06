import pytest

from mcstas_ess_instr_citool.todo import parse_todo

TYPICAL = """\
TODO items for the EXAMPLE model
================================

Some introduction, which may span
several lines.

* First item, which
  continues here.

  - with a list
  - inside it

* Second item.
* Third item, without a blank line before it.
"""


def test_typical():
    items = parse_todo(TYPICAL)
    assert items == [
        "First item, which continues here. - with a list - inside it",
        "Second item.",
        "Third item, without a blank line before it.",
    ]


@pytest.mark.parametrize("text", ["", "\n\n", "Title\n=====\n\nNothing yet.\n"])
def test_no_items(text):
    assert parse_todo(text) == []


@pytest.mark.parametrize("text,match", [
    ("* One\nNot indented\n", r"line 2: unexpected line after the first item"),
    ("* One\n\nSection title\n=====\n", r"line 3: unexpected line"),
    ("* One\n- Two\n", r"line 2: unexpected line"),
    ("* One\n\tindented with a tab\n", r"line 2: indent with spaces"),
    ("* \n", r"line 1: empty item"),
])
def test_bad(text, match):
    with pytest.raises(ValueError, match=match):
        parse_todo(text, filename="TODO")


def test_error_mentions_file_and_doc():
    with pytest.raises(ValueError) as e:
        parse_todo("* One\nOops\n", filename="/some/project/TODO")
    assert str(e.value).startswith("/some/project/TODO, line 2:")
    assert "layout.html#the-todo-file" in str(e.value)
