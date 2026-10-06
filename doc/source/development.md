# Development

## Tests

Run the tests with:

```
pip install -e ".[test]"
pytest
```

Tests that need McStas or McStasScript are skipped when these are not
available. The GitHub workflow in `.github/workflows/ci.yml` (run for each
push by `pypi.yml`, see [](#versions-and-releases), and for pull requests) runs the tests
both without McStas (on several Python versions) and with McStas from
conda-forge (including running `mctest` on all examples). It also runs
`runci` on each example project in the conda environment from its own
`conda.yml` (as the CI of an instrument repository would), and checks the
code with `ruff check` (configured in `pyproject.toml`).

## Versions and releases

The version is taken from the git tags, with
[setuptools-git-versioning](https://setuptools-git-versioning.readthedocs.io/)
(as for [simplebuild](https://github.com/mctools/simplebuild)): a build of
the commit tagged `vX.Y.Z` gets version `X.Y.Z`, and a build of a later
commit e.g. `X.Y.Z.post3+git.1a2b3c4d` (3 commits after the tag). Without
any tag, the version is `0.0.1`. To make a release, tag the commit and push
the tag:

```
git tag v0.1.0
git push origin v0.1.0
```

The workflow `.github/workflows/pypi.yml` runs for every push: it runs all
tests (`ci.yml`), builds the distribution (sdist and wheel), checks it with
`twine check`, and checks the version reported by the installed wheel
(which, for a `vX.Y.Z` tag, must be `X.Y.Z`). The distribution is only
uploaded to PyPI for `vX.Y.Z` tags, and only when the repository variable
`PYPI_UPLOAD` is set to `true`. Before enabling that, trusted publishing must
be configured for the project on PyPI (with this repository and the workflow
`pypi.yml`), see the
[PyPI documentation](https://docs.pypi.org/trusted-publishers/).

## Documentation

This documentation is written in Markdown (with
[MyST](https://myst-parser.readthedocs.io/)) in `doc/source/`, and built
with [Sphinx](https://www.sphinx-doc.org/). The command line reference and
the list of instrument repositories are generated from the tool, which must
therefore be installed:

```
pip install . -r doc/requirements.txt
make -C doc html
```

The result is in `doc/build/html/`. The workflow `.github/workflows/doc.yml`
builds the documentation (treating warnings as errors) and checks its links
for every push and pull request. The workflow `publish-doc.yml` publishes it
on GitHub Pages, for pushes to `main` and version tags, and after each run of
`instrument-repos.yml` (since [](dmsc_repos.md) shows the results of its
latest run, from the GitHub API). GitHub Pages is enabled in the repository
settings, with "GitHub Actions" as the source.
