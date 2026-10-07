import json
import shlex
import subprocess

from .errors import CheckFailed, SetupError


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

#Neutrons per %Example test in the quick modes (the results are not compared
#with the expected values):
FAST_NCOUNT = 100

def runtest( info, outdir, mpi = None, mode = 'full' ):
    """Run the CI tests of the project. The mode is "full" (all checks and the
    %Example tests, as in CI), "fast" (the %Example tests with only
    FAST_NCOUNT neutrons, which must compile and run without crashing, but
    whose results are not compared with the expected ones) or "build" (the
    instruments are only compiled). The quick modes stop at the first
    failure, and do not run the tests in extra_pytests/."""
    assert mode in ('full','fast','build')
    from .generate import generate
    from .localfiles import check_local_components, check_local_data
    from .util import mcstas_info
    mctest_cmd = mcstas_info()['cmd']['mctest']
    from .modelcheck import modelcheck
    check_local_components( info )
    check_local_data( info )
    modeldir = outdir.joinpath('modelcheck')
    modeldir.mkdir()
    modelcheck( info, modeldir )
    instrdir = generate( info, outdir )
    testdir = outdir.joinpath('tests').absolute().resolve()
    if mode != 'full':
        return runtest_quick( mctest_cmd, instrdir, testdir, mpi, mode )
    cmd = mctest_args( instrdir, testdir, mpi )
    print(f"Launching: mctest {shlex.join(cmd)}", flush=True)
    ec = subprocess.run( [ mctest_cmd ] + cmd,
                         check = False, capture_output = False )
    if not ec.returncode==0:
        raise CheckFailed('mctest command failed')
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

def runtest_quick( mctest_cmd, instrdir, testdir, mpi, mode ):
    """The quick modes of runtest: test one instrument at a time, stopping at
    the first failure."""
    ncount = 0 if mode == 'build' else FAST_NCOUNT#mcrun only compiles for 0
    #generate() puts each instrument (with its extra files) in a subdirectory:
    instruments = []
    for d in sorted( p for p in instrdir.iterdir() if p.is_dir() ):
        for f in d.glob('*.instr'):
            instruments.append( ( f.stem, d ) )
    instruments.sort( key = lambda e : ( not e[0].endswith('_main'), e[0] ) )
    if not instruments:
        raise CheckFailed('no instruments found')
    testdir.mkdir( parents = True, exist_ok = True )#mctest creates the subdirs
    what = ( 'compile' if mode == 'build'
             else f'compile and run ({ncount} neutrons)' )
    if mode == 'build':
        print('Note: with 0 neutrons, the instruments are only compiled, and'
              ' mctest reports a RUNTIME ERROR for each test, which is'
              ' expected here.', flush = True)
    else:
        print('Note: with fewer neutrons, the results differ from the'
              ' expected values, which mctest reports (e.g. as BIG'
              ' DISCREPANCY), but which is expected here.', flush = True)
    for i, ( name, d ) in enumerate(instruments):
        print(f'\n=== ({i+1}/{len(instruments)}) {name}: {what}', flush = True)
        itestdir = testdir.joinpath(name)
        cmd = mctest_args( d, itestdir, mpi ) + [ '--ncount', str(ncount) ]
        print(f"Launching: mctest {shlex.join(cmd)}", flush=True)
        #The exit code is not used, since mctest fails when the results differ
        #from the expected values (as they do with fewer neutrons):
        subprocess.run( [ mctest_cmd ] + cmd, check = False )
        json_files = list(itestdir.glob('*/testresults_*.json'))
        if len(json_files) != 1:
            raise CheckFailed(f'{name}: mctest produced no (or several) results')
        res = json.loads(json_files[0].read_text())
        tests = { k : v for k, v in res.items() if k != '_meta' }
        problems = []
        if not tests:
            problems.append('no tests found (no %Example lines?)')
        for tname, t in sorted(tests.items()):
            if not t.get('compiled'):
                problems.append(f'{tname}: did not compile')
            elif mode == 'fast' and not t.get('didrun'):
                problems.append(f'{tname}: did not run (crashed?)')
        if problems:
            raise CheckFailed( f'{name} failed (stopping at the first failure):'
                               '\n  ' + '\n  '.join(problems) )
        print(f'=== {name}: OK ({len(tests)} test(s))', flush = True)
    print(f'\nAll {len(instruments)} instruments OK ({what})')

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
        raise SetupError("pytest is needed to run the tests in extra_pytests/")
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
        raise CheckFailed('pytest failed for the tests in extra_pytests/')

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
        raise CheckFailed('mctest results contain failures:\n  '
                          + '\n  '.join(problems))
