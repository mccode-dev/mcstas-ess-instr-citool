"""Tests of the model checks (-a modelcheck)."""
import shutil
from types import SimpleNamespace

import pytest

from conftest import EXAMPLES
from mcstas_ess_instr_citool.cli import main
from mcstas_ess_instr_citool.modelcheck import check_instrument

needs_mcstas = pytest.mark.skipif(
    not all(shutil.which(c) for c in ["mcstas", "mcstas-pygen"]),
    reason="McStas not available",
)


def _instr(params=(), comps=()):
    """A stand-in for a McStasScript instrument object: params are (name,
    value) and comps are (name, AT_reference, ROTATED_reference)."""
    return SimpleNamespace(
        parameters=SimpleNamespace(parameters={
            name: SimpleNamespace(value=value) for name, value in params}),
        component_list=[
            SimpleNamespace(name=name, AT_reference=at,
                            ROTATED_specified=rot is not None,
                            ROTATED_reference=rot)
            for name, at, rot in comps])


def test_check_instrument_ok():
    assert check_instrument(_instr(
        params=[("a", 1.0), ("s", '""')],
        comps=[("Origin", None, None), ("Arm1", "PREVIOUS", "PREVIOUS"),
               ("Arm2", "Origin", "Arm1"), ("Arm3", "PREVIOUS(2)", None)],
    )) == []


def test_check_instrument_parameter_defaults():
    assert check_instrument(_instr(params=[("a", 1.0), ("b", None)])) == [
        ("parameter-defaults",
         "instrument parameter 'b' has no default value")]


def test_check_instrument_relative_references():
    problems = check_instrument(_instr(comps=[
        ("Origin", None, None),
        ("Arm1", "Arm2", None),
        ("Arm2", "Origin", "Arm2"),
    ]))
    assert problems == [
        ("relative-references",
         "component 'Arm1': AT RELATIVE 'Arm2' refers to a component which"
         " is not defined earlier in the instrument"),
        ("relative-references",
         "component 'Arm2': ROTATED RELATIVE 'Arm2' refers to the component"
         " itself"),
    ]


def _modelcheck_error(d, capsys):
    """Run the model checks on project d, which must fail. Returns the error
    message."""
    with pytest.raises(SystemExit) as e:
        main(["-a", "modelcheck", str(d)])
    assert e.value.code == 1
    err = capsys.readouterr().err
    assert err.startswith("ERROR: ")
    assert "Traceback" not in err
    return err


def _edit(path, old, new):
    text = path.read_text()
    assert text.count(old) == 1
    path.write_text(text.replace(old, new))


@needs_mcstas
@pytest.mark.parametrize("example", EXAMPLES)
def test_modelcheck_examples(example, copy_example, capsys):
    pytest.importorskip("mcstasscript")
    main(["-a", "modelcheck", str(copy_example(example))])
    assert "Model checks OK" in capsys.readouterr().out


@needs_mcstas
def test_modelcheck_instr_parameter_default(copy_example, capsys):
    pytest.importorskip("mcstasscript")
    d = copy_example("ExInstrBasic")
    _edit(d / "instr" / "ExInstrBasic_main.instr", "Lmin=0.2,", "Lmin,")
    err = _modelcheck_error(d, capsys)
    assert ("instr/ExInstrBasic_main.instr (mode MAIN): instrument parameter"
            " 'Lmin' has no default value [rule parameter-defaults:") in err
    assert "layout.html#model-checks" in err


@needs_mcstas
def test_modelcheck_instr_string_parameter_default(copy_example, capsys):
    pytest.importorskip("mcstasscript")
    from mcstas_ess_instr_citool.util import mcstas_info
    d = copy_example("ExInstrBasic")
    instr = d / "instr" / "ExInstrBasic_main.instr"
    _edit(instr, 'string sector="S",', "string sector,")
    err = _modelcheck_error(d, capsys)
    msg = "instrument parameter 'sector' has no default value"
    if mcstas_info()["version"] >= (3, 9, 2):
        assert f"{msg} [rule parameter-defaults:" in err
    else:
        assert f'{msg}, or the default value ""' in err

    # The default value "" is fine:
    _edit(instr, "string sector,", 'string sector="",')
    main(["-a", "modelcheck", str(d)])
    assert "Model checks OK" in capsys.readouterr().out


@needs_mcstas
def test_modelcheck_instr_unknown_reference(copy_example, capsys):
    pytest.importorskip("mcstasscript")
    d = copy_example("ExInstrBasic")
    _edit(d / "instr" / "ExInstrBasic_main.instr",
          "AT (0,0,0) RELATIVE BackTrace",
          "AT (0,0,0) RELATIVE NoSuchComponent")
    err = _modelcheck_error(d, capsys)
    assert ("McStas reports errors in instr/ExInstrBasic_main.instr"
            " (mode MAIN)") in err


@needs_mcstas
def test_modelcheck_instrpy_parameter_default(copy_example, capsys):
    pytest.importorskip("mcstasscript")
    d = copy_example("ExPyGenerated")
    _edit(d / "instrpy" / "ExPyGenerated_instr" / "ExPyGenerated_main.py",
          "'Lmin', value=0.2,", "'Lmin',")
    err = _modelcheck_error(d, capsys)
    assert ("instrpy/ExPyGenerated_instr/ExPyGenerated_main.py (mode MAIN):"
            " instrument parameter 'Lmin' has no default value") in err
