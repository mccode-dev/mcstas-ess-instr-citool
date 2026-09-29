import subprocess
import shlex
import json

def mctest_args( instrdir, testdir, mpi = None ):
    """Arguments for mctest. If mpi is an integer or "auto" (meaning the
    number of available processors), the instruments are compiled and run
    with MPI, using that number of processes."""
    cmd = [ '--strict' ]
    if mpi is not None:
        if mpi == 'auto':
            from .util import get_nprocs
            mpi = get_nprocs()
        cmd += [ '--mpi', str(int(mpi)) ]
    cmd += [ '--local', str(instrdir), '--testdir', str(testdir) ]
    return cmd

def runtest( info, outdir, mpi = None ):
    from .util import mcstas_info
    from .generate import generate
    from .localfiles import check_local_components
    mctest_cmd = mcstas_info()['cmd']['mctest']
    check_local_components( info )
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
    return res

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
