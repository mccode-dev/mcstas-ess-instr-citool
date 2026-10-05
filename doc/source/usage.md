# Installation and usage

Install the tool with pip (Python 3.11 or newer), e.g. directly from GitHub:

```
pip install git+https://github.com/tkittel/dmsc-instr-repo-prototype.git
```

or with `pip install -e .` from a clone of the repository.
`mcstas-ess-instr-citool --version` shows the installed version (see
[](development.md#versions-and-releases)). The `generate`,
`generatepy` and `runci` actions need McStas 3.9.0 or newer (with
McStasScript 0.0.94 or newer for `instrpy` projects), for example from a conda
environment created with:

```
conda create -n mcstas -c conda-forge --override-channels "mcstas>=3.9.0" "mcstasscript>=0.0.94"
```

Usage (see also the [](cmdline.md)):

```
mcstas-ess-instr-citool [-a ACTION] [-o OUTDIR] [--mpi N] [--lenient] PROJECT_DIR
```

All actions first validate the project layout and the `conda.yml` file,
failing with an error message on any violation. Available actions:

* `list` (default): print a human-readable summary of the project.
* `check`: only validate the project.
* `json`, `pprint`: print the extracted project information as JSON or as a
  pretty-printed python dictionary.
* `generate`: generate `OUTDIR/instr/MODE/` for each mode (with `MAIN` for
  the main instrument). For the `instr` layout, the `.instr` file and any
  `includes/`, `snippets/`, `localcomps/` and `localdata/` files are copied.
  For the `instrpy` layout, each `make()` function is called in a separate
  process (with a timeout of 600 seconds) and must write exactly one `.instr`
  file (and may create `localdata/` next to it). The `includes/`,
  `localcomps/` and `localdata/` files are not copied, since `make()` must
  make them available itself (see [](layout.md)).
* `generatepy`: generate a complete `instrpy` project in `OUTDIR` (`-o` is
  required), with `conda.yml`, `instrpy/pyproject.toml` and the python
  package. For an `instrpy` project, the files are simply copied. For an
  `instr` project, each `.instr` file is translated with `mcstas-pygen`
  (`snippets/` are thereby included, and `includes/`, `localcomps/` and
  `localdata/` files are copied into the package, with code making them
  available to the instrument). The
  instrument is named after the file, `%Example` lines are translated into
  McStasScript tests (`instr.add_test`), and dates and local paths are
  removed from the output, so it is reproducible. The generated `make()`
  writes the instrument into McStasScript's default `input_path` (the working
  directory), not into the python package.
* `repos`, `repos-json`: list the instrument repositories at DMSC (see
  [](dmsc_repos.md)), as a table or as JSON. These
  actions take no `PROJECT_DIR`.
* `runci`: check that local components do not shadow McStas components, and
  that local data files do not have the names of McStas data files or
  NCrystal standard library materials, then
  run `generate`, followed by `mctest --strict --local` on the result. With `--strict`, each instrument must have at least one `%Example`
  line, and all examples must pass. `--noplots` is also given, so `mctest`
  does not plot the output of the tests, which can take much longer than the
  tests for instruments with many monitors. Finally, if the project has an
  `extra_pytests/` directory, the tests in it are run with `pytest` (see
  [](layout.md#tests-in-extra_pytests)).
  With `--mpi N` (or `--mpi auto` for the number of available processors),
  the instruments are compiled and run with MPI, using N processes. This
  tests that the instruments work with MPI. It does not necessarily make
  the tests faster, since compilation with MPI takes longer, and the default
  `mctest` simulations are short.

If `-o OUTDIR` is not given (it must be empty or not exist), a temporary
directory is used and cleaned up afterwards.

With `--lenient`, unexpected files and directories in the project (which
the layout rules do not allow) are ignored with a warning, instead of
causing an error. They are also left out of the generated instruments (for
the `instr` layout). This is for testing a working copy locally, which may
contain temporary files, e.g. compiled instruments or simulation output.
The other rules still apply. `--lenient` is not allowed in CI (it is refused
when the `CI` environment variable is set, as it is in GitLab CI), since the
committed files must follow the layout.
