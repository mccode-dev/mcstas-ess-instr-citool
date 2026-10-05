# Instrument repositories at DMSC

The tool contains a database of the instrument repositories at DMSC (in the
GitLab group [dmsc-instrumentmodels](https://git.esss.dk/dmsc-instrumentmodels)),
in [`src/mcstas_ess_instr_citool/repodb.py`](https://github.com/tkittel/dmsc-instr-repo-prototype/blob/main/src/mcstas_ess_instr_citool/repodb.py), which
`mcstas-ess-instr-citool -a repos` lists. For each repository, it records
whether its default branch follows the standard layout, and whether it is
public:

```{include} _generated/dmsc_repos_table.md
```

The workflow [`instrument-repos.yml`](https://github.com/tkittel/dmsc-instr-repo-prototype/actions/workflows/instrument-repos.yml) tests these
repositories with the current version of the tool (for pushes to `main`,
weekly, and when started manually). Repositories which follow the standard
layout are tested like their own CI does (`runci` in the conda environment
from their `conda.yml`), and must pass. For the others, the result of the
layout check is only reported, with a warning if one of them passes it (then
`standard_layout` should be set to `True` in the database). Repositories
which are not public are skipped, unless the repository secret
`DMSC_GITLAB_TOKEN` holds a GitLab access token which can read them.
