# Examples

The repository of the tool contains small example projects, in
[`example_repos/`](https://github.com/mccode-dev/mcstas-ess-instr-citool/tree/main/example_repos), which are tested in its CI
(see [](development.md)):


* [`ExInstrBasic`](https://github.com/mccode-dev/mcstas-ess-instr-citool/tree/main/example_repos/ExInstrBasic): classic `.instr` files, with a main
  instrument and two modes (`FOO` and `BAR`).
* [`ExInstrIncludes`](https://github.com/mccode-dev/mcstas-ess-instr-citool/tree/main/example_repos/ExInstrIncludes): classic `.instr` files using shared C code
  from `includes/` and an entire instrument pulled in from `snippets/` via
  `%include`.
* [`ExPyGenerated`](https://github.com/mccode-dev/mcstas-ess-instr-citool/tree/main/example_repos/ExPyGenerated): McStasScript files generated with
  `generatepy` (i.e. `mcstas-pygen`) from the main instrument of
  `ExInstrBasic`, with a main instrument and one mode (`SomeMode`).
* [`ExPyHelpers`](https://github.com/mccode-dev/mcstas-ess-instr-citool/tree/main/example_repos/ExPyHelpers): a small hand-written McStasScript instrument
  (source, guide and monitors), with a main instrument and one mode (`Long`)
  built from code shared in the helper modules `common.py`, `geometry.py`
  and `monitors.py`. It also shows how to add `%Example` tests with other
  parameter values than the defaults.
* [`ExInstrLocalFiles`](https://github.com/mccode-dev/mcstas-ess-instr-citool/tree/main/example_repos/ExInstrLocalFiles): classic `.instr` file using a
  project-specific component (`localcomps/ExCountMonitor.comp`, with its own
  C library) and an NCrystal material file (`localdata/ExAlLike.ncmat`).
* [`ExPyLocalFiles`](https://github.com/mccode-dev/mcstas-ess-instr-citool/tree/main/example_repos/ExPyLocalFiles): the same instrument, as hand-written
  McStasScript code.
* [`ExPyExtra`](https://github.com/mccode-dev/mcstas-ess-instr-citool/tree/main/example_repos/ExPyExtra): a small hand-written McStasScript instrument,
  with an analysis package and a script in `extra/`, and tests in
  `extra_pytests/` which use both (one of them runs a short simulation).
