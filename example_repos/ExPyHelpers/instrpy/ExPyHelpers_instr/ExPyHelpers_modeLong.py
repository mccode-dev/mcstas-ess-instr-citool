"""ExPyHelpers mode "Long": Like the main mode, but with a 40 m long guide.

Run from the instrpy/ directory as "python -m ExPyHelpers_instr.ExPyHelpers_modeLong" to
write the ExPyHelpers_modeLong.instr file.
"""

from .common import add_example, build

GUIDE_LENGTH = 40.0


def make(input_path=None):
    instr = build("ExPyHelpers_modeLong", GUIDE_LENGTH, input_path=input_path)
    add_example(instr, "sample_psd", intensity=9.94e9)
    return instr


if __name__ == "__main__":
    make().write_full_instrument()
