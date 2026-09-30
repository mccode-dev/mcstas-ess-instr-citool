"""Construction of the ExPyExtra instrument."""

import mcstasscript as ms


def build(name, input_path=None):
    """Build the ExPyExtra instrument: a simple source and a wavelength
    monitor 10 m downstream."""
    instr = ms.McStas_instr(name, author="ESS DMSC", origin="ESS DMSC",
                            input_path=input_path)
    lambda0 = instr.add_parameter("double", "lambda0", value=4.0,
                                  comment="Mean wavelength [AA]")
    dlambda = instr.add_parameter("double", "dlambda", value=1.0,
                                  comment="Wavelength half-width [AA]")

    origin = instr.add_component("origin", "Progress_bar")
    source = instr.add_component("source", "Source_simple",
                                 AT=[0, 0, 0], RELATIVE=origin)
    source.radius = 0.02
    source.dist = 10
    source.focus_xw = 0.02
    source.focus_yh = 0.02
    source.lambda0 = lambda0
    source.dlambda = dlambda
    source.flux = 1e12

    monitor = instr.add_component("lambda_monitor", "L_monitor",
                                  AT=[0, 0, 10], RELATIVE=source)
    monitor.xwidth = 0.02
    monitor.yheight = 0.02
    monitor.nL = 100
    monitor.Lmin = 0.0
    monitor.Lmax = 8.0
    monitor.filename = '"lambda.dat"'
    return instr


def add_example(instr, monitor, intensity, **parameters):
    """Add a McStas %Example test for the given monitor and parameter values,
    without changing the parameter defaults of the instrument."""
    saved = {p: instr.parameters[p].value for p in instr.get_parameter_names()}
    instr.set_parameters(parameters)
    instr.add_test(monitor, intensity=intensity, included_pars=list(parameters))
    instr.set_parameters(saved)
