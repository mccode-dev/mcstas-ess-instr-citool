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
    resourcedir = Path(resourcedir)
    names = set()
    for f in resourcedir.rglob('*.comp'):
        if 'examples' in f.relative_to(resourcedir).parts:
            continue
        names.add(f.stem)
    return names

def mcstas_resourcedir():
    from .util import mcstas_info
    mcrun = mcstas_info()['cmd']['mcrun']
    return subprocess.run( [ mcrun, '--showcfg=resourcedir' ],
                           capture_output = True, text = True,
                           check = True ).stdout.strip()

def check_local_components( info, resourcedir = None ):
    """Raise an error if a component in localcomps/ has the same name as a
    component in the McStas library (it would shadow that component)."""
    comps = [ fn for fn in info['extra_files'].get('localcomps', [])
              if fnmatch.fnmatch(fn, '*.comp') ]
    if not comps:
        return
    if resourcedir is None:
        resourcedir = mcstas_resourcedir()
    standard = standard_component_names( resourcedir )
    shadowing = sorted( Path(fn).stem for fn in comps
                        if Path(fn).stem in standard )
    if shadowing:
        raise RuntimeError(
            'Local components must not have the same names as components'
            ' in the McStas library (which they would shadow): '
            + ', '.join(shadowing) + '. Please rename them (or use the'
            ' McStas library versions).')
