"""ESS04 main mode: A 10 m long guide.

Run from the instrpy/ directory as "python -m ESS04_instr.ESS04_main" to
write the ESS04_main.instr file.
"""

from .common import add_example, build

GUIDE_LENGTH = 10.0


def make(input_path=None):
    instr = build("ESS04_main", GUIDE_LENGTH, input_path=input_path)
    add_example(instr, "sample_psd", intensity=1.26e10)
    add_example(instr, "sample_lambda", intensity=1.45e9, lambda0=2.0,
                dlambda=0.5)
    return instr


if __name__ == "__main__":
    make().write_full_instrument()
