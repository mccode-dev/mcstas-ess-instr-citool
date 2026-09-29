"""Tests which need McStas (and McStasScript) to be installed."""
import json
import shutil

import pytest

from mcstas_ess_instr_citool.cli import main
from mcstas_ess_instr_citool.generate import generate
from mcstas_ess_instr_citool.analyse import analyse_dir
from conftest import EXAMPLES, EXAMPLES_DIR

needs_mcstas = pytest.mark.skipif(
    not all(shutil.which(c) for c in ["mcstas", "mcrun", "mctest"]),
    reason="McStas not available",
)


@needs_mcstas
def test_mcstas_version():
    from mcstas_ess_instr_citool.util import (mcstas_info,
                                              minimum_mcstas_version)
    assert mcstas_info()["version"] >= minimum_mcstas_version


def test_generate_instrpy(tmp_path, monkeypatch):
    pytest.importorskip("mcstasscript")
    monkeypatch.chdir(tmp_path)  # generate() changes the working directory
    info = analyse_dir(EXAMPLES_DIR / "ExPyGenerated")
    instrdir = generate(info, tmp_path)
    files = sorted(p.relative_to(instrdir).as_posix()
                   for p in instrdir.rglob("*") if p.is_file())
    assert files == ["MAIN/ExPyGenerated_main.instr",
                     "SomeMode/ExPyGenerated_modeSomeMode.instr"]
    assert "%Example:" in (instrdir / files[0]).read_text()


def test_generate_instrpy_timeout(tmp_path, copy_example, monkeypatch):
    pytest.importorskip("mcstasscript")
    monkeypatch.chdir(tmp_path)
    d = copy_example("ExPyGenerated")
    f = d / "instrpy" / "ExPyGenerated_instr" / "ExPyGenerated_main.py"
    f.write_text(f.read_text().replace(
        "def make(input_path=None):\n",
        "def make(input_path=None):\n    import time; time.sleep(60)\n"))
    info = analyse_dir(d)
    outdir = tmp_path / "out"
    outdir.mkdir()
    with pytest.raises(TimeoutError, match="timed out after 2 seconds"):
        generate(info, outdir, pygen_timeout=2)


@needs_mcstas
@pytest.mark.parametrize("example", EXAMPLES)
def test_runci(example, tmp_path):
    outdir = tmp_path / "out"
    main(["-a", "runci", "-o", str(outdir), str(EXAMPLES_DIR / example)])
    (jsonfile,) = (outdir / "tests").glob("*/testresults_*.json")
    assert json.loads(jsonfile.read_text())


needs_mpi = pytest.mark.skipif(
    not (shutil.which("mpirun") or shutil.which("mpiexec")),
    reason="MPI not available",
)


@needs_mcstas
@needs_mpi
def test_runci_mpi(tmp_path):
    outdir = tmp_path / "out"
    main(["-a", "runci", "--mpi", "2", "-o", str(outdir),
          str(EXAMPLES_DIR / "ExPyHelpers")])
    (jsonfile,) = (outdir / "tests").glob("*/testresults_*.json")
    assert json.loads(jsonfile.read_text())
    # The simulations really ran with MPI:
    run_outputs = list((outdir / "tests").rglob("run_stdout_*.txt"))
    assert run_outputs
    for f in run_outputs:
        assert "running on 2 nodes" in f.read_text(errors="replace")


@needs_mcstas
def test_runci_rejects_shadowing_component(copy_example, tmp_path):
    d = copy_example("ExInstrLocalFiles")
    comps = d / "instr" / "localcomps"
    (comps / "ExCountMonitor.comp").rename(comps / "Arm.comp")
    with pytest.raises(RuntimeError, match="must not have the same names.*Arm"):
        main(["-a", "runci", "-o", str(tmp_path / "out"), str(d)])
