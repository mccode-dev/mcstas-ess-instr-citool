# Instrument repositories at DMSC

The instrument repositories at DMSC are in the GitLab group
[dmsc-instrumentmodels](https://git.esss.dk/dmsc-instrumentmodels). The tool
knows them (`mcstas-ess-instr-citool -a repos` lists them), and they are
regularly tested with the current version of the tool (weekly, and for
changes of the tool). This page is updated after each of these tests.

```{include} _generated/dmsc_repos_table.md
```

The columns:

* **Standard layout**: whether the main branch of the repository follows
  the standard layout (see [](layout.md)).
* **Test with this tool**: the result of the latest test of the repository
  with the current version of the tool, done like the CI of the repository
  itself (`mcstas-ess-instr-citool -a runci` in the conda environment from
  its `conda.yml`), with a link to the log. Repositories which do not follow
  the standard layout yet are only checked, and repositories which are not
  public can not be tested.
* **Own CI (main)**: the status of the latest CI pipeline of the repository
  itself, on its main branch (live, for public repositories).
