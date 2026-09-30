"""Tests of the ExPyExtra instrument, using the analysis code in extra/.

Run by mcstas-ess-instr-citool (action runci) from within this directory,
with instrpy/ and extra/ in PYTHONPATH.
"""

import mcstasscript as ms
import pytest

from ExPyExtra_instr.ExPyExtra_main import make
from expyextra_analysis.spectrum import mean_wavelength


def test_components():
    instr = make()
    names = [c.name for c in instr.component_list]
    assert names == ["origin", "source", "lambda_monitor"]


def test_parameters():
    assert make().get_parameter_names() == ["lambda0", "dlambda"]


def test_mean_wavelength(tmp_path):
    instr = make(input_path=str(tmp_path))
    instr.set_parameters(lambda0=3.0)
    instr.settings(ncount=1e5, output_path=str(tmp_path / "data"),
                   suppress_output=True)
    data = instr.backengine()
    monitor = ms.name_search("lambda_monitor", data)
    assert mean_wavelength(monitor) == pytest.approx(3.0, abs=0.05)
