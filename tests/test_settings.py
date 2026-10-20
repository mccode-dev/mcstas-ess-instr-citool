import pytest

from mcstas_ess_instr_citool.settings import parse_settings


@pytest.mark.parametrize("text,ncount", [
    ("", None),
    ("# only a comment\n", None),
    ("ncount = 1e4\n", 10000),
    ("ncount = 2000\n", 2000),
    ("ncount = 1\n", 1),
])
def test_ncount(text, ncount):
    assert parse_settings(text) == {"ncount": ncount}


@pytest.mark.parametrize("text,match", [
    ("ncount = 0\n", r"ncount must be a whole number of at least 1, not 0"),
    ("ncount = -1e4\n", r"not -10000.0"),
    ("ncount = 10.5\n", r"not 10.5"),
    ("ncount = '1e4'\n", r"not '1e4'"),
    ("ncount = true\n", r"not True"),
    ("ncount = inf\n", r"not inf"),
    ("ncont = 1e4\n", r"unknown setting 'ncont' \(the only setting is 'ncount'\)"),
    ("ncount = \n", r"not valid TOML"),
])
def test_bad(text, match):
    with pytest.raises(ValueError, match=match):
        parse_settings(text)


def test_error_mentions_file_and_doc():
    with pytest.raises(ValueError) as e:
        parse_settings("ncount = 0\n", filename="/some/dir/citool.toml")
    assert str(e.value).startswith("/some/dir/citool.toml: ")
    assert "layout.html#the-citooltoml-file" in str(e.value)
