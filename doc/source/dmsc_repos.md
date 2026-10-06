# Instrument repositories at DMSC

The instrument repositories at DMSC are in the GitLab group
[dmsc-instrumentmodels](https://git.esss.dk/dmsc-instrumentmodels). The tool
knows them (`mcstas-ess-instr-citool -a repos` lists them), and they are
regularly tested with the current version of the tool (weekly, and for
changes of the tool). This page is updated after each of these tests.

```{include} _generated/dmsc_repos_table.md
```

The columns:

* **Test with this tool**: the result of the latest test of the repository
  with the current version of the tool, done like the CI of the repository
  itself (`mcstas-ess-instr-citool -a runci` in the conda environment from
  its `conda.yml`), with a link to the log. "not migrated" means that the
  main branch does not follow the standard layout yet (so it is only
  checked), and "not public" that the repository can not be tested, since
  it is not public.
* **Own CI (main)**: the status of the latest CI pipeline of the repository
  itself, on its main branch (live, for public repositories).
* **TODO**: the number of items in the `TODO` file on the main branch of the
  repository (see [](layout.md#the-todo-file)), with a link to it ("–" if
  there is no `TODO` file, or if the repository is not public).
