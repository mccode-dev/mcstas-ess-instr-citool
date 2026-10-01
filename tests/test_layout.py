import shutil
import sys

import pytest

from conftest import EXAMPLES, EXAMPLES_DIR
from mcstas_ess_instr_citool.analyse import analyse_dir


def fails(project_dir, match):
    with pytest.raises(ValueError, match=match):
        analyse_dir(project_dir)


@pytest.mark.parametrize("example", EXAMPLES)
def test_examples_valid(example):
    info = analyse_dir(EXAMPLES_DIR / example)
    assert info["project_name"] == example
    assert list(info["setups"])[0] == "MAIN"


def test_example_details():
    info = analyse_dir(EXAMPLES_DIR / "ExInstrBasic")
    assert info["layout"] == "instr"
    assert info["mode_names"] == ["BAR", "FOO"]
    assert info["pypkgname"] is None
    info = analyse_dir(EXAMPLES_DIR / "ExPyGenerated")
    assert info["layout"] == "instrpy"
    assert info["mode_names"] == ["SomeMode"]
    assert info["pypkgname"] == "ExPyGenerated_instr"
    info = analyse_dir(EXAMPLES_DIR / "ExInstrIncludes")
    assert info["extra_files"] == {
        "includes": ["foobar.c", "foobar.h", "instr_declare.h",
                     "instr_initialize.h"],
        "snippets": ["ExInstrIncludes.instr"],
    }
    assert info["helper_modules"] == []
    info = analyse_dir(EXAMPLES_DIR / "ExPyHelpers")
    assert info["layout"] == "instrpy"
    assert info["mode_names"] == ["Long"]
    assert info["helper_modules"] == ["common", "geometry", "monitors"]
    for example in ["ExInstrLocalFiles", "ExPyLocalFiles"]:
        info = analyse_dir(EXAMPLES_DIR / example)
        assert info["extra_files"] == {
            "localcomps": ["ExCountMonitor.comp", "ex-count-lib.c",
                           "ex-count-lib.h"],
            "localdata": ["ExAlLike.ncmat"],
        }


def test_missing_condayml(copy_example):
    d = copy_example("ExInstrBasic")
    (d / "conda.yml").unlink()
    fails(d, "Missing conda requirements file")


def test_both_or_neither_layout(copy_example):
    d = copy_example("ExInstrBasic")
    (d / "instrpy").mkdir()
    fails(d, "Must have exactly one of directories")
    (d / "instrpy").rmdir()
    shutil.rmtree(d / "instr")
    fails(d, "Must have exactly one of directories")


def test_empty_allowed_subdirs(copy_example):
    d = copy_example("ExInstrIncludes")
    for f in (d / "instr" / "includes").iterdir():
        f.unlink()
    info = analyse_dir(d)
    assert list(info["extra_files"]) == ["snippets"]


def test_ignored_files(copy_example):
    d = copy_example("ExInstrIncludes")
    for f in [".DS_Store", ".#ExInstrIncludes_main.instr", "ExInstrIncludes_main.instr~"]:
        (d / "instr" / f).touch()
        (d / "instr" / "includes" / f).touch()
    (d / "instr" / ".hiddendir").mkdir()
    info = analyse_dir(d)
    assert info["mode_names"] == ["BAR"]
    assert ".DS_Store" not in info["extra_files"]["includes"]


def test_stray_file(copy_example):
    d = copy_example("ExInstrIncludes")
    (d / "instr" / "README.md").touch()
    fails(d, r"Unexpected file 'README.md'.*in addition to subdirs: "
             r"includes snippets localcomps localdata\.$")


def test_root_allowed_entries(copy_example):
    d = copy_example("ExInstrBasic")
    for f in ["README.md", "README", "TODO", "LICENSE", "CHANGELOG.md",
              ".gitignore", ".gitlab-ci.yml", "backup~"]:
        (d / f).touch()
    for sub in ["extra", "extra_pytests", ".github", "__pycache__"]:
        (d / sub).mkdir()
    (d / "extra" / "anything.ipynb").touch()
    (d / "extra" / "somedir").mkdir()
    with open(d / "conda.yml", "a") as f:
        f.write("  - pytest\n")
    info = analyse_dir(d)
    assert info["extra_dir"] == str(d / "extra")
    assert info["extra_pytests_dir"] == str(d / "extra_pytests")


def test_root_no_extras(copy_example):
    info = analyse_dir(copy_example("ExPyHelpers"))
    assert info["extra_dir"] is None
    assert info["extra_pytests_dir"] is None


@pytest.mark.parametrize("entry,is_dir", [
    ("notebook.ipynb", False), ("tests", True), ("pyproject.toml", False),
    ("readme.md", False), ("docs", True)])
def test_root_unexpected_entries(copy_example, entry, is_dir):
    d = copy_example("ExInstrBasic")
    if is_dir:
        (d / entry).mkdir()
    else:
        (d / entry).touch()
    fails(d, rf"Unexpected file or directory '{entry}'.*extra/")


@pytest.mark.parametrize("entry", ["extra", "extra_pytests"])
def test_root_extras_must_be_dirs(copy_example, entry):
    d = copy_example("ExInstrBasic")
    (d / entry).touch()
    fails(d, f"'{entry}' .* must be a directory")


def test_root_extra_pytests_needs_pytest(copy_example):
    d = copy_example("ExInstrBasic")
    (d / "extra_pytests").mkdir()
    fails(d, "pytest must be listed in conda.yml")


def test_stray_file_instrpy_msg(copy_example):
    d = copy_example("ExPyGenerated")
    (d / "instrpy" / "ExPyGenerated_instr" / "README.md").touch()
    with pytest.raises(ValueError) as e:
        analyse_dir(d)
    assert "Unexpected file 'README.md'" in str(e.value)
    assert str(e.value).endswith(
        "in addition to subdirs: includes localcomps localdata.")


def test_file_named_like_subdir(copy_example):
    d = copy_example("ExInstrBasic")
    (d / "instr" / "includes").touch()
    fails(d, "Unexpected file 'includes'")


def test_bad_subdir(copy_example):
    d = copy_example("ExInstrBasic")
    (d / "instr" / "data").mkdir()
    fails(d, "Directory data not allowed")


def test_bad_file_in_subdir(copy_example):
    d = copy_example("ExInstrIncludes")
    (d / "instr" / "includes" / "foo.py").touch()
    fails(d, "File foo.py not allowed")


def test_nested_subdir(copy_example):
    d = copy_example("ExInstrIncludes")
    (d / "instr" / "includes" / "sub").mkdir()
    fails(d, "Forbidden subdir")


def test_dash_in_project_name(copy_example):
    d = copy_example("ExInstrBasic", "ESS-01")
    instr = d / "instr"
    for f in instr.glob("ExInstrBasic_*.instr"):
        f.rename(instr / f.name.replace("ExInstrBasic", "ESS-01"))
    fails(d, "Unexpected file 'ESS-01_")


def test_dash_in_py_project_name(copy_example):
    d = copy_example("ExPyGenerated")
    pkg = d / "instrpy" / "ExPyGenerated_instr"
    for f in pkg.glob("ExPyGenerated_*.py"):
        f.rename(pkg / f.name.replace("ExPyGenerated", "ESS-02"))
    pkg.rename(d / "instrpy" / "ESS-02_instr")
    fails(d, "exactly one subdirectory named 'PROJECTNAME_instr'")


def test_inconsistent_project_names(copy_example):
    d = copy_example("ExInstrBasic")
    (d / "instr" / "ExInstrBasic_modeFOO.instr").rename(
        d / "instr" / "OTHER_modeFOO.instr")
    fails(d, "All main/mode files must share PROJECTNAME")


def test_no_main(copy_example):
    d = copy_example("ExInstrBasic")
    (d / "instr" / "ExInstrBasic_main.instr").unlink()
    fails(d, "Must have exactly one file named 'ExInstrBasic_main.instr'")


@pytest.mark.parametrize("mode", ["main", "Test"])
def test_reserved_mode_names(copy_example, mode):
    d = copy_example("ExInstrBasic")
    (d / "instr" / f"ExInstrBasic_mode{mode}.instr").touch()
    fails(d, "is not allowed as a mode name")


def test_clashing_mode_names(copy_example):
    d = copy_example("ExInstrBasic")
    if (d / "instr" / "ExInstrBasic_modefoo.instr").exists():
        pytest.skip("case-insensitive file system")
    (d / "instr" / "ExInstrBasic_modeFoo.instr").touch()
    fails(d, "Clashing mode names")


def test_instrpy_nonempty_init(copy_example):
    d = copy_example("ExPyGenerated")
    (d / "instrpy" / "ExPyGenerated_instr" / "__init__.py").write_text("x = 1\n")
    fails(d, "must be empty")


def test_instrpy_pyproject_name_mismatch(copy_example):
    d = copy_example("ExPyGenerated")
    pp = d / "instrpy" / "pyproject.toml"
    pp.write_text(pp.read_text().replace('name = "ExPyGenerated"', 'name = "ESS99"'))
    fails(d, r"pyproject.toml \[project\].name must match PROJECTNAME")


def test_instrpy_missing_pyproject(copy_example):
    d = copy_example("ExPyGenerated")
    (d / "instrpy" / "pyproject.toml").unlink()
    fails(d, "pyproject.toml must exist")


def test_helper_modules(copy_example):
    d = copy_example("ExPyGenerated")
    pkg = d / "instrpy" / "ExPyGenerated_instr"
    (pkg / "utils.py").touch()
    (pkg / "_private.py").touch()
    assert analyse_dir(d)["helper_modules"] == ["_private", "utils"]


@pytest.mark.parametrize("fname,match", [
    ("ExPyGenerated_utils.py", "Files named ExPyGenerated_\\* must be either"),
    ("ExPyGenerated_mode_foo.py", "Files named ExPyGenerated_\\* must be either"),
    ("my-utils.py", "Invalid helper module name 'my-utils.py'"),
    ("import.py", "Invalid helper module name 'import.py'"),
    ("utils.txt", r"Unexpected file 'utils.txt'.*helper modules named"),
])
def test_bad_helper_modules(copy_example, fname, match):
    d = copy_example("ExPyGenerated")
    (d / "instrpy" / "ExPyGenerated_instr" / fname).touch()
    fails(d, match)


def test_no_helper_modules_in_instr_layout(copy_example):
    d = copy_example("ExInstrBasic")
    (d / "instr" / "utils.instr").touch()
    fails(d, "Unexpected file 'utils.instr'")


def test_instrument_name_must_match_file(copy_example):
    d = copy_example("ExInstrBasic")
    f = d / "instr" / "ExInstrBasic_modeFOO.instr"
    f.write_text(f.read_text().replace("DEFINE INSTRUMENT ExInstrBasic_modeFOO",
                                       "DEFINE INSTRUMENT SomethingElse"))
    fails(d, r"must be named after the file, i.e. 'DEFINE INSTRUMENT "
             r"ExInstrBasic_modeFOO\(...\)' \(found 'SomethingElse'\)")
    f.write_text("/* no instrument here */\n")
    fails(d, "no DEFINE INSTRUMENT found")


def test_instrument_name_ignores_comments(copy_example):
    d = copy_example("ExInstrBasic")
    f = d / "instr" / "ExInstrBasic_main.instr"
    f.write_text("/* DEFINE INSTRUMENT Wrong1 */\n// DEFINE INSTRUMENT Wrong2\n"
                 + f.read_text())
    analyse_dir(d)


def test_instrument_name_snippets_not_checked():
    # The snippet in ExInstrIncludes defines instrument "ExInstrIncludes", which is fine:
    info = analyse_dir(EXAMPLES_DIR / "ExInstrIncludes")
    assert info["extra_files"]["snippets"] == ["ExInstrIncludes.instr"]


@pytest.mark.parametrize("entry,is_dir", [
    ("README.md", False),
    ("tests", True),
    ("setup.py", False),
])
def test_instrpy_dir_strict(copy_example, entry, is_dir):
    d = copy_example("ExPyHelpers")
    p = d / "instrpy" / entry
    p.mkdir() if is_dir else p.touch()
    fails(d, f"Unexpected file or directory '{entry}'.*Only pyproject.toml"
             " and ExPyHelpers_instr/ are allowed")


def test_instrpy_dir_ignored_entries(copy_example):
    d = copy_example("ExPyHelpers")
    for name in ["__pycache__", "ExPyHelpers.egg-info", ".hidden"]:
        (d / "instrpy" / name).mkdir()
    (d / "instrpy" / "pyproject.toml~").touch()
    analyse_dir(d)


LOCALDIRS = [("ExInstrLocalFiles", ("instr",)),
             ("ExPyLocalFiles", ("instrpy", "ExPyLocalFiles_instr"))]


@pytest.mark.parametrize("example,basedir", LOCALDIRS)
@pytest.mark.parametrize("fname", [
    "Si.lau", "C60.hkl", "table.dat", "refl.ref", "source.mcpl.gz",
    "geometry.off", "struct.cif",
])
def test_localdata_allowed(copy_example, example, basedir, fname):
    d = copy_example(example)
    (d.joinpath(*basedir) / "localdata" / fname).touch()
    assert fname in analyse_dir(d)["extra_files"]["localdata"]


@pytest.mark.parametrize("example,basedir", LOCALDIRS)
@pytest.mark.parametrize("subdir,fname", [
    ("localdata", "notes.md"),
    ("localdata", "script.py"),
    ("localdata", "other.instr"),
    ("localdata", "Comp.comp"),
    ("localcomps", "other.instr"),
    ("localcomps", "helper.py"),
    ("localcomps", "data.ncmat"),
])
def test_localfiles_not_allowed(copy_example, example, basedir, subdir, fname):
    d = copy_example(example)
    (d.joinpath(*basedir) / subdir / fname).touch()
    fails(d, f"File {fname} not allowed")


@pytest.mark.parametrize("example,basedir", LOCALDIRS)
@pytest.mark.parametrize("subdir", ["localcomps", "localdata"])
def test_localfiles_no_subdirs(copy_example, example, basedir, subdir):
    d = copy_example(example)
    (d.joinpath(*basedir) / subdir / "sub").mkdir()
    fails(d, "Forbidden subdir")


def test_local_component_shadowing(tmp_path):
    from mcstas_ess_instr_citool.localfiles import check_local_components
    resdir = tmp_path / "resources"
    (resdir / "optics").mkdir(parents=True)
    (resdir / "optics" / "Arm.comp").touch()
    (resdir / "examples" / "Some").mkdir(parents=True)
    (resdir / "examples" / "Some" / "ExampleOnly.comp").touch()
    (resdir / "share").mkdir()
    (resdir / "share" / "union-lib.c").touch()
    (resdir / "share" / "read_table-lib.h").touch()
    info = {"extra_files": {"localcomps": ["Arm.comp", "Mine.comp", "lib.c"]}}
    with pytest.raises(RuntimeError,
                       match="must not have the same names.*: Arm.comp\\."):
        check_local_components(info, resdir)
    info = {"extra_files": {"localcomps": ["union-lib.c", "read_table-lib.h",
                                           "union-lib.comp"]}}
    with pytest.raises(RuntimeError,
                       match=": read_table-lib.h, union-lib.c\\."):
        check_local_components(info, resdir)
    for comps in (["Mine.comp", "ExampleOnly.comp", "lib.c", "Arm.c"], []):
        check_local_components({"extra_files": {"localcomps": comps}}, resdir)
    check_local_components({"extra_files": {}}, resdir)


def test_local_data_shadowing(tmp_path):
    from mcstas_ess_instr_citool.localfiles import check_local_data
    resdir = tmp_path / "resources"
    (resdir / "data" / "Gas_tables").mkdir(parents=True)
    (resdir / "data" / "Al.laz").touch()
    (resdir / "data" / "Gas_tables" / "He3inAr.table").touch()
    (resdir / "examples" / "Some").mkdir(parents=True)
    (resdir / "examples" / "Some" / "example_only.txt").touch()
    ncnames = ["Al_sg225.ncmat", "Cu_sg225.ncmat"]

    def check(files):
        check_local_data({"extra_files": {"localdata": files}}, resdir, ncnames)

    with pytest.raises(RuntimeError, match="must not have the same names.*:"
                       " Al.laz \\(McStas data file\\)\\."):
        check(["Al.laz", "mine.laz"])
    with pytest.raises(RuntimeError, match=": Al_sg225.ncmat \\(NCrystal"
                       " standard library material\\), he3inar.table \\(McStas"
                       " data file\\)\\."):
        check(["Al_sg225.ncmat", "he3inar.table", "mine.ncmat"])
    # Case-insensitive:
    with pytest.raises(RuntimeError, match=": cu_SG225.NCMAT"):
        check(["cu_SG225.NCMAT"])
    for files in (["mine.laz", "example_only.txt", "Al.lau", "Al.ncmat"], []):
        check(files)
    check_local_data({"extra_files": {}}, resdir, ncnames)


@pytest.mark.xfail(sys.platform == "win32", reason="NCrystal 4.4.6 fails to"
                   " list the standard library on Windows (globbing error 267)")
def test_ncrystal_stdlib_file_names():
    pytest.importorskip("NCrystal")
    from mcstas_ess_instr_citool.localfiles import ncrystal_stdlib_file_names
    names = ncrystal_stdlib_file_names()
    assert "Al_sg225.ncmat" in names
    assert all(n.endswith(".ncmat") for n in names)
