"""Generate an instrpy/ (McStasScript) project from any project."""

import re
import shutil
import subprocess
import tempfile
from pathlib import Path

# The same regex used by mctest to find %Example lines:
_EXAMPLE_RE = re.compile(r"\%Example:([^\n]*)Detector\:([^\n]*)_I=([0-9.+-e]+)")

_INSTR_CTOR_RE = re.compile(r'(ms\.(?:McStas|McXtrace)_instr\()"[^"]*"')

_PARAM_RE = re.compile(r"instr\.add_parameter\('(\w*)', '(\w+)'")

_TESTS_ANCHOR = "    # Instruct McStasscript not to 'check everythng'\n"


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
    pygen_has_name_opt = '--instrument-name' in subprocess.run(
        [pygen, '--help'], capture_output=True, text=True).stderr

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
            cmd = [pygen]
            if pygen_has_name_opt:
                cmd += ['--instrument-name', path.stem]
            cmd += ['-o', str(pyfile), path.name]
            # Run in the instr/ dir, so %include "snippets/..." works:
            p = subprocess.run(cmd, cwd=path.parent, capture_output=True,
                               text=True)
            if p.returncode != 0 or not pyfile.is_file():
                raise RuntimeError(f'mcstas-pygen failed for {path}:\n'
                                   + p.stdout + p.stderr)
            code = pyfile.read_text()
        code = postprocess_pygen_output( code, path.stem, path.read_text() )
        (pkgdir / f'{path.stem}.py').write_text(code)

    # The includes/ files are needed by the generated code, while the
    # snippets/ have already been included by mcstas-pygen:
    _copy_extra_files( info, Path(info['base_dir']), pkgdir,
                       subdirs = ['includes'] )

    (outdir / 'instrpy' / 'pyproject.toml').write_text(
        _pyproject_toml( project, pkgname,
                         'includes' in info['extra_files'] ))


def postprocess_pygen_output( code, name, instr_text ):
    """Post-process output from mcstas-pygen: Set the instrument name, add
    tests corresponding to %Example lines (unless mcstas-pygen already did
    it), and remove non-reproducible information like dates and local paths
    from comments."""
    # Instrument name (needed when mcstas-pygen does not support the
    # --instrument-name option, like in McStas 3.8.8):
    code, n = _INSTR_CTOR_RE.subn(rf'\g<1>"{name}"', code)
    if n != 1:
        raise RuntimeError('Could not find instrument creation in output'
                           ' of mcstas-pygen')

    # Tests (needed when mcstas-pygen does not translate %Example lines,
    # like in McStas 3.8.8):
    examples = _EXAMPLE_RE.findall(instr_text)
    if 'instr.add_test(' not in code and examples:
        code = _add_tests( code, examples )
    ntests = code.count('instr.add_test(')
    if ntests != len(examples):
        raise RuntimeError(f'Could not translate all %Example lines in {name}'
                           f' into tests ({len(examples)} lines, but'
                           f' {ntests} tests)')

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


def _add_tests( code, examples ):
    """Add McStasScript tests to generated code, in exactly the same way as
    newer versions of mcstas-pygen do it (except that problems are errors
    rather than warnings)."""
    partypes = dict((n, t) for t, n in _PARAM_RE.findall(code))
    testcode = []
    for parvals, monitor, value in examples:
        monitor = monitor.strip()
        value = value.strip()
        if not monitor.isidentifier() or not _is_number(value):
            raise RuntimeError('Invalid monitor name or value in %Example'
                               f' line: {parvals}Detector:{monitor}_I={value}')
        setpars, inclpars = [], []
        for tok in parvals.split():
            parname, eq, parval = tok.partition('=')
            if not eq or not parname:
                raise RuntimeError(f'Invalid parameter setting "{tok}" in'
                                   ' %Example line')
            if parname not in partypes:
                raise RuntimeError(f'Unknown instrument parameter "{parname}"'
                                   ' in %Example line')
            if partypes[parname] == 'string':
                if ( len(parval) >= 2 and parval[0] in '"\''
                     and parval[-1] == parval[0] ):
                    parval = parval[1:-1]
                if any(c in parval for c in '"\'\\'):
                    raise RuntimeError('Unsupported string value for'
                                       f' parameter "{parname}" in'
                                       ' %Example line')
                # Without the double quotes usually needed for McStasScript
                # string parameter values, since add_test would otherwise put
                # them in the %Example line (parameters are restored before
                # the instrument is used):
                setpars.append(f"'{parname}': '{parval}'")
            elif partypes[parname] in ('int', 'double'):
                if not _is_number(parval):
                    raise RuntimeError('Non-numeric value for parameter'
                                       f' "{parname}" in %Example line')
                setpars.append(f"'{parname}': {parval}")
            else:
                raise RuntimeError(f'Parameter "{parname}" of unsupported'
                                   ' type in %Example line')
            inclpars.append(f"'{parname}'")
        if setpars:
            testcode.append(f"    instr.set_parameters({{{', '.join(setpars)}}})\n")
        testcode.append(f"    instr.add_test('{monitor}', intensity={value},"
                        f" included_pars=[{', '.join(inclpars)}])\n")

    block = [ "    # Tests corresponding to the %Example lines of the instrument. The\n",
              "    # parameter values are restored afterwards, since add_test uses the\n",
              "    # current parameter values:\n",
              "    _parameter_values = {p: instr.parameters[p].value"
              " for p in instr.get_parameter_names()}\n" ]
    block += testcode
    block += [ "    instr.set_parameters(_parameter_values)\n", "\n" ]

    anchor = _TESTS_ANCHOR if _TESTS_ANCHOR in code else "    return instr\n"
    if code.count(anchor) != 1:
        raise RuntimeError('Could not find where to add tests in output of'
                           ' mcstas-pygen')
    return code.replace(anchor, ''.join(block) + anchor)


def _is_number( s ):
    try:
        float(s)
    except ValueError:
        return False
    return True


def _pyproject_toml( project, pkgname, has_includes ):
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
    if has_includes:
        res += f'''
[tool.setuptools.package-data]
{pkgname} = ["includes/*.h", "includes/*.c"]
'''
    return res
