"""Model checks: rules for the instruments of a project, checked on the
McStasScript instrument object of each mode (without compiling or running
the instrument).

For the instrpy layout, the instrument object is made by the make() function
of each mode. For the instr layout, each .instr file is first processed by
the McStas code generator (mcstas, without compiling), which reports errors
in the instrument (e.g. a RELATIVE reference to an unknown component) and
lists the instrument parameters (also those from %include), whose defaults
are checked. Then the .instr files are translated with mcstas-pygen (as for
the generatepy action), and the instrument object is made by the generated
make() function. Each make() is called in a separate process (with a
timeout), as for the generate action.

For the instr layout, a string parameter without a default value can not be
distinguished from one with the default value "" in the output of mcstas. It
is found in the output of mcstas-pygen instead, which (from McStas 3.9.2)
writes no default value for it, unlike for "". Older versions of
mcstas-pygen crash on such parameters, which is then reported as a problem
with one of the possible parameters.

McStasScript and McStas are only used when the checks are run.
"""

import multiprocessing as mp
import os
import re
import subprocess
import sys
import tempfile
import traceback
from pathlib import Path

from .errors import CheckFailed

DOC_URL = ("https://mccode-dev.github.io/mcstas-ess-instr-citool/"
           "layout.html#model-checks")

# Max time (seconds) allowed for making the instrument object of one mode:
DEFAULT_TIMEOUT = 600

# The first McStas version where mcstas-pygen handles parameters without
# default values (McCode PR #2762):
_PYGEN_NODEFAULT_MCSTAS_VERSION = (3,9,2)

# The rules, as (name, description):
RULES = [
    ("parameter-defaults",
     "All instrument parameters must have default values."),
    ("relative-references",
     "AT and ROTATED of each component must be RELATIVE to a component"
     " defined earlier in the instrument (or ABSOLUTE or PREVIOUS)."),
]
_RULE_DESCRIPTIONS = dict(RULES)


class ModelCheckError(CheckFailed):
    pass


def check_instrument( instr ):
    """Check a McStasScript instrument object against the rules. Returns a
    list of violations, each as (rule name, description of the problem)."""
    violations = []

    for name, par in instr.parameters.parameters.items():
        if par.value is None:
            violations.append(("parameter-defaults",
                               f"instrument parameter '{name}' has no"
                               " default value"))

    defined = set()
    for comp in instr.component_list:
        refs = [ ("AT", comp.AT_reference) ]
        if comp.ROTATED_specified:
            refs.append( ("ROTATED", comp.ROTATED_reference) )
        for what, ref in refs:
            if ref is None or str(ref).startswith("PREVIOUS"):
                continue
            if ref == comp.name:
                problem = "refers to the component itself"
            elif ref not in defined:
                problem = ("refers to a component which is not defined"
                           " earlier in the instrument")
            else:
                continue
            violations.append(("relative-references",
                               f"component '{comp.name}': {what} RELATIVE"
                               f" '{ref}' {problem}"))
        defined.add(comp.name)

    return violations


def modelcheck( info, workdir, timeout = DEFAULT_TIMEOUT ):
    """Run the model checks for all modes of the project described by info
    (from analyse_dir). Files are written only in workdir (an existing,
    empty directory). Raises ModelCheckError if any rule is broken."""
    workdir = Path(workdir).resolve()
    projdir = Path(info['project_dir'])
    if info['layout'] == 'instr':
        # First with the McStas code generator, which gives clear error
        # messages, and finds numeric parameters without defaults (which
        # mcstas-pygen before McStas 3.9.2 crashes on):
        string_params = _check_instr_files( info, projdir )
    if info['layout'] == 'instrpy':
        from .util import check_mcstasscript_version
        check_mcstasscript_version()
        pkgdir = Path(info['base_dir'])
    else:
        from .generatepy import generatepy
        try:
            newinfo = generatepy( info, workdir / 'generatepy' )
        except CheckFailed:
            _raise_if_old_pygen_crash( string_params )
            raise
        pkgdir = Path(newinfo['base_dir'])

    failures = []
    for mode, path in info['setups'].items():
        relpath = Path(path).relative_to(projdir).as_posix()
        rundir = workdir / 'run' / mode
        rundir.mkdir(parents=True)
        print(f"Model check of {relpath} (mode {mode})", flush=True)
        violations = _check_mode( pkgdir, Path(path).stem, rundir, timeout )
        for rule, problem in violations:
            print(f"  {rule}: {problem}")
            failures.append( (relpath, mode, rule, problem) )

    _raise_if_failures( failures )
    print(f"Model checks OK ({len(info['setups'])} instrument(s))")


# An entry of the table of instrument parameters in the C code from mcstas:
_PARAM_RE = re.compile(r'^\s*"(\w+)", &\(_instrument_var\._parameters\.\w+\),'
                       r' instr_type_(\w+), "(.*?)", ', re.MULTILINE)


def _check_instr_files( info, projdir ):
    """Check the .instr files with the McStas code generator: errors in the
    instruments, and instrument parameters without default values. Returns
    the string parameters which might have no default value, as a list of
    (relpath, mode, name)."""
    from .util import mcstas_info
    mcstas = mcstas_info()['cmd']['mcstas']
    failures = []
    string_params = []
    for mode, path in info['setups'].items():
        path = Path(path)
        relpath = path.relative_to(projdir).as_posix()
        print(f"Checking {relpath} (mode {mode}) with McStas", flush=True)
        with tempfile.TemporaryDirectory() as tmpdir:
            cfile = Path(tmpdir) / f'{path.stem}.c'
            # Run in the instr/ dir, so %include "snippets/..." works:
            p = subprocess.run([mcstas, '-o', str(cfile), path.name],
                               cwd=path.parent, capture_output=True,
                               text=True)
            if p.returncode != 0 or not cfile.is_file():
                errors = [ line.strip() for line in
                           (p.stdout + p.stderr).splitlines()
                           if 'error' in line.lower() ]
                raise ModelCheckError(
                    f"McStas reports errors in {relpath} (mode {mode}):\n  "
                    + "\n  ".join(errors or [ "(no error message)" ]))
            ctext = cfile.read_text(errors='replace')
        for name, ptype, default in _PARAM_RE.findall(ctext):
            if default == "" and ptype == "string":
                string_params.append( (relpath, mode, name) )
            elif default == "":
                failures.append( (relpath, mode, "parameter-defaults",
                                  f"instrument parameter '{name}' has no"
                                  " default value") )
    _raise_if_failures( failures )
    return string_params


def _raise_if_old_pygen_crash( string_params ):
    """mcstas-pygen failed. Before McStas 3.9.2, it crashes on parameters
    without default values. Since numeric ones are already reported, this
    must be one of the string parameters, if there are any."""
    from .util import mcstas_info
    if not string_params or ( mcstas_info()['version']
                              >= _PYGEN_NODEFAULT_MCSTAS_VERSION ):
        return
    failures = [ (relpath, mode, "parameter-defaults",
                  f"instrument parameter '{name}' has no default value, or"
                  ' the default value "" (mcstas-pygen failed, which happens'
                  ' before McStas 3.9.2 for parameters without default'
                  ' values)')
                 for relpath, mode, name in string_params ]
    _raise_if_failures( failures )


def _raise_if_failures( failures ):
    if failures:
        lines = [ f"{relpath} (mode {mode}): {problem} [rule {rule}:"
                  f" {_RULE_DESCRIPTIONS[rule]}]"
                  for relpath, mode, rule, problem in failures ]
        raise ModelCheckError(
            f"The model checks failed ({len(failures)} problem(s)):\n  "
            + "\n  ".join(lines) + f"\nSee {DOC_URL}")


def _check_mode( pkgdir, module, rundir, timeout ):
    ctx = mp.get_context("spawn")
    parent, child = ctx.Pipe(duplex=False)
    process = ctx.Process(target=_worker,
                          args=(child, str(pkgdir), module, str(rundir)))
    process.start()
    child.close()
    try:
        if not parent.poll(timeout):
            process.terminate()
            process.join()
            raise ModelCheckError(f"Making the instrument {module} timed out"
                                  f" after {timeout} seconds")
        try:
            status, result = parent.recv()
        except EOFError:
            status, result = "error", ("Process exited without reporting"
                                       f" (exit code {process.exitcode})")
    finally:
        parent.close()
    process.join()
    if status != "ok":
        raise ModelCheckError(f"Could not make the instrument {module} for"
                              f" the model checks:\n{result}")
    return result


def _worker( conn, pkgdir, module, rundir ):
    try:
        # Do not write __pycache__ directories into the project:
        sys.dont_write_bytecode = True
        pkgdir = Path(pkgdir)
        sys.path.insert(0, str(pkgdir.parent))
        os.chdir(rundir)
        import importlib
        import inspect
        mod = importlib.import_module(f"{pkgdir.name}.{module}")
        if 'input_path' in inspect.signature(mod.make).parameters:
            instr = mod.make(input_path=rundir)
        else:
            instr = mod.make()
        conn.send(("ok", check_instrument(instr)))
    except BaseException:
        conn.send(("error", traceback.format_exc()))
    finally:
        conn.close()
