import json

import pytest

from conftest import EXAMPLES, EXAMPLES_DIR
from mcstas_ess_instr_citool.cli import main


@pytest.mark.parametrize("example", EXAMPLES)
def test_list(example, capsys):
    main([str(EXAMPLES_DIR / example)])
    out = capsys.readouterr().out
    assert f"Instrument project: {example}" in out
    assert "MAIN" in out


def test_json(capsys):
    main(["-a", "json", str(EXAMPLES_DIR / "ExPyGenerated")])
    info = json.loads(capsys.readouterr().out)
    assert info["project_name"] == "ExPyGenerated"
    assert list(info["setups"]) == ["MAIN", "SomeMode"]


def test_pprint(capsys):
    main(["-a", "pprint", str(EXAMPLES_DIR / "ExInstrBasic")])
    assert "'project_name': 'ExInstrBasic'" in capsys.readouterr().out


def test_check(capsys):
    main(["-a", "check", str(EXAMPLES_DIR / "ExInstrIncludes")])
    assert capsys.readouterr().out == "File and directory structure OK\n"


def test_check_fails(copy_example):
    d = copy_example("ExInstrBasic")
    (d / "instr" / "junk.txt").touch()
    with pytest.raises(ValueError, match="Unexpected file 'junk.txt'"):
        main(["-a", "check", str(d)])


def test_bad_action(capsys):
    with pytest.raises(SystemExit):
        main(["-a", "nosuchaction", str(EXAMPLES_DIR / "ExInstrBasic")])


def test_outdir_must_be_empty(tmp_path, capsys):
    (tmp_path / "somefile").touch()
    with pytest.raises(SystemExit):
        main(["-a", "generate", "-o", str(tmp_path),
              str(EXAMPLES_DIR / "ExInstrBasic")])
    assert "is not empty" in capsys.readouterr().err


@pytest.mark.parametrize("example", ["ExInstrBasic", "ExInstrIncludes",
                                     "ExInstrLocalFiles"])
def test_generate_instr(example, tmp_path):
    outdir = tmp_path / "out"
    main(["-a", "generate", "-o", str(outdir), str(EXAMPLES_DIR / example)])
    srcdir = EXAMPLES_DIR / example / "instr"
    expected = sorted(
        p.relative_to(srcdir).as_posix() for p in srcdir.rglob("*") if p.is_file())
    for mode in (outdir / "instr").iterdir():
        files = sorted(p.relative_to(mode).as_posix()
                       for p in mode.rglob("*") if p.is_file())
        # Every mode gets its own .instr file plus all extra files:
        main_or_mode = [f for f in files if "/" not in f]
        assert len(main_or_mode) == 1
        assert [f for f in files if "/" in f] == [
            f for f in expected if "/" in f]
        assert (mode / main_or_mode[0]).read_text() == (
            srcdir / main_or_mode[0]).read_text()


def test_check_results():
    from mcstas_ess_instr_citool.runtest import check_results
    ok = {"compiled": True, "didrun": True, "testval": 1.5e11}
    check_results({"A": ok, "B_2": ok, "_meta": {"ncount": "1e6"}})
    for bad, msg in [
        ({"compiled": False, "didrun": None, "testval": None}, "did not compile"),
        ({"compiled": True, "didrun": False, "testval": None}, "did not run"),
        ({"compiled": True, "didrun": True, "testval": -1}, "no test value"),
        ({"compiled": True, "didrun": True, "testval": None}, "no test value"),
    ]:
        with pytest.raises(RuntimeError, match=f"B: {msg}"):
            check_results({"A": ok, "B": bad, "_meta": {}})
    with pytest.raises(RuntimeError, match="no tests found"):
        check_results({"_meta": {}})


@pytest.mark.parametrize("value", ["0", "-1", "abc", "1.5"])
def test_mpi_invalid(value, capsys):
    with pytest.raises(SystemExit):
        main(["-a", "runci", "--mpi", value, str(EXAMPLES_DIR / "ExInstrBasic")])
    assert "must be a positive integer" in capsys.readouterr().err


def test_mpi_only_for_runci(capsys):
    with pytest.raises(SystemExit):
        main(["-a", "generate", "--mpi", "2",
              str(EXAMPLES_DIR / "ExInstrBasic")])
    assert "--mpi can only be used with action runci" in capsys.readouterr().err


def test_mctest_args():
    from mcstas_ess_instr_citool.runtest import mctest_args
    from mcstas_ess_instr_citool.util import get_nprocs
    base = ["--local", "INSTR", "--testdir", "TESTS"]
    assert mctest_args("INSTR", "TESTS") == ["--strict", "--noplots"] + base
    assert mctest_args("INSTR", "TESTS", 3) == [
        "--strict", "--noplots", "--mpi", "3"] + base
    assert mctest_args("INSTR", "TESTS", "auto") == [
        "--strict", "--noplots", "--mpi", str(get_nprocs())] + base
