import subprocess

minimum_mcstas_version = (3,8,8)
minimum_mcstasscript_version = (0,0,94)

_cache = [None]
def mcstas_info():
    if _cache[0] is not None:
        return _cache[0]
    import shutil
    def cmd(n):
        c = shutil.which(n)
        if not c:
            raise RuntimeError(f'Command not found: {n}')
        return c
    cmds = dict( (n,cmd(n)) for n in ['mcstas','mcrun','mctest','mcstas-pygen'] )
    o = subprocess.run( [cmds['mcstas'], "--version-num"],
                        check=True, capture_output=True,
                        text=True ).stdout.strip()
    major, minor, patch = o.split(".", 2)
    version = ( int(major), int(minor), int(patch) )
    if not version >= minimum_mcstas_version:
        needed = '.'.join(str(i) for i in minimum_mcstas_version)
        raise RuntimeError('Too old McStas found: '
                           f'{major}.{minor}.{patch} (needs {needed})')
    _cache[0] = { 'cmd' : cmds, 'version' : version }
    return _cache[0]

def check_mcstasscript_version():
    from importlib.metadata import PackageNotFoundError, version
    try:
        v = version('mcstasscript')
    except PackageNotFoundError:
        raise RuntimeError('McStasScript not found') from None
    needed = '.'.join(str(i) for i in minimum_mcstasscript_version)
    try:
        ok = tuple(int(i) for i in v.split('.')[:3]) >= minimum_mcstasscript_version
    except ValueError:
        ok = True  # unusual version string, e.g. a development version
    if not ok:
        raise RuntimeError(f'Too old McStasScript found: {v} (needs {needed})')

def get_nprocs( nice_factor = 0.9 ):
    import os
    if hasattr(os,'sched_getaffinity'):
        n = len(os.sched_getaffinity(0))
    else:
        import multiprocessing
        n = multiprocessing.cpu_count()
    n = min(1024,max(1,n))
    if n >= 4:
        #Be nice, leave a tiny bit for other tasks on the machine:
        n = round( n * nice_factor )
    return n
