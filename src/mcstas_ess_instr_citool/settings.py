"""The settings file of a project (optional): a TOML file named citool.toml,
at the top level of the project. The only setting is:

    ncount: the number of neutrons of each %Example test in the full tests
            (runci), instead of the default of mctest (1e6), e.g. for models
            whose tests would otherwise take too long. It is a whole number,
            written as an integer or float, e.g. "ncount = 1e4".

Example:

    # Settings of mcstas-ess-instr-citool:
    ncount = 1e4
"""

import tomllib

from .errors import ProjectError

SETTINGS_FILE_NAME = "citool.toml"
DOC_URL = ("https://mccode-dev.github.io/mcstas-ess-instr-citool/"
           "layout.html#the-citooltoml-file")


def parse_settings(text: str, filename: str = SETTINGS_FILE_NAME) -> dict:
    """The settings of a settings file (as a dict with all settings, None for
    those not given), or a ProjectError (a ValueError) explaining the
    problem."""
    def bad(msg):
        return ProjectError(f"{filename}: {msg} (see {DOC_URL})")
    try:
        data = tomllib.loads(text)
    except tomllib.TOMLDecodeError as e:
        raise bad(f"not valid TOML ({e})") from None
    unknown = sorted(set(data) - {"ncount"})
    if unknown:
        raise bad(f"unknown setting {unknown[0]!r} (the only setting is"
                  " 'ncount')")
    ncount = data.get("ncount")
    if ncount is not None:
        if ( isinstance(ncount, bool) or not isinstance(ncount, (int, float))
             or not ncount >= 1 or not float(ncount).is_integer() ):
            raise bad(f"ncount must be a whole number of at least 1, not {ncount!r}")
        ncount = int(ncount)
    return {"ncount": ncount}
