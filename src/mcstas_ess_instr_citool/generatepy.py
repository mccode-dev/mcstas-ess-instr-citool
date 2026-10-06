"""Generate an instrpy/ (McStasScript) project from any project."""

import re
import shutil
import subprocess
import tempfile
from pathlib import Path

from .errors import CheckFailed

# The same regex used by mctest to find %Example lines:
_EXAMPLE_RE = re.compile(r"\%Example:([^\n]*)Detector\:([^\n]*)_I=([0-9.+-e]+)")

_INSTR_CTOR_RE = re.compile(r'ms\.(?:McStas|McXtrace)_instr\("([^"]*)"')

# The generated make() uses the directory of the script as default
# input_path, i.e. it would write the instrument into the python package:
_INPUT_PATH_DEFAULT = """\
    # Default: the directory of this script
    if input_path is None:
        input_path = os.path.dirname(os.path.abspath(__file__))
"""

# SEARCH statements, as absolute paths of the source project (since the
# script is not written in the instr/ directory):
_SEARCH_RE = re.compile(r"    # SEARCH statements\n(    instr\.add_search\([^\n]*\n)+")


def generatepy( info, outdir ):
    """Generate a complete instrpy project in outdir (which must be empty or
    not exist) from the project described by info."""
    outdir = Path(outdir)
    outdir.mkdir(parents=True, exist_ok=True)
    assert not any(outdir.iterdir())
    projdir = Path(info['project_dir'])
    shutil.copyfile(projdir / 'conda.yml', outdir / 'conda.yml')
    if info['layout'] == 'instrpy':
        _copy_instrpy( info, outdir )
    else:
        _generate_from_instr( info, outdir )

    # Validate the result:
    from .analyse import analyse_dir
    newinfo = analyse_dir(outdir)
    assert newinfo['layout'] == 'instrpy'
    assert newinfo['project_name'] == info['project_name']
    assert list(newinfo['setups']) == list(info['setups'])
    print(f"Generated McStasScript project in {outdir}")
    return newinfo


def _copy_instrpy( info, outdir ):
    srcpkgdir = Path(info['base_dir'])
    pkgdir = outdir / 'instrpy' / srcpkgdir.name
    pkgdir.mkdir(parents=True)
    shutil.copyfile(Path(info['pyproject']['path']),
                    outdir / 'instrpy' / 'pyproject.toml')
    (pkgdir / '__init__.py').write_text('')
    for path in info['setups'].values():
        shutil.copyfile(path, pkgdir / Path(path).name)
    for module in info['helper_modules']:
        shutil.copyfile(srcpkgdir / f'{module}.py', pkgdir / f'{module}.py')
    _copy_extra_files( info, srcpkgdir, pkgdir )


def _copy_extra_files( info, srcdir, destdir, subdirs = None ):
    for subdir, fns in sorted(info['extra_files'].items()):
        if subdirs is not None and subdir not in subdirs:
            continue
        (destdir / subdir).mkdir()
        for fn in fns:
            shutil.copyfile(srcdir / subdir / fn, destdir / subdir / fn)


def _generate_from_instr( info, outdir ):
    from .util import mcstas_info
    pygen = mcstas_info()['cmd']['mcstas-pygen']

    project = info['project_name']
    pkgname = f'{project}_instr'
    pkgdir = outdir / 'instrpy' / pkgname
    pkgdir.mkdir(parents=True)
    (pkgdir / '__init__.py').write_text('')

    for path in info['setups'].values():
        path = Path(path)
        print(f"Generating {path.stem}.py from {path.name}")
        with tempfile.TemporaryDirectory() as tmpdir:
            pyfile = Path(tmpdir) / f'{path.stem}.py'
            cmd = [pygen, '--instrument-name', path.stem,
                   '-o', str(pyfile), path.name]
            # Run in the instr/ dir, so %include "snippets/..." works:
            p = subprocess.run(cmd, cwd=path.parent, capture_output=True,
                               text=True)
            if p.returncode != 0 or not pyfile.is_file():
                raise CheckFailed(f'mcstas-pygen failed for {path}:\n'
                                  + p.stdout + p.stderr)
            code = pyfile.read_text()
        code = postprocess_pygen_output( code, path.stem, path.read_text() )
        if 'includes' in info['extra_files']:
            code = add_includes_search_path( code )
        code = add_local_files_code(
            code,
            localcomps = 'localcomps' in info['extra_files'],
            localdata = 'localdata' in info['extra_files'] )
        (pkgdir / f'{path.stem}.py').write_text(code)

    # The includes/, localcomps/ and localdata/ files are needed by the
    # generated code, while the snippets/ have already been included by
    # mcstas-pygen:
    subdirs = ['includes', 'localcomps', 'localdata']
    _copy_extra_files( info, Path(info['base_dir']), pkgdir,
                       subdirs = subdirs )

    (outdir / 'instrpy' / 'pyproject.toml').write_text(
        _pyproject_toml( project, pkgname,
                         [ d for d in subdirs if d in info['extra_files'] ] ))


def postprocess_pygen_output( code, name, instr_text ):
    """Post-process output from mcstas-pygen: Check the instrument name and
    the tests corresponding to %Example lines, remove the default input_path
    and the SEARCH statements (which are replaced by add_local_files_code),
    and remove non-reproducible information like dates and local paths from
    comments."""
    names = _INSTR_CTOR_RE.findall(code)
    if names != [name]:
        raise RuntimeError('Could not find instrument creation with name'
                           f' "{name}" in output of mcstas-pygen')

    ntests = code.count('instr.add_test(')
    nexamples = len(_EXAMPLE_RE.findall(instr_text))
    if ntests != nexamples:
        raise CheckFailed(f'Could not translate all %Example lines in {name}'
                          f' into tests ({nexamples} lines, but'
                          f' {ntests} tests)')

    # Use the input_path of McStasScript by default (the working directory),
    # so the instrument is not written into the python package:
    code = code.replace(_INPUT_PATH_DEFAULT, '')
    code = _SEARCH_RE.sub('', code)
    if 'os.' not in code:
        code = code.replace('import os\n', '')

    # Reproducible output:
    lines = []
    for line in code.splitlines(keepends=True):
        if line.startswith('# Date:'):
            continue
        if line.startswith('# File:'):
            line = f'# File:       {name}.py\n'
        elif line.startswith('# end of generated Python code'):
            line = f'# end of generated Python code {name}.py\n'
        elif re.match(r'^ *# \w+ system dir is ', line):
            continue
        lines.append(line)
    return ''.join(lines)


_INCLUDES_CODE = """\
    # Let the C compiler find the files in includes/ in this python package:
    instr.add_include_dir(pathlib.Path(__file__).resolve().parent)
"""


def add_includes_search_path( code ):
    """Add code to generated instrument code, which adds the directory of the
    python package to the search path of the C compiler (via the DEPENDENCY
    line), so #include "includes/..." works wherever the instrument is
    written and compiled by McStasScript."""
    code = _add_import( code, 'pathlib' )
    return _insert_after_dependency_line( code, _INCLUDES_CODE )


_LOCALCOMPS_CODE = """\
    # Let McStas(Script) find the components in localcomps/ in this python
    # package:
    instr.add_search((pathlib.Path(__file__).resolve().parent
                      / 'localcomps').as_posix())
"""

_LOCALDATA_CODE = """\
    # The instrument refers to data files as "localdata/<file>", relative to
    # the directory in which it runs, i.e. the McStasScript input_path. So
    # copy localdata/ from this python package there:
    _localdata_src = pathlib.Path(__file__).resolve().parent / 'localdata'
    _localdata_dest = pathlib.Path(instr.input_path).resolve() / 'localdata'
    if _localdata_dest != _localdata_src:
        shutil.copytree(_localdata_src, _localdata_dest, dirs_exist_ok=True)
"""


def add_local_files_code( code, localcomps, localdata ):
    """Add code to generated instrument code, which makes the files in
    localcomps/ and localdata/ in the python package available to the
    instrument (replacing the SEARCH statements of the .instr, which
    mcstas-pygen writes as absolute paths of the source project)."""
    block = ''
    if localcomps:
        code = _add_import( code, 'pathlib' )
        block += _LOCALCOMPS_CODE
    if localdata:
        code = _add_import( code, 'pathlib' )
        code = _add_import( code, 'shutil' )
        block += _LOCALDATA_CODE
    if not block:
        return code
    return _insert_after_dependency_line( code, block, after_blocks = True )


def _add_import( code, module ):
    if f'import {module}\n' in code:
        return code
    if code.count('import argparse\n') != 1:
        raise RuntimeError('Could not find imports in output of mcstas-pygen')
    return code.replace('import argparse\n',
                        f'import argparse\nimport {module}\n')


def _insert_after_dependency_line( code, block, after_blocks = False ):
    """Insert block after the set_dependency line (which comes right after the
    instrument creation, before any components are added). With
    after_blocks, it is inserted after other blocks already inserted there
    (i.e. after the following non-empty lines)."""
    lines = code.splitlines(keepends=True)
    idx = [i for i, line in enumerate(lines)
           if line.startswith('    instr.set_dependency(')]
    if len(idx) != 1:
        raise RuntimeError('Could not find the DEPENDENCY line in output of'
                           ' mcstas-pygen')
    pos = idx[0] + 1
    if after_blocks:
        while pos < len(lines) and lines[pos].strip():
            pos += 1
    lines.insert(pos, block)
    return ''.join(lines)


def _pyproject_toml( project, pkgname, datadirs ):
    res = f'''[build-system]
requires = ["setuptools>=68"]
build-backend = "setuptools.build_meta"

[project]
name = "{project}"
version = "0.0.0"
description = "McStasScript instrument files for {project}"
requires-python = ">=3.11"
dependencies = []

[tool.setuptools]
packages = ["{pkgname}"]
'''
    if datadirs:
        patterns = ', '.join(f'"{d}/*"' for d in datadirs)
        res += f'''
[tool.setuptools.package-data]
{pkgname} = [{patterns}]
'''
    return res
