# Configuration file for the Sphinx documentation builder, see
# https://www.sphinx-doc.org/en/master/usage/configuration.html
#
# The tool must be installed (e.g. with "pip install ."), since the version,
# the command line reference and the list of instrument repositories are
# taken from it.

import pathlib

from mcstas_ess_instr_citool import version as _tool_version
from mcstas_ess_instr_citool.repodb import repos
from mcstas_ess_instr_citool.todo import TODO_FILE_NAME, parse_todo

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
    'github_user': 'mccode-dev',
    'github_repo': 'mcstas-ess-instr-citool',
    'github_version': 'main',
    'conf_py_path': '/doc/source/',
}

# The table of the instrument repositories at DMSC (included in
# dmsc_repos.md), from the database of the tool, with the results of the
# latest run of the workflow instrument-repos.yml (from the GitHub API), and
# the pipeline status badges of the repositories themselves (from GitLab):

GITHUB_REPO = 'mccode-dev/mcstas-ess-instr-citool'

def _latest_test_run():
    """The latest completed (and not cancelled) run of instrument-repos.yml on
    main, and its jobs, or (None, None) if they can not be obtained (e.g.
    without network access)."""
    import json
    import os
    import urllib.request
    api = f'https://api.github.com/repos/{GITHUB_REPO}/actions'
    headers = { 'Accept': 'application/vnd.github+json' }
    if os.environ.get('GITHUB_TOKEN'):
        headers['Authorization'] = f"Bearer {os.environ['GITHUB_TOKEN']}"
    def get( url ):
        req = urllib.request.Request( url, headers = headers )
        with urllib.request.urlopen( req, timeout = 30 ) as f:
            return json.load( f )
    try:
        runs = get( f'{api}/workflows/instrument-repos.yml/runs'
                    '?branch=main&status=completed&per_page=20' )
        runs = [ r for r in runs['workflow_runs']
                 if r['conclusion'] in ('success', 'failure') ]
        if not runs:
            return None, None
        run = runs[0]
        jobs = get( f"{api}/runs/{run['id']}/jobs?per_page=100" )['jobs']
    except Exception as e:  # noqa: BLE001
        print( f'Note: could not get the latest test results ({e})' )
        return None, None
    return run, { j['name']: j for j in jobs }

def _test_result( job ):
    """Summary of the job testing a repository in instrument-repos.yml."""
    if job is None:
        return 'not tested'
    steps = { st['name']: st['conclusion'] for st in job['steps'] }
    if steps.get('Run the tests (runci)') == 'success':
        text = '✅ passes'
    elif job['conclusion'] == 'failure':
        text = '❌ fails'
    elif steps.get('Check the layout (not expected to pass)') == 'success':
        text = 'not migrated'
    elif steps.get('Install the tool') == 'skipped':
        text = 'not public'
    else:
        text = job['conclusion']
    return f"[{text}]({job['html_url']})"

def _todo_cell( r ):
    """The number of items in the TODO file on the main branch of a (public)
    repository, linked to the file, or '–'."""
    import urllib.error
    import urllib.request
    if not r['public']:
        return '–'
    url = f"{r['url']}/-/raw/main/{TODO_FILE_NAME}"
    try:
        with urllib.request.urlopen( url, timeout = 30 ) as f:
            text = f.read().decode( 'utf-8', errors = 'replace' )
    except urllib.error.HTTPError as e:
        if e.code == 404:
            return '–'  # No TODO file
        print( f'Note: could not get {url} ({e})' )
        return '?'
    except Exception as e:  # noqa: BLE001
        print( f'Note: could not get {url} ({e})' )
        return '?'
    link = f"{r['url']}/-/blob/main/{TODO_FILE_NAME}"
    try:
        n = len( parse_todo( text ) )
    except ValueError:
        return f'[⚠ invalid]({link})'
    return f'[{n}]({link})'

def _write_repos_table():
    run, jobs = _latest_test_run()
    lines = [ '| Instrument | Test with this tool | Own CI (main) | TODO'
              ' | Description |',
              '|---|---|---|---|---|' ]
    for r in repos():
        result = ( _test_result( jobs.get(r['name']) ) if jobs is not None
                   else 'no results' )
        badge = ( f"[![pipeline status]({r['url']}/badges/main/pipeline.svg)]"
                  f"({r['url']}/-/pipelines?ref=main)" if r['public'] else '–' )
        lines.append( f"| [{r['name']}]({r['url']}) | {result} | {badge}"
                      f" | {_todo_cell( r )} | {r['description']} |" )
    if run is not None:
        lines += [ '', f"Test results from the [run of {run['created_at'][:10]}]"
                   f"({run['html_url']}) (commit {run['head_sha'][:7]} of the"
                   " tool)." ]
    outdir = pathlib.Path(__file__).parent / '_generated'
    outdir.mkdir(exist_ok=True)
    (outdir / 'dmsc_repos_table.md').write_text('\n'.join(lines) + '\n')

_write_repos_table()

# Repositories which are not public can not be checked by "make linkcheck"
# (they redirect to the login page):
linkcheck_ignore = [ r['url'] for r in repos() if not r['public'] ]
