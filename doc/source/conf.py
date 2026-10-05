# Configuration file for the Sphinx documentation builder, see
# https://www.sphinx-doc.org/en/master/usage/configuration.html
#
# The tool must be installed (e.g. with "pip install ."), since the version,
# the command line reference and the list of instrument repositories are
# taken from it.

import pathlib

from mcstas_ess_instr_citool import version as _tool_version
from mcstas_ess_instr_citool.repodb import repos

project = 'mcstas-ess-instr-citool'
copyright = '2025-2026, European Spallation Source ERIC'
author = 'Peter Willendrup and Thomas Kittelmann'
release = _tool_version()
version = release

nitpicky = True
extensions = [
    'myst_parser',
    'sphinxarg.ext',
]
myst_heading_anchors = 3
templates_path = []
exclude_patterns = ['_generated']

html_theme = 'sphinx_rtd_theme'
html_static_path = ['_static']
html_title = f'{project} {release}'
html_theme_options = {
    'sticky_navigation': True,
    'navigation_with_keys': True,
}
html_context = {
    'display_github': True,
    'github_user': 'tkittel',
    'github_repo': 'dmsc-instr-repo-prototype',
    'github_version': 'main',
    'conf_py_path': '/doc/source/',
}

# The table of the instrument repositories at DMSC, from the database of the
# tool (included in dmsc_repos.md):
def _write_repos_table():
    yes_no = lambda b: 'yes' if b else 'no'  # noqa: E731
    lines = [ '| Name | Description | Standard layout | Public | Repository |',
              '|---|---|---|---|---|' ]
    for r in repos():
        lines.append( f"| {r['name']} | {r['description']}"
                      f" | {yes_no(r['standard_layout'])}"
                      f" | {yes_no(r['public'])}"
                      f" | [{r['repo']}]({r['url']}) |" )
    outdir = pathlib.Path(__file__).parent / '_generated'
    outdir.mkdir(exist_ok=True)
    (outdir / 'dmsc_repos_table.md').write_text('\n'.join(lines) + '\n')

_write_repos_table()

# Repositories which are not public can not be checked by "make linkcheck"
# (they redirect to the login page):
linkcheck_ignore = [ r['url'] for r in repos() if not r['public'] ]
