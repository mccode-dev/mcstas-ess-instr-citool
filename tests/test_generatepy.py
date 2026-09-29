import shutil

import pytest

from mcstas_ess_instr_citool.analyse import analyse_dir
from mcstas_ess_instr_citool.cli import main
from mcstas_ess_instr_citool.generatepy import (generatepy,
                                                postprocess_pygen_output)
from conftest import EXAMPLES_DIR

needs_mcstas = pytest.mark.skipif(
    not all(shutil.which(c) for c in ["mcstas", "mcrun", "mctest",
                                      "mcstas-pygen"]),
    reason="McStas not available",
)

# Output from mcstas-pygen (McStas 3.8.8), heavily shortened:
FAKE_PYGEN_OUTPUT = """\
#!/usr/bin/env python3
# Automatically generated file.
# Format:    Python script code
# McStas <http://www.mcstas.org>
# Instrument: X_main.instr (Foo)
# Date:       Mon Sep 28 21:48:50 2026
# File:       /tmp/tmpabc/X_main.py

import mcstasscript as ms
import argparse

# Python McStas instrument description
def make(input_path=None):
    instr = ms.McStas_instr("Foo_generated", author = "McCode Py-Generator", origin = "ESS DMSC", input_path=input_path)
    # MCSTAS system dir is "/home/someone/mcstas/resources/"
    sector = instr.add_parameter('string', 'sector', value='"S"', comment='Parameter type (string) added by McCode py-generator')
    Lambda = instr.add_parameter('double', 'lambda', value=1.0, comment='Parameter type (double) added by McCode py-generator')
    n = instr.add_parameter('int', 'n', value=1, comment='Parameter type (int) added by McCode py-generator')
    # Instruct McStasscript not to 'check everythng'
    instr.settings(checks=False)
    return instr


# end of generated Python code /tmp/tmpabc/X_main.py
"""

INSTR_HEADER = """\
/* %I
* %Example: sector=N lambda=2.5 n=3 Detector: mon_I=1.5e+11
* %Example: Detector: mon_I=12
* %Example: sector="W" Detector: mon_I=1
*/
"""

EXPECTED_TESTS = """\
    # Tests corresponding to the %Example lines of the instrument. The
    # parameter values are restored afterwards, since add_test uses the
    # current parameter values:
    _parameter_values = {p: instr.parameters[p].value for p in instr.get_parameter_names()}
    instr.set_parameters({'sector': 'N', 'lambda': 2.5, 'n': 3})
    instr.add_test('mon', intensity=1.5e+11, included_pars=['sector', 'lambda', 'n'])
    instr.add_test('mon', intensity=12, included_pars=[])
    instr.set_parameters({'sector': 'W'})
    instr.add_test('mon', intensity=1, included_pars=['sector'])
    instr.set_parameters(_parameter_values)

    # Instruct McStasscript not to 'check everythng'
"""


def assert_same_dirs(a, b):
    files_a = sorted(p.relative_to(a) for p in a.rglob("*") if p.is_file())
    files_b = sorted(p.relative_to(b) for p in b.rglob("*") if p.is_file())
    assert files_a == files_b
    for f in files_a:
        assert (a / f).read_bytes() == (b / f).read_bytes(), f


def test_postprocess():
    code = postprocess_pygen_output(FAKE_PYGEN_OUTPUT, "X_main",
                                    INSTR_HEADER)
    assert 'ms.McStas_instr("X_main", author' in code
    assert EXPECTED_TESTS in code
    # Reproducible output:
    assert "# Date:" not in code
    assert "system dir" not in code
    assert "/tmp/tmpabc" not in code
    assert "# File:       X_main.py\n" in code
    assert code.endswith("# end of generated Python code X_main.py\n")
    # Idempotent:
    assert postprocess_pygen_output(code, "X_main", INSTR_HEADER) == code


def test_postprocess_no_examples():
    code = postprocess_pygen_output(FAKE_PYGEN_OUTPUT, "X_main", "/* */")
    assert "add_test" not in code


def test_postprocess_tests_added_by_pygen():
    # Newer mcstas-pygen adds the tests itself:
    fake = FAKE_PYGEN_OUTPUT.replace(
        "    # Instruct McStasscript",
        "    instr.add_test('mon', intensity=12, included_pars=[])\n"
        "    # Instruct McStasscript")
    header = "%Example: Detector: mon_I=12\n"
    code = postprocess_pygen_output(fake, "X_main", header)
    assert code.count("add_test") == 1
    with pytest.raises(RuntimeError, match=r"2 lines, but 1 tests"):
        postprocess_pygen_output(fake, "X_main", header + header)


@pytest.mark.parametrize("example,match", [
    ("nosuchpar=1 Detector: mon_I=1", "Unknown instrument parameter"),
    ("n=abc Detector: mon_I=1", "Non-numeric value"),
    ("n Detector: mon_I=1", "Invalid parameter setting"),
    ("sector=a'b Detector: mon_I=1", "Unsupported string value"),
    ("Detector: 1mon_I=1", "Invalid monitor name or value"),
])
def test_postprocess_bad_examples(example, match):
    with pytest.raises(RuntimeError, match=match):
        postprocess_pygen_output(FAKE_PYGEN_OUTPUT, "X_main",
                                 f"%Example: {example}\n")


def test_postprocess_bad_pygen_output():
    with pytest.raises(RuntimeError, match="Could not find instrument"):
        postprocess_pygen_output("def make():\n    pass\n", "X_main", "")


def test_generatepy_requires_outdir(capsys):
    with pytest.raises(SystemExit):
        main(["-a", "generatepy", str(EXAMPLES_DIR / "ESS01")])
    assert "--outdir is required" in capsys.readouterr().err


@pytest.mark.parametrize("example", ["ESS02", "ESS04"])
def test_generatepy_from_instrpy(example, tmp_path):
    outdir = tmp_path / "out"
    main(["-a", "generatepy", "-o", str(outdir),
          str(EXAMPLES_DIR / example)])
    src = tmp_path / "src"
    shutil.copytree(EXAMPLES_DIR / example, src,
                    ignore=shutil.ignore_patterns("__pycache__"))
    assert_same_dirs(src, outdir)


def test_instrpy_with_includes(copy_example):
    d = copy_example("ESS02")
    inc = d / "instrpy" / "ESS02_instr" / "includes"
    inc.mkdir()
    (inc / "foo.h").touch()
    (inc / "foo.c").touch()
    info = analyse_dir(d)
    assert info["extra_files"] == {"includes": ["foo.c", "foo.h"]}
    (inc / "foo.txt").touch()
    with pytest.raises(ValueError, match="File foo.txt not allowed"):
        analyse_dir(d)


def test_instrpy_no_snippets(copy_example):
    d = copy_example("ESS02")
    (d / "instrpy" / "ESS02_instr" / "snippets").mkdir()
    with pytest.raises(ValueError, match="Directory snippets not allowed"):
        analyse_dir(d)


@needs_mcstas
@pytest.mark.parametrize("example", ["ESS01", "ESS03"])
def test_generatepy_from_instr(example, tmp_path):
    outdir = tmp_path / "out"
    main(["-a", "generatepy", "-o", str(outdir), str(EXAMPLES_DIR / example)])
    info = analyse_dir(outdir)
    orig_info = analyse_dir(EXAMPLES_DIR / example)
    assert info["layout"] == "instrpy"
    assert info["project_name"] == example
    assert list(info["setups"]) == list(orig_info["setups"])
    assert (outdir / "conda.yml").read_text() == (
        EXAMPLES_DIR / example / "conda.yml").read_text()
    if example == "ESS03":
        assert info["extra_files"] == {
            "includes": orig_info["extra_files"]["includes"]}
    for mode, path in info["setups"].items():
        code = open(path).read()
        name = f"{example}_{'main' if mode == 'MAIN' else 'mode' + mode}"
        assert f'ms.McStas_instr("{name}",' in code
        orig = open(orig_info["setups"][mode]).read()
        assert code.count("instr.add_test(") == orig.count("%Example:")
    # Output is reproducible:
    outdir2 = tmp_path / "out2"
    main(["-a", "generatepy", "-o", str(outdir2), str(EXAMPLES_DIR / example)])
    assert_same_dirs(outdir, outdir2)

@needs_mcstas
def test_generatepy_roundtrip_runci(tmp_path):
    # ESS03 is the most complicated example (includes/ and snippets/):
    pydir = tmp_path / "py"
    main(["-a", "generatepy", "-o", str(pydir), str(EXAMPLES_DIR / "ESS03")])
    main(["-a", "runci", "-o", str(tmp_path / "ci"), str(pydir)])
