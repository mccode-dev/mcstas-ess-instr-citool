import subprocess
import shlex
import json

def runtest( info, outdir ):
    from .util import mcstas_info
    from .generate import generate
    do_mpi = False # FIXME make this work
    if do_mpi:
        from .util import get_nprocs
        nprocs = get_nprocs()
    mctest_cmd = mcstas_info()['cmd']['mctest']
    instrdir = generate( info, outdir )
    testdir = outdir.joinpath('tests').absolute().resolve()
    cmd = []
    cmd += [ '--strict' ]
    if do_mpi:
        cmd += ['--mpi', str(nprocs) ]
    cmd += [ '--local', str(instrdir), '--testdir', str(testdir) ]
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
    #TODO: Use the json results for anything?
    return res
