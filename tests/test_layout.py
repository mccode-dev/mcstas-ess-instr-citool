import shutil

import pytest

from mcstas_ess_instr_citool.analyse import analyse_dir
from conftest import EXAMPLES, EXAMPLES_DIR


def fails(project_dir, match):
    with pytest.raises(ValueError, match=match):
        analyse_dir(project_dir)


@pytest.mark.parametrize("example", EXAMPLES)
def test_examples_valid(example):
    info = analyse_dir(EXAMPLES_DIR / example)
    assert info["project_name"] == example
    assert list(info["setups"])[0] == "MAIN"


def test_example_details():
    info = analyse_dir(EXAMPLES_DIR / "ESS01")
    assert info["layout"] == "instr"
    assert info["mode_names"] == ["BAR", "FOO"]
    assert info["pypkgname"] is None
    info = analyse_dir(EXAMPLES_DIR / "ESS02")
    assert info["layout"] == "instrpy"
    assert info["mode_names"] == ["SomeMode"]
    assert info["pypkgname"] == "ESS02_instr"
    info = analyse_dir(EXAMPLES_DIR / "ESS03")
    assert info["extra_files"] == {
        "includes": ["foobar.c", "foobar.h", "instr_declare.h",
                     "instr_initialize.h"],
        "snippets": ["ESS03.instr"],
    }
    assert info["helper_modules"] == []
    info = analyse_dir(EXAMPLES_DIR / "ESS04")
    assert info["layout"] == "instrpy"
    assert info["mode_names"] == ["Long"]
    assert info["helper_modules"] == ["common", "geometry", "monitors"]


def test_missing_condayml(copy_example):
    d = copy_example("ESS01")
    (d / "conda.yml").unlink()
    fails(d, "Missing conda requirements file")


def test_both_or_neither_layout(copy_example):
    d = copy_example("ESS01")
    (d / "instrpy").mkdir()
    fails(d, "Must have exactly one of directories")
    (d / "instrpy").rmdir()
    shutil.rmtree(d / "instr")
    fails(d, "Must have exactly one of directories")


def test_empty_allowed_subdirs(copy_example):
    d = copy_example("ESS03")
    for f in (d / "instr" / "includes").iterdir():
        f.unlink()
    info = analyse_dir(d)
    assert list(info["extra_files"]) == ["snippets"]


def test_ignored_files(copy_example):
    d = copy_example("ESS03")
    for f in [".DS_Store", ".#ESS03_main.instr", "ESS03_main.instr~"]:
        (d / "instr" / f).touch()
        (d / "instr" / "includes" / f).touch()
    (d / "instr" / ".hiddendir").mkdir()
    info = analyse_dir(d)
    assert info["mode_names"] == ["BAR"]
    assert ".DS_Store" not in info["extra_files"]["includes"]


def test_stray_file(copy_example):
    d = copy_example("ESS03")
    (d / "instr" / "README.md").touch()
    fails(d, r"Unexpected file 'README.md'.*in addition to subdirs: "
             r"includes snippets\.$")


def test_stray_file_instrpy_msg(copy_example):
    d = copy_example("ESS02")
    (d / "instrpy" / "ESS02_instr" / "README.md").touch()
    with pytest.raises(ValueError) as e:
        analyse_dir(d)
    assert "Unexpected file 'README.md'" in str(e.value)
    assert str(e.value).endswith("in addition to subdirs: includes.")


def test_file_named_like_subdir(copy_example):
    d = copy_example("ESS01")
    (d / "instr" / "includes").touch()
    fails(d, "Unexpected file 'includes'")


def test_bad_subdir(copy_example):
    d = copy_example("ESS01")
    (d / "instr" / "data").mkdir()
    fails(d, "Directory data not allowed")


def test_bad_file_in_subdir(copy_example):
    d = copy_example("ESS03")
    (d / "instr" / "includes" / "foo.py").touch()
    fails(d, "File foo.py not allowed")


def test_nested_subdir(copy_example):
    d = copy_example("ESS03")
    (d / "instr" / "includes" / "sub").mkdir()
    fails(d, "Forbidden subdir")


def test_dash_in_project_name(copy_example):
    d = copy_example("ESS01", "ESS-01")
    instr = d / "instr"
    for f in instr.glob("ESS01_*.instr"):
        f.rename(instr / f.name.replace("ESS01", "ESS-01"))
    fails(d, "Unexpected file 'ESS-01_")


def test_dash_in_py_project_name(copy_example):
    d = copy_example("ESS02")
    pkg = d / "instrpy" / "ESS02_instr"
    for f in pkg.glob("ESS02_*.py"):
        f.rename(pkg / f.name.replace("ESS02", "ESS-02"))
    pkg.rename(d / "instrpy" / "ESS-02_instr")
    fails(d, "exactly one subdirectory named 'PROJECTNAME_instr'")


def test_inconsistent_project_names(copy_example):
    d = copy_example("ESS01")
    (d / "instr" / "ESS01_modeFOO.instr").rename(
        d / "instr" / "OTHER_modeFOO.instr")
    fails(d, "All main/mode files must share PROJECTNAME")


def test_no_main(copy_example):
    d = copy_example("ESS01")
    (d / "instr" / "ESS01_main.instr").unlink()
    fails(d, "Must have exactly one file named 'ESS01_main.instr'")


@pytest.mark.parametrize("mode", ["main", "Test"])
def test_reserved_mode_names(copy_example, mode):
    d = copy_example("ESS01")
    (d / "instr" / f"ESS01_mode{mode}.instr").touch()
    fails(d, "is not allowed as a mode name")


def test_clashing_mode_names(copy_example):
    d = copy_example("ESS01")
    if (d / "instr" / "ESS01_modefoo.instr").exists():
        pytest.skip("case-insensitive file system")
    (d / "instr" / "ESS01_modeFoo.instr").touch()
    fails(d, "Clashing mode names")


def test_instrpy_nonempty_init(copy_example):
    d = copy_example("ESS02")
    (d / "instrpy" / "ESS02_instr" / "__init__.py").write_text("x = 1\n")
    fails(d, "must be empty")


def test_instrpy_pyproject_name_mismatch(copy_example):
    d = copy_example("ESS02")
    pp = d / "instrpy" / "pyproject.toml"
    pp.write_text(pp.read_text().replace('name = "ESS02"', 'name = "ESS99"'))
    fails(d, r"pyproject.toml \[project\].name must match PROJECTNAME")


def test_instrpy_missing_pyproject(copy_example):
    d = copy_example("ESS02")
    (d / "instrpy" / "pyproject.toml").unlink()
    fails(d, "pyproject.toml must exist")


def test_helper_modules(copy_example):
    d = copy_example("ESS02")
    pkg = d / "instrpy" / "ESS02_instr"
    (pkg / "utils.py").touch()
    (pkg / "_private.py").touch()
    assert analyse_dir(d)["helper_modules"] == ["_private", "utils"]


@pytest.mark.parametrize("fname,match", [
    ("ESS02_utils.py", "Files named ESS02_\\* must be either"),
    ("ESS02_mode_foo.py", "Files named ESS02_\\* must be either"),
    ("my-utils.py", "Invalid helper module name 'my-utils.py'"),
    ("import.py", "Invalid helper module name 'import.py'"),
    ("utils.txt", r"Unexpected file 'utils.txt'.*helper modules named"),
])
def test_bad_helper_modules(copy_example, fname, match):
    d = copy_example("ESS02")
    (d / "instrpy" / "ESS02_instr" / fname).touch()
    fails(d, match)


def test_no_helper_modules_in_instr_layout(copy_example):
    d = copy_example("ESS01")
    (d / "instr" / "utils.instr").touch()
    fails(d, "Unexpected file 'utils.instr'")


def test_instrument_name_must_match_file(copy_example):
    d = copy_example("ESS01")
    f = d / "instr" / "ESS01_modeFOO.instr"
    f.write_text(f.read_text().replace("DEFINE INSTRUMENT ESS01_modeFOO",
                                       "DEFINE INSTRUMENT SomethingElse"))
    fails(d, r"must be named after the file, i.e. 'DEFINE INSTRUMENT "
             r"ESS01_modeFOO\(...\)' \(found 'SomethingElse'\)")
    f.write_text("/* no instrument here */\n")
    fails(d, "no DEFINE INSTRUMENT found")


def test_instrument_name_ignores_comments(copy_example):
    d = copy_example("ESS01")
    f = d / "instr" / "ESS01_main.instr"
    f.write_text("/* DEFINE INSTRUMENT Wrong1 */\n// DEFINE INSTRUMENT Wrong2\n"
                 + f.read_text())
    analyse_dir(d)


def test_instrument_name_snippets_not_checked():
    # The snippet in ESS03 defines instrument "ESS03", which is fine:
    info = analyse_dir(EXAMPLES_DIR / "ESS03")
    assert info["extra_files"]["snippets"] == ["ESS03.instr"]


@pytest.mark.parametrize("entry,is_dir", [
    ("README.md", False),
    ("tests", True),
    ("setup.py", False),
])
def test_instrpy_dir_strict(copy_example, entry, is_dir):
    d = copy_example("ESS04")
    p = d / "instrpy" / entry
    p.mkdir() if is_dir else p.touch()
    fails(d, f"Unexpected file or directory '{entry}'.*Only pyproject.toml"
             " and ESS04_instr/ are allowed")


def test_instrpy_dir_ignored_entries(copy_example):
    d = copy_example("ESS04")
    for name in ["__pycache__", "ESS04.egg-info", ".hidden"]:
        (d / "instrpy" / name).mkdir()
    (d / "instrpy" / "pyproject.toml~").touch()
    analyse_dir(d)
