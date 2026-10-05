"""Construction of the ExPyHelpers instrument, shared by all modes."""

import mcstasscript as ms

from . import geometry
from .monitors import add_monitor_set


def build(name, guide_length, input_path=None):
    """Build the ExPyHelpers instrument: a simple source, a straight guide of the
    given length, and monitors at the guide entrance and at the sample
    position."""
    instr = ms.McStas_instr(name, author="ESS DMSC", origin="ESS DMSC",
                            input_path=input_path)

    lambda0 = instr.add_parameter("double", "lambda0", value=4.0,
                                  comment="Mean wavelength [AA]")
    dlambda = instr.add_parameter("double", "dlambda", value=2.0,
                                  comment="Wavelength half-width [AA]")

    origin = instr.add_component("origin", "Progress_bar")

    source = instr.add_component("source", "Source_simple",
                                 AT=[0, 0, 0], RELATIVE=origin)
    source.radius = geometry.SOURCE_RADIUS
    source.dist = geometry.SOURCE_TO_GUIDE
    source.focus_xw = geometry.GUIDE_WIDTH
    source.focus_yh = geometry.GUIDE_HEIGHT
    source.lambda0 = lambda0
    source.dlambda = dlambda
    source.flux = 1e12

    guide_start = instr.add_component("guide_start", "Arm",
                                      AT=[0, 0, geometry.SOURCE_TO_GUIDE],
                                      RELATIVE=source)
    add_monitor_set(instr, "entrance", 0, guide_start, lmin=0.5, lmax=8.0)

    guide = instr.add_component("guide", "Guide",
                                AT=[0, 0, 1e-3], RELATIVE=guide_start)
    guide.w1 = geometry.GUIDE_WIDTH
    guide.h1 = geometry.GUIDE_HEIGHT
    guide.l = guide_length
    guide.m = 2

    add_monitor_set(instr, "sample", geometry.sample_distance(guide_length),
                    guide_start, lmin=0.5, lmax=8.0)
    return instr


def add_example(instr, monitor, intensity, **parameters):
    """Add a McStas %Example test for the given monitor and parameter values,
    without changing the parameter defaults of the instrument (add_test uses
    the current parameter values, so they are set and restored here).

    If no parameter values are given, the %Example line has no parameters,
    i.e. the test uses the default values."""
    saved = {p: instr.parameters[p].value for p in instr.get_parameter_names()}
    instr.set_parameters(parameters)
    instr.add_test(monitor, intensity=intensity,
                   included_pars=list(parameters))
    instr.set_parameters(saved)
