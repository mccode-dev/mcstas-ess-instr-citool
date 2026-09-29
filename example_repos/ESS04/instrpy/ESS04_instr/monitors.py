"""Helpers for adding monitors to the ESS04 instrument."""

from .geometry import GUIDE_HEIGHT, GUIDE_WIDTH


def add_monitor_set(instr, prefix, distance, relative, lmin, lmax):
    """Add a PSD and a wavelength monitor at the given distance after the
    component relative. The monitors cover a little more than the guide
    cross section, and do not absorb neutrons (restore_neutron=1).

    Returns the names of the added monitors."""
    names = []
    for kind, comp_name in [("psd", "PSD_monitor"), ("lambda", "L_monitor")]:
        name = f"{prefix}_{kind}"
        mon = instr.add_component(name, comp_name,
                                  AT=[0, 0, distance], RELATIVE=relative)
        mon.xwidth = 1.2 * GUIDE_WIDTH
        mon.yheight = 1.2 * GUIDE_HEIGHT
        mon.filename = f'"{name}.dat"'
        mon.restore_neutron = 1
        if kind == "lambda":
            mon.nL = 50
            mon.Lmin = lmin
            mon.Lmax = lmax
        else:
            mon.nx = 30
            mon.ny = 30
        names.append(name)
    return names
