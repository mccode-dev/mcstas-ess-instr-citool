# dmsc-instr-repo-prototype

Test repo for work on ESS instrument repos at DMSC.

This repository prototypes what an ESS instrument simulation repository
should look like, and contains a tool, `mcstas-ess-instr-citool`, which
validates such a repository and runs its instruments through McStas' `mctest`
in CI.

Contents:

* `src/mcstas_ess_instr_citool/`: the validation and CI tool.
* `example_repos/`: example instrument projects (see below).
* `tests/`: tests of the tool (run with `pytest`).
* `TODO`: known open issues.

## Instrument project layout

An instrument project is a directory containing:

* A `conda.yml` file describing the conda environment (see rules below).
* Exactly one of the following two directories:
  * `instr/`: classic McStas `.instr` files:
    * Exactly one `PROJECT_main.instr`.
    * Zero or more `PROJECT_modeMODENAME.instr`.
    * Optionally an `includes/` subdirectory with `*.h` and `*.c` files, and
      a `snippets/` subdirectory with `*.instr` files (for use via `%include`
      in the main and mode files). No other files or subdirectories are
      allowed.
    * The instrument in each main and mode file must be named after the file,
      e.g. `DEFINE INSTRUMENT ESS01_main(...)` in `ESS01_main.instr`.
  * `instrpy/`: McStasScript python files:
    * An `instrpy/pyproject.toml` with a PEP 621 `[project]` table whose
      `name` matches `PROJECT`.
    * An `instrpy/PROJECT_instr/` python package with an empty `__init__.py`,
      exactly one `PROJECT_main.py`, and zero or more
      `PROJECT_modeMODENAME.py`. Each of these must provide a `make()`
      function returning a McStasScript instrument named after the file
      (e.g. `ESS02_main`).
    * Optionally helper modules `MODULE.py` in the same directory, for code
      shared between the main and mode files (imported with relative
      imports like `from .common import build`). `MODULE` must be a valid
      python identifier, and must not start with `PROJECT_` (so misnamed
      mode files are not silently accepted as helper modules).
    * Optionally an `includes/` subdirectory (inside the python package) with
      `*.h` and `*.c` files. No other files or subdirectories are allowed.
      Note that when using the McStasScript instrument directly (rather than
      via this tool), the `includes/` directory must be copied to the
      McStasScript `input_path` directory.

`PROJECT` must match `[A-Za-z][A-Za-z0-9]*` and `MODENAME` must match
`[A-Za-z][A-Za-z0-9]*`. The mode names `main` and `test` are reserved, and
mode names differing only in case are not allowed. Hidden files (names
starting with `.`) and backup files (names ending with `~`) are ignored.

### The conda.yml file

The `conda.yml` file is parsed by a strict parser supporting only a small
subset of YAML (top-level keys `name`, `channels` and `dependencies`, with an
optional `pip:` subsection in the dependencies). Additionally:

* The channels must be exactly `conda-forge` and `nodefaults`.
* `mcstas`, `python` and `pip` must be listed as conda dependencies.
* `mcstas` must have an explicit lower bound of at least 3.8.8
  (e.g. `mcstas >= 3.8.8`).
* Only lower bounds (`>=` or `>`) are allowed as version constraints. Exact
  versions, upper bounds etc. (including conda's bare version syntax like
  `numpy 1.26.*`) are only allowed for packages on a hardwired allowlist
  (currently empty).
* `conda`, `conda-build`, `mamba` and `pip-tools` are forbidden.
* Packages in the `pip:` subsection must be on a hardwired allowlist
  (currently empty). Pip package names are compared after PEP 503
  normalisation.

Example:

```yaml
name: mcstas-environment

channels:
  - conda-forge
  - nodefaults

dependencies:
  - mcstas >= 3.8.8
  - python >= 3.12
  - pip
  - numpy >= 1.26
```

## Examples

* `example_repos/ESS01`: classic `.instr` files, with a main instrument and
  two modes (`FOO` and `BAR`).
* `example_repos/ESS02`: McStasScript variant, with a main instrument and one
  mode (`SomeMode`).
* `example_repos/ESS03`: classic `.instr` files using shared C code from
  `includes/` and an entire instrument pulled in from `snippets/` via
  `%include`.
* `example_repos/ESS04`: a small hand-written McStasScript instrument (source,
  guide and monitors), with a main instrument and one mode (`Long`) built from
  code shared in the helper modules `common.py`, `geometry.py` and
  `monitors.py`. It also shows how to add `%Example` tests with other
  parameter values than the defaults.

## The mcstas-ess-instr-citool tool

Install with `pip install -e .` (Python 3.11 or newer). The `generate`,
`generatepy` and `runci` actions need McStas 3.8.8 or newer (with
McStasScript for `instrpy` projects), for example from a conda environment created with:

```
conda create -n mcstas -c conda-forge --override-channels "mcstas>=3.8.8"
```

Usage:

```
mcstas-ess-instr-citool [-a ACTION] [-o OUTDIR] PROJECT_DIR
```

All actions first validate the project layout and the `conda.yml` file,
failing with an error message on any violation. Available actions:

* `list` (default): print a human-readable summary of the project.
* `check`: only validate the project.
* `json`, `pprint`: print the extracted project information as JSON or as a
  pretty-printed python dictionary.
* `generate`: generate `OUTDIR/instr/MODE/` for each mode (with `MAIN` for
  the main instrument). For the `instr` layout, the `.instr` file and any
  `includes/` and `snippets/` files are copied. For the `instrpy` layout,
  each `make()` function is called in a separate process (with a timeout of
  600 seconds) and must write exactly one `.instr` file.
* `generatepy`: generate a complete `instrpy` project in `OUTDIR` (`-o` is
  required), with `conda.yml`, `instrpy/pyproject.toml` and the python
  package. For an `instrpy` project, the files are simply copied. For an
  `instr` project, each `.instr` file is translated with `mcstas-pygen`
  (`snippets/` are thereby included, and `includes/` files are copied). The
  instrument is named after the file, `%Example` lines are translated into
  McStasScript tests (`instr.add_test`), and dates and local paths are
  removed from the output, so it is reproducible.
* `runci`: run `generate`, followed by `mctest --strict --local` on the
  result. With `--strict`, each instrument must have at least one `%Example`
  line, and all examples must pass.

If `-o OUTDIR` is not given (it must be empty or not exist), a temporary
directory is used and cleaned up afterwards.

## Tests

Run the tests with:

```
pip install -e ".[test]"
pytest
```

Tests that need McStas or McStasScript are skipped when these are not
available. The GitHub workflow in `.github/workflows/ci.yml` runs the tests
both without McStas (on several Python versions) and with McStas from
conda-forge (including running `mctest` on all examples).
