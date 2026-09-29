"""Rules for local components (localcomps/) and data files (localdata/)."""

import fnmatch
import subprocess
from pathlib import Path

# Files allowed in localcomps/: components, and C libraries which they
# include (e.g. with %include "mylib" in a SHARE section).
LOCALCOMPS_PATTERNS = ['*.comp', '*.c', '*.h']

# Types of data files allowed in localdata/:
LOCALDATA_PATTERNS = [
    '*.ncmat',                # NCrystal materials (preferred for samples)
    '*.laz', '*.lau',         # PowderN / Single_crystal reflection lists
    '*.hkl',                  # reflection lists (e.g. Single_crystal)
    '*.cif',                  # crystal structures
    '*.rfl', '*.trm',         # McStas reflectivity/transmission tables
    '*.ref',                  # reflectivity curves
    '*.sqw',                  # S(q,w) tables (Isotropic_Sqw)
    '*.dat', '*.txt',         # generic tables (e.g. read with Table_Read)
    '*.off', '*.ply',         # geometry files (e.g. Union, Guide_anyshape)
    '*.mcpl', '*.mcpl.gz',    # MCPL particle lists
]

def subdir_patterns( prefix = '' ):
    """Patterns for the layout checks, e.g. 'localcomps/*.comp'."""
    return ( [ f'{prefix}localcomps/{p}' for p in LOCALCOMPS_PATTERNS ]
             + [ f'{prefix}localdata/{p}' for p in LOCALDATA_PATTERNS ] )

def standard_component_names( resourcedir ):
    """Names of the components in the McStas library (except examples)."""
    return { f.stem for f in _library_files( resourcedir, '*.comp' ) }

def standard_library_file_names( resourcedir ):
    """File names of the C libraries (*.c, *.h) in the McStas library (except
    examples), e.g. read_table-lib.c."""
    return { f.name for pattern in ('*.c', '*.h')
             for f in _library_files( resourcedir, pattern ) }

def _library_files( resourcedir, pattern ):
    resourcedir = Path(resourcedir)
    for f in resourcedir.rglob(pattern):
        if 'examples' not in f.relative_to(resourcedir).parts:
            yield f

def mcstas_resourcedir():
    from .util import mcstas_info
    mcrun = mcstas_info()['cmd']['mcrun']
    return subprocess.run( [ mcrun, '--showcfg=resourcedir' ],
                           capture_output = True, text = True,
                           check = True ).stdout.strip()

def check_local_components( info, resourcedir = None ):
    """Raise an error if a component (or C library file) in localcomps/ has
    the same name as a component (or C library file) in the McStas library,
    since it would shadow that."""
    files = info['extra_files'].get('localcomps', [])
    if not files:
        return
    if resourcedir is None:
        resourcedir = mcstas_resourcedir()
    std_comps = standard_component_names( resourcedir )
    std_libs = standard_library_file_names( resourcedir )
    shadowing = sorted(
        fn for fn in files
        if ( fnmatch.fnmatch(fn, '*.comp') and Path(fn).stem in std_comps )
        or ( not fnmatch.fnmatch(fn, '*.comp') and fn in std_libs ) )
    if shadowing:
        raise RuntimeError(
            'Files in localcomps/ must not have the same names as components'
            ' or C library files in the McStas library (which they would'
            ' shadow): ' + ', '.join(shadowing) + '. Please rename them (or'
            ' use the McStas library versions).')
