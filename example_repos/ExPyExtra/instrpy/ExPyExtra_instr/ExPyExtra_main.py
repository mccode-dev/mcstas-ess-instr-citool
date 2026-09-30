"""ExPyExtra main mode: a source and a wavelength monitor.

Run from the instrpy/ directory as "python -m ExPyExtra_instr.ExPyExtra_main"
to write the ExPyExtra_main.instr file.
"""

from .common import add_example, build


def make(input_path=None):
    instr = build("ExPyExtra_main", input_path=input_path)
    add_example(instr, "lambda_monitor", intensity=1.005e8, lambda0=4.0)
    return instr


if __name__ == "__main__":
    make().write_full_instrument()
