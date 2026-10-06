# mcstas-ess-instr-citool

`mcstas-ess-instr-citool` validates ESS instrument simulation repositories
(McStas instrument models), and runs their instruments through McStas'
`mctest` in CI. It defines a *standard layout* for these repositories, so
that all instrument models at DMSC are organised the same way, and can be
tested automatically, both with classic McStas `.instr` files and with
McStasScript python code.

In short, an instrument repository contains a `conda.yml` file describing
its conda environment, the instrument files in `instr/` (or a McStasScript
python package in `instrpy/`), each with at least one `%Example` test, and
anything else in `extra/`. In its CI, the tool checks the layout, and runs
all tests with `mctest`:

```
pip install git+https://github.com/mccode-dev/mcstas-ess-instr-citool.git
mcstas-ess-instr-citool -a runci .
```

The source code and the issue tracker are in the GitHub repository
[mccode-dev/mcstas-ess-instr-citool](https://github.com/mccode-dev/mcstas-ess-instr-citool).

```{toctree}
:maxdepth: 2

layout
usage
instrument_repos
dmsc_repos
cmdline
```

```{toctree}
:maxdepth: 2
:caption: Development

development
examples
```
