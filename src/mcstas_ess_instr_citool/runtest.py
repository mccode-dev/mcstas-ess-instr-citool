import json
import shlex
import subprocess


def mctest_args( instrdir, testdir, mpi = None ):
    """Arguments for mctest. If mpi is an integer or "auto" (meaning the
    number of available processors), the instruments are compiled and run
    with MPI, using that number of processes. With --noplots, mctest does not
    plot the test output (which can take long for instruments with many
    monitors, and is not looked at)."""
    cmd = [ '--strict', '--noplots' ]
    if mpi is not None:
        if mpi == 'auto':
            from .util import get_nprocs
            mpi = get_nprocs()
        cmd += [ '--mpi', str(int(mpi)) ]
    cmd += [ '--local', str(instrdir), '--testdir', str(testdir) ]
    return cmd

def runtest( info, outdir, mpi = None ):
    from .generate import generate
    from .localfiles import check_local_components, check_local_data
    from .util import mcstas_info
    mctest_cmd = mcstas_info()['cmd']['mctest']
    check_local_components( info )
    check_local_data( info )
    instrdir = generate( info, outdir )
    testdir = outdir.joinpath('tests').absolute().resolve()
    cmd = mctest_args( instrdir, testdir, mpi )
    print(f"Launching: mctest {shlex.join(cmd)}", flush=True)
    ec = subprocess.run( [ mctest_cmd ] + cmd,
                         check = False, capture_output = False )
    if not ec.returncode==0:
        raise RuntimeError('mctest command failed')
    json_files = list(testdir.glob('*/testresults_*.json'))
    if len(json_files)>1:
        raise RuntimeError('mctest command produced multiple testresults_*.json')
    if len(json_files) != 1:
        raise RuntimeError('mctest command produced no testresults_*.json')
    jsonfile = json_files[0]
    print(f"Loading json results from {jsonfile.name}")
    res = json.loads(jsonfile.read_text())
    check_results(res)
    #TODO: Use the json results for anything else?
    run_extra_pytests( info, outdir )
    return res

def run_extra_pytests( info, outdir ):
    """Run the tests in extra_pytests/ (if present) with pytest. The directory
    is copied to outdir and pytest is run from within it, with instrpy/ (for
    the instrpy layout) and extra/ (and extra/src/, if present) added to
    PYTHONPATH."""
    import importlib.util
    import os
    import shutil
    import sys
    srcdir = info.get("extra_pytests_dir")
    if not srcdir:
        return
    if importlib.util.find_spec("pytest") is None:
        raise RuntimeError("pytest is needed to run the tests in extra_pytests/")
    testdir = outdir.joinpath("extra_pytests").absolute()
    shutil.copytree( srcdir, testdir,
                     ignore = shutil.ignore_patterns('__pycache__', '.*') )
    paths = []
    if info["layout"] == "instrpy":
        paths.append( os.path.dirname(info["base_dir"]) )
    extra_dir = info.get("extra_dir")
    if extra_dir:
        paths.append( extra_dir )
        if os.path.isdir(os.path.join(extra_dir, "src")):
            paths.append( os.path.join(extra_dir, "src") )
    env = dict(os.environ)
    if env.get("PYTHONPATH"):
        paths.append( env["PYTHONPATH"] )
    env["PYTHONPATH"] = os.pathsep.join(paths)
    cmd = [ sys.executable, '-m', 'pytest', '-p', 'no:cacheprovider' ]
    print(f"Launching: python {shlex.join(cmd[1:])} (in {testdir})", flush=True)
    ec = subprocess.run( cmd, cwd = testdir, env = env, check = False )
    if ec.returncode != 0:
        raise RuntimeError('pytest failed for the tests in extra_pytests/')

def check_results( res ):
    """Double-check the mctest json results, since mctest does not always
    report failures in its exit code (e.g. an instrument with a single
    %Example which fails to compile)."""
    problems = []
    tests = { k : v for k, v in res.items() if k != '_meta' }
    if not tests:
        problems.append('no tests found')
    for name, t in sorted(tests.items()):
        if not t.get('compiled'):
            problems.append(f'{name}: did not compile')
        elif not t.get('didrun'):
            problems.append(f'{name}: did not run')
        elif t.get('testval') in (None, -1):
            problems.append(f'{name}: no test value extracted')
    if problems:
        raise RuntimeError('mctest results contain failures:\n  '
                           + '\n  '.join(problems))
