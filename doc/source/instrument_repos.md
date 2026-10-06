# Using the tool in an instrument repository

To reproduce the CI tests locally before committing, run the following from
the repository root, in the conda environment created from its `conda.yml`
(`conda env create -f conda.yml`):

```
pip install git+https://github.com/mccode-dev/mcstas-ess-instr-citool.git
mcstas-ess-instr-citool -a runci .
```

`mcstas-ess-instr-citool -a check .` quickly validates the layout, and
`mcstas-ess-instr-citool .` shows a summary of the project. If the working
copy contains temporary files which the layout does not allow (e.g. output
from running the instruments), the checks fail on them; `--lenient` ignores
them instead (with a warning), but CI will still fail if they are committed.

A GitLab CI configuration (`.gitlab-ci.yml`) for ESS instrument repositories
at git.esss.dk, doing the same:

```
runci:
  tags:
    - python311  # as used by other ESS instrument repositories
  variables:
    MAMBA_ROOT_PREFIX: "$CI_PROJECT_DIR/.micromamba"
  script:
    # The package cache is shared by all jobs on the runner (outside the
    # project directory), so packages are only downloaded and stored once,
    # and the environment mostly consists of hard links into the cache:
    - export CONDA_PKGS_DIRS="$HOME/.cache/mcstas-ess-instr-citool/conda-pkgs"
    # Uncompressed micromamba executable (the runner has no bzip2), in a hidden
    # directory since other files are not allowed at the top level:
    - curl -Ls -o .micromamba/bin/micromamba --create-dirs https://github.com/mamba-org/micromamba-releases/releases/latest/download/micromamba-linux-64
    - chmod +x .micromamba/bin/micromamba
    - .micromamba/bin/micromamba create -y -q -n ci -f conda.yml
    - .micromamba/bin/micromamba run -n ci pip install -q git+https://github.com/mccode-dev/mcstas-ess-instr-citool.git
    - .micromamba/bin/micromamba run -n ci mcstas-ess-instr-citool -a runci .
  after_script:
    # Remove the environment (also after failures), so it does not stay on the
    # runner's disk:
    - rm -rf .micromamba
```

The micromamba files are kept in the hidden `.micromamba/` directory, since
other files are not allowed at the top level of the repository. The package
cache is shared by all jobs on the runner (`CONDA_PKGS_DIRS`, outside the
project directory), so packages are only downloaded and stored once, and the
environment mostly consists of hard links into the cache. The environment is
removed at the end of each job (`after_script`), so it does not stay on the
runner. Without this, each job put about 5 GB and 180,000 files into its
project directory, which filled the disk of a runner (see
[issue #2](https://github.com/mccode-dev/mcstas-ess-instr-citool/issues/2)).
