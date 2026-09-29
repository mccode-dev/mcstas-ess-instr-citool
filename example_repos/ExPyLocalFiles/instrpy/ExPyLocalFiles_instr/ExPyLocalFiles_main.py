"""ExPyLocalFiles main mode: an instrument using a project-specific component
(localcomps/ExCountMonitor.comp) and data file (localdata/ExAlLike.ncmat).

Run from the instrpy/ directory as "python -m ExPyLocalFiles_instr.ExPyLocalFiles_main"
to write the ExPyLocalFiles_main.instr file.
"""

import pathlib
import shutil

import mcstasscript as ms

PACKAGE_DIR = pathlib.Path(__file__).resolve().parent


def make(input_path=None):
    instr = ms.McStas_instr("ExPyLocalFiles_main", author="ESS DMSC",
                            origin="ESS DMSC", input_path=input_path)

    # Let McStas(Script) find the components in localcomps/:
    instr.add_search((PACKAGE_DIR / "localcomps").as_posix())

    # The instrument refers to data files as "localdata/<file>", relative to
    # the directory in which it runs (the McStasScript input_path), so copy
    # localdata/ there:
    localdata = pathlib.Path(instr.input_path).resolve() / "localdata"
    if localdata != PACKAGE_DIR / "localdata":
        shutil.copytree(PACKAGE_DIR / "localdata", localdata,
                        dirs_exist_ok=True)

    instr.add_parameter("double", "temperature", value=300,
                        comment="Temperature of the sample [K]")
    instr.add_declare_var("char", "sample_cfg", array=256)
    instr.append_initialize(
        'snprintf(sample_cfg, sizeof(sample_cfg),'
        ' "localdata/ExAlLike.ncmat;temp=%gK", temperature);')

    origin = instr.add_component("origin", "Progress_bar")

    source = instr.add_component("source", "Source_simple",
                                 AT=[0, 0, 0], RELATIVE=origin)
    source.radius = 0.01
    source.dist = 5
    source.focus_xw = 0.01
    source.focus_yh = 0.01
    source.lambda0 = 4
    source.dlambda = 2
    source.flux = 1e10

    sample = instr.add_component("sample", "NCrystal_sample",
                                 AT=[0, 0, 5], RELATIVE=source)
    sample.cfg = "sample_cfg"
    sample.radius = 0.005
    sample.yheight = 0.01

    counter = instr.add_component("counter", "ExCountMonitor",
                                  AT=[0, 0, 1], RELATIVE=sample)
    counter.xwidth = 0.02
    counter.yheight = 0.02
    counter.filename = '"counter"'
    counter.restore_neutron = 1

    instr.add_test("counter", intensity=4.69e5, included_pars=["temperature"])
    return instr


if __name__ == "__main__":
    make().write_full_instrument()
